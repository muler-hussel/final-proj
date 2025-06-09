import { defineStore } from 'pinia'

export const useDrawerStore = defineStore('drawer', {
  state: () => ({
    isOpen: false
  }),
  actions: {
    showDrawer() {
      this.isOpen = true
    },
    onClose() {
      this.isOpen = false
    }
  }
})