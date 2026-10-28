from datetime import datetime
from decimal import Decimal
from typing import Any, ClassVar

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    LargeBinary,
    Numeric,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, deferred, mapped_column, relationship

from app.vocabulary import (
    Decision,
    IndexStatus,
    OcrStatus,
    ProjectStatus,
    RequiredDocumentSource,
    RunStatus,
    Scope,
    Severity,
    Verdict,
    check_in,
)


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[Any, Any]] = {dict[str, Any]: JSONB, list[Any]: JSONB}


def created_at_column() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class AiCall(Base):
    """One row per request to an AI provider, successful or not."""

    __tablename__ = "ai_calls"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    purpose: Mapped[str]
    provider: Mapped[str]
    model: Mapped[str]
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    duration_ms: Mapped[int]
    error: Mapped[str | None]


class ProjectType(Base):
    """A kind of funding project; each has its own client and reviewer rule sets."""

    __tablename__ = "project_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    description: Mapped[str] = mapped_column(default="")
    active: Mapped[bool] = mapped_column(default=True)


class RegulationDocument(Base):
    """A regulation PDF an admin uploaded for one scope, at one level: every project (neither
    a type nor a project), every project of a type, or one project."""

    __tablename__ = "regulation_documents"
    __table_args__ = (
        CheckConstraint(check_in("verification_scope", Scope), name="scope"),
        CheckConstraint("project_type_id IS NULL OR project_id IS NULL", name="one_level"),
        CheckConstraint(check_in("index_status", IndexStatus), name="index_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_types.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    verification_scope: Mapped[str]
    filename: Mapped[str]
    sha256: Mapped[str]
    content: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
    text: Mapped[str] = deferred(mapped_column(Text, nullable=False))
    uploaded_by: Mapped[str]
    created_at: Mapped[datetime] = created_at_column()
    # Pages without a text layer, and how reading them went (None when there are none).
    scanned_pages: Mapped[int] = mapped_column(default=0, server_default="0")
    ocr_status: Mapped[str | None]
    # Passages split, embedded and searchable (app/regulations/processing.py).
    index_status: Mapped[str] = mapped_column(
        default=IndexStatus.PENDING, server_default=IndexStatus.PENDING
    )
    index_error: Mapped[str | None]


class RegulationPassage(Base):
    """A piece of a regulation (a page, or part of a long one) with its embedding, so a check
    retrieves the passages that matter for each document."""

    __tablename__ = "regulation_passages"

    id: Mapped[int] = mapped_column(primary_key=True)
    regulation_document_id: Mapped[int] = mapped_column(
        ForeignKey("regulation_documents.id", ondelete="CASCADE"), index=True
    )
    page: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    # shortcut: no fixed dimension and no HNSW index, so any embedding model fits and search is
    # exact; add Vector(dim) with an HNSW index when regulations reach tens of thousands of pages.
    embedding: Mapped[list[float] | None] = mapped_column(Vector())
    embedding_model: Mapped[str | None]  # searches compare only vectors from the same model


class RegulationRule(Base):
    """A requirement an admin wrote in plain words, for every project (no type) or every
    project of one type; the model judges documents against it like a regulation passage."""

    __tablename__ = "regulation_rules"
    __table_args__ = (
        CheckConstraint(check_in("verification_scope", Scope), name="scope"),
        CheckConstraint(check_in("severity", Severity), name="severity"),
        UniqueConstraint(
            "project_type_id",
            "verification_scope",
            "code",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_types.id", ondelete="CASCADE"), index=True
    )
    verification_scope: Mapped[str]
    code: Mapped[str]
    title: Mapped[str]
    description: Mapped[str] = mapped_column(default="")  # the requirement, in plain words
    severity: Mapped[str] = mapped_column(default=Severity.BAD)
    active: Mapped[bool] = mapped_column(default=True)


class Project(Base):
    """A client's funding application: the form they filled in and the documents they uploaded."""

    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint(check_in("status", ProjectStatus), name="status"),
        CheckConstraint(f"verdict IS NULL OR {check_in('verdict', Verdict)}", name="verdict"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_type_id: Mapped[int] = mapped_column(ForeignKey("project_types.id"), index=True)
    owner_id: Mapped[str] = mapped_column(index=True)  # Keycloak user id (sub)
    # The owner's name when they last saved; None on projects from before it was kept.
    owner_name: Mapped[str | None]
    title: Mapped[str]
    # The application form; personal identifiers are stored only hashed and masked.
    form: Mapped[dict[str, Any]] = mapped_column(default=dict)
    status: Mapped[str] = mapped_column(default=ProjectStatus.DRAFT, index=True)
    created_at: Mapped[datetime] = created_at_column()
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The reviewer's decision on the whole project; cleared when the owner submits again.
    verdict: Mapped[str | None]
    verdict_note: Mapped[str | None]
    verdict_by: Mapped[str | None]
    verdict_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    documents: Mapped[list["ProjectDocument"]] = relationship(
        order_by="ProjectDocument.id", cascade="all, delete-orphan"
    )


class RequiredDocument(Base):
    """A document the applicant must add to one project: written by an admin, or read from the
    client-scope regulations that apply to the project (app/projects/required_documents.py)."""

    __tablename__ = "required_documents"
    __table_args__ = (CheckConstraint(check_in("source", RequiredDocumentSource), name="source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str]
    description: Mapped[str] = mapped_column(default="")
    source: Mapped[str]
    # Where a regulations item was read; None on admin items and when the regulation is deleted.
    regulation_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("regulation_documents.id", ondelete="SET NULL")
    )
    regulation_page: Mapped[int | None]
    regulation_quote: Mapped[str | None]


class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    # The list item this upload was added for; None for uploads outside the list.
    required_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("required_documents.id", ondelete="SET NULL"), index=True
    )
    filename: Mapped[str]
    sha256: Mapped[str] = mapped_column(index=True)
    content: Mapped[bytes] = deferred(mapped_column(LargeBinary, nullable=False))
    page_count: Mapped[int]
    # Set by the extraction agent ("invoice", "contract"...); None until a run classifies it.
    document_type: Mapped[str | None]
    uploaded_at: Mapped[datetime] = created_at_column()

    pages: Mapped[list["DocumentPage"]] = relationship(
        order_by="DocumentPage.number", cascade="all, delete-orphan"
    )


class DocumentPage(Base):
    """Extracted text and word boxes of one page, plus the facts extracted from it (a cache)."""

    __tablename__ = "document_pages"
    __table_args__ = (
        UniqueConstraint("document_id", "number"),
        CheckConstraint(f"ocr_status IS NULL OR {check_in('ocr_status', OcrStatus)}", name="ocr"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("project_documents.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int]  # 1-based
    text: Mapped[str]
    width: Mapped[float]  # PDF points
    height: Mapped[float]
    # [[text, x0, top, x1, bottom, confidence?], ...] in PDF points from the top-left corner;
    # the OCR confidence (0 to 1) only on words read by OCR.
    words: Mapped[list[Any]] = mapped_column(default=list)
    is_scan: Mapped[bool] = mapped_column(default=False)  # no text layer: read by OCR
    ocr_status: Mapped[str | None]  # None on pages with a text layer
    ocr_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    ocr_error: Mapped[str | None]
    # When reading this page last started or finished; tells a stalled reading from a slow one.
    ocr_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    facts: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # "<prompt version>:<model>" the facts were extracted with; a mismatch re-extracts.
    facts_version: Mapped[str | None]


class PersonalIdentifier(Base):
    """A personal identifier (CNP) found in a document or the form, kept only as a keyed hash."""

    __tablename__ = "personal_identifiers"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    # None when the value comes from the application form.
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_documents.id", ondelete="CASCADE")
    )
    page: Mapped[int | None]
    kind: Mapped[str]
    value_hash: Mapped[str] = mapped_column(index=True)
    masked: Mapped[str]
    valid: Mapped[bool]
    start: Mapped[int | None]  # character offsets in DocumentPage.text
    end: Mapped[int | None]


class VerificationRun(Base):
    __tablename__ = "verification_runs"
    __table_args__ = (
        CheckConstraint(check_in("scope", Scope), name="scope"),
        CheckConstraint(check_in("status", RunStatus), name="status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    scope: Mapped[str]
    status: Mapped[str] = mapped_column(default=RunStatus.PENDING)
    error: Mapped[str | None]
    started_by: Mapped[str]
    created_at: Mapped[datetime] = created_at_column()
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentFinding(Base):
    """One flagged problem with its evidence, highlight boxes and the person's decision."""

    __tablename__ = "document_findings"
    __table_args__ = (
        CheckConstraint(check_in("scope", Scope), name="scope"),
        CheckConstraint(check_in("severity", Severity), name="severity"),
        CheckConstraint(f"decision IS NULL OR {check_in('decision', Decision)}", name="decision"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("verification_runs.id", ondelete="CASCADE"), index=True
    )
    scope: Mapped[str]
    rule_code: Mapped[str]
    agent: Mapped[str]
    severity: Mapped[str]
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3))
    # {"en": ..., "ro": ...}: every interface language, the web shows the reader's.
    reason: Mapped[dict[str, Any]]
    recommendation: Mapped[dict[str, Any]]
    # Evidence; document_id is None for findings about the form or a missing document.
    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_documents.id", ondelete="CASCADE"), index=True
    )
    page: Mapped[int | None]
    quote: Mapped[str | None]
    # [[x0, top, x1, bottom], ...] in PDF points on `page`, one box per line of the quote.
    rects: Mapped[list[Any]] = mapped_column(default=list)
    # The evidence was read by OCR; `confidence` is then capped at the words' OCR confidence.
    ocr: Mapped[bool] = mapped_column(default=False, server_default=false())
    # The regulation passage the finding rests on; None for findings from an admin's own rule.
    regulation_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("regulation_documents.id", ondelete="SET NULL")
    )
    regulation_page: Mapped[int | None]
    regulation_quote: Mapped[str | None]
    decision: Mapped[str | None]
    decision_note: Mapped[str | None]
    decided_by: Mapped[str | None]
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
