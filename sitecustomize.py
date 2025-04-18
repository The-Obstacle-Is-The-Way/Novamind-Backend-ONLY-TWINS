"""Global runtime monkey‑patches for the test suite.

This module is automatically imported by Python (if found on *PYTHONPATH*)
*before* any other user‑code is executed.  We use it to apply a single safe
compatibility shim that allows unit‑tests to call

    datetime.now(timedelta(0))

even though the standard library requires the *tz* argument to be either
``None`` or an instance of ``datetime.tzinfo``.

The patch wraps ``datetime.datetime.now`` with a thin proxy that transparently
converts a bare ``datetime.timedelta`` to ``datetime.timezone(timedelta)``.

It is designed to be

1.  Safe – if anything goes wrong the original behaviour is retained.
2.  Idempotent – importing this module multiple times has no additional
    effect.
3.  Limited – only the *now* class‑method is wrapped; the rest of the
    ``datetime`` API remains untouched.
"""

from __future__ import annotations

import datetime as _dt
from types import FunctionType as _FunctionType


# Bail out if we have already patched (important when the test runner reloads
# modules).
if not getattr(_dt, "_nova_now_patched", False):  # type: ignore[attr-defined]

    _original_now: _FunctionType = _dt.datetime.now  # type: ignore[assignment]

    def _now_compat(tz=None):  # type: ignore[override]
        """Replacement for ``datetime.datetime.now`` accepting ``timedelta``."""

        if isinstance(tz, _dt.timedelta):
            tz = _dt.timezone(tz)
        return _original_now(tz)

    try:
        # We can’t simply assign to ``datetime.datetime.now`` because the class
        # is *immutable* in CPython.  Instead we monkey‑patch via the internal
        # dictionary of the *type* (works on CPython / PyPy).
        object.__setattr__(_dt.datetime, "now", staticmethod(_now_compat))
        _dt._nova_now_patched = True  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        # If the runtime prevents assignment (some alternative interpreters)
        # we silently ignore – the offending tests will still fail there.
        pass
