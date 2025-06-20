import { defineStore } from "pinia";

export const useFirstPromStore = defineStore('firstProm', {
  state: () => ({
    firstPromptData: {
      isEasyPlan: false,
      user_input: ''
    }
  })
})