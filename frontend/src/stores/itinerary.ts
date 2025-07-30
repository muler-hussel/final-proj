import { defineStore } from 'pinia';
import { useSessionStore } from '@/stores/session';
import type { DailyItinerary } from '@/types';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import { toRaw } from 'vue';

export const useItineraryStore = defineStore('itinerary', {
  state: () => ({
    currentIndex: null as number | null,
    extractFns: {} as Record<string, () => DailyItinerary[]>,
    itineraryOpen: false,
  }),
  actions: {
    registerExtractFn(fn: () => DailyItinerary[]) {
      const useSession = useSessionStore();
      const sessionId = useSession.sessionId;
      if (sessionId) {
        this.extractFns[sessionId] = fn;
      }
    },

    getExtractFn(sessionId: string) {
      return this.extractFns[sessionId];
    },
    
    async handleSave() {
      if (this.currentIndex && this.extractFns) {
        const useSession = useSessionStore();
        const sessionId = useSession.sessionId;
        if (!sessionId) return;
        const extract = this.getExtractFn(sessionId);
        if (extract) {
          const newItinerary = extract();
          if (useSession.chatHistory[this.currentIndex] && useSession.chatHistory[this.currentIndex].role === 'ai') {
            useSession.chatHistory[this.currentIndex].message.itinerary = newItinerary;
            const auth = useAuthStore();
            try {
              await axios.post(`chat/${useSession.sessionId}/saveItinerary`, {user_id: auth.token, itinerary: newItinerary, chat_idx: this.currentIndex});
              this.clearChange();
              useSession.saveToLocalStorage();
            } catch (error) {
              console.error("Fail to save itinerary:", error);
            }
          }
        }
      }
    },

    async handleUpdate() {
      if (this.currentIndex && this.extractFns) {
        const useSession = useSessionStore();
        const sessionId = useSession.sessionId;
        if (!sessionId) return;
        const extract = this.getExtractFn(sessionId);
        if (extract) {
          const newItinerary = extract();
          if (useSession.chatHistory[this.currentIndex] && useSession.chatHistory[this.currentIndex].role === 'ai') {
            useSession.chatHistory[this.currentIndex].message.itinerary = newItinerary;
            const auth = useAuthStore();
            try {
              await axios.post(`chat/${useSession.sessionId}/updateItinerary`, {user_id: auth.token, itinerary: newItinerary, chat_idx: this.currentIndex});
              this.clearChange();
              useSession.saveToLocalStorage();
            } catch (error) {
              console.error("Fail to save itinerary:", error);
            }
          }
        }
      }
    },

    clearChange() {
      this.currentIndex = null;
      this.itineraryOpen = false;
      this.extractFns = {};
    },

    ifChanged() {
      if (this.currentIndex) {
        const useSession = useSessionStore();
        const sessionId = useSession.sessionId;
        if (!sessionId) return false;
        const extract = this.getExtractFn(sessionId);
        if (extract) {
          const newItinerary = extract();
          const proxyArray = useSession.chatHistory[this.currentIndex].message.itinerary;
          const rawArray = toRaw(proxyArray); // Get an array in the proxy reactive data
          return JSON.stringify(rawArray) != JSON.stringify(newItinerary);
        }
      }
      return false;
    }
  }
})