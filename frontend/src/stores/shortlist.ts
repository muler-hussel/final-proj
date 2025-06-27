import { defineStore } from 'pinia';

interface PlaceGeo {
  location: [number, number]; // [lat, lng]
  viewport: [[number, number], [number, number]]; // [northeast, southwest]
}

interface PlacePhoto {
  height: number;
  width: number;
  html_attributions?: string[];
  photo_reference: string;
}

interface PlaceReview {
  review: string;
  type: 0 | 1 | 2 | 3; // 0-Google latest, etc.
}

interface PlaceInfo {
  photos?: PlacePhoto[];
  description?: string;
  website?: string;
  address?: string;
  weekday_text?: string[];
  rating?: number;
  reviews?: PlaceReview[];
  review_updated?: Date;
  pros?: string[];
  contra?: string[];
  summarized_review?: string;
  prices?: string[];
}

export interface ShortlistItem {
  name: string;
  type: 'city' | 'attraction';
  place_id: string;
  city?: string; // if type='attraction'
  tags?: string[]; //'museum', 'history'
  info?: PlaceInfo;
  sub_items?: string[]; // if type='city'
  geometry?: PlaceGeo;
}

export const useShortlistStore = defineStore('shortlist', {
  state: () => ({
    items: [] as ShortlistItem[],
  }),
  actions: {
    addToShortlist(item: ShortlistItem) {
      this.items.push(item);
    },
    removeFromShortlist(placeId: string) {
      this.items = this.items.filter(item => item.place_id !== placeId);
    },
  },
  getters: {
    shortlistNum(): number {
      return this.items.length;
    },
  },
});