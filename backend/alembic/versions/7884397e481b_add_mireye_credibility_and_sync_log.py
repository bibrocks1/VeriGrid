"""add mireye credibility fields and sync log

Revision ID: 7884397e481b
Revises: eef71b43e0cf
Create Date: 2026-08-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7884397e481b'
down_revision: Union[str, Sequence[str], None] = 'eef71b43e0cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('reports', sa.Column('mireye_credibility_score', sa.Integer(), nullable=True))
    op.add_column('reports', sa.Column('mireye_credibility_notes', sa.Text(), nullable=True))

    op.create_table(
        'mireye_sync_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_mireye_sync_log_created_at'), 'mireye_sync_log', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_mireye_sync_log_created_at'), table_name='mireye_sync_log')
    op.drop_table('mireye_sync_log')
    op.drop_column('reports', 'mireye_credibility_notes')
    op.drop_column('reports', 'mireye_credibility_score')
