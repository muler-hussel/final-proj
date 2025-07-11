import { defineStore } from 'pinia';
import axios from 'axios';
import type { DailyItinerary, ShortlistItem } from '@/types';

interface ChatMessage {
  role: string;
  message: {
    content?: string;
    recommendations?: ShortlistItem[];
    itinerary?: DailyItinerary[];
  }
}

interface TagWeight{
  tag: string;
  weight: number;
  consecutive_sessions?: number;
}

interface ShortTermProfile{
  preferences: Record<string, TagWeight>;
  avoids: string[];
}

interface Response {
  role: string;
  message: {
    content?: string;
    recommendations?: ShortlistItem[];
    itinerary?: DailyItinerary[];
  }
  short_term_profile?: ShortTermProfile;
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
      const res = await axios.get(`/chat/${sessionId}`);
      this.chatHistory = res.data.messages;
      this.shortTermProfile = res.data.short_term_profile;
      this.title = res.data.title || 'New Chat';
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