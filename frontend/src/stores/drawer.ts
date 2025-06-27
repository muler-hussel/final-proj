import { defineStore } from 'pinia'

export const useDrawerStore = defineStore('drawer', {
  state: () => ({
    preference: {
      isOpen: false,
    },
    shortlist: {
      isOpen: false,
    },
  }),
  actions: {
    showPreference() {
      this.preference.isOpen = true
    },
    showShortlist() {
      this.shortlist.isOpen = true
    },
    onPreferenceClose() {
      this.preference.isOpen = false
    },
    onShortlistClose() {
      this.shortlist.isOpen = false
    }
  }
})