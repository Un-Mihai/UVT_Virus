"""Regulations at three levels, embedded passages for retrieval, written rules only

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-28
"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RULE_KEY = "regulation_rules_project_type_id_verification_scope_code_key"


def upgrade() -> None:
    # Regulation documents: every project, a project type, or one project.
    op.alter_column("regulation_documents", "project_type_id", nullable=True)
    op.add_column("regulation_documents", sa.Column("project_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "regulation_documents_project_id_fkey",
        "regulation_documents",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_regulation_documents_project_id", "regulation_documents", ["project_id"])
    op.create_check_constraint(
        "one_level", "regulation_documents", "project_type_id IS NULL OR project_id IS NULL"
    )
    op.add_column(
        "regulation_documents",
        sa.Column("index_status", sa.String(), server_default="pending", nullable=False),
    )
    op.add_column("regulation_documents", sa.Column("index_error", sa.String(), nullable=True))
    op.create_check_constraint(
        "index_status", "regulation_documents", "index_status IN ('pending', 'done', 'failed')"
    )
    # Documents uploaded before passages existed have none; the admin processes them again.
    op.execute(
        "UPDATE regulation_documents SET index_status = 'failed', "
        "index_error = 'Uploaded before regulations were indexed; process it again.'"
    )

    op.create_table(
        "regulation_passages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("regulation_document_id", sa.Integer(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(), nullable=True),
        sa.Column("embedding_model", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["regulation_document_id"], ["regulation_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_regulation_passages_regulation_document_id",
        "regulation_passages",
        ["regulation_document_id"],
    )

    # Rules are now only what an admin writes in plain words, for every project or for a type.
    # Rules that pointed at a code check are removed: the model now asks for those checks.
    op.execute("DELETE FROM regulation_rules WHERE kind = 'check'")
    op.drop_constraint("check_needs_id", "regulation_rules", type_="check")
    op.drop_constraint("kind", "regulation_rules", type_="check")
    op.drop_column("regulation_rules", "kind")
    op.drop_column("regulation_rules", "check_id")
    op.drop_column("regulation_rules", "params")
    op.alter_column("regulation_rules", "project_type_id", nullable=True)
    op.drop_constraint(RULE_KEY, "regulation_rules", type_="unique")
    op.create_unique_constraint(
        RULE_KEY,
        "regulation_rules",
        ["project_type_id", "verification_scope", "code"],
        postgresql_nulls_not_distinct=True,
    )

    # Findings cite the regulation passage they rest on.
    op.add_column(
        "document_findings", sa.Column("regulation_document_id", sa.Integer(), nullable=True)
    )
    op.add_column("document_findings", sa.Column("regulation_page", sa.Integer(), nullable=True))
    op.add_column("document_findings", sa.Column("regulation_quote", sa.String(), nullable=True))
    op.create_foreign_key(
        "document_findings_regulation_document_id_fkey",
        "document_findings",
        "regulation_documents",
        ["regulation_document_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "document_findings_regulation_document_id_fkey", "document_findings", type_="foreignkey"
    )
    op.drop_column("document_findings", "regulation_quote")
    op.drop_column("document_findings", "regulation_page")
    op.drop_column("document_findings", "regulation_document_id")

    op.execute("DELETE FROM regulation_rules WHERE project_type_id IS NULL")
    op.drop_constraint(RULE_KEY, "regulation_rules", type_="unique")
    op.create_unique_constraint(
        RULE_KEY, "regulation_rules", ["project_type_id", "verification_scope", "code"]
    )
    op.alter_column("regulation_rules", "project_type_id", nullable=False)
    op.add_column(
        "regulation_rules",
        sa.Column("params", sa.dialects.postgresql.JSONB(), server_default="{}", nullable=False),
    )
    op.add_column("regulation_rules", sa.Column("check_id", sa.String(), nullable=True))
    op.add_column(
        "regulation_rules", sa.Column("kind", sa.String(), server_default="ai", nullable=False)
    )
    op.create_check_constraint("kind", "regulation_rules", "kind IN ('check', 'ai')")
    op.create_check_constraint(
        "check_needs_id", "regulation_rules", "kind <> 'check' OR check_id IS NOT NULL"
    )

    op.drop_index("ix_regulation_passages_regulation_document_id", "regulation_passages")
    op.drop_table("regulation_passages")

    op.execute("DELETE FROM regulation_documents WHERE project_type_id IS NULL")
    op.drop_constraint("index_status", "regulation_documents", type_="check")
    op.drop_column("regulation_documents", "index_error")
    op.drop_column("regulation_documents", "index_status")
    op.drop_constraint("one_level", "regulation_documents", type_="check")
    op.drop_index("ix_regulation_documents_project_id", "regulation_documents")
    op.drop_constraint(
        "regulation_documents_project_id_fkey", "regulation_documents", type_="foreignkey"
    )
    op.drop_column("regulation_documents", "project_id")
    op.alter_column("regulation_documents", "project_type_id", nullable=False)
