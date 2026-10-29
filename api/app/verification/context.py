"""Everything one verification run reads, loaded once. Agents never touch the database."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.models import (
    DocumentPage,
    PersonalIdentifier,
    Project,
    ProjectDocument,
    RegulationDocument,
    RegulationRule,
    RequiredDocument,
)
from app.pdf import Word
from app.personal_data import IdentifierHasher
from app.regulations.levels import documents_for, rules_for
from app.regulations.search import PassageSearch, PgvectorPassageSearch
from app.verification.facts import PageFacts
from app.vocabulary import Scope, Severity


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
class RequiredDocumentView:
    """An item of the project's list of documents to add, and whether one was uploaded for it."""

    name: str
    has_document: bool


@dataclass(frozen=True)
class RuleView:
    """A requirement findings are reported against: an admin's written rule, or the code
    check the model asked for on behalf of a regulation passage."""

    code: str
    title: str
    description: str
    severity: Severity


@dataclass
class VerificationContext:
    project_id: int
    project_title: str
    form: dict[str, Any]
    scope: Scope
    documents: list[DocumentView]
    identifiers: list[IdentifierView]
    rules: list[RuleView]  # the admins' written rules that apply
    passages: PassageSearch  # the regulation passages that apply, searchable
    hasher: IdentifierHasher
    notes: dict[str, Any] = field(default_factory=dict)  # free space for agents in later stages
    required_documents: list[RequiredDocumentView] = field(default_factory=list)

    def document(self, document_id: int) -> DocumentView | None:
        return next((doc for doc in self.documents if doc.id == document_id), None)

    def page_facts(self) -> Iterator[tuple[DocumentView, PageView, PageFacts]]:
        for document in self.documents:
            for page in document.pages:
                if page.facts is not None:
                    yield document, page, page.facts


async def load_context(
    session: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    project_id: int,
    scope: Scope,
    hasher: IdentifierHasher,
    embedding_model: str,
) -> VerificationContext:
    """The project with its documents, and the regulations and written rules that apply to it."""
    project = await session.get_one(
        Project,
        project_id,
        options=[selectinload(Project.documents).selectinload(ProjectDocument.pages)],
    )
    rules = await session.scalars(
        select(RegulationRule)
        .where(rules_for(project.project_type_id, scope))
        .order_by(RegulationRule.project_type_id.nulls_first(), RegulationRule.id)
    )
    regulation_ids = await session.scalars(
        select(RegulationDocument.id).where(
            documents_for(project.id, project.project_type_id, scope)
        )
    )
    identifiers = await session.scalars(
        select(PersonalIdentifier)
        .where(PersonalIdentifier.project_id == project_id)
        .order_by(PersonalIdentifier.id)
    )
    required = await session.scalars(
        select(RequiredDocument)
        .where(RequiredDocument.project_id == project_id)
        .order_by(RequiredDocument.id)
    )
    uploaded_for = {document.required_document_id for document in project.documents}
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
            RuleView(rule.code, rule.title, rule.description, Severity(rule.severity))
            for rule in rules
        ],
        passages=PgvectorPassageSearch(sessions, list(regulation_ids), embedding_model),
        hasher=hasher,
        required_documents=[
            RequiredDocumentView(item.name, item.id in uploaded_for) for item in required
        ],
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
