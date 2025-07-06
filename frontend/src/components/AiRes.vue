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
            <a-scroll class="grid grid-cols-2 gap-4 items-stretch">
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
          <a-button @click="$emit('load-more')">Load more</a-button>
          <a-button type="primary" @click="$emit('generate')">Generate trip with shortlist</a-button>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import SpotSelected from './SpotSelected.vue';
import { marked } from 'marked';
import type { ShortlistItem } from '@/types';
import type { PropType } from 'vue';

const {content, recommendations} = defineProps({
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

defineEmits([
  'next',
  'load-more', 
  'generate'
])

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
</style>