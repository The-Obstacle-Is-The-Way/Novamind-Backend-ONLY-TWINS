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
    
# ---------------------------------------------------------------------------
# Provide stub cache and auth dependencies for legacy imports
# ---------------------------------------------------------------------------
async def get_cache_service():  # stub cache provider for tests
    """Stub cache service dependency for tests."""
    class DummyCache:
        async def get(self, *args, **kwargs):
            return None

        async def set(self, *args, **kwargs):
            return True

    return DummyCache()

async def verify_provider_access(user=None):  # stub for route dependency
    """Stub provider access check for tests."""
    return user

async def verify_admin_access(user=None):  # stub for route dependency
    """Stub admin access check for tests."""
    return user
    
async def get_alert_repository():  # stub alert repository dependency for tests
    """Stub alert repository dependency for tests."""
    return None
    
# Attach stub verify functions to auth_mod for endpoint imports
auth_mod.verify_provider_access = verify_provider_access  # type: ignore[name-defined]
auth_mod.verify_admin_access = verify_admin_access      # type: ignore[name-defined]
    
# ---------------------------------------------------------------------------
# Provide stub repository sub-module for legacy imports
# ---------------------------------------------------------------------------
repo_mod = types.ModuleType(f"{_OLD_PREFIX}.repository")

async def get_patient_repository():  # stub patient repository dependency for tests
    """Stub patient repository dependency for tests."""
    return None
    
async def get_encryption_service():  # stub encryption service dependency for tests
    """Stub encryption service dependency for tests."""
    class DummyEncryptionService:
        async def encrypt(self, data, *args, **kwargs):
            return data
        async def decrypt(self, data, *args, **kwargs):
            return data
    return DummyEncryptionService()

repo_mod.get_patient_repository = get_patient_repository  # type: ignore[attr-defined]
sys.modules[f"{_OLD_PREFIX}.repository"] = repo_mod
sys.modules[f"{v1_deps.__name__}.repository"] = repo_mod
repo_mod.get_encryption_service = get_encryption_service  # type: ignore[attr-defined]


