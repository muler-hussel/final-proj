import { defineStore } from 'pinia';
import type { ShortlistItem } from '@/types';
import { reactive } from 'vue';

export const useShortlistStore = defineStore('shortlist', {
  state: () => ({
    items: reactive(new Map<string, ShortlistItem>()),
  }),
  actions: {
    addToShortlist(item: ShortlistItem) {
      this.items.set(item.name, item);
      this.saveToLocalStorage();
    },

    removeFromShortlist(placeName: string) {
      this.items.delete(placeName);
      this.saveToLocalStorage();
    },

    clearShortlist() {
      this.items = new Map<string, ShortlistItem>();
      this.saveToLocalStorage();
    },

    initialize() {
      if (typeof window === 'undefined') return;
      
      const rawData = localStorage.getItem('shortlist_items');
      if (!rawData) return;

      try {
        const parsedData = JSON.parse(rawData);
        if (Array.isArray(parsedData)) {
          parsedData.forEach(item => {
            if (item?.name) {
              this.items.set(item.name, item);
            }
          });
        }
      } catch (error) {
        console.error('Failed to parse shortlist data:', error);
        this.clearLocalStorage();
      }
    },

    saveToLocalStorage() {
      if (typeof window === 'undefined') return;
      
      const dataToSave = this.itemList; // Change map to list. Map cannot be serialized
      localStorage.setItem(
        'shortlist_items',
        JSON.stringify(dataToSave)
      );
    },

    clearLocalStorage() {
      if (typeof window === 'undefined') return;
      localStorage.removeItem('shortlist_items');
    },

  },
  getters: {
    shortlistNum: (state) => state.items.size,
    hasItem: (state) => (placeName: string) => state.items.has(placeName),
    itemList: (state) => Array.from(state.items.values()),
  },
});