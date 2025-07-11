<template>
  <div class="flex flex-col p-4 gap-y-4">
    <div class="inline-block">
      <p class="text-gray-700 text-justify leading-8 whitespace-normal" v-html="renderedMessage"></p>
      <FastForwardOutlined style="color:#9370DB;" class="hover:cursor-pointer" @click="$emit('next')" />
    </div>

    <div v-if="recommendations && recommendations.length > 0">
      <a-card class="w-full h-fit shadow-md shadow-violet-200/50">
        <a-tabs v-model:activeKey="activeKey">
          <a-tab-pane key="1" tab="Recommended">
            <div class="grid grid-cols-2 gap-4 items-stretch">
              <SpotSelected
                v-for="item in recommendations"
                :key="item.place_id"
                :item="item"
              ></SpotSelected>
            </div>
          </a-tab-pane>
          <a-tab-pane key="2" tab="You May Like" force-render>Content of Tab Pane 2</a-tab-pane>
          <a-tab-pane key="3" tab="Have A Look">Content of Tab Pane 3</a-tab-pane>
        </a-tabs>
        <a-divider />
        <div class="flex flex-row justify-end gap-x-4">
          <a-button @click="$emit('load-more')">Load more</a-button>
          <a-button type="primary" @click="$emit('generate')">Generate trip with shortlist</a-button>
        </div>
      </a-card>
    </div>

    <div v-if="itinerary && itinerary.length > 0">
      <a-button @click="openItinerary">
        Open in canvas
        <template #icon><ExpandAltOutlined /></template>
      </a-button>
    </div>
  </div>
  <a-modal
    v-model:open="itineraryOpen"
    width="100%"
    wrap-class-name="full-modal"
  >
    <ItineraryCalendar :events="itinerary"></ItineraryCalendar>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, type PropType } from 'vue';
import SpotSelected from './SpotSelected.vue';
import { marked } from 'marked';
import type { DailyItinerary, ShortlistItem } from '@/types';
import ItineraryCalendar from './ItineraryCalendar.vue';

const {content, recommendations, itinerary} = defineProps({
  content: {
    type: String,
    default: null,
  },
  recommendations: {
    type: Array as PropType<ShortlistItem[]>,
    default: () => [],
  },
  itinerary: {
    type: Array as PropType<DailyItinerary[]>,
    default: () => [],
  },
});

const activeKey = ref('1');
const itineraryOpen = ref(false);

defineEmits([
  'next',
  'load-more', 
  'generate'
])

const openItinerary = () => {
  itineraryOpen.value = true;
}

const renderedMessage = computed(() => marked.parse(content ?? ''));
</script>

<style>
/* 覆盖渲染内容中的 ul/li 样式 */
.whitespace-normal ul {
  margin: 0.75em 0;
  padding-left: 1.5em;
}

.whitespace-normal li p {
  margin: 0.75em 0;
}

.full-modal {
  .ant-modal {
    max-width: 100%;
    top: 0;
    padding-bottom: 0;
    margin: 0;
  }
  .ant-modal-content {
    display: flex;
    flex-direction: column;
    height: calc(100vh);
  }
  .ant-modal-body {
    flex: 1;
  }
}
</style>