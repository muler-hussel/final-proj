<template>
  <a-drawer title="Your Shortlist" :open="drawer.shortlists.isOpen" @close="drawer.onShortlistsClose()" class="flex flex-col" width="500">
    <a-scroll class="grid grid-cols-1 gap-4 items-stretch">
      <SpotSelected
        v-for="item in Array.from(items.values())" 
        :key="item.name"
        :item="item"
      ></SpotSelected>
    </a-scroll>
  </a-drawer>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue';
import { useDrawerStore } from '@/stores/drawer.ts';
import { useShortlistStore } from '@/stores/shortlist.ts';
import SpotSelected from './SpotSelected.vue';

export default defineComponent({
  components: { SpotSelected },
  setup() {
    const drawer = useDrawerStore();
    const shortlistStore = useShortlistStore();
    const items = computed(() => Array.from(shortlistStore.items.values()))

    return {
      drawer,
      SpotSelected,
      shortlistStore,
      items,
    }
  }
})
</script>