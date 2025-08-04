"""
Create TaskDuration table
Create Series.set_url column

Revision ID: 753b403e12d2
Revises: e290ff7005ff
Create Date: 2025-03-24 10:59:59.136723
"""

from alembic import op
import sqlalchemy as sa

from app.logging.logger import contextualize 

# Revision identifiers, used by Alembic.
revision = '753b403e12d2'
down_revision = 'e290ff7005ff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize()
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    op.create_table('task_durations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_name', sa.String(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('set_url', sa.String(), nullable=True))

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize()
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('set_url')

    op.drop_table('task_durations')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
