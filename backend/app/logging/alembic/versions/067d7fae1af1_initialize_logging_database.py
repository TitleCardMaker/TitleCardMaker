"""
Initialize Logging Database

Revision ID: 067d7fae1af1
Revises: 
Create Date: 2025-06-15 19:14:47.335669
"""

from alembic import op
import sqlalchemy as sa

from app.logging.logger import contextualize, log 

# Revision identifiers, used by Alembic.
revision = '067d7fae1af1'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    op.create_table('logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, index=True),
        sa.Column('level_name', sa.String(), nullable=False),
        sa.Column('level_number', sa.Integer(), nullable=False, index=True),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('context_id', sa.String(), nullable=True, index=True),
        sa.Column('file', sa.String(), nullable=True),
        sa.Column('line', sa.Integer(), nullable=True),
        sa.Column('exception_type', sa.String(), nullable=True),
        sa.Column('exception_value', sa.String(), nullable=True),
        sa.Column('exception_traceback', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    op.drop_table('logs')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')