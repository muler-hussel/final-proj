<template>
  <a-drawer title="Your Preference" :open="drawer.shortlist.isOpen" @close="drawer.onShortlistClose" class="flex flex-col">
    <a-scroll class="h-2/3 grid-cols-1 gap-y-2">
      <div v-for="(item, idx) in items" :key="idx"><SpotSelected></SpotSelected></div>
    </a-scroll>
  </a-drawer>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useDrawerStore } from '@/stores/drawer.ts';
import { useShortlistStore } from '@/stores/shortlist.ts';
import { storeToRefs } from 'pinia';
import SpotSelected from './SpotSelected.vue';

export default defineComponent({
  setup() {
    const drawer = useDrawerStore();
    const shortlistStore = useShortlistStore();
    const { items } = storeToRefs(shortlistStore); 

    return {
      drawer,
      SpotSelected,
      items,
    }
  }
})
</script>