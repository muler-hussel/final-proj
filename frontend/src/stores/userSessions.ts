import { defineStore } from 'pinia';
import { useAuthStore } from '@/stores/auth';
import axios from 'axios';
import { useSessionStore } from './session';
import { useShortlistStore } from './shortlist';
import { useUserBehaviorStore } from './userBehavior';

interface SessionInfo {
  session_id: string;
  title: string;
  update_time: string;
}

export const useUserSessionsStore = defineStore('userSessions', {
  state: () => ({
    sessions: [] as SessionInfo[],
    currentSessionId: null as string | null,
  }),
  actions: {
    async initialize() {
      if (typeof window === 'undefined') return;

      const rawData = localStorage.getItem('user_sessions_data');
      if (!rawData) {
        await this.getSessions();
        return;
      }

      try {
        const parsed = JSON.parse(rawData);
        if (Array.isArray(parsed?.sessions)) {
          this.sessions = parsed.sessions;
        }
        if (parsed?.currentSessionId) {
          this.currentSessionId = parsed.currentSessionId;
        }
      } catch (error) {
        console.error('Failed to parse sessions data:', error);
        this.clearStorage();
      }
    },

    async getSessions() {
      if (this.sessions.length > 0) {
        return;
      }
      const auth = useAuthStore();
      if (auth.isAuthenticated) {
        try {
          const userId = auth.token;
          console.log(userId)
          const res = await axios.post("/chat/allSessions", { user_id: userId });
          this.sessions = [...res.data];
          this.saveToStorage();
        } catch (error) {
          console.error("Failed to fetch sessions:", error);
        }
      }
    },

    updateSession(session_id: string, title: string) {
      const index = this.sessions.findIndex(s => s.session_id === session_id);
      const now = new Date().toISOString();
      if (index >= 0) {
        this.sessions[index] = {
          ...this.sessions[index],
          title,
          session_id,
          update_time: now
        };
        this.sessions.sort((a, b) => 
          new Date(b.update_time).getTime() - new Date(a.update_time).getTime()
        );
      } else {
        this.sessions.unshift({
          session_id,
          title,
          update_time: now
        });
      }
      this.saveToStorage();
    },

    updateSessionTime(session_id: string) {
      const index = this.sessions.findIndex(s => s.session_id === session_id);
      if (index >= 0) {
        this.sessions[index].update_time = new Date().toISOString();
        const [session] = this.sessions.splice(index, 1);
        this.sessions.unshift(session);
        this.saveToStorage();
      }
    },

    setCurrentSession(sessionId: string | null) {
      this.currentSessionId = sessionId;
      this.saveToStorage();
    },
    
    getCurrentSession(): SessionInfo | null {
      return this.sessions.find(s => s.session_id === this.currentSessionId) || null;
    },

    async deleteSession(sessionId: string) {
      const auth = useAuthStore();
      if (auth.isAuthenticated) {
        try {
          const updatedSessions = this.sessions.filter(s => s.session_id != sessionId);
          this.sessions = updatedSessions;
          this.saveToStorage();

          const session = useSessionStore();
          session.clearLocalStorage(sessionId);

          const useShortlist = useShortlistStore();
          useShortlist.clearLocalStorage(sessionId);

          const userBehavior = useUserBehaviorStore();
          userBehavior.clearStorage(sessionId);
          
          await axios.post(`chat/${sessionId}/delete`, {user_id: auth.token});
        } catch (error) {
          console.error("Failed to delete session:", error);
        }
      }
    },

    saveToStorage() {
      if (typeof window === 'undefined') return;
      
      const data = {
        sessions: this.sessions,
        currentSessionId: this.currentSessionId,
      };

      localStorage.setItem('user_sessions_data', JSON.stringify(data));
    },

    clearStorage() {
      if (typeof window === 'undefined') return;
      localStorage.removeItem('user_sessions_data');
    },
  },
});