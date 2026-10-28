"""The client's application form, and how it is stored without personal identifiers in clear."""

from typing import Any

from pydantic import BaseModel

from app.models import PersonalIdentifier
from app.personal_data import IdentifierHasher
from app.romanian import is_valid_cnp


class ApplicationForm(BaseModel):
    """What the client fills in. Values are kept as written; checks parse them in code.

    Add a field here and a check in app/verification/checks to compare it with the documents.
    """

    applicant_name: str
    applicant_cui: str | None = None
    legal_representative_name: str | None = None
    # Write-only: stored as a keyed hash and a masked copy, never in clear.
    legal_representative_cnp: str | None = None
    requested_amount: str | None = None  # as written, e.g. "1.234.567,89"
    iban: str | None = None
    start_date: str | None = None  # "28.10.2026"
    end_date: str | None = None


def stored_form(
    project_id: int, form: ApplicationForm, hasher: IdentifierHasher
) -> tuple[dict[str, Any], list[PersonalIdentifier]]:
    """The JSON to store on the project, and the form's personal identifiers as hashes."""
    data = form.model_dump(exclude={"legal_representative_cnp"})
    identifiers = []
    if cnp := (form.legal_representative_cnp or "").strip():
        data["legal_representative_cnp_masked"] = hasher.mask(cnp)
        identifiers.append(
            PersonalIdentifier(
                project_id=project_id,
                document_id=None,
                page=None,
                kind="cnp",
                value_hash=hasher.hash("cnp", cnp),
                masked=hasher.mask(cnp),
                valid=is_valid_cnp(cnp),
            )
        )
    return data, identifiers
