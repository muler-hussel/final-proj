import type { ShortlistItem } from '@/types'
import { defineStore } from 'pinia'

export const useDrawerStore = defineStore('drawer', {
  state: () => ({
    preference: {
      isOpen: false,
    },
    shortlists: {
      isOpen: false,
    },
    spaceInfo: {
      isOpen: false,
      item: null as ShortlistItem | null,
    },
  }),
  actions: {
    showPreference() {
      this.preference.isOpen = true
    },
    showShortlists() {
      this.shortlists.isOpen = true
    },
    showSpaceInfo(item: ShortlistItem) {
      this.spaceInfo.isOpen = true
      this.spaceInfo.item = item
    },
    onPreferenceClose() {
      this.preference.isOpen = false
    },
    onShortlistsClose() {
      this.shortlists.isOpen = false
    },
    onSpaceInfoClose() {
      this.spaceInfo.isOpen = false
      this.spaceInfo.item = null
    },
  }
})