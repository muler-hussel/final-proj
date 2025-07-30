
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

export interface DiscardPlace {
  name: string;
  duration: number; //Hours
  extendedProps: {
    openingHours: string[],
    type: string,
  }
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

export interface RouteStep {
  step_mode: string;
  step_duration: string;
  departure_stop: string | null;
  departure_time: string | null;
  arrival_stop: string | null;
  arrival_time: string | null;
  transit_name: string | null;
  color: string | null;
}

export interface DailyItinerary {
  date: number;
  type: string;
  place_name: string | null;
  start_time: string;
  end_time: string;
  commute_mode: string | null;
  route_steps: RouteStep[] | null;
  discarded_places: DiscardPlace[];
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