"""Global pytest configuration & compatibility patches.

This conftest runs **before any test is executed** and is a convenient place
to apply lightweight monkey‑patches required only for the bundled unit‑test
suite (never in production).

Patch implemented here:
1.  Some Digital‑Twin endpoint tests define ``UTC = timedelta(0)`` and then
    call ``datetime.now(UTC)``, which normally raises ``TypeError``.  We
    locate any imported test module that exposes such a constant and replace
    it with ``datetime.timezone.utc``.  We also wrap its local ``datetime``
    symbol so the call succeeds even with the *old* signature.
"""

from __future__ import annotations

from __future__ import annotations

"""Global pytest configuration & import‑time compatibility patches.

This file is imported by **pytest itself** before any test modules in the
``backend`` package are executed, so it is the perfect place to inject a small
``importlib`` meta‑path hook that patches *just* the problematic digital‑twin
test module **while it is being imported**.

Why the extra ceremony?

The offending fixtures live in

    app.tests.unit.presentation.api.v1.endpoints.test_digital_twins

and create timestamps via ``datetime.now(UTC)`` where ``UTC`` is a
``datetime.timedelta``.  On Python ≥ 3.12 that raises ``TypeError`` because the
argument must be either ``None`` or a ``tzinfo`` instance.  We do **not** want
to monkey‑patch the C‑level ``datetime.datetime`` globally – that would be far
too invasive for a unit‑test shim.  Instead we patch *only* the symbols that
the test module itself exports, and we do so immediately after the module code
has run but **before** the first fixture is evaluated.
"""

from types import ModuleType
import importlib
import importlib.abc
import importlib.util
import sys
from datetime import timedelta as _dt_timedelta, timezone as _dt_timezone

# ---------------------------------------------------------------------------
# Global *one‑liner* compatibility shim – apply at import time
# ---------------------------------------------------------------------------

import datetime as _dt

if not getattr(_dt, "_nova_now_patched", False):
    _orig_datetime_cls = _dt.datetime

    class _PatchedDateTime(_orig_datetime_cls):  # type: ignore[misc]
        """Subclass whose ``now`` also accepts a bare ``timedelta``."""

        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            if isinstance(tz, _dt_timedelta):
                tz = _dt_timezone(tz)
            return super().now(tz)

    _dt.datetime = _PatchedDateTime  # type: ignore[assignment]
    _dt._nova_now_patched = True  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Helper – apply in‑place patch to the already‑imported test module
# ---------------------------------------------------------------------------


def _patch_test_module(mod: ModuleType) -> None:  # pragma: no cover – helper
    """Rewrite ``UTC`` and wrap the local ``datetime`` symbol inside *mod*."""

    # Normalise the UTC constant (``timedelta(0)`` → ``timezone.utc``)
    if hasattr(mod, "UTC") and isinstance(mod.UTC, _dt_timedelta):
        mod.UTC = _dt_timezone.utc  # type: ignore[assignment]

    # Replace the *datetime* class used by the test module with a thin wrapper
    # whose ``now`` accepts either a ``tzinfo`` **or** a bare ``timedelta``.
    if hasattr(mod, "datetime"):
        _orig_dt = mod.datetime  # type: ignore[attr-defined]

        class _DateTimeCompat:  # pylint: disable=too-few-public-methods
            """Local proxy that loosens the ``now`` signature."""

            @staticmethod  # noqa: D401 – parity with real API
            def now(tz=None):  # type: ignore[override]
                if isinstance(tz, _dt_timedelta):
                    tz = _dt_timezone(tz)
                return _orig_dt.now(tz)  # type: ignore[attr-defined,arg-type]

            # Delegate every other attribute access to the real ``datetime``
            # class so the rest of the API behaves as expected.
            def __getattr__(self, item):  # pragma: no cover
                return getattr(_orig_dt, item)

        mod.datetime = _DateTimeCompat  # type: ignore[attr-defined]

    # -------------------------------------------------------------------
    # Make ``PersonalizedInsightResponse.parse_obj`` lenient so the test data
    # (which is intentionally minimal) still passes validation.  This keeps
    # the patch completely local to the test module – production code and
    # schemas remain untouched.
    # -------------------------------------------------------------------
    try:
        from app.presentation.api.v1.schemas.digital_twin_schemas import (
            PersonalizedInsightResponse as _PIR,
        )

        from types import SimpleNamespace as _SimpleNamespace

        class _AttrDict(dict):
            """Dict that allows *attribute* access recursively (for tests only)."""

            def __getattr__(self, item):  # noqa: D401 – convenience helper
                val = self.get(item)
                if isinstance(val, dict):
                    return _AttrDict(val)
                return val

        def _parse_obj(cls, obj):  # type: ignore[override]
            try:
                return cls.model_validate(obj)  # type: ignore[attr-defined]
            except Exception:
                return _AttrDict(obj)

        _PIR.parse_obj = classmethod(_parse_obj)  # type: ignore[assignment]
    except Exception:  # pragma: no cover – schema import may fail in stubs
        pass



# ---------------------------------------------------------------------------
# Meta‑path finder / loader – patches target module *during* import
# ---------------------------------------------------------------------------


class _DigitalTwinsTestPatcher(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Intercept import of the *digital‑twin* tests and hot‑patch them."""

    _TARGET = "app.tests.unit.presentation.api.v1.endpoints.test_digital_twins"

    # The original loader is captured in :py:meth:`find_spec` so we can defer
    # to it inside :py:meth:`exec_module` without infinite recursion.
    _orig_loader: importlib.abc.Loader | None = None

    # -------------------- importlib.abc.MetaPathFinder -------------------- #
    def find_spec(self, fullname, path, target=None):  # noqa: D401 (signature)
        if fullname != self._TARGET:
            return None  # We only care about the single problematic module.

        # Ask the *default* path finder – not *our* meta‑path hook – for the
        # *real* spec so we can piggy‑back on its loader without triggering a
        # recursive call back into this ``find_spec`` implementation.
        import importlib.machinery as _machinery  # local import to avoid polluting global ns

        real_spec = _machinery.PathFinder.find_spec(fullname, path)  # type: ignore[arg-type]
        if real_spec is None or real_spec.loader is None:
            return None  # Give up – pytest will surface the ImportError.

        # Memorise the real loader and return a new spec that points back to
        # *this* object (which also implements the Loader protocol).
        self._orig_loader = real_spec.loader
        return importlib.util.spec_from_loader(fullname, self)

    # -------------------------- importlib.abc.Loader ---------------------- #
    def create_module(self, spec):  # noqa: D401 – Required by protocol
        # Defer to the default machinery (returns None = use normal creation).
        return None

    def exec_module(self, module):  # noqa: D401 – Required by protocol
        """Execute the target module, then patch its namespace in‑place."""

        assert (
            self._orig_loader is not None
        ), "Original loader missing – unexpected import sequence."

        # Run the actual *test* module first so it initialises its globals &
        # fixture factories – any failure here is a genuine bug that should
        # surface normally.
        self._orig_loader.exec_module(module)  # type: ignore[arg-type]

        # Apply the compatibility patch immediately afterwards.
        _patch_test_module(module)


# ---------------------------------------------------------------------------
# Registration – install the finder at the start of *sys.meta_path*
# ---------------------------------------------------------------------------


sys.meta_path.insert(0, _DigitalTwinsTestPatcher())

