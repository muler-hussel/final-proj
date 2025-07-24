<template>
  <div id="sidebar" class="bg-violet-50 p-4 w-16 flex flex-col items-center">
    <RocketOutlined style="color:#8A54FF;" class="text-3xl" />
    <a-divider />
    <div class="gap-y-7 flex-col flex text-xl flex-grow">
      <HomeOutlined style="color:#9370DB;" class="hover:cursor-pointer" @click="toHomePage" />
      <FormOutlined style="color:#9370DB;" class="hover:cursor-pointer" @click="toChatPage" />
      <HistoryOutlined style="color:#9370DB;" class="hover:cursor-pointer" @click="toggleCard" />
    </div>
    <div class="flex pb-10 text-2xl">
      <UserOutlined 
        style="color:#9370DB;" 
        class="hover:cursor-pointer" 
        v-if="!auth.isAuthenticated"
        @click="handleLogin"
        />
      <LogoutOutlined 
        style="color:#9370DB;" 
        class="hover:cursor-pointer" 
        v-else 
        @click="handleLogout"
      />
    </div>
  </div>

  <!-- History sidebar -->
  <div
    v-if="historyOpen" id="history"
    class="absolute left-16 w-64 h-full border-l-1 border-r-1 border-violet-200 bg-violet-50 flex flex-col z-1000 p-4 gap-y-2"
  >
    <span class="text-gradient font-bold text-xl mb-4">YOURTravel</span>
    <p class="text-xs text-gray-500 font-bold mb-2">
      Recent Chats
    </p>
    <div v-for="(s, idx) in sessions" :key="idx" 
      class="flex flex-row p-3 text-sm text-gray-700 hover:bg-gray-200/50 hover:cursor-pointer active:bg-gray-200/100 rounded-lg "
      :class="{ 'bg-violet-200 hover:bg-violet-200': currentSessionId === s.session_id }"
    >
      <div v-if="s" @click="loadSession(s.session_id)">{{ s.title }}</div>
      <DeleteOutlined class="flex ml-auto hover:bg-gray-300/100 hover:cursor-pointer rounded-lg" @click.stop="deleteSession(s.session_id)"/>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref, onBeforeUnmount } from 'vue';
import { useAuthStore } from '@/stores/auth.ts';
import { useRouter } from 'vue-router';
import { useSessionStore } from '@/stores/session';
import { useUserSessionsStore } from '@/stores/userSessions';
import { storeToRefs } from 'pinia';

export default defineComponent({
  setup() {
    const auth = useAuthStore();
    const router = useRouter();
    const session = useSessionStore();
    const historyOpen = ref<boolean>(false);
    const userSession = useUserSessionsStore();
    const { sessions, currentSessionId } = storeToRefs(userSession);
    
    const toHomePage = () => {
      session.clearSession();
      router.push('/');
    }

    const toChatPage = () => {
      session.clearSession();
      router.push('/chat/new');
    }

    const handleLogout = () => {
      session.clearSession();
      auth.clearToken();
      router.push('/');
    };

    const handleLogin = () => {
      router.push('/login');
    };

    const toggleCard = () => {
      historyOpen.value = !historyOpen.value;
    }

    const loadSession = async (sessionId: string) => {
      historyOpen.value = false;
      router.push(`/chat/${sessionId}`);
      userSession.setCurrentSession(sessionId);
    }

    const handleClickOutside = (event: MouseEvent) => {
      const sidebarEl = document.getElementById("sidebar");
      const historyEl = document.getElementById("history");
      if (
        sidebarEl &&
        historyEl &&
        !sidebarEl.contains(event.target as Node) &&
        !historyEl.contains(event.target as Node)
      ) {
        historyOpen.value = false;
      }
    }

    const deleteSession = async (sessionId: string) => {
      await userSession.deleteSession(sessionId);
    }

    onMounted(async () => {
      await userSession.initialize();
      document.addEventListener('click', handleClickOutside);
    });

    onBeforeUnmount(() => {
      document.removeEventListener('click', handleClickOutside)
    });

    return {
      auth,
      toHomePage,
      toChatPage,
      handleLogin,
      handleLogout,
      historyOpen,
      toggleCard,
      sessions,
      loadSession,
      currentSessionId,
      deleteSession,
    }
  }
})
</script>

<style>
.text-gradient {
  background-image: linear-gradient(to bottom, #6498ff , #a928f9);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  -webkit-text-fill-color: transparent;
}
</style>