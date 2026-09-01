"""reconcile uuid ids and authority complaints

Merges the Frontend branch's applied schema (Integer ids, device_id,
mireye_sync_log, the old authority_reports table) with main's UUID-based
user/report identity and cluster-assessment/authority-complaint design,
per the product doc's explicit decision to use UUIDs. Existing dev data
in reports/users/hazard_clusters is trivial (1 report, 2 users, 0
clusters at the time of writing) and is not preserved — an id-type
change on a shared PK isn't a meaningful ALTER, and backfilling real
UUIDs onto two throwaway dev rows isn't worth the complexity.

Revision ID: cf992a5ad9ad
Revises: 9e337ae3bad5
Create Date: 2026-08-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.dialects.postgresql import UUID
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'cf992a5ad9ad'
down_revision: Union[str, Sequence[str], None] = '9e337ae3bad5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # authority_reports is superseded by authority_complaints below (richer
    # schema, LLM-authored draft text) — drop it, it's empty.
    op.drop_table('authority_reports')

    # reports.user_id and users.id are moving from Integer to UUID —
    # simplest correct path given trivial existing data is to drop and
    # recreate both rather than a fragile in-place ALTER + backfill.
    op.drop_table('reports')
    op.drop_table('users')

    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('device_id', sa.String(), nullable=True),
        sa.Column('trust_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_device_id'), 'users', ['device_id'], unique=True)

    op.create_table(
        'reports',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column(
            'category',
            # create_type=False: this enum type already exists (created by
            # 132903ca8573 and never dropped) — without this, create_table
            # tries to CREATE TYPE again and fails. Must be the dialect-
            # specific postgresql.ENUM, not generic sa.Enum — the generic
            # type doesn't reliably honor create_type=False here.
            PGEnum(
                'flooding', 'waterlogging', 'road_damage', 'construction',
                'safety', 'environmental', 'traffic', 'other',
                name='reportcategory', create_type=False,
            ),
            nullable=False,
        ),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'geom',
            geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeogFromText', name='geography'),
            nullable=False,
        ),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('mireye_credibility_score', sa.Integer(), nullable=True),
        sa.Column('mireye_credibility_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['hazard_clusters.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reports_category'), 'reports', ['category'], unique=False)
    op.create_index(op.f('ix_reports_cluster_id'), 'reports', ['cluster_id'], unique=False)

    # hazard_clusters: bring in Day 9/10's reasoning-agent assessment
    # columns (main's design). verified_at already exists here — added by
    # eef71b43e0cf (Frontend's chain, already applied) — needed for the
    # Day 8 sync-log trigger and the trust-reward-on-verify rule.
    op.add_column('hazard_clusters', sa.Column('severity', sa.String(length=20), nullable=True))
    op.add_column('hazard_clusters', sa.Column('explanation', sa.Text(), nullable=True))
    op.add_column('hazard_clusters', sa.Column('recommended_action', sa.Text(), nullable=True))
    op.add_column('hazard_clusters', sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=True))

    complaint_status = PGEnum('draft', 'approved', 'sent', name='complaintstatus', create_type=False)
    complaint_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'authority_complaints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('recommended_action', sa.Text(), nullable=True),
        sa.Column('responsible_authority', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('confidence', sa.Integer(), nullable=True),
        sa.Column('contributor_count', sa.Integer(), nullable=True),
        sa.Column('status', complaint_status, nullable=False),
        sa.Column('delivery_detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['hazard_clusters.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_authority_complaints_cluster_id'), 'authority_complaints', ['cluster_id'], unique=True)
    op.create_index(op.f('ix_authority_complaints_status'), 'authority_complaints', ['status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_authority_complaints_status'), table_name='authority_complaints')
    op.drop_index(op.f('ix_authority_complaints_cluster_id'), table_name='authority_complaints')
    op.drop_table('authority_complaints')
    sa.Enum(name='complaintstatus').drop(op.get_bind(), checkfirst=True)

    op.drop_column('hazard_clusters', 'assessed_at')
    op.drop_column('hazard_clusters', 'recommended_action')
    op.drop_column('hazard_clusters', 'explanation')
    op.drop_column('hazard_clusters', 'severity')

    op.drop_index(op.f('ix_reports_cluster_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_category'), table_name='reports')
    op.drop_table('reports')

    op.drop_index(op.f('ix_users_device_id'), table_name='users')
    op.drop_table('users')

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('trust_score', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column(
            'category',
            sa.Enum(
                'flooding', 'waterlogging', 'road_damage', 'construction',
                'safety', 'environmental', 'traffic', 'other',
                name='reportcategory',
            ),
            nullable=False,
        ),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'geom',
            geoalchemy2.types.Geography(geometry_type='POINT', srid=4326, dimension=2, from_text='ST_GeogFromText', name='geography'),
            nullable=False,
        ),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cluster_id'], ['hazard_clusters.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
