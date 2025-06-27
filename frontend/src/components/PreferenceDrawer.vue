<template>
  <a-drawer title="Your Preference" :open="drawer.preference.isOpen" @close="drawer.onPreferenceClose" class="flex flex-col">
    <p class="text-sm text-gray-300 w-44">If the ai fails to summarize your preferences, you can add a tag yourself.</p>
    <div class="flex mb-2 mt-2 flex-col gap-y-1">
      <div v-for="(p, idx) in state.tags" :key="idx">
        <a-tooltip v-if="p && p.length > 20" :title="p">
          <a-tag :closable="p" @close="handleClose(p)">
            {{ `${p.slice(0, 20)}...` }}
          </a-tag>
        </a-tooltip>
        <a-tag v-else :closable="p" @close="handleClose(p)">
          {{ p }}
        </a-tag>
      </div>
      <a-input
        v-if="state.inputVisible"
        ref="inputRef"
        v-model:value="state.inputValue"
        type="text"
        size="small"
        :style="{ width: '78px' }"
        @blur="handleInputConfirm"
        @keyup.enter="handleInputConfirm"
      />
      <a-tag v-else style="background: #fff; border-style: dashed" @click="showInput">
        <plus-outlined />
        New Tag
      </a-tag>
    </div>
    <a-button>Save</a-button>
  </a-drawer>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, nextTick } from 'vue';
import { useDrawerStore } from '@/stores/drawer.ts';

export default defineComponent({
  setup() {
    const drawer = useDrawerStore();
    const inputRef = ref();
    const state = reactive({
      tags: ['Unremovable', 'Tag 2', 'Tag 3Tag 3Tag 3Tag 3Tag 3Tag 3Tag 3'],
      inputVisible: false,
      inputValue: '',
    });

    const handleClose = (removedTag: string) => {
      const tags = state.tags.filter(tag => tag !== removedTag);
      console.log(tags);
      state.tags = tags;
    };

    const showInput = () => {
      state.inputVisible = true;
      nextTick(() => {
        inputRef.value.focus();
      });
    };

    const handleInputConfirm = () => {
      const inputValue = state.inputValue;
      let tags = state.tags;
      if (inputValue && tags.indexOf(inputValue) === -1) {
        tags = [...tags, inputValue];
      }
      console.log(tags);
      Object.assign(state, {
        tags,
        inputVisible: false,
        inputValue: '',
      });
    };

    return {
      drawer,
      handleClose,
      inputRef,
      handleInputConfirm,
      state,
      showInput,
    }
  }
})
</script>