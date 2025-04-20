"""Change Series.monitored column to status

Revision ID: f4afea8860cf
Revises: 753b403e12d2
Create Date: 2025-04-19 19:43:09.739141
"""

from alembic import op
import sqlalchemy as sa

from modules.Debug import contextualize
from modules.Debug2 import logger 

# Revision identifiers, used by Alembic.
revision = 'f4afea8860cf'
down_revision = '753b403e12d2'
branch_labels = None
depends_on = None

# Models necessary for data migration
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()

class Series(Base):
    __tablename__ = 'series'

    # Columns not being modified
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    monitored = sa.Column(sa.Boolean, nullable=False)
    status = sa.Column(sa.String, nullable=False)

def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    # Add new status column
    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(), nullable=False, server_default='monitored'))

    # Convert all existing monitored values to status
    # Perform data migration
    session = Session(bind=op.get_bind())

    for series in session.query(Series).all():
        if series.monitored:
            series.status = 'monitored'
        else:
            series.status = 'unmonitored'

    session.commit()

    # Drop old monitored column
    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.drop_column('monitored')

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column('monitored', sa.BOOLEAN(), nullable=False))
        batch_op.drop_column('status')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
