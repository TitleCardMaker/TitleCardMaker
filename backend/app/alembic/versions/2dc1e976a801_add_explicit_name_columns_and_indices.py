"""
Add explicit name columns and indices

Revision ID: 2dc1e976a801
Revises: a1520b6160c4
Create Date: 2024-11-08 15:46:39.930263
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from app.logging.logger import contextualize, log

# Revision identifiers, used by Alembic.
revision = '2dc1e976a801'
down_revision = 'a1520b6160c4'
branch_labels = None
depends_on = None

# Models necessary for data migration
from re import sub as re_sub, IGNORECASE

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from unidecode import unidecode

def _get_sort_name(name: str, pattern: str = r'^(a|an|the)(\s)') -> str:
    """Get the sort name equivalent of the given name"""

    return re_sub(pattern, '', name.lower(), flags=IGNORECASE)

Base = declarative_base()

class Font(Base):
    __tablename__ = 'font'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name: str = sa.Column(sa.String, nullable=False)
    sort_name: str = sa.Column(sa.String, nullable=False)

class Series(Base):
    __tablename__ = 'series'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name: str = sa.Column(sa.String, nullable=False)
    clean_name: str = sa.Column(sa.String, nullable=False)
    full_name: str = sa.Column(sa.String, nullable=False)
    sort_name: str = sa.Column(sa.String, nullable=False)
    year: int = sa.Column(sa.Integer, nullable=False)

class Template(Base):
    __tablename__ = 'template'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name: str = sa.Column(sa.String, nullable=False)
    sort_name: str = sa.Column(sa.String, nullable=False)


def upgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    # Add Font.sort_name; make it an index
    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'sort_name',
            sa.String(),
            server_default=sa.text('_'),
            nullable=False
        ))
        batch_op.create_index(
            batch_op.f('ix_font_sort_name'),
            ['sort_name'],
            unique=False
        )

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'clean_name',
            sa.String(),
            server_default=sa.text('_'),
            nullable=False
        ))
        batch_op.add_column(sa.Column(
            'full_name',
            sa.String(),
            server_default=sa.text('_'),
            nullable=False
        ))
        batch_op.add_column(sa.Column(
            'sort_name',
            sa.String(),
            server_default=sa.text('_'),
            nullable=False
        ))
        batch_op.alter_column(
            'use_per_season_assets',
            existing_type=sa.BOOLEAN(),
            server_default=None,
            existing_nullable=False
        )
        batch_op.create_index(
            batch_op.f('ix_series_sort_name'),
            ['sort_name'],
            unique=False
        )

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sort_name',
            sa.String(),
            server_default=sa.text('_'),
            nullable=False
        ))
        batch_op.create_index(
            batch_op.f('ix_template_sort_name'),
            ['sort_name'],
            unique=False
        )

    # Perform data migration
    session = Session(bind=op.get_bind())

    # Assign Font.sort_name
    for font in session.query(Font).all():
        font.sort_name = _get_sort_name(font.name)
        log.trace(f'Font[{font.id}].sort_name = "{font.sort_name}"')
    # Assign Series.clean_name, Series.full_name, Series.sort_name
    for series in session.query(Series).all():
        series.clean_name = unidecode(series.name, errors='preserve')
        series.full_name = f'{series.name} ({series.year})'
        series.sort_name = _get_sort_name(series.name)
    log.trace(f'Initialized Series.clean_name, Series.full_name, Series.sort_name')
    for template in session.query(Template).all():
        template.sort_name = _get_sort_name(template.name, r'^(a|an|the|\[\d+\])(\s)')
        log.trace(f'Template[{template.id}].sort_name = "{template.sort_name}"')

    # Commit changes
    session.commit()

    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log = contextualize(logger)
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('template', schema=None) as batch_op:
        batch_op.alter_column(
            'image_source_priority',
            existing_type=sqlite.JSON(),
            nullable=True
        )
        batch_op.drop_column('sort_name')
        batch_op.drop_index(batch_op.f('ix_template_sort_name'))

    with op.batch_alter_table('series', schema=None) as batch_op:
        batch_op.alter_column(
            'use_per_season_assets',
            existing_type=sa.BOOLEAN(),
            server_default=sa.text('0'),
            existing_nullable=False
        )
        batch_op.drop_column('sort_name')
        batch_op.drop_column('full_name')
        batch_op.drop_column('clean_name')
        batch_op.drop_index(batch_op.f('ix_series_sort_name'))

    with op.batch_alter_table('font', schema=None) as batch_op:
        batch_op.drop_column('sort_name')
        batch_op.drop_index(batch_op.f('ix_font_sort_name'))

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
