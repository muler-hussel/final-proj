import { defineStore } from 'pinia';
import type { ShortlistItem } from '@/types';
import { reactive } from 'vue';
import { useUserSessionsStore } from '@/stores/userSessions';

export const useShortlistStore = defineStore('shortlist', {
  state: () => ({
    items: reactive(new Map<string, ShortlistItem>()),
    sessionId: null as string | null,
  }),
  actions: {
    addToShortlist(item: ShortlistItem) {
      if (!this.sessionId) throw new Error('No active session');
      
      const userSessions = useUserSessionsStore();
      this.items.set(item.name, item);
      this.saveToLocalStorage();
      userSessions.updateSessionTime(this.sessionId);
    },

    removeFromShortlist(placeName: string) {
      if (!this.sessionId) throw new Error('No active session');
      
      const userSessions = useUserSessionsStore();
      this.items.delete(placeName);
      this.saveToLocalStorage();
      userSessions.updateSessionTime(this.sessionId);
    },

    clearShortlist() {
      this.items = new Map<string, ShortlistItem>();
      this.sessionId = null;
    },

    initialize(sessionId: string) {
      if (typeof window === 'undefined' || !sessionId) return;
      this.sessionId = sessionId;
      const rawData = localStorage.getItem(`shortlist_items:${sessionId}`);
      
      if (!rawData) {
        this.sessionId = sessionId;
        this.saveToLocalStorage();
        return;
      }

      try {
        const parsedData = JSON.parse(rawData);
        for (const item of parsedData) {
          if (item?.name) this.items.set(item.name, item);
        }
      } catch (error) {
        console.error('Failed to parse shortlist data:', error);
        this.clearLocalStorage(sessionId);
      }
    },

    saveToLocalStorage() {
      if (typeof window === 'undefined') return;
      
      const dataToSave = this.itemList; // Change map to list. Map cannot be serialized
      localStorage.setItem(
        `shortlist_items:${this.sessionId}`,
        JSON.stringify(dataToSave)
      );
    },

    clearLocalStorage(sessionId: string) {
      if (typeof window === 'undefined') return;
      this.clearShortlist();
      localStorage.removeItem(`shortlist_items:${sessionId}`);
    },

  },
  getters: {
    shortlistNum: (state) => state.items.size,
    hasItem: (state) => (placeName: string) => state.items.has(placeName),
    itemList: (state) => Array.from(state.items.values()),
  },
});