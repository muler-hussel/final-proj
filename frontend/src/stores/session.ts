import { defineStore } from 'pinia';
import axios from 'axios';
import type { DailyItinerary, ShortlistItem, ShortTermProfile, ChatMessage } from '@/types';
import { useShortlistStore } from '@/stores/shortlist.ts';
import { useAuthStore } from '@/stores/auth';
import { useUserBehaviorStore } from './userBehavior';
import { useUserSessionsStore } from '@/stores/userSessions';

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
      if (!sessionId) return;
      const result = this.loadFromLocalStorage(sessionId);
      if (!result && sessionId && sessionId !== this.sessionId) {
        this.sessionId = sessionId;
        await this.fetchSessionData(sessionId);
        this.saveToLocalStorage();
      }
    },

    async fetchSessionData(sessionId: string) {
      const shortlistStore = useShortlistStore();
      const auth = useAuthStore();
      if (!auth.isAuthenticated) return;
      const userBehavior = useUserBehaviorStore();
      
      try {
        const res = await axios.post(`/chat/${sessionId}`,{user_id: auth.token});
        const shortlist: ShortlistItem[] | undefined = res.data.shortlist;

        shortlistStore.initialize(sessionId);
        shortlist?.forEach((item) => {
          shortlistStore.addToShortlist(item);
        });
        this.chatHistory = res.data.messages;
        this.shortTermProfile = res.data.short_term_profile;
        this.title = res.data.title || 'New Chat';

        this.saveToLocalStorage();
        shortlistStore.saveToLocalStorage();
        userBehavior.initialize(sessionId);
      } catch (error) {
        console.error('Failed to fetch session:', error);
        throw error;
      }
    },

    sendMessage(content: string) {
      if (!this.sessionId) return;

      const userSessions = useUserSessionsStore();
      const newMsg: ChatMessage = {
        role: 'user',
        message: {
          content: content
        }
      };
      
      this.chatHistory.push(newMsg);
      this.saveToLocalStorage();
      userSessions.updateSessionTime(this.sessionId);
    },

    async setTitle(title: string) {
      if (!this.sessionId) return;
      const auth = useAuthStore();
      if (!auth.isAuthenticated) return;
      const userSessions = useUserSessionsStore();
      this.title = title;
      this.saveToLocalStorage();
      userSessions.updateSessionTime(this.sessionId);
      try {
        await axios.post(`/chat/${this.sessionId}/title`, {user_id: auth.token, title: title});
      } catch (error) {
        console.error('Fail to save title:', error);
        throw error;
      }
      
    },

    setSessionId(sessionId: string) {
      this.sessionId = sessionId;
      this.saveToLocalStorage();
      const userSessions = useUserSessionsStore();
      userSessions.updateSessionTime(this.sessionId);
    },

    appendHistory(data: Response) {
      if (!this.sessionId) return;
      
      const newMsg: ChatMessage = {
        role: data.role,
        message: data.message
      };
      this.chatHistory.push(newMsg);
      this.saveToLocalStorage();
      const userSessions = useUserSessionsStore();
      userSessions.updateSessionTime(this.sessionId);
    },

    // Update recommended places infomation after enrich
    updateRecommendation(placeName: string, newData: Partial<ShortlistItem>) {
      this.chatHistory.forEach((msg) => {
        if (msg.role === 'ai' && msg.message.recommendations) {
          const targetIndex = msg.message.recommendations.findIndex(
            (item) => item.name === placeName
          );
          if (targetIndex !== -1) {
            msg.message.recommendations[targetIndex] = {
              ...msg.message.recommendations[targetIndex],
              ...newData,
            };
            this.saveToLocalStorage();
          }
        }
      });
    },
    
    setShortTermProfile(data: Response) {
      this.shortTermProfile = data.short_term_profile ? data.short_term_profile : null;
      this.saveToLocalStorage();
    },

    clearSession() {
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

    loadFromLocalStorage(sessionId: string) {
      if (typeof window === 'undefined') return false;
      const rawData = localStorage.getItem(`session_${sessionId}`);
      if (!rawData) return false;
      
      try {
        const data = JSON.parse(rawData);
        
        // 24h out of date
        const isExpired = data.timestamp && (Date.now() - data.timestamp > 24 * 3600 * 1000);
        if (isExpired) {
          this.clearSession();
          return false;
        }
        
        this.sessionId = data.sessionId;
        this.chatHistory = data.chatHistory || [];
        this.shortTermProfile = data.shortTermProfile;
        this.title = data.title || 'New Chat';

        const shortlistStore = useShortlistStore();
        const auth = useAuthStore();
        if (!auth.isAuthenticated) return;
        const userBehavior = useUserBehaviorStore();
        shortlistStore.initialize(sessionId);
        userBehavior.initialize(sessionId);
        return true;
      } catch (error) {
        console.error('Failed to parse session data:', error);
        this.clearLocalStorage(sessionId);
      }
    },

    clearLocalStorage(sessionId?: string) {
      if (typeof window === 'undefined') return;
      
      const idToClear = sessionId || this.sessionId;
      this.clearSession();
      if (idToClear) {
        localStorage.removeItem(`session_${idToClear}`);
      }
    },
    
  }
});