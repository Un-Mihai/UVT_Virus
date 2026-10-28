"""Reads typed facts from every page, keeping only facts whose quote is really on the page."""

import asyncio
from collections import Counter

from app.ai.client import AIClient
from app.personal_data import MaskedText, mask_for_model
from app.romanian import quote_in_page
from app.verification.context import DocumentView, PageView, VerificationContext
from app.verification.facts import (
    AMOUNT_KINDS,
    DOCUMENT_TYPES,
    ExtractedAmount,
    ExtractedValue,
    PageFacts,
)
from app.verification.findings import CERTAIN, Evidence, FindingDraft
from app.verification.messages import message
from app.vocabulary import Severity

# Bump when the prompt or PageFacts changes: cached facts from older versions are re-extracted.
PROMPT_VERSION = "page-facts-v1"

INSTRUCTIONS = f"""You read one page of a Romanian funding or procurement document and extract facts.
Rules:
- Copy every value exactly as written on the page (keep "1.234.567,89", keep "RO 123456").
- Every fact needs `quote`: the exact sentence or table row from the page that contains the value.
- Never compute, convert or correct a value. Leave out what is not on the page.
- document_type is one of: {", ".join(DOCUMENT_TYPES)}; null when the page does not say.
- amount kind is one of: {", ".join(AMOUNT_KINDS)}.
- Text like [CNP#1a2b3c] stands for a masked personal identifier; copy it unchanged."""


class FactExtractionAgent:
    name = "extraction"

    def __init__(self, ai: AIClient, concurrency: int) -> None:
        self._ai = ai
        self._limit = asyncio.Semaphore(concurrency)

    @property
    def version(self) -> str:
        return f"{PROMPT_VERSION}:{self._ai.chat_model}"

    async def run(self, context: VerificationContext) -> list[FindingDraft]:
        pending = [
            (document, page)
            for document in context.documents
            for page in document.pages
            if page.text.strip() and page.facts_version != self.version
        ]
        await asyncio.gather(*(self._extract(context, page) for _, page in pending))
        for document in context.documents:
            document.document_type = _majority_type(document) or document.document_type
        return [
            _unreadable_page_finding(document, page)
            for document in context.documents
            for page in document.pages
            if page.is_scan and not page.text.strip()
        ]

    async def _extract(self, context: VerificationContext, page: PageView) -> None:
        masked = mask_for_model(page.text, context.hasher)
        async with self._limit:
            facts = await self._ai.complete(
                purpose="extract page facts",
                messages=[
                    {"role": "system", "content": INSTRUCTIONS},
                    {"role": "user", "content": masked.text},
                ],
                schema=PageFacts,
            )
        page.facts = _verified(facts, masked, page.text)
        page.facts_version = self.version
        page.facts_changed = True


def _verified(facts: PageFacts, masked: MaskedText, page_text: str) -> PageFacts:
    """Drops facts whose quote is not on the page, or whose value is not in its quote."""
    parties = []
    for party in facts.parties:
        quote = masked.restore(party.quote)
        if quote_in_page(quote, page_text) and (
            party.cui is None or quote_in_page(party.cui, quote)
        ):
            parties.append(party.model_copy(update={"quote": quote}))
    return PageFacts(
        document_type=facts.document_type if facts.document_type in DOCUMENT_TYPES else None,
        parties=parties,
        ibans=_quoted_values(facts.ibans, masked, page_text),
        amounts=_quoted_values(facts.amounts, masked, page_text),
        dates=_quoted_values(facts.dates, masked, page_text),
    )


def _quoted_values[V: (ExtractedValue, ExtractedAmount)](
    items: list[V], masked: MaskedText, page_text: str
) -> list[V]:
    kept = []
    for item in items:
        quote, value = masked.restore(item.quote), masked.restore(item.value)
        if quote_in_page(quote, page_text) and quote_in_page(value, quote):
            kept.append(item.model_copy(update={"quote": quote, "value": value}))
    return kept


def _majority_type(document: DocumentView) -> str | None:
    types = Counter(
        page.facts.document_type
        for page in document.pages
        if page.facts and page.facts.document_type and page.facts.document_type != "other"
    )
    return types.most_common(1)[0][0] if types else None


def _unreadable_page_finding(document: DocumentView, page: PageView) -> FindingDraft:
    """A scanned page OCR could not read (or OCR is off): nobody checked it."""
    reason, recommendation = message(
        "page_unreadable", page=page.number, document=document.filename
    )
    return FindingDraft(
        rule_code="extraction.unreadable_page",
        agent="extraction",
        severity=Severity.WARN,
        confidence=CERTAIN,
        reason=reason,
        recommendation=recommendation,
        evidence=Evidence(document.id, page.number, ""),
    )
