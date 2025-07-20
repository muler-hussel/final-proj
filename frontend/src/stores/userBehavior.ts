import { defineStore } from 'pinia';
import { useAuthStore } from './auth';
import { useSessionStore } from './session';
import axios from "axios";

type TrackEvent = { place_name: string; event_type: string; duration_sec?: number }

interface TrackingSession {
  userId: string;
  sessionId: string;
  events: TrackEvent[];
}

export const useUserBehaviorStore = defineStore('userBehavior', {
  state: () => ({
    sessionId: null as string | null,
    currentSession: null as TrackingSession | null,
    activeViews: new Map<string, number>(), // Viewing place name and start time
    pendingUpload: false,
  }),
  actions: {
    initialize(session_id: string) {
      if (typeof window === 'undefined') return;

      this.sessionId = session_id;
      const rawData = localStorage.getItem(`tracking_data:${session_id}`);
      if (!rawData) {
        this.sessionId = session_id;
        this.saveToStorage();
        return;
      }

      try {
        const parsed = JSON.parse(rawData);
        if (parsed?.currentSession) {
          this.currentSession = parsed.currentSession;
        }
        
        if (Array.isArray(parsed?.activeViews)) {
          parsed.activeViews.forEach(([placeName, timestamp]:[string, number]) => {
            this.activeViews.set(placeName, timestamp);
          });
        }
      } catch (error) {
        console.error('Failed to parse tracking data:', error);
        this.clearStorage(session_id);
      }
    },

    startTracking() {
      const authStore = useAuthStore();
      const sessionStore = useSessionStore();

      if (!authStore.token || !sessionStore.sessionId || this.sessionId != sessionStore.sessionId) return;
      
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
      this.saveToStorage();
    },

    // add to shortlist, remove from shortlist, click
    recordAction(type: string, place_name: string) {
      this.currentSession?.events.push({"event_type": type, "place_name": place_name});
      this.saveToStorage();
    },

    startViewing(place_name: string) {
      this.activeViews.set(place_name, Date.now());
      this.saveToStorage();
    },

    endViewing(place_name: string) {
      const startTime = this.activeViews.get(place_name);
      if (startTime) {
        const duration = (Date.now() - startTime) / 1000;
        if (duration >= 10.0) { // Valid only when more than 10 seconds
          this.currentSession?.events.push({"event_type": "view", "place_name": place_name, "duration_sec": duration});
        }
        this.activeViews.delete(place_name);
        this.saveToStorage();
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
        await axios.post('/recommend/tracking', this.currentSession);
        this.currentSession = null;
        this.clearStorage(this.sessionId as string);
      } catch (error) {
        console.error('Fail to upload tracking data', error);
        throw error;
      }
    },

    saveToStorage() {
      if (typeof window === 'undefined') return;
      
      const data = {
        currentSession: this.currentSession,
        activeViews: Array.from(this.activeViews.entries()),
        savedAt: Date.now()
      };

      localStorage.setItem(`tracking_data:${this.sessionId}`, JSON.stringify(data));
    },

    clearStorage(sessionId: string) {
      if (typeof window === 'undefined') return;
      localStorage.removeItem(`tracking_data:${sessionId}`);
    },

    clearBehavior() {
      this.sessionId = null;
      this.currentSession = null;
      this.activeViews = new Map<string, number>();
      this.pendingUpload = false;
    }
  },
});