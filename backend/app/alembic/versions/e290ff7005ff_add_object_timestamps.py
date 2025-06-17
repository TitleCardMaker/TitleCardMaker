"""Add object timestamps

Revision ID: e290ff7005ff
Revises: 2dc1e976a801
Create Date: 2025-03-09 14:20:40.051130
"""

from datetime import datetime, timedelta
from alembic import op
import sqlalchemy as sa

from app.logging.logger import contextualize, log, Logger
from app.settings import settings 

# Revision identifiers, used by Alembic.
revision = 'e290ff7005ff'
down_revision = '2dc1e976a801'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

class Card(Base):
    __tablename__ = 'card'
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    created = sa.Column(sa.DateTime, nullable=True)

class Episode(Base):
    __tablename__ = 'episode'
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    created = sa.Column(sa.DateTime, nullable=True)

class Series(Base):
    __tablename__ = 'series'
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    created = sa.Column(sa.DateTime, nullable=True)

def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    # Begin initialization with columns as nullable so they can be migrated
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created', sa.DateTime(), nullable=True))

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created', sa.DateTime(), nullable=True))

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.alter_column('clean_name',
            existing_type=sa.VARCHAR(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.alter_column('full_name',
            existing_type=sa.VARCHAR(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.alter_column('sort_name',
            existing_type=sa.VARCHAR(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.add_column(sa.Column('created', sa.DateTime(), nullable=True))

    # Perform data migration
    # Initialize existing records sequentially from now just for ordering
    session = Session(bind=op.get_bind())

    for model in [Card, Episode, Series]:
        now = datetime.now(tz=settings.TIMEZONE)
        index = 0
        for index, obj in enumerate(
            session.query(model).order_by(model.id.desc()).all()
        ):
            obj.created = now - timedelta(seconds=index)
        log.trace(
            f'Initialized {(index + 1):,} '
            f'{model.__tablename__.title()}.creation timestamps'
        )

    # Commit changes
    session.commit()

    # Alter table columns to become nullable
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.alter_column('created', nullable=False)

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.alter_column('created', nullable=False)

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.alter_column('created', nullable=False)

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('created')
        batch_op.alter_column('sort_name',
            existing_type=sa.VARCHAR(),
            server_default=sa.text('(_)'),
            existing_nullable=False
        )
        batch_op.alter_column('full_name',
            existing_type=sa.VARCHAR(),
            server_default=sa.text('(_)'),
            existing_nullable=False
        )
        batch_op.alter_column('clean_name',
            existing_type=sa.VARCHAR(),
            server_default=sa.text('(_)'),
            existing_nullable=False
        )

    with op.batch_alter_table('episode', schema=None) as batch_op:
        batch_op.drop_column('created')

    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('created')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
