import { defineStore } from 'pinia';
import { useAuthStore } from '@/stores/auth';
import axios from 'axios';

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
    async getSessions() {
      const auth = useAuthStore();
      if (auth.isAuthenticated) {
        try {
          const userId = auth.token;
          const res = await axios.post("/chat/allSessions", { user_id: userId });
          this.sessions = res.data;
        } catch (error) {
          console.error("Failed to fetch sessions:", error);
        }
      }
    },

    addToSessions(session_id: string, title: string) {
      if (!this.sessions.some(s => s.session_id === session_id)) {
        this.sessions.unshift({
          session_id,
          title,
          update_time: new Date().toISOString()
        });
      }
    },

    updateSessionTime(session_id: string) {
      const index = this.sessions.findIndex(s => s.session_id === session_id);
      if (index >= 0) {
        this.sessions[index].update_time = new Date().toISOString();
        const [session] = this.sessions.splice(index, 1);
        this.sessions.unshift(session);
      }
    },

    setCurrentSession(sessionId: string | null) {
      this.currentSessionId = sessionId;
    },
    
    getCurrentSession(): SessionInfo | null {
      return this.sessions.find(s => s.session_id === this.currentSessionId) || null;
    }
  },
});