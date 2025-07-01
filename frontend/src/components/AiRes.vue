<template>
  <div class="flex flex-col items-center p-4 gap-y-4">
    <p class="text-gray-700 text-justify leading-7 whitespace-pre-line" v-html="renderedMessage"></p>
    <a-card class="w-full h-fit shadow-md shadow-violet-200/50">
      <a-tabs v-model:activeKey="activeKey" v-if="recommendations">
        <a-tab-pane key="1" tab="Recommended">
          <a-scroll class="grid grid-cols-2 gap-4">
            <SpotSelected
              v-for="item in recommendations"
              :key="item.place_id"
              :item="item"
            ></SpotSelected>
          </a-scroll>
        </a-tab-pane>
        <a-tab-pane key="2" tab="You May Like" force-render>Content of Tab Pane 2</a-tab-pane>
        <a-tab-pane key="3" tab="Have A Look">Content of Tab Pane 3</a-tab-pane>
      </a-tabs>
      <a-divider />
      <div class="flex flex-row justify-end gap-x-4">
        <a-button @click="emit('ADVANCE_STEP')">Next</a-button>
        <a-button @click="emit('MORE_RECOMMENDATIONS')">Load more</a-button>
        <a-button type="primary" @click="emit('ITINERARY_GENERATION')">Generate trip with shortlist</a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import SpotSelected from './SpotSelected.vue';
import { marked } from 'marked';
import type { ShortlistItem } from '@/types';
import type { PropType } from 'vue';

const props = defineProps({
  content: {
    type: String,
    default: null,
  },
  recommendations: {
    type: Array as PropType<ShortlistItem[]>,
    default: () => [],
  },
});
const activeKey = ref('1');
const emit = defineEmits(["ADVANCE_STEP", "MORE_RECOMMENDATIONS", "ITINERARY_GENERATION"]);
const renderedMessage = computed(() => marked.parse(props.content ?? ''));

</script>