"""The list of documents to add to each project, and the uploads made for its items

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "required_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column(
            "regulation_document_id",
            sa.Integer(),
            sa.ForeignKey("regulation_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("regulation_page", sa.Integer(), nullable=True),
        sa.Column("regulation_quote", sa.String(), nullable=True),
        sa.CheckConstraint("source IN ('admin', 'regulations')", name="source"),
    )
    op.create_index("ix_required_documents_project_id", "required_documents", ["project_id"])
    op.add_column(
        "project_documents",
        sa.Column(
            "required_document_id",
            sa.Integer(),
            sa.ForeignKey("required_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_project_documents_required_document_id", "project_documents", ["required_document_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_project_documents_required_document_id", table_name="project_documents")
    op.drop_column("project_documents", "required_document_id")
    op.drop_index("ix_required_documents_project_id", table_name="required_documents")
    op.drop_table("required_documents")
