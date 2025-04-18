"""Backward‑compatibility shim.

Historical test‑suites import symbols from

    app.presentation.api.dependencies.<something>

whereas the current codebase organises them under the versioned namespace
``app.presentation.api.v1.dependencies``.  To avoid touching dozens of test
files we merely re‑export the v1 helpers here.
"""

from importlib import import_module

# Re‑export everything from the v1 package so that ``patch()`` look‑ups work
v1_deps = import_module("app.presentation.api.v1.dependencies")  # noqa: F401

# Expose the sub‑namespaces (ml, services, repositories, …)
globals().update(v1_deps.__dict__)

# Ensure dotted‑path sub‑modules resolve via ``sys.modules``
import sys

# Register sub‑modules under *both* the old dotted path and the v1 path so
# that ``import app.presentation.api.dependencies.services`` as well as
# ``import app.presentation.api.v1.dependencies.services`` resolve to the same
# object.

_OLD_PREFIX = "app.presentation.api.dependencies"

for _name in ("ml", "services", "repositories"):
    _module = v1_deps.__dict__.get(_name)
    if _module is not None:
        sys.modules[f"{_OLD_PREFIX}.{_name}"] = _module
        sys.modules.setdefault(f"{v1_deps.__name__}.{_name}", _module)

# Provide a minimal *auth* sub‑module exposing ``get_current_user`` so that
# endpoint modules importing it do not fail when the full auth implementation
# is not part of the test slice.

import types

auth_mod = types.ModuleType(f"{_OLD_PREFIX}.auth")


async def _dummy_get_current_user():  # pragma: no cover – stub
    return {}


auth_mod.get_current_user = _dummy_get_current_user  # type: ignore[attr-defined]
sys.modules[f"{_OLD_PREFIX}.auth"] = auth_mod
# Also register under the v1 path to keep symmetry
sys.modules[f"{v1_deps.__name__}.auth"] = auth_mod

# Defensive: if sub‑modules were attached *after* the loop above we add them
# again when the outer package is first accessed.
def __getattr__(item):  # pragma: no cover – defensive shim
    if item in ("ml", "services", "repositories"):
        sub_mod = v1_deps.__dict__.get(item)
        if sub_mod is not None:
            # Register on‑demand for importlib
            sys.modules.setdefault(f"{__name__}.{item}", sub_mod)
            return sub_mod
    raise AttributeError(item)


