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
from datetime import datetime, date
from typing import Any, Optional
from app.domain.value_objects.emergency_contact import EmergencyContact


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
    # Gender is optional in integration scenarios
    gender: Optional[str] = None

    # ------------------------------------------------------------------
    # Dual‑API identification fields
    # ------------------------------------------------------------------

    # Full patient name (optional – may be derived from first_name/last_name)
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
    # Additional PHI & administrative fields
    emergency_contact: Optional[EmergencyContact] = None
    insurance: Optional[dict[str, Any]] = None
    insurance_info: Optional[dict[str, Any]] = None
    active: bool = True
    created_by: Any = None

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

        def _ensure_datetime(value: datetime | str | None) -> datetime | date | str | None:
            # Accept date or datetime as already valid
            if value is None or isinstance(value, (datetime, date)):
                return value
            # Handle simple date strings (YYYY-MM-DD)
            if isinstance(value, str):
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    pass
                # Try ISO‑8601 datetime string
                try:
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError:
                    pass
                # Fallback to simple date parsing
                try:
                    return datetime.strptime(value, "%Y-%m-%d").date()
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
    
    # ------------------------------------------------------------------
    # Helper methods for updating patient data
    # ------------------------------------------------------------------
    def update_contact_info(self, email: str | None = None, phone: str | None = None, address: str | None = None) -> None:
        """Update contact fields and refresh updated_at timestamp."""
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address
        self.updated_at = datetime.now()

    def add_medical_history_item(self, item: str) -> None:
        """Add an item to medical_history and refresh updated_at."""
        self.medical_history.append(item)
        self.updated_at = datetime.now()

    def add_medication(self, medication: str) -> None:
        """Add a medication and refresh updated_at."""
        self.medications.append(medication)
        self.updated_at = datetime.now()

    def add_allergy(self, allergy: str) -> None:
        """Add an allergy if not existing and refresh updated_at."""
        if allergy not in self.allergies:
            self.allergies.append(allergy)
            self.updated_at = datetime.now()

    def add_treatment_note(self, note: dict) -> None:
        """Add a treatment note with timestamp and refresh updated_at."""
        entry = dict(note)
        entry["date"] = datetime.now()
        self.treatment_notes.append(entry)
        self.updated_at = datetime.now()
