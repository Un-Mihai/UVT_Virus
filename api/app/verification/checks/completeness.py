from pydantic import BaseModel

from app.verification.checks.common import finding
from app.verification.checks.registry import register_check
from app.verification.context import RuleView, VerificationContext
from app.verification.facts import DOCUMENT_TYPES
from app.verification.findings import FindingDraft
from app.verification.messages import document_type_name


class RequiredDocumentsParams(BaseModel):
    document_types: list[str]  # from app.verification.facts.DOCUMENT_TYPES


@register_check(
    "completeness.required_documents",
    {
        "en": f"Each listed document type is among the uploads. Types: {', '.join(DOCUMENT_TYPES)}.",
        "ro": "Fiecare tip de document din listă se află printre documentele încărcate. Tipuri:"
        f" {', '.join(DOCUMENT_TYPES)}.",
    },
    RequiredDocumentsParams,
)
def required_documents(
    context: VerificationContext, rule: RuleView, params: RequiredDocumentsParams
) -> list[FindingDraft]:
    present = {document.document_type for document in context.documents}
    return [
        finding(rule, "document_missing", document_type=document_type_name(required))
        for required in params.document_types
        if required not in present
    ]
