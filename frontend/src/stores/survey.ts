import axios from 'axios';
import { defineStore } from 'pinia';
import { useAuthStore } from '@/stores/auth.ts';

export const useSurveyStore = defineStore('survey', {
  state: () => ({
    projectInfoOpen: false,
    consentOpen: false,
    surveyShow: false,
    surveyCompleted: false,
  }),
  actions: {
    showProjectInfo() {
      this.projectInfoOpen = true;
    },
    showConsent() {
      this.consentOpen = true;
    },
    showSurvey() {
      this.surveyShow = true;
    },
    onSurveyCompleted() {
      this.surveyShow = false;
      this.surveyCompleted = true;
    },
    onProjectInfoConfirm() {
      this.projectInfoOpen = false;
      this.showConsent();
    },
    onProjectInfoCancel() {
      this.projectInfoOpen = false;
    },
    async onConsentConfirm(consentHash: string) {
      const auth = useAuthStore();
      await axios.post("/survey/save-consent", {user_id: auth.token, consent_hash: consentHash});
      this.consentOpen = false;
      this.showSurvey();
    },
    onConsentCancel() {
      this.consentOpen = false;
    },
    clear() {
      this.projectInfoOpen = false;
      this.consentOpen = false;
      this.surveyShow = false;
      this.surveyCompleted = false;
    }
  }
})