<template>
  <div class="relative flex items-center
    border rounded-xl border-gray-200 
    hover:shadow hover:shadow-violet-200/50 hover:cursor-pointer p-3"
    @click="showDrawer()"
  >
    <div class="flex-shrink-0 w-1/3 rounded-lg overflow-hidden mr-4" style="aspect-ratio: 16/10; overflow: hidden;">
      <img
        v-if="displayItem.photos"
        :src="displayItem.photos[0]"
        class="w-full h-full object-cover block" />
      <a-skeleton-image v-else />
    </div>
    <div class="flex-grow"> 
      <h3 class="text-lg font-semibold text-indigo-900 mb-2 leading-tight">{{ displayItem.name }}</h3>
      <p class="text-sm text-indigo-900 leading-tight">{{ displayItem.description }}</p>
    </div>
    <div class="absolute top-2 right-2">
      <HeartOutlined 
        v-if="!shortlistStore.hasItem(displayItem.name)" 
        style="color:#9370DB;" class="ml-auto" 
        @click.stop="handleAddToShortlist()" />
      <HeartFilled 
        v-else style="color:#9370DB;" class="ml-auto"
        @click.stop="handleRemoveShortlist()"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue';
import type { PropType } from 'vue';
import type { ShortlistItem } from '@/types';
import { useShortlistStore } from '@/stores/shortlist.ts';
import { useUserBehaviorStore } from '@/stores/userBehavior';
import { useDrawerStore } from '@/stores/drawer.ts';
import axios from 'axios';

export default defineComponent({
  props: {
    item: {
      type: Object as PropType<ShortlistItem>,
      required: true,
    },
  },
  setup(props) {
    const shortlistStore = useShortlistStore();
    const userBehaviorStore = useUserBehaviorStore();
    const drawer = useDrawerStore();
    const displayItem = computed(() => {
      return shortlistStore.items.get(props.item.name) || props.item;
    });

    const showDrawer = async () => {
      const item = displayItem.value;
      if (!item.updated_time || (+new Date() - +new Date(item.updated_time)) / (1000 * 60 * 60 * 24) > 30 || (!item.info?.cons && item.sub_items?.length == 0)) {
        const res = await axios.post("/recommend/enrich", {place_name: item.name})
        shortlistStore.addToShortlist(res.data)
      }
      drawer.showSpaceInfo(displayItem.value);
      userBehaviorStore.recordAction('click', displayItem.value.name);
      userBehaviorStore.startViewing(displayItem.value.name);
    };

    const onClose = () => {
      drawer.onSpaceInfoClose();
      userBehaviorStore.endViewing(displayItem.value.name);
    };

    const handleAddToShortlist = () => {
      shortlistStore.addToShortlist(displayItem.value);
      userBehaviorStore.recordAction('shortlist', displayItem.value.name);
    };

    const handleRemoveShortlist = () => {
      shortlistStore.removeFromShortlist(displayItem.value.name);
      userBehaviorStore.recordAction('unshortlist', displayItem.value.name);
    }

    return {
      showDrawer,
      onClose,
      open,
      shortlistStore,
      handleAddToShortlist,
      handleRemoveShortlist,
      displayItem,
    }
  }
})
</script>