
interface Page {
  items: any[];
  total: number;
  page: number;
  size: number;
  pages: number;
}


export type ConditionExpression = (
  'equals'
  | 'does not equal'
  | 'contains'
  | 'does not contain'
  | 'starts with'
  | 'does not start with'
  | 'ends with'
  | 'does not end with'
  | 'matches'
  | 'does not match'
  | 'is less than'
  | 'is less than or equal to'
  | 'is greater than'
  | 'is greater than or equal to'
  | 'is null'
  | 'is not null'
  | 'is true'
  | 'is false'
  | 'is empty'
  | 'is not empty'
  | 'includes'
  | 'does not include'
)

export type ConditionField = (
  'auto_split_titles'
  | 'card_filename_format'
  | 'card_type'
  | 'data_source_id'
  | 'directory'
  | 'emby_id'
  | 'episode_text_format'
  | 'extras'
  | 'font_color'
  | 'font_id'
  | 'font_interline_spacing'
  | 'font_interword_spacing'
  | 'font_kerning'
  | 'font_size'
  | 'font_stroke_width'
  | 'font_title_case'
  | 'font_vertical_shift'
  | 'has_no_episodes'
  | 'hide_episode_text'
  | 'hide_season_text'
  | 'id'
  | 'image_source_priority'
  | 'imdb_id'
  | 'jellyfin_id'
  | 'libraries'
  | 'match_titles'
  | 'missing_cards'
  | 'name'
  | 'season_titles'
  | 'skip_localized_images'
  | 'sonarr_id'
  | 'status'
  | 'sync_id'
  | 'sync_specials'
  | 'tmdb_id'
  | 'translations'
  | 'tvdb_id'
  | 'tvrage_id'
  | 'unwatched_style'
  | 'use_per_season_assets'
  | 'watched_style'
  | 'year'
)

export type MediaServer = 'Emby' | 'Jellyfin' | 'Plex';

export interface MediaServerLibrary {
  interface: MediaServer;
  interface_id: number;
  name: string;
}

export type SeriesOrder = (
  | "alphabetical"
  | "reverse-alphabetical"
  | "cards"
  | "reverse-cards"
  | "year"
  | "id"
  | "reverse-id"
  | "sync"
  | "year"
  | "reverse-year"
);

export type Status = 'disabled' | 'monitored' | 'unmonitored';

export interface SeriesCondition {
  field: ConditionField;
  expression: ConditionExpression;
  reference: string | null;
}

export interface SeriesFilter {
  condictions: SeriesCondition[];
}

export interface SeriesOverview {
  id: number;
  name: string;
  full_name: string;
  sort_name: string;
  year: number;
  poster_url: string;
  libraries: MediaServerLibrary[];
  status: string;
}

export interface SeriesOverviewPage extends Page {
  items: SeriesOverview[];
}
