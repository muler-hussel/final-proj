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
          <a-input v-model:value="title" placeholder="Enter your trip title" v-else @pressEnter="completeChange">
            <template #suffix>
              <EnterOutlined style="color:#9370DB; font-size: smaller;" />
            </template>
          </a-input>
        </div>
        <div class="flex ml-auto mr-3 px-3 py-1 border gap-3 rounded-lg border-gray-300 hover:cursor-pointer" @click="drawer.showShortlists()">
          <HeartOutlined style="color:#9370DB;" />
          <p class="text-sm text-indigo-900">Shortlist</p>
          <a-badge
            show-zero
            :count="shortlistNum"
            :number-style="{
              backgroundColor: '#fff',
              color: '#999',
              boxShadow: '0 0 0 1px #d9d9d9 inset',
            }"
          />
        </div>
      
        <div class="flex mr-3 px-3 py-1 bg-[#9370DB] gap-3 rounded-lg hover:cursor-pointer" @click="drawer.showPreference()">
          <p class="text-sm text-white">Your Preference</p>
        </div>
        
      </div>
      <!-- scroll -->
      <div id="messageContainer" class="w-full flex flex-col items-center flex-grow overflow-y-auto">
        <div class="grid w-3/5 py-10 gap-y-7">
          <template v-for="(content, idx) in chatHistory" :key="idx">
            <UserProm 
              v-if="content.role === 'user'"
              :content="content.message.content || null"
            />
            <AiRes
              v-else-if="content.role === 'ai'"
              :content="content.message.content"
              :recommendations="content.message.recommendations"
              :itinerary="content.message.itinerary"
              :messageIndex="idx"
              :populars="content.message.populars"
              @next="fetchAiRes('ADVANCE_STEP')"
              @load-more="fetchAiRes('MORE_RECOMMENDATIONS')"
              @generate="fetchAiRes('ITINERARY_GENERATION')"
            />
          </template>
          <a-spin v-if="isAiGenerating" />
        </div>
      </div>
      <!-- bottom -->
      <div class="w-3/5 h-10 mb-3 mx-auto">
        <a-input v-model:value="prompt" placeholder="Tell me something..." size="large" class="gap-x-1" @pressEnter="fetchAiRes(prompt)">
          <template #prefix>
            <PlusCircleOutlined style="color:#9370DB;" class="hover:cursor-pointer" />
          </template>
          <template #suffix>
            <EnterOutlined style="color:#9370DB; font-size: smaller;" @click="fetchAiRes(prompt)"/>
          </template>
        </a-input>
      </div>
    </div>
  </div>

  <PreferenceDrawer></PreferenceDrawer>
  <ShortlistDrawer></ShortlistDrawer>
  <SpaceInfoDrawer></SpaceInfoDrawer>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, watch } from 'vue';
import SideBar from '@/components/SideBar.vue';
import UserProm from '@/components/UserProm.vue';
import AiRes from '@/components/AiRes.vue';
import { useDrawerStore } from '@/stores/drawer.ts';
import PreferenceDrawer from '@/components/PreferenceDrawer.vue';
import { useAuthStore } from '@/stores/auth';
import axios from "axios";
import { useFirstPromStore } from '@/stores/firstPrompt';
import { useSessionStore } from '@/stores/session';
import { useRoute, useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useShortlistStore } from '@/stores/shortlist.ts';
import { useUserBehaviorStore } from '@/stores/userBehavior';
import ShortlistDrawer from '@/components/ShortlistDrawer.vue';
import SpaceInfoDrawer from '@/components/PlaceInfoDrawer.vue';
import { useUserSessionsStore } from '@/stores/userSessions';
import { onBeforeRouteLeave } from 'vue-router';
import { Modal } from 'ant-design-vue';
import { useItineraryStore } from '@/stores/itinerary.ts';

export default defineComponent({
  components: {
    SideBar,
    UserProm,
    AiRes,
    PreferenceDrawer,
    ShortlistDrawer,
    SpaceInfoDrawer,
  },
  setup() {
    const auth = useAuthStore();
    const userId = auth.token;
    const route = useRoute();
    const router = useRouter();
    const session = useSessionStore();
    const firstPrompt = ref<string>('');
    const isEasyPlan = ref<boolean>(false);
    const { title, sessionId, chatHistory } = storeToRefs(session); 
    const drawer = useDrawerStore();
    const changeTitle = ref<Boolean>(false);
    const prompt = ref<string>('');
    const firstPromptStore = useFirstPromStore();
    const isAiGenerating = ref(false);
    const shortlistStore = useShortlistStore();
    const { shortlistNum } = storeToRefs(shortlistStore);
    const userBehavior = useUserBehaviorStore();
    const userSessions = useUserSessionsStore();
    const useItinerary = useItineraryStore();

    const fetchNewSession = async () => {
      try {
        const res = await axios.post("/chat/init", {
          user_id: userId,
          user_input: firstPrompt.value,
        })
        const session_id = res.data.session_id;
        const newTitle = res.data.title;
        title.value = newTitle;
        session.setSessionId(session_id);
        userSessions.updateSession(session_id, newTitle);
        userSessions.setCurrentSession(session_id);
        userBehavior.initialize(session_id);
        shortlistStore.initialize(session_id);
        router.push(`/chat/${sessionId.value}`);
      } catch (error) {
        console.error("Error start new session:", error);
      }
    };

    const onEditTitle = () => {
      changeTitle.value = true;
    }

    const completeChange = async () => {
      if (sessionId.value) {
        await session.setTitle(title.value);
        userSessions.updateSession(sessionId.value, title.value);
        changeTitle.value = false;
      }
    }

    const fetchAiRes = async(userInput: string) => {
      if (!userInput) return;
      isAiGenerating.value = true;
      prompt.value = '';
      session.appendHistory({
        role: "user",
        message: {
          content: userInput
        }
      });

      if (userBehavior.currentSession) {
        if (userId === userBehavior.currentSession.userId && sessionId.value === userBehavior.currentSession.sessionId && userBehavior.currentSession.events) {
          // Deal with user behavior
          userBehavior.uploadAndRestart();
        }
      }
      
      try {
        const res = await axios.post(`/chat/${sessionId.value}/res`,{
          user_id: userId,
          user_input: userInput,
        })
        session.appendHistory(res.data);
        session.setShortTermProfile(res.data);
      } catch(e) {
        alert(`Failed to answer you. Please try again, ${e}`);
      } finally {
        isAiGenerating.value = false;
      }
    }

    watch(
      () => route.params.sessionId,
      async (newSessionId, oldSessionId) => {
        if (newSessionId && newSessionId !== oldSessionId) {
          try {
            shortlistStore.clearShortlist();
            userBehavior.clearBehavior();
            await session.initializeSession(newSessionId as string);
            userBehavior.startTracking();
          } catch (error) {
            console.error('Fail to load session:', error);
          }
        }
      },
      { immediate: true }
    );
    
    window.addEventListener('beforeunload', (e) => {
      // Have to use returnValue, otherwise doesn't work
      if (useItinerary.currentIndex && useItinerary.ifChanged()) {
        e.preventDefault();
        const confirmationMessage = '';
        e.returnValue = confirmationMessage;
        return confirmationMessage;
      }
    });

    const scrollBottom = () => {
      const container = document.getElementById("messageContainer");
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }

    onMounted(async () => {
      const sessionId = route.params.sessionId as string | undefined;
      if (sessionId) {
        await session.initializeSession(sessionId);
      } else {
        session.clearSession();
        shortlistStore.clearShortlist();
        userBehavior.clearBehavior();
        firstPrompt.value = firstPromptStore.firstPromptData.user_input;
        isEasyPlan.value = firstPromptStore.firstPromptData.isEasyPlan;
        await fetchNewSession();
        if (isEasyPlan.value) {
        } else {
          await fetchAiRes(firstPrompt.value);
          userBehavior.startTracking();
        }
      }
      scrollBottom();
    });

    onBeforeRouteLeave(async (to, from, next) => {
      firstPromptStore.clearFirstPrompt();
      if (useItinerary.currentIndex && useItinerary.ifChanged()) {
        Modal.confirm({
          title: "Changes you made may not be saved.",
          content: "Do you want to save?",
          onOk: async () => {
            await useItinerary.handleSave();
            next();
          },
          onCancel: () => next()
        });
      } else {
        next();
      }
    });

    return {
      title,
      drawer,
      changeTitle,
      onEditTitle,
      completeChange,
      prompt,
      isAiGenerating,
      chatHistory,
      fetchAiRes,
      shortlistNum,
    }
  }
})
</script>