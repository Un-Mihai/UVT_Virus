"""Runs agents in stages and turns their drafts into findings with highlight boxes."""

import asyncio
from collections.abc import Sequence
from decimal import Decimal

from app.ai.client import AIClient
from app.config import Settings
from app.pdf import line_boxes, locate_words
from app.verification.agents.base import VerificationAgent
from app.verification.agents.compliance import RegulationComplianceAgent
from app.verification.agents.extraction import FactExtractionAgent
from app.verification.context import VerificationContext
from app.verification.findings import FindingDraft, ResolvedFinding


class VerificationOrchestrator:
    """Stages run in order; the agents inside one stage run concurrently.

    Later stages read what earlier ones put in the context (extracted facts), so a new agent
    goes into the stage after the data it needs.
    """

    def __init__(self, stages: Sequence[Sequence[VerificationAgent]]) -> None:
        self.stages = stages

    async def run(self, context: VerificationContext) -> list[ResolvedFinding]:
        drafts: list[FindingDraft] = []
        for stage in self.stages:
            results = await asyncio.gather(*(agent.run(context) for agent in stage))
            drafts += [draft for result in results for draft in result]
        return [_resolve(context, draft) for draft in drafts]


def default_orchestrator(ai: AIClient, settings: Settings) -> VerificationOrchestrator:
    """Facts first, then the documents against the regulations (with the code checks the
    model asks for). The same agents serve both scopes; the scope decides which regulations."""
    concurrency = settings.verification_concurrency
    return VerificationOrchestrator(
        [
            [FactExtractionAgent(ai, concurrency)],
            [RegulationComplianceAgent(ai, concurrency, settings.compliance_context_chars)],
        ]
    )


def _resolve(context: VerificationContext, draft: FindingDraft) -> ResolvedFinding:
    """Highlight boxes for the evidence; on an OCR'd page, confidence capped by the reading.

    A misread digit must not reach a client as a certain error, so evidence read by OCR is at
    most as certain as its least certain word (the page's mean when the quote is not found).
    """
    evidence = draft.evidence
    document = context.document(evidence.document_id) if evidence else None
    page = document.page(evidence.page) if document and evidence else None
    target = (evidence.locate or evidence.quote) if evidence else ""
    if page is None or not target:
        return ResolvedFinding(draft, [], draft.confidence, ocr=False)
    matched = locate_words(page.words, target) or []
    rects = line_boxes(matched)
    if not page.is_scan:
        return ResolvedFinding(draft, rects, draft.confidence, ocr=False)
    read = [word.confidence for word in matched if word.confidence is not None]
    cap = Decimal(str(min(read))) if read else (page.ocr_confidence or Decimal(0))
    confidence = min(draft.confidence, cap).quantize(Decimal("0.001"))
    return ResolvedFinding(draft, rects, confidence, ocr=True)
