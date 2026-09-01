"""add mireye_sync_log.cluster_id

Revision ID: fa53468a75c9
Revises: cf992a5ad9ad
Create Date: 2026-09-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa53468a75c9'
down_revision: Union[str, Sequence[str], None] = 'cf992a5ad9ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('mireye_sync_log', sa.Column('cluster_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_mireye_sync_log_cluster_id', 'mireye_sync_log', 'hazard_clusters', ['cluster_id'], ['id']
    )
    op.create_index(op.f('ix_mireye_sync_log_cluster_id'), 'mireye_sync_log', ['cluster_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_mireye_sync_log_cluster_id'), table_name='mireye_sync_log')
    op.drop_constraint('fk_mireye_sync_log_cluster_id', 'mireye_sync_log', type_='foreignkey')
    op.drop_column('mireye_sync_log', 'cluster_id')
