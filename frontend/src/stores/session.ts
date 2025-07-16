import { defineStore } from 'pinia';
import axios from 'axios';
import type { DailyItinerary, ShortlistItem, ShortTermProfile, ChatMessage } from '@/types';
import { useShortlistStore } from '@/stores/shortlist.ts';
import { useAuthStore } from '@/stores/auth';

interface Response {
  role: string;
  message: {
    content?: string;
    recommendations?: ShortlistItem[];
    itinerary?: DailyItinerary[];
  }
  short_term_profile?: ShortTermProfile;
  shortlist?: ShortlistItem[];
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessionId: null as string | null,
    chatHistory: [] as ChatMessage[],
    shortTermProfile: null as ShortTermProfile | null,
    title: 'New Trip',
  }),

  actions: {
    async initializeSession(sessionId?: string) {
      if (sessionId) {
        this.sessionId = sessionId;
        await this.fetchSessionData(sessionId); 
      }
    },

    async fetchSessionData(sessionId: string) {
      const shortlistStore = useShortlistStore();
      const auth = useAuthStore();
      if (!auth.isAuthenticated) return;
      
      const res = await axios.post(`/chat/${sessionId}`,{user_id: auth.token});
      this.chatHistory = res.data.messages;
      this.shortTermProfile = res.data.short_term_profile;
      this.title = res.data.title || 'New Chat';
      const shortlist: ShortlistItem[] | undefined = res.data.shortlist;
      shortlist?.forEach((item) => {
        shortlistStore.addToShortlist(item);
      });
    },

    async sendMessage(content: string) {
      if (!this.sessionId) return;
      
      const newMsg: ChatMessage = {
        role: 'user',
        message: {
          content: content
        }
      };
      
      this.chatHistory.push(newMsg);
    },

    setTitle(title: string) {
      this.title = title;
    },

    setSessionId(sessionId: string) {
      this.sessionId = sessionId;
    },

    appendHistory(data: Response) {
      const newMsg: ChatMessage = {
        role: data.role,
        message: data.message
      };
      this.chatHistory.push(newMsg);
    },
    
    setShortTermProfile(data: Response) {
      this.shortTermProfile = data.short_term_profile ? data.short_term_profile : null;
    },

    clearSession() {
      this.sessionId = null;
      this.chatHistory = [];
      this.shortTermProfile = null;
      this.title = 'New Chat';
    }
  }
});