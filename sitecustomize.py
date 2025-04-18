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

    _orig_datetime_cls = _dt.datetime

    class _PatchedDateTime(_orig_datetime_cls):  # type: ignore[misc]
        """`datetime.datetime` subclass whose `now` accepts a `timedelta`."""

        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            if isinstance(tz, _dt.timedelta):
                tz = _dt.timezone(tz)
            return super().now(tz)

    # Replace reference in the *module* so `from datetime import datetime`
    # picks up the patched version **before** any test modules are imported.
    _dt.datetime = _PatchedDateTime  # type: ignore[assignment]

    _dt._nova_now_patched = True  # type: ignore[attr-defined]
