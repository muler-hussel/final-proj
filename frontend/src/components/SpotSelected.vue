<template>
  <div class="relative flex items-center h-fit 
    border rounded-xl border-gray-200 
    hover:shadow hover:shadow-violet-200/50 hover:cursor-pointer p-3"
    @click="showDrawer()"
  >
    <div class="flex-shrink-0 w-1/3 rounded-lg overflow-hidden mr-4">
      <img src="https://gw.alipayobjects.com/zos/rmsportal/JiqGstEfoWAOHiTxclqi.png" class="w-full h-full object-cover block" />
    </div>
    <div class="flex-grow"> 
      <h3 class="text-xl font-semibold text-indigo-900 mb-2 leading-tight">Maldives</h3>
      <p class="text-sm text-indigo-900 leading-tight">Pristine atolls, 84°F crystal-clear waters</p>
    </div>
    <div class="absolute top-2 right-2">
      <HeartOutlined style="color:#9370DB;" class="ml-auto"/>
    </div>
  </div>

  <a-drawer title="Maldives" size=large :open="open" @close="onClose">
    <p>Some contents...</p>
    <p>Some contents...</p>
    <p>Some contents...</p>
  </a-drawer>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';

export default defineComponent({
  setup() {
    const open = ref<boolean>(false);

    const showDrawer = () => {
      open.value = true;
    };

    const onClose = () => {
      open.value = false;
    };

    return {
      showDrawer,
      onClose,
      open,
    }
  }
})
</script>