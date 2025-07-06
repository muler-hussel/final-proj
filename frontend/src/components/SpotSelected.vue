<template>
  <div class="relative flex items-center
    border rounded-xl border-gray-200 
    hover:shadow hover:shadow-violet-200/50 hover:cursor-pointer p-3"
    @click="showDrawer()"
  >
    <div class="flex-shrink-0 w-1/3 rounded-lg overflow-hidden mr-4" style="aspect-ratio: 16/10; overflow: hidden;">
      <img
        v-if="item.photos"
        :src="item.photos[0]"
        class="w-full h-full object-cover block" />
      <a-skeleton-image v-else />
    </div>
    <div class="flex-grow"> 
      <h3 class="text-lg font-semibold text-indigo-900 mb-2 leading-tight">{{ item.name }}</h3>
      <p class="text-sm text-indigo-900 leading-tight">{{ item.description }}</p>
    </div>
    <div class="absolute top-2 right-2">
      <HeartOutlined 
        v-if="!shortlistStore.hasItem(item.name)" 
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
import { defineComponent } from 'vue';
import type { PropType } from 'vue';
import type { ShortlistItem } from '@/types';
import { useShortlistStore } from '@/stores/shortlist.ts';
import { useUserBehaviorStore } from '@/stores/userBehavior';
import { useDrawerStore } from '@/stores/drawer.ts';

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

    const showDrawer = () => {
      drawer.showSpaceInfo(props.item);
      userBehaviorStore.recordAction('click', props.item.name);
      userBehaviorStore.startViewing(props.item.name);
    };

    const onClose = () => {
      drawer.onSpaceInfoClose();
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