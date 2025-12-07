"""
Add Sync Timestamps to Series

Revision ID: 39bbc83023cb
Revises: f4afea8860cf
Create Date: 2025-12-07 11:19:07.955611
"""

from alembic import op
import sqlalchemy as sa

from app.logging.logger import log

# Revision identifiers, used by Alembic.
revision = '39bbc83023cb'
down_revision = 'f4afea8860cf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_synced', sa.DateTime(), nullable=True))

    with op.batch_alter_table('task_durations', schema=None) as batch_op:
        batch_op.alter_column(
            'duration',
            existing_type=sa.INTEGER(),
            type_=sa.Float(),
            existing_nullable=False
        )

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('task_durations', schema=None) as batch_op:
        batch_op.alter_column(
            'duration',
            existing_type=sa.Float(),
            type_=sa.INTEGER(),
            existing_nullable=False
        )

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('last_synced')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
