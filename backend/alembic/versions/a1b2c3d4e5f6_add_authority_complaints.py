"""add authority complaints

Revision ID: a1b2c3d4e5f6
Revises: 79f28b8d0875
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "79f28b8d0875"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "authority_complaints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cluster_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("responsible_authority", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "approved", "sent", name="complaintstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cluster_id"], ["hazard_clusters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_authority_complaints_id"), "authority_complaints", ["id"], unique=False)
    op.create_index(op.f("ix_authority_complaints_cluster_id"), "authority_complaints", ["cluster_id"], unique=False)
    op.create_index(op.f("ix_authority_complaints_status"), "authority_complaints", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_authority_complaints_status"), table_name="authority_complaints")
    op.drop_index(op.f("ix_authority_complaints_cluster_id"), table_name="authority_complaints")
    op.drop_index(op.f("ix_authority_complaints_id"), table_name="authority_complaints")
    op.drop_table("authority_complaints")
    sa.Enum(name="complaintstatus").drop(op.get_bind(), checkfirst=True)