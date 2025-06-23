import { defineStore } from 'pinia';

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
      this.token = null;
      this.tokenExpires = null;
      localStorage.removeItem('auth');
    },
    initialize() {
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
    }
  },
  getters: {
    isAuthenticated(state): boolean {
      return !!state.token && !!state.tokenExpires && state.tokenExpires > Date.now();
    },
  }
});