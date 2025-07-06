<template>
  <a-drawer title="Your Preference" :open="drawer.preference.isOpen" @close="drawer.onPreferenceClose">
    <p class="text-sm text-gray-300">If the AI fails to summarize your preferences, you can add a tag yourself.</p>
    <div class="flex mb-2 mt-2 flex-col gap-y-1">
      <div v-for="(p, idx) in tags" :key="idx">
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
import { defineComponent, ref, reactive, nextTick, computed } from 'vue';
import { useDrawerStore } from '@/stores/drawer.ts';
import { useSessionStore } from '@/stores/session';
import { storeToRefs } from 'pinia';

export default defineComponent({
  setup() {
    const drawer = useDrawerStore();
    const session = useSessionStore();
    const { shortTermProfile } = storeToRefs(session); 
    const inputRef = ref();

    const tags = computed(() => 
      shortTermProfile.value?.preferences 
        ? Object.keys(shortTermProfile.value.preferences) 
        : []
    );

    const state = reactive({
      inputVisible: false,
      inputValue: '',
    });

    const handleClose = (removedTag: string) => {
      if (shortTermProfile.value?.preferences) {
        delete shortTermProfile.value.preferences[removedTag];
      }
      // TODO: 在后端删除这个tag
    };

    const showInput = () => {
      state.inputVisible = true;
      nextTick(() => {
        inputRef.value.focus();
      });
    };

    const handleInputConfirm = () => {
      const inputValue = state.inputValue.trim();
      if (!inputValue) return;

      if (!shortTermProfile.value) {
        shortTermProfile.value = { preferences: {}, avoids: [] };
      }

      if (!shortTermProfile.value.preferences[inputValue]) {
        shortTermProfile.value.preferences[inputValue] = { tag: inputValue, weight: 1 };
      }
      // TODO: 在后端增加tag和weight
      Object.assign(state, {
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
      tags,
    }
  }
})
</script>