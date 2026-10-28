"""OCR state on pages and regulation documents; findings in every interface language

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "document_findings",
        sa.Column("ocr", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    # Earlier findings were written in English only.
    for column in ("reason", "recommendation"):
        op.alter_column(
            "document_findings",
            column,
            existing_type=sa.VARCHAR(),
            type_=postgresql.JSONB(astext_type=sa.Text()),
            existing_nullable=False,
            postgresql_using=f"jsonb_build_object('en', {column})",
        )
    op.add_column("document_pages", sa.Column("ocr_status", sa.String(), nullable=True))
    op.add_column(
        "document_pages",
        sa.Column("ocr_confidence", sa.Numeric(precision=4, scale=3), nullable=True),
    )
    op.add_column("document_pages", sa.Column("ocr_error", sa.String(), nullable=True))
    op.add_column(
        "document_pages",
        sa.Column("ocr_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ocr",
        "document_pages",
        "ocr_status IS NULL OR ocr_status IN ('pending', 'done', 'failed', 'unavailable')",
    )
    # Scanned pages uploaded before OCR existed were never read.
    op.execute(
        "UPDATE document_pages SET ocr_status = 'pending', ocr_updated_at = now() WHERE is_scan"
    )
    op.add_column(
        "regulation_documents",
        sa.Column("scanned_pages", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column("regulation_documents", sa.Column("ocr_status", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("regulation_documents", "ocr_status")
    op.drop_column("regulation_documents", "scanned_pages")
    op.drop_constraint("ocr", "document_pages", type_="check")
    op.drop_column("document_pages", "ocr_updated_at")
    op.drop_column("document_pages", "ocr_error")
    op.drop_column("document_pages", "ocr_confidence")
    op.drop_column("document_pages", "ocr_status")
    for column in ("recommendation", "reason"):
        op.alter_column(
            "document_findings",
            column,
            existing_type=postgresql.JSONB(astext_type=sa.Text()),
            type_=sa.VARCHAR(),
            existing_nullable=False,
            postgresql_using=f"{column} ->> 'en'",
        )
    op.drop_column("document_findings", "ocr")
