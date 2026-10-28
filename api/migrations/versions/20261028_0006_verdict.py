"""A reviewer's verdict on a whole project

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("verdict", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("verdict_note", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("verdict_by", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("verdict_at", sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        "verdict", "projects", "verdict IS NULL OR verdict IN ('approved', 'changes_requested')"
    )


def downgrade() -> None:
    op.drop_constraint("verdict", "projects", type_="check")
    op.drop_column("projects", "verdict_at")
    op.drop_column("projects", "verdict_by")
    op.drop_column("projects", "verdict_note")
    op.drop_column("projects", "verdict")
