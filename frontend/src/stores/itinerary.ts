import { defineStore } from 'pinia';
import { useSessionStore } from '@/stores/session';
import type { DailyItinerary } from '@/types';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

export const useItineraryStore = defineStore('drawer', {
  state: () => ({
    currentIndex: null as number | null,
    newItinerary: [] as DailyItinerary[] | [],
    itineraryOpen: false,
  }),
  actions: {
    async handleSave() {
      if (this.currentIndex) {
        const useSession = useSessionStore();
        if (useSession.chatHistory[this.currentIndex] && useSession.chatHistory[this.currentIndex].role === 'ai') {
          useSession.chatHistory[this.currentIndex].message.itinerary = this.newItinerary;
          const auth = useAuthStore();
          try {
            await axios.post(`chat/${useSession.sessionId}/updateItinerary`, {user_id: auth.token, itinerary: this.newItinerary, chat_idx: this.currentIndex});
            this.clearChange();
          } catch (error) {
            console.error("Fail to update itinerary:", error);
          }
        }
      }
    },

    clearChange() {
      this.currentIndex = null;
      this.newItinerary = [];
      this.itineraryOpen = false;
    },

    ifChanged() {
      if (this.currentIndex) {
        const useSession = useSessionStore();
        return JSON.stringify(useSession.chatHistory[this.currentIndex].message.itinerary) === JSON.stringify(this.newItinerary);
      }
    }
  }
})