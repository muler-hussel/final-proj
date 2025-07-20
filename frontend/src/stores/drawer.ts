import type { ShortlistItem } from '@/types';
import { defineStore } from 'pinia';

export const useDrawerStore = defineStore('drawer', {
  state: () => ({
    preference: {
      isOpen: false,
    },
    shortlists: {
      isOpen: false,
    },
    placeInfo: {
      isOpen: false,
      item: null as ShortlistItem | null,
    },
  }),
  actions: {
    showPreference() {
      this.preference.isOpen = true;
    },
    showShortlists() {
      this.shortlists.isOpen = true;
    },
    showPlaceInfo(item: ShortlistItem) {
      this.placeInfo.isOpen = true;
      this.placeInfo.item = item;
    },
    onPreferenceClose() {
      this.preference.isOpen = false;
    },
    onShortlistsClose() {
      this.shortlists.isOpen = false;
    },
    onPlaceInfoClose() {
      this.placeInfo.isOpen = false;
      this.placeInfo.item = null;
    },
  }
})