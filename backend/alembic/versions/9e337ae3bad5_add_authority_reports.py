"""add authority_reports table

Revision ID: 9e337ae3bad5
Revises: 7884397e481b
Create Date: 2026-08-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e337ae3bad5'
down_revision: Union[str, Sequence[str], None] = '7884397e481b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    authority_report_status = sa.Enum('draft', 'approved', 'sent', name='authorityreportstatus')

    op.create_table(
        'authority_reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cluster_id', sa.Integer(), sa.ForeignKey('hazard_clusters.id'), nullable=False, unique=True),
        sa.Column('issue_type', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('confidence', sa.Integer(), nullable=False),
        sa.Column('contributor_count', sa.Integer(), nullable=False),
        sa.Column('identified_authority', sa.String(), nullable=False),
        sa.Column('draft_text', sa.Text(), nullable=False),
        sa.Column('status', authority_report_status, nullable=False, server_default='draft'),
        sa.Column('delivery_detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_authority_reports_cluster_id'), 'authority_reports', ['cluster_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_authority_reports_cluster_id'), table_name='authority_reports')
    op.drop_table('authority_reports')
    sa.Enum(name='authorityreportstatus').drop(op.get_bind(), checkfirst=True)
