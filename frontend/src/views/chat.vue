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
            @click="onEditTitle"
            v-if="!changeTitle"
          >{{ title }}</p>
          <EditOutlined style="color:#9370DB;" class="hover:cursor-pointer" @click="onEditTitle" v-if="!changeTitle" />
          <a-input v-model:value="title" placeholder="Enter your trip title" v-else pressEnter="completeChange">
            <template #suffix>
              <EnterOutlined style="color:#9370DB; font-size: smaller;" />
            </template>
          </a-input>
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
      
        <div class="flex mr-3 px-3 py-1 bg-[#9370DB] gap-3 rounded-lg hover:cursor-pointer" @click="drawer.showDrawer()">
          <p class="text-sm text-white">Your Preference</p>  
          <SettingOutlined style="color:white;" />
        </div>
        
      </div>
      <!-- scroll -->
      <a-scroll class="w-full flex flex-col items-center flex-grow overflow-y-auto">
        <div class="grid w-3/5 py-10 gap-y-7">
          <UserProm></UserProm>
          <AiRes></AiRes>
          <UserProm></UserProm>
          <AiRes></AiRes>
        </div>
      </a-scroll>
      <!-- bottom -->
      <div class="w-3/5 h-10 mb-3 mx-auto">
        <a-input v-model:value="prompt" placeholder="Tell me something..." size="large" class="gap-x-1">
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

  <PreferenceDrawer></PreferenceDrawer>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import SideBar from '@/components/SideBar.vue';
import UserProm from '@/components/UserProm.vue';
import AiRes from '@/components/AiRes.vue';
import { useDrawerStore } from '@/stores/drawer.ts'
import PreferenceDrawer from '@/components/PreferenceDrawer.vue';
import { useRoute } from 'vue-router';
import axios from "axios";

export default defineComponent({
  components: {
    SideBar,
    UserProm,
    AiRes,
    PreferenceDrawer,
  },
  setup() {
    const route = useRoute();
    const isEasyPlan = ref(route.query.isEasyPlan === 'true');
    const userId = route.params.userId;
    const sessionId = route.params.sessionId;
    const chatHistory = ref([]);
    const currentSlots = ref({});
    const title = ref<string>('');
    const drawer = useDrawerStore();
    const changeTitle = ref<Boolean>(false);
    const prompt = ref<string>('');

    const fetchSessionState = async () => {
      try {
        const res = await axios.get(`/chat/${userId}/${sessionId}`);
        const sessionState = res.data;
        console.log(sessionState);
        // Update all relevant reactive variables
        title.value = sessionState.title;
        // chatHistory.value = sessionState.history.map((msg: string, idx: number) => ({
        //     id: idx,
        //     sender: idx % 2 === 0 ? 'User' : 'AI', // Simple sender logic
        //     text: msg
        // }));
        // currentSlots.value = sessionState.slots;
        // currentTodo.value = sessionState.todo || [];
        // todoStep.value = sessionState.todo_step || 0;
        // itineraryDraft.value = sessionState.itinerary_draft || null; // Ensure default is null
        // recommendations.value = sessionState.recommendations || []; // Ensure default is empty array

      } catch (error) {
        console.error("Error fetching session state:", error);
      }
    };

    const onEditTitle = () => changeTitle.value = true;
    const completeChange = () => {
      changeTitle.value = false;
    }

    const fetchAiRes = async() => {
      try {
        const res = await axios.post(`/chat/${userId}/${sessionId}/res`,{
          user_input: prompt.value,
        })
      } catch {
        alert("Failed to answer you. Please try again.");
      }
    }

    onMounted(async () => {
      await fetchSessionState();
      
      if (isEasyPlan.value) {
      } else {
        // fetchAiRes();
      }
    });

    return {
      title,
      drawer,
      changeTitle,
      onEditTitle,
      completeChange,
      prompt,
    }
  }
})
</script>