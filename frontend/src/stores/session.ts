import { defineStore } from 'pinia';
import axios from 'axios';
import type { DailyItinerary, ShortlistItem, ShortTermProfile, ChatMessage } from '@/types';
import { useShortlistStore } from '@/stores/shortlist.ts';
import { useAuthStore } from '@/stores/auth';
import { useRoute } from 'vue-router';

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
      this.loadFromLocalStorage();
      
      if (sessionId && sessionId !== this.sessionId) {
        this.sessionId = sessionId;
        await this.fetchSessionData(sessionId);
        this.saveToLocalStorage();
      }
    },

    async fetchSessionData(sessionId: string) {
      const shortlistStore = useShortlistStore();
      const auth = useAuthStore();
      if (!auth.isAuthenticated) return;
      
      try {
        const res = await axios.post(`/chat/${sessionId}`,{user_id: auth.token});
        const shortlist: ShortlistItem[] | undefined = res.data.shortlist;
        shortlist?.forEach((item) => {
          shortlistStore.addToShortlist(item);
        });
        this.chatHistory = res.data.messages;
        this.shortTermProfile = res.data.short_term_profile;
        this.title = res.data.title || 'New Chat';

        this.saveToLocalStorage();
      } catch (error) {
        console.error('Failed to fetch session:', error);
        throw error;
      }
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
      this.saveToLocalStorage();
    },

    setTitle(title: string) {
      this.title = title;
      this.saveToLocalStorage();
    },

    setSessionId(sessionId: string) {
      this.sessionId = sessionId;
      this.saveToLocalStorage();
    },

    appendHistory(data: Response) {
      const newMsg: ChatMessage = {
        role: data.role,
        message: data.message
      };
      this.chatHistory.push(newMsg);
      this.saveToLocalStorage();
    },
    
    setShortTermProfile(data: Response) {
      this.shortTermProfile = data.short_term_profile ? data.short_term_profile : null;
      this.saveToLocalStorage();
    },

    clearSession() {
      this.clearLocalStorage();
      this.sessionId = null;
      this.chatHistory = [];
      this.shortTermProfile = null;
      this.title = 'New Chat';
    },

    saveToLocalStorage() {
      if (typeof window === 'undefined') return;
      
      const data = {
        sessionId: this.sessionId,
        chatHistory: this.chatHistory,
        shortTermProfile: this.shortTermProfile,
        title: this.title,
        timestamp: Date.now()
      };
      
      localStorage.setItem(`session_${this.sessionId}`, JSON.stringify(data));
    },

    loadFromLocalStorage() {
      if (typeof window === 'undefined') return;
      
      const route = useRoute();
      const sessionId = route.params.sessionId?.toString() || null;
      
      if (!sessionId) return;
      
      const rawData = localStorage.getItem(`session_${sessionId}`);
      if (!rawData) return;
      
      try {
        const data = JSON.parse(rawData);
        
        // 24h out of date
        const isExpired = data.timestamp && (Date.now() - data.timestamp > 24 * 3600 * 1000);
        if (isExpired) {
          this.clearSession();
          return;
        }
        
        this.sessionId = data.sessionId;
        this.chatHistory = data.chatHistory || [];
        this.shortTermProfile = data.shortTermProfile;
        this.title = data.title || 'New Chat';
      } catch (error) {
        console.error('Failed to parse session data:', error);
        this.clearLocalStorage(sessionId);
      }
    },

    clearLocalStorage(sessionId?: string) {
      if (typeof window === 'undefined') return;
      
      const idToClear = sessionId || this.sessionId;
      if (idToClear) {
        localStorage.removeItem(`session_${idToClear}`);
      }
    },
    
  }
});