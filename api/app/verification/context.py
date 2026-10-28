"""Everything one verification run reads, loaded once. Agents never touch the database."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, undefer

from app.models import (
    DocumentPage,
    PersonalIdentifier,
    Project,
    ProjectDocument,
    RegulationDocument,
    RegulationRule,
)
from app.pdf import Word
from app.personal_data import IdentifierHasher
from app.verification.facts import PageFacts
from app.vocabulary import RuleKind, Scope, Severity


@dataclass
class PageView:
    id: int
    number: int
    text: str
    words: list[Word]
    is_scan: bool  # no text layer: `text` and `words` come from OCR, when it could read them
    ocr_confidence: Decimal | None
    facts: PageFacts | None
    facts_version: str | None
    facts_changed: bool = False  # set by the extraction agent; the runner saves the cache


@dataclass
class DocumentView:
    id: int
    filename: str
    document_type: str | None
    pages: list[PageView]

    def page(self, number: int) -> PageView | None:
        return next((page for page in self.pages if page.number == number), None)


@dataclass(frozen=True)
class IdentifierView:
    document_id: int | None  # None: from the application form
    page: int | None
    kind: str
    value_hash: str
    masked: str
    valid: bool
    start: int | None
    end: int | None


@dataclass(frozen=True)
class RuleView:
    code: str
    title: str
    description: str
    kind: RuleKind
    check_id: str | None
    params: dict[str, Any]
    severity: Severity


@dataclass
class VerificationContext:
    project_id: int
    project_title: str
    form: dict[str, Any]
    scope: Scope
    documents: list[DocumentView]
    identifiers: list[IdentifierView]
    rules: list[RuleView]
    regulation_text: str
    hasher: IdentifierHasher
    notes: dict[str, Any] = field(default_factory=dict)  # free space for agents in later stages

    def document(self, document_id: int) -> DocumentView | None:
        return next((doc for doc in self.documents if doc.id == document_id), None)

    def page_facts(self) -> Iterator[tuple[DocumentView, PageView, PageFacts]]:
        for document in self.documents:
            for page in document.pages:
                if page.facts is not None:
                    yield document, page, page.facts

    def rules_of(self, kind: RuleKind) -> list[RuleView]:
        return [rule for rule in self.rules if rule.kind == kind]


async def load_context(
    session: AsyncSession, project_id: int, scope: Scope, hasher: IdentifierHasher
) -> VerificationContext:
    project = await session.get_one(
        Project,
        project_id,
        options=[selectinload(Project.documents).selectinload(ProjectDocument.pages)],
    )
    rules = await session.scalars(
        select(RegulationRule)
        .where(
            RegulationRule.project_type_id == project.project_type_id,
            RegulationRule.verification_scope == scope,
            RegulationRule.active,
        )
        .order_by(RegulationRule.id)
    )
    regulations = await session.scalars(
        select(RegulationDocument)
        .options(undefer(RegulationDocument.text))
        .where(
            RegulationDocument.project_type_id == project.project_type_id,
            RegulationDocument.verification_scope == scope,
        )
        .order_by(RegulationDocument.id)
    )
    identifiers = await session.scalars(
        select(PersonalIdentifier)
        .where(PersonalIdentifier.project_id == project_id)
        .order_by(PersonalIdentifier.id)
    )
    return VerificationContext(
        project_id=project.id,
        project_title=project.title,
        form=project.form,
        scope=scope,
        documents=[_document_view(document) for document in project.documents],
        identifiers=[
            IdentifierView(
                row.document_id,
                row.page,
                row.kind,
                row.value_hash,
                row.masked,
                row.valid,
                row.start,
                row.end,
            )
            for row in identifiers
        ],
        rules=[
            RuleView(
                rule.code,
                rule.title,
                rule.description,
                RuleKind(rule.kind),
                rule.check_id,
                rule.params,
                Severity(rule.severity),
            )
            for rule in rules
        ],
        regulation_text="\n\n".join(
            f"=== {regulation.filename} ===\n{regulation.text}" for regulation in regulations
        ),
        hasher=hasher,
    )


def _document_view(document: ProjectDocument) -> DocumentView:
    return DocumentView(
        id=document.id,
        filename=document.filename,
        document_type=document.document_type,
        pages=[_page_view(page) for page in document.pages],
    )


def _page_view(page: DocumentPage) -> PageView:
    return PageView(
        id=page.id,
        number=page.number,
        text=page.text,
        # Five values per word from the text layer, six (with confidence) from OCR.
        words=[Word(*row) for row in page.words],
        is_scan=page.is_scan,
        ocr_confidence=page.ocr_confidence,
        facts=PageFacts.model_validate(page.facts) if page.facts is not None else None,
        facts_version=page.facts_version,
    )
