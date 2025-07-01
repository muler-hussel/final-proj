import { defineStore } from 'pinia';
import axios from 'axios';
import type { ShortlistItem } from '@/types';

interface ChatMessage {
  role: string;
  message: {
    content?: string;
    recommendations?: ShortlistItem[];
  }
}

interface TravelSlots {
  destination: string | null;
  date: string | null;
  people: string | null;
  preferences: string | null;
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    sessionId: null as string | null,
    chatHistory: [] as ChatMessage[],
    currentSlots: null as TravelSlots | null,
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
      this.currentSlots = res.data.slots;
      this.title = res.data.title || 'New Chat';
    },

    async sendMessage(content: string) {
      if (!this.sessionId) return;
      
      const newMsg: ChatMessage = {
        role: 'user',
        message: {
          response: content
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

    appendHistory(content: ChatMessage) {
      this.chatHistory.push(content);
    },

    clearSession() {
      this.sessionId = null;
      this.chatHistory = [];
      this.currentSlots = null;
      this.title = 'New Chat';
    }
  }
});