from typing import Literal

from app.schemas.base import Base


ConditionField = Literal[
   'auto_split_titles',
   'card_filename_format',
   'card_type',
   'data_source_id',
   'directory',
   'emby_id',
   'episode_text_format',
   'extras',
   'font_color',
   'font_id',
   'font_interline_spacing',
   'font_interword_spacing',
   'font_kerning',
   'font_size',
   'font_stroke_width',
   'font_title_case',
   'font_vertical_shift',
   'has_no_episodes',
   'hide_episode_text',
   'hide_season_text',
   'id',
   'image_source_priority',
   'imdb_id',
   'jellyfin_id',
   'libraries',
   'match_titles',
   'missing_cards',
   'name',
   'season_titles',
   'skip_localized_images',
   'sonarr_id',
   'status',
   'sync_id',
   'sync_specials',
   'tmdb_id',
   'translations',
   'tvdb_id',
   'tvrage_id',
   'unwatched_style',
   'use_per_season_assets',
   'watched_style',
   'year',
]

ConditionExpression = Literal[
    'equals',
    'does not equal',
    'contains',
    'does not contain',
    'starts with',
    'does not start with',
    'ends with',
    'does not end with',
    'matches',
    'does not match',
    'is less than',
    'is less than or equal to',
    'is greater than',
    'is greater than or equal to',
    'is null',
    'is not null',
    'is true',
    'is false',
    'is empty',
    'is not empty',
    'includes',
    'does not include',
]


class SeriesCondition(Base):
    field: ConditionField
    expression: ConditionExpression
    reference: str | None

class SeriesFilter(Base):
    conditions: list[SeriesCondition]
