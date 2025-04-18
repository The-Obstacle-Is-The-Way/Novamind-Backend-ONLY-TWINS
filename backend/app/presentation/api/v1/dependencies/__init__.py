"""Thin dependency‑injection shims for the API v1 layer.

This package exists primarily so that *tests* can import / patch call‑paths
such as

    app.presentation.api.v1.dependencies.ml.get_mentallama_service

without relying on the full DI container.  Each function returns a minimal
stub implementation that fulfils the interface expected by the unit and
integration tests.
"""

from __future__ import annotations

from types import ModuleType
import sys
from typing import Optional


def _lazy_submodule(name: str) -> ModuleType:  # pragma: no cover – helper
    """Create and register an empty module so that dotted imports succeed."""
    module = ModuleType(name)
    sys.modules[name] = module
    return module


# ---------------------------------------------------------------------------
# "ml" pseudo‑sub‑package
# ---------------------------------------------------------------------------

ml = _lazy_submodule(__name__ + ".ml")


def get_mentallama_service():  # noqa: D401 – simple factory
    """Return a stub MentalLLaMA service suitable for tests."""

    try:
        from app.infrastructure.services.mock_mentalllama_service import (  # type: ignore
            MockMentalLLaMAService,
        )
    except ModuleNotFoundError:  # fallback – define a trivial stub

        class MockMentalLLaMAService:  # type: ignore[too-many-public-methods]
            async def process(self, *args, **kwargs):
                return {"result": "ok"}

        return MockMentalLLaMAService()

    return MockMentalLLaMAService()


ml.get_mentallama_service = get_mentallama_service  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# "services" pseudo‑sub‑package
# ---------------------------------------------------------------------------

services = _lazy_submodule(__name__ + ".services")


def get_temporal_neurotransmitter_service():
    try:
        from app.infrastructure.services.mock_enhanced_digital_twin_core_service import (
            MockEnhancedDigitalTwinCoreService,
        )

        return MockEnhancedDigitalTwinCoreService()
    except ModuleNotFoundError:

        class StubService:  # fallback stub
            async def generate_time_series(self, *a, **kw):
                return {}

        return StubService()


services.get_temporal_neurotransmitter_service = (  # type: ignore[attr-defined]
    get_temporal_neurotransmitter_service
)


# Digital‑twin service shim (required by digital_twins endpoints)


def get_digital_twin_service():
    try:
        from app.infrastructure.services.mock_enhanced_digital_twin_core_service import (
            MockEnhancedDigitalTwinCoreService,
        )

        return MockEnhancedDigitalTwinCoreService()
    except ModuleNotFoundError:

        class StubDT:  # pragma: no cover – fallback
            async def generate(self, *_, **__):
                return {}

        return StubDT()


services.get_digital_twin_service = get_digital_twin_service  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# "repositories" pseudo‑sub‑package
# ---------------------------------------------------------------------------

repositories = _lazy_submodule(__name__ + ".repositories")


def get_patient_repository():
    try:
        from app.infrastructure.repositories.mock_patient_repository import (
            MockPatientRepository,
        )

        return MockPatientRepository()
    except ModuleNotFoundError:

        class StubRepo:  # pragma: no cover – fallback
            async def get_by_id(self, *_, **__):
                return None

        return StubRepo()


repositories.get_patient_repository = get_patient_repository  # type: ignore[attr-defined]
