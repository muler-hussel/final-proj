<template>
  <div class="bg-violet-50 p-4 w-16 flex flex-col items-center">
    <RocketOutlined style="color:#8A54FF;" class="text-3xl" />
    <a-divider />
    <div class="gap-y-7 flex-col flex text-xl flex-grow">
      <HomeOutlined style="color:#9370DB;" class="hover:cursor-pointer" />
      <FormOutlined style="color:#9370DB;" class="hover:cursor-pointer" />
      <HistoryOutlined style="color:#9370DB;" class="hover:cursor-pointer" />
    </div>
    <div class="flex pb-10 text-2xl">
      <UserOutlined style="color:#9370DB;" class="hover:cursor-pointer" />
      <!-- <LogoutOutlined style="color:#9370DB;" class="hover:cursor-pointer" /> -->
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
})
</script>