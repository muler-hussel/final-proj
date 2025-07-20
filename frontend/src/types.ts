
interface PlaceGeo {
  location: [number, number]; // [lat, lng]
  viewport: [[number, number], [number, number]]; // [northeast, southwest]
}

interface PlaceReview {
  review: string;
  type: 0 | 1 | 2 | 3; // 0-Google latest, etc.
}

interface PlaceCard {
  place_name: string;
  description: string;
  recommend_reason: string;
}

interface PlaceInfo {
  recommend_reason?: string;
  website?: string;
  address?: string;
  weekday_text?: string[];
  rating?: number;
  reviews?: PlaceReview[];
  pros?: string[];
  cons?: string[];
  advice_trip?: string;
  prices?: string[];
  price_level?: number
  total_ratings?: number
}

export interface ShortlistItem {
  name: string;
  type?: string;
  place_id?: string;
  description: string;
  tags?: string[]; //'museum', 'history'
  info?: PlaceInfo;
  sub_items: ShortlistItem[]; // if type='city'
  geometry?: PlaceGeo;
  updated_time?: string | null
  status?: string;
  photos: string[];
}

export interface DailyItinerary {
  date: number;
  type: string;
  place_name?: string;
  start_time: string;
  end_time: string;
  commute_mode?: string;
}

export interface ChatMessage {
  role: string;
  message: {
    content?: string;
    recommendations?: ShortlistItem[];
    populars?: ShortlistItem[];
    itinerary?: DailyItinerary[];
  }
}

export interface TagWeight{
  tag: string;
  weight: number;
  consecutive_sessions?: number;
}

export interface ShortTermProfile{
  preferences: Record<string, TagWeight>;
  avoids: string[];
}