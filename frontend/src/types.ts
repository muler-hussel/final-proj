
interface PlaceGeo {
  location: [number, number]; // [lat, lng]
  viewport: [[number, number], [number, number]]; // [northeast, southwest]
}

interface PlaceReview {
  review: string;
  type: 0 | 1 | 2 | 3; // 0-Google latest, etc.
}

interface PlaceInfo {
  recommend_reason?: string;
  website?: string;
  address?: string;
  weekday_text?: string[];
  rating?: number;
  reviews?: PlaceReview[];
  pros?: string[];
  contra?: string[];
  summarized_review?: string;
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
  sub_items?: string[]; // if type='city'
  geometry?: PlaceGeo;
  updated_time?: string | null
  status?: string;
  photos: string[];
}

export interface DailyItinerary {
  date: number;
  place_name: string;
  start_time: string;
  end_time: string;
}