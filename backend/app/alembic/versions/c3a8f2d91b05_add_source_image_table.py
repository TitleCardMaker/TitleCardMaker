"""Add source_image table

Revision ID: c3a8f2d91b05
Revises: 39bbc83023cb
Create Date: 2026-04-17 00:00:00.000000
"""

from datetime import datetime
import re

from alembic import op
from imagesize import get as im_get
import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.sources import get_imagemagick_interface
from app.logging.logger import log

# Revision identifiers, used by Alembic.
revision = 'c3a8f2d91b05'
down_revision = '39bbc83023cb'
branch_labels = None
depends_on = None

# Minimal model definitions for the data migration
from sqlalchemy.ext.declarative import declarative_base
_Base = declarative_base()


class _Episode(_Base):
    __tablename__ = 'episode'
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    series_id = sa.Column(sa.Integer)
    season_number = sa.Column(sa.Integer)
    episode_number = sa.Column(sa.Integer)
    source_file = sa.Column(sa.String)


class _Series(_Base):
    __tablename__ = 'series'
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name = sa.Column(sa.String)
    year = sa.Column(sa.Integer)


class _SourceImage(_Base):
    __tablename__ = 'source_image'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    episode_id = sa.Column(sa.Integer, sa.ForeignKey('episode.id'), unique=True)
    created = sa.Column(sa.DateTime)
    source_file = sa.Column(sa.String)
    filesize = sa.Column(sa.Integer)
    width = sa.Column(sa.Integer)
    height = sa.Column(sa.Integer)
    source = sa.Column(sa.String)


_SOURCE_PATTERN = re.compile(r'^s(\d+)e(\d+)\.jpg$', re.IGNORECASE)


def upgrade() -> None:
    log.debug(f'Upgrading SQL Schema to Version[{revision}]..')

    op.create_table(
        'source_image',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('episode_id', sa.Integer(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.Column('source_file', sa.String(), nullable=False),
        sa.Column('filesize', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['episode_id'], ['episode.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('episode_id'),
    )
    with op.batch_alter_table('source_image', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_source_image_id'), ['id'], unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_source_image_episode_id'),
            ['episode_id'],
            unique=True,
        )

    # Backfill: scan the source directory and create records for files
    # that match the standard sXeY.jpg naming pattern.
    try:
        from app.settings import settings
        source_dir = settings.source_directory
    except Exception:
        log.warning('Cannot access settings during migration - skipping backfill')
        log.debug(f'Upgraded SQL Schema to Version[{revision}]')
        return

    session = Session(bind=op.get_bind())

    # Build a lookup: path_safe_name -> list of episodes
    episodes = session.query(_Episode).all()
    series_map = {s.id: s for s in session.query(_Series).all()}

    # Build a lookup: (series_id, season, episode_number) -> _Episode
    ep_lookup: dict[tuple[int, int, int], _Episode] = {}
    for ep in episodes:
        ep_lookup[(ep.series_id, ep.season_number, ep.episode_number)] = ep

    # Build a lookup: path_safe_folder_name -> series_id
    def _path_safe(name: str, year: int) -> str:
        return f'{name} ({year})'

    folder_to_series_id: dict[str, int] = {}
    for s in series_map.values():
        folder_to_series_id[_path_safe(s.name, s.year)] = s.id

    records_created = 0
    if source_dir.is_dir():
        for series_folder in source_dir.iterdir():
            if not series_folder.is_dir():
                continue

            series_id = folder_to_series_id.get(series_folder.name)
            if series_id is None:
                continue

            for image_file in series_folder.glob('*.jpg'):
                match = _SOURCE_PATTERN.match(image_file.name)
                if not match:
                    continue

                season = int(match.group(1))
                ep_num = int(match.group(2))
                ep = ep_lookup.get((series_id, season, ep_num))
                if ep is None:
                    continue

                # Skip if a record already exists (shouldn't happen but
                # be safe in case migration runs twice)
                existing = (
                    session.query(_SourceImage)
                        .filter_by(episode_id=ep.id)
                        .first()
                )
                if existing:
                    continue

                mtime = datetime.fromtimestamp(image_file.stat().st_mtime)
                width, height = im_get(image_file)

                record = _SourceImage(
                    episode_id=ep.id,
                    created=mtime,
                    source_file=str(image_file.resolve()),
                    filesize=image_file.stat().st_size,
                    width=int(width),
                    height=int(height),
                    source='unknown',
                )
                session.add(record)
                records_created += 1

    session.commit()
    log.debug(
        f'Backfilled {records_created:,} SourceImage records from disk'
    )
    log.debug(f'Upgraded SQL Schema to Version[{revision}]')


def downgrade() -> None:
    log.debug(f'Downgrading SQL Schema to Version[{down_revision}]..')

    with op.batch_alter_table('source_image', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_source_image_episode_id'))
        batch_op.drop_index(batch_op.f('ix_source_image_id'))

    op.drop_table('source_image')

    log.debug(f'Downgraded SQL Schema to Version[{down_revision}]')
