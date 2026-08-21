"""add device_id verified_at and geom gist indexes

Revision ID: eef71b43e0cf
Revises: 132903ca8573
Create Date: 2026-08-21 15:38:19.505432

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eef71b43e0cf'
down_revision: Union[str, Sequence[str], None] = '132903ca8573'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('device_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_users_device_id'), 'users', ['device_id'], unique=True)

    op.add_column('hazard_clusters', sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True))

    # NOTE: idx_reports_geom / idx_hazard_clusters_geom are NOT created here.
    # GeoAlchemy2's DDL listener auto-creates a GIST index under those exact
    # names whenever a Geography column's table is created (see the
    # 132903ca8573 migration) — that's why its downgrade() references them
    # even though its own upgrade() never calls create_index for them.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('hazard_clusters', 'verified_at')
    op.drop_index(op.f('ix_users_device_id'), table_name='users')
    op.drop_column('users', 'device_id')
