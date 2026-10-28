"""Judges the documents against each regulation clause an admin wrote as an "ai" rule."""

import asyncio
import json
from decimal import Decimal

from pydantic import BaseModel

from app.ai.client import AIClient
from app.personal_data import MaskedText, mask_for_model
from app.romanian import quote_in_page
from app.verification.context import RuleView, VerificationContext
from app.verification.findings import Evidence, FindingDraft
from app.vocabulary import RuleKind, Severity

INSTRUCTIONS = """You check a funding application against ONE rule of a regulation.
Report only clear violations of that rule, each with:
- document_id and page where the problem is, and `quote`: the exact text from that page;
- reason: one sentence a reviewer understands; recommendation: the change that fixes it.
  Write both in English (reason_en, recommendation_en) and Romanian (reason_ro,
  recommendation_ro), saying the same thing;
- severity: "bad" for a definite breach, "warn" when it needs a person's look;
- confidence between 0 and 1 that this really breaks the rule.
Return no violations when the documents comply or the rule does not apply.
Never compute sums or compare dates yourself; quote what you rely on.
Text like [CNP#1a2b3c] stands for a masked personal identifier."""


class Violation(BaseModel):
    document_id: int
    page: int
    quote: str
    reason_en: str
    reason_ro: str
    recommendation_en: str
    recommendation_ro: str
    severity: str
    confidence: float


class ComplianceVerdict(BaseModel):
    violations: list[Violation]


class RegulationComplianceAgent:
    name = "compliance"

    def __init__(self, ai: AIClient, concurrency: int, context_chars: int) -> None:
        self._ai = ai
        self._limit = asyncio.Semaphore(concurrency)
        self._context_chars = context_chars

    async def run(self, context: VerificationContext) -> list[FindingDraft]:
        rules = context.rules_of(RuleKind.AI)
        if not rules:
            return []
        documents = _documents_for_model(context, self._context_chars * 2 // 3)
        regulation = context.regulation_text[: self._context_chars // 3]
        results = await asyncio.gather(
            *(self._judge(context, rule, documents, regulation) for rule in rules)
        )
        return [finding for findings in results for finding in findings]

    async def _judge(
        self, context: VerificationContext, rule: RuleView, documents: MaskedText, regulation: str
    ) -> list[FindingDraft]:
        prompt = "\n\n".join(
            [
                f"RULE {rule.code}: {rule.title}\n{rule.description}",
                f"REGULATION EXCERPT:\n{regulation or '(none uploaded)'}",
                f"APPLICATION FORM:\n{json.dumps(context.form, ensure_ascii=False)}",
                f"DOCUMENTS:\n{documents.text}",
            ]
        )
        async with self._limit:
            verdict = await self._ai.complete(
                purpose=f"compliance {rule.code}",
                messages=[
                    {"role": "system", "content": INSTRUCTIONS},
                    {"role": "user", "content": prompt},
                ],
                schema=ComplianceVerdict,
            )
        return [
            draft
            for violation in verdict.violations
            if (draft := _verified(context, rule, violation, documents)) is not None
        ]


def _documents_for_model(context: VerificationContext, limit: int) -> MaskedText:
    # shortcut: the first `limit` characters only; use pgvector retrieval per rule when files
    # outgrow the context window (references/pgvector.md in the document-verification skill).
    parts = []
    for document in context.documents:
        parts.append(
            f"=== document_id {document.id}: {document.filename} "
            f"({document.document_type or 'unknown type'}) ==="
        )
        parts += [f"--- page {page.number} ---\n{page.text}" for page in document.pages]
    return mask_for_model("\n".join(parts)[:limit], context.hasher)


def _verified(
    context: VerificationContext, rule: RuleView, violation: Violation, masked: MaskedText
) -> FindingDraft | None:
    """The violation as a finding, or None when its quote is not on the page it names."""
    document = context.document(violation.document_id)
    page = document.page(violation.page) if document else None
    quote = masked.restore(violation.quote)
    if page is None or not quote_in_page(quote, page.text):
        return None
    severity = Severity(violation.severity) if violation.severity in Severity else rule.severity
    confidence = min(max(Decimal(str(violation.confidence)), Decimal(0)), Decimal(1))
    return FindingDraft(
        rule_code=rule.code,
        agent="compliance",
        severity=severity,
        confidence=confidence.quantize(Decimal("0.001")),
        reason={"en": violation.reason_en, "ro": violation.reason_ro},
        recommendation={"en": violation.recommendation_en, "ro": violation.recommendation_ro},
        evidence=Evidence(violation.document_id, violation.page, quote),
    )
