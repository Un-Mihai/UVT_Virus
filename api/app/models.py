from datetime import datetime
from decimal import Decimal
from typing import Any, ClassVar

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
    OcrStatus,
    ProjectStatus,
    RuleKind,
    RunStatus,
    Scope,
    Severity,
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
    """A regulation file an admin uploaded for one project type and one scope."""

    __tablename__ = "regulation_documents"
    __table_args__ = (CheckConstraint(check_in("verification_scope", Scope), name="scope"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_type_id: Mapped[int] = mapped_column(
        ForeignKey("project_types.id", ondelete="CASCADE"), index=True
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


class RegulationRule(Base):
    """One rule of a scope's rule set: a deterministic check or a clause the AI judges."""

    __tablename__ = "regulation_rules"
    __table_args__ = (
        CheckConstraint(check_in("verification_scope", Scope), name="scope"),
        CheckConstraint(check_in("kind", RuleKind), name="kind"),
        CheckConstraint(check_in("severity", Severity), name="severity"),
        CheckConstraint("kind <> 'check' OR check_id IS NOT NULL", name="check_needs_id"),
        UniqueConstraint("project_type_id", "verification_scope", "code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_type_id: Mapped[int] = mapped_column(
        ForeignKey("project_types.id", ondelete="CASCADE"), index=True
    )
    verification_scope: Mapped[str]
    code: Mapped[str]
    title: Mapped[str]
    description: Mapped[str] = mapped_column(default="")
    kind: Mapped[str]
    check_id: Mapped[str | None]
    params: Mapped[dict[str, Any]] = mapped_column(default=dict)
    severity: Mapped[str] = mapped_column(default=Severity.BAD)
    active: Mapped[bool] = mapped_column(default=True)


class Project(Base):
    """A client's funding application: the form they filled in and the documents they uploaded."""

    __tablename__ = "projects"
    __table_args__ = (CheckConstraint(check_in("status", ProjectStatus), name="status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_type_id: Mapped[int] = mapped_column(ForeignKey("project_types.id"), index=True)
    owner_id: Mapped[str] = mapped_column(index=True)  # Keycloak user id (sub)
    title: Mapped[str]
    # The application form; personal identifiers are stored only hashed and masked.
    form: Mapped[dict[str, Any]] = mapped_column(default=dict)
    status: Mapped[str] = mapped_column(default=ProjectStatus.DRAFT, index=True)
    created_at: Mapped[datetime] = created_at_column()
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    documents: Mapped[list["ProjectDocument"]] = relationship(
        order_by="ProjectDocument.id", cascade="all, delete-orphan"
    )


class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
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
    decision: Mapped[str | None]
    decision_note: Mapped[str | None]
    decided_by: Mapped[str | None]
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
