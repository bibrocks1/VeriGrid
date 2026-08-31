"""add cluster assessment

Revision ID: 79f28b8d0875
Revises: 132903ca8573
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "79f28b8d0875"
down_revision: Union[str, Sequence[str], None] = "132903ca8573"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "hazard_clusters",
        sa.Column(
            "severity",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.add_column(
        "hazard_clusters",
        sa.Column(
            "explanation",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "hazard_clusters",
        sa.Column(
            "recommended_action",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "hazard_clusters",
        sa.Column(
            "assessed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("hazard_clusters", "assessed_at")
    op.drop_column("hazard_clusters", "recommended_action")
    op.drop_column("hazard_clusters", "explanation")
    op.drop_column("hazard_clusters", "severity")