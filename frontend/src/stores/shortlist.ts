import { defineStore } from 'pinia';
import type { ShortlistItem } from '@/types';

export const useShortlistStore = defineStore('shortlist', {
  state: () => ({
    items: new Map<string, ShortlistItem>(),
  }),
  actions: {
    addToShortlist(item: ShortlistItem) {
      this.items.set(item.name, item);
    },
    removeFromShortlist(placeName: string) {
      this.items.delete(placeName);
    },
  },
  getters: {
    shortlistNum: (state) => state.items.size,
    hasItem: (state) => (placeName: string) => state.items.has(placeName),
    itemList: (state) => Array.from(state.items.values()),
  },
});