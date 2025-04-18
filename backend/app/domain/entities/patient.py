"""Domain entity representing a patient.

This module defines the *pure* domain model for a patient.  Earlier revisions
of the codebase represented a person's name with separate ``first_name`` and
``last_name`` fields, while newer code – including the patient‑repository test
suite we are currently fixing – passes a single ``name`` string instead.

To maintain backwards‑compatibility we therefore support **both** calling
styles:

1.  ``Patient(id=uuid4(), name="Jane Doe", ...)``
2.  ``Patient(id=uuid4(), first_name="Jane", last_name="Doe", ...)``

If only the **full** name is provided we split it on whitespace to populate
``first_name`` / ``last_name``; if only the *parts* are provided we join them
to synthesise the ``name`` field.  When all three are supplied we leave the
values untouched – caller wins.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class Patient:
    """Core domain model for a patient."""

    # ------------------------------------------------------------------
    # Required (non‑default) attributes – these have to come first so the
    # dataclass‑generated ``__init__`` does not raise the classic *non‑default
    # argument follows default argument* error.
    # ------------------------------------------------------------------

    id: str
    date_of_birth: datetime | str
    gender: str

    # ------------------------------------------------------------------
    # Dual‑API identification fields
    # ------------------------------------------------------------------

    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    # ------------------------------------------------------------------
    # Contact & administrative info
    # ------------------------------------------------------------------

    # Composite contact info for flexibility (e.g. {'email': ..., 'phone': ...})
    contact_info: dict[str, Any] = field(default_factory=dict)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    insurance_number: Optional[str] = None

    # ------------------------------------------------------------------
    # Clinical data
    # ------------------------------------------------------------------

    diagnoses: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    medical_history: list[str] = field(default_factory=list)
    treatment_notes: list[dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Audit timestamps
    # ------------------------------------------------------------------

    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None

    # ------------------------------------------------------------------
    # Post‑initialisation normalisation helpers
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:  # noqa: C901 – complexity is acceptable here
        """Normalise fields and ensure correct data types."""

        # 1. Harmonise the name fields -------------------------------------------------
        if self.name and not (self.first_name or self.last_name):
            parts = self.name.split()
            if parts:
                self.first_name = parts[0]
                if len(parts) > 1:
                    self.last_name = parts[-1]

        if not self.name and (self.first_name or self.last_name):
            self.name = " ".join(p for p in (self.first_name, self.last_name) if p)

        # 2. Timestamps ----------------------------------------------------------------
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

        # 3. Datetime parsing convenience ---------------------------------------------

        def _ensure_datetime(value: datetime | str | None) -> datetime | str | None:
            if value is None or isinstance(value, datetime):
                return value

            # Try ISO‑8601 first; fall back to simple YYYY‑MM‑DD.
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                try:
                    return datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    return value  # leave unchanged – caller can handle

        self.date_of_birth = _ensure_datetime(self.date_of_birth)
        self.created_at = _ensure_datetime(self.created_at)  # type: ignore[arg-type]
        self.updated_at = _ensure_datetime(self.updated_at)  # type: ignore[arg-type]

    # ------------------------------------------------------------------
    # Dunder helpers – mostly for debug / logging purposes
    # ------------------------------------------------------------------

    def __str__(self) -> str:  # pragma: no cover – trivial
        return f"Patient<{self.id}> {self.name or ''}".strip()

    def __repr__(self) -> str:  # pragma: no cover – trivial
        return (
            "Patient(id={!r}, name={!r}, first_name={!r}, last_name={!r})".format(
                self.id, self.name, self.first_name, self.last_name
            )
        )

    # Hashing: we consider the *id* to be the immutable primary key.
    def __hash__(self) -> int:  # pragma: no cover – required for set() in tests
        return hash(self.id)
