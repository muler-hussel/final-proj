<template>
  <div class="flex">
    <SideBar></SideBar>
    <div class="flex flex-col h-screen w-full">
      <!-- top -->
      <div class="flex h-15 border-b border-violet-100 shadow-lg shadow-violet-200/30 p-6 items-center">
        <div class="w-1/4 flex flex-row gap-2">
          <p class="ml-2 font-semibold text-indigo-900 
            hover:cursor-pointer hover:underline 
            truncate overflow-hidden text-ellipsis"
          >Title of trip Title of trip Title of trip Title of trip</p>
          <EditOutlined style="color:#9370DB;" class="hover:cursor-pointer" />
          <!-- <a-input v-model:value="value" placeholder="Basic usage">
            <template #suffix>
              <EnterOutlined style="color:#9370DB; font-size: smaller;" />
            </template>
          </a-input> -->
        </div>
        <div class="flex ml-auto mr-3 px-3 py-1 border gap-3 rounded-lg border-gray-300 hover:cursor-pointer">
          <HeartOutlined style="color:#9370DB;" />
          <p class="text-sm text-indigo-900">Shortlist</p>
          <a-badge
            count="4"
            :number-style="{
              backgroundColor: '#fff',
              color: '#999',
              boxShadow: '0 0 0 1px #d9d9d9 inset',
            }"
          />
        </div>
        <SettingOutlined style="color:#9370DB;" class="hover:cursor-pointer" />
      </div>
      <!-- scroll -->
      <a-scroll class="w-full flex flex-col items-center flex-grow overflow-y-auto">
        <div class="grid w-3/5 py-10 gap-y-5">
          <UserProm></UserProm>
          <AiRes></AiRes>
        </div>
      </a-scroll>
      <!-- bottom -->
      <div class="w-3/5 h-10 mb-3 mx-auto">
        <a-input v-model:value="value" placeholder="Tell me something..." size="large" class="gap-x-1">
          <template #prefix>
            <PlusCircleOutlined style="color:#9370DB;" class="hover:cursor-pointer" />
          </template>
          <template #suffix>
            <EnterOutlined style="color:#9370DB; font-size: smaller;" />
          </template>
        </a-input>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import SideBar from '@/components/SideBar.vue';
import UserProm from '@/components/UserProm.vue';
import AiRes from '@/components/AiRes.vue';

export default defineComponent({
  components: {
    SideBar,
    UserProm,
    AiRes,
  },
})
</script>