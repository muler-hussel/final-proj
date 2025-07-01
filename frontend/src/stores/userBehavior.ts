import { defineStore } from 'pinia';
import { useAuthStore } from './auth';
import { useSessionStore } from './session';
import axios from "axios";

type TrackEvent = { type: string; itemName: string; duration?: number }

interface TrackingSession {
  userId: string;
  sessionId: string;
  events: TrackEvent[];
}

export const useUserBehaviorStore = defineStore('userBehavior', {
  state: () => ({
    currentSession: null as TrackingSession | null,
    activeViews: new Map<string, number>(), // Viewing place name and start time
    pendingUpload: false,
  }),
  actions: {
    startTracking() {
      const authStore = useAuthStore();
      const sessionStore = useSessionStore();

      if (!authStore.token || !sessionStore.sessionId) return;
      
      if (!this.currentSession) {
        this.currentSession = {
          userId: authStore.token,
          sessionId: sessionStore.sessionId,
          events: [],
        };
      } else {
        this.currentSession.userId = authStore.token;
        this.currentSession.sessionId = sessionStore.sessionId;
      }
    },

    // add to shortlist, remove from shortlist, click
    recordAction(type: string, place_name: string) {
      this.currentSession?.events.push({"type": type, "itemName": place_name});
    },

    startViewing(place_name: string) {
      this.activeViews.set(place_name, Date.now());
    },

    endViewing(place_name: string) {
      const startTime = this.activeViews.get(place_name);
      if (startTime) {
        const duration = (Date.now() - startTime) / 1000;
        if (duration >= 10.0) { // Valid only when more than 10 seconds
          this.currentSession?.events.push({"type": "view", "itemName": place_name, "duration": duration});
        }
        this.activeViews.delete(place_name);
      }
    },

    // Atomic. After uploading, restart tracking immediately
    async uploadAndRestart() {
      if (!this.currentSession || this.pendingUpload) return;
      
      this.pendingUpload = true;
      try {
        await this.uploadData();
        this.startTracking();
      } finally {
        this.pendingUpload = false;
      }
    },

    async uploadData() {
      if (!this.currentSession) return;

      try {
        await axios.post('/recommend/tracking', {
          data: JSON.stringify(this.currentSession),
        });
        this.currentSession = null;
      } catch (error) {
        console.error('Fail to upload tracking data', error);
      }
    },
  },
});