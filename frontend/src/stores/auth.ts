import { defineStore } from 'pinia';
import { useUserSessionsStore } from './userSessions';
import { useSessionStore } from './session';
import { useShortlistStore } from './shortlist';
import { useUserBehaviorStore } from './userBehavior';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null as string | null,
    tokenExpires: null as number | null
  }),
  actions: {
    setToken(token: string) {
      if (!token) return;
      const expires = Date.now() + 3600 * 1000 * 24;
      this.token = token;
      this.tokenExpires = expires;
      localStorage.setItem('auth', JSON.stringify({
        token,
        expires
      }));
    },
    
    clearToken() {
      this.clearStorage();
      this.token = null;
      this.tokenExpires = null;
      localStorage.removeItem('auth');
    },

    async initialize() {
      const raw = localStorage.getItem('auth');
      if (!raw) return;

      try {
        const { token, expires } = JSON.parse(raw);
        if (expires > Date.now()) {
          this.token = token;
          this.tokenExpires = expires;
        } else {
          this.clearToken();
        }
      } catch {
        this.clearToken();
      }
    },

    clearStorage() {
      const userSessions = useUserSessionsStore();
      const useSession = useSessionStore();
      const useShortlist = useShortlistStore();
      const userBehavior = useUserBehaviorStore();

      const allSessions = userSessions.sessions;
      for (const session of allSessions) {
        const session_id = session.session_id;
        useSession.clearLocalStorage(session_id);
        useShortlist.clearLocalStorage(session_id);
        userBehavior.clearStorage(session_id);
      }
      userSessions.clearStorage();
    }
  },
  getters: {
    isAuthenticated(state): boolean {
      return !!state.token && !!state.tokenExpires && state.tokenExpires > Date.now();
    },
  }
});