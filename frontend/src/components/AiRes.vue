<template>
  <div class="flex flex-col items-center p-4 gap-y-4">
    <p class="text-gray-700 text-justify leading-7">February is the perfect time to escape to some stunning beach destinations in the Southern Hemisphere and near the equator! These locations offer warm temperatures, minimal rainfall, and ideal beach conditions during this time. Many of these destinations also feature vibrant beach cultures, water sports, and excellent resort facilities.</p>
    <a-card class="w-full h-fit shadow-md shadow-violet-200/50">
      <a-tabs v-model:activeKey="activeKey">
        <a-tab-pane key="1" tab="Recommended">
          <a-scroll class="grid grid-cols-2 gap-4">
            <div v-for="i in 8" :key="i"><SpotSelected></SpotSelected></div>
          </a-scroll>
        </a-tab-pane>
        <a-tab-pane key="2" tab="You May Like" force-render>Content of Tab Pane 2</a-tab-pane>
        <a-tab-pane key="3" tab="Have A Look">Content of Tab Pane 3</a-tab-pane>
      </a-tabs>
      <a-divider />
      <div class="flex flex-row justify-end gap-x-4">
        <a-button>Load more</a-button>
        <a-button type="primary">Generate trip with shortlist</a-button>
      </div>
    </a-card>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';
import SpotSelected from './SpotSelected.vue';

export default defineComponent({
  components: {
    SpotSelected,
  },
  setup() {
    const activeKey = ref('1');

    return {
      activeKey,
    }
  }
})
</script>