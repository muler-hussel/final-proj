<template>
  <div class="relative flex items-center
    border rounded-xl border-gray-200 
    hover:shadow hover:shadow-violet-200/50 hover:cursor-pointer p-3"
    @click="showDrawer()"
  >
    <!-- 注意图片加载的骨架占位符 -->
    <div class="flex-shrink-0 w-1/3 rounded-lg overflow-hidden mr-4" style="aspect-ratio: 16/10; overflow: hidden;">
      <img
        :src="item.photos[0]"
        class="w-full h-full object-cover block" />
    </div>
    <div class="flex-grow"> 
      <h3 class="text-lg font-semibold text-indigo-900 mb-2 leading-tight">{{ item.name }}</h3>
      <p class="text-sm text-indigo-900 leading-tight">{{ item.description }}</p>
    </div>
    <div class="absolute top-2 right-2">
      <HeartOutlined 
        v-if="!shortlistStore.hasItem(item.name)" 
        style="color:#9370DB;" class="ml-auto" 
        @click="handleAddToShortlist()" />
      <HeartFilled 
        v-else style="color:#9370DB;" class="ml-auto"
        @click="handleRemoveShortlist()"
      />
    </div>
  </div>

  <a-drawer title="{item.name}" size=large :open="open" @close="onClose">
    <!-- 此处需做走马灯，遍历图片。注意图片加载的骨架占位符 -->
    <img src="https://gw.alipayobjects.com/zos/rmsportal/JiqGstEfoWAOHiTxclqi.png" />
  </a-drawer>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';
import type { PropType } from 'vue';
import type { ShortlistItem } from '@/types';
import { useShortlistStore } from '@/stores/shortlist.ts';
import { useUserBehaviorStore } from '@/stores/userBehavior';

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<ShortlistItem>,
      required: true,
    },
  },
  setup(props) {
    const open = ref<boolean>(false);
    const shortlistStore = useShortlistStore();
    const userBehaviorStore = useUserBehaviorStore();

    const showDrawer = () => {
      open.value = true;
      userBehaviorStore.recordAction('click', props.item.name);
      userBehaviorStore.startViewing(props.item.name);
    };

    const onClose = () => {
      open.value = false;
      userBehaviorStore.endViewing(props.item.name);
    };

    const handleAddToShortlist = () => {
      shortlistStore.addToShortlist(props.item);
      userBehaviorStore.recordAction('shortlist', props.item.name);
    };

    const handleRemoveShortlist = () => {
      shortlistStore.removeFromShortlist(props.item.name);
      userBehaviorStore.recordAction('unshortlist', props.item.name);
    }

    return {
      showDrawer,
      onClose,
      open,
      shortlistStore,
      props,
      handleAddToShortlist,
      handleRemoveShortlist,
    }
  }
})
</script>