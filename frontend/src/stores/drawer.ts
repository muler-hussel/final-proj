import { defineStore } from 'pinia'

export const useDrawerStore = defineStore('drawer', {
  state: () => ({
    preference: {
      isOpen: false,
    },
    shortlists: {
      isOpen: false,
    },
  }),
  actions: {
    showPreference() {
      this.preference.isOpen = true
    },
    showShortlists() {
      this.shortlists.isOpen = true
    },
    onPreferenceClose() {
      this.preference.isOpen = false
    },
    onShortlistsClose() {
      this.shortlists.isOpen = false
    }
  }
})