<template>
  <div class="bg-violet-50 p-4 w-16 flex flex-col items-center">
    <RocketOutlined style="color:#8A54FF;" class="text-3xl" />
    <a-divider />
    <div class="gap-y-7 flex-col flex text-xl flex-grow">
      <HomeOutlined style="color:#9370DB;" class="hover:cursor-pointer" @click="toHomePage" />
      <FormOutlined style="color:#9370DB;" class="hover:cursor-pointer" @click="toChatPage" />
      <HistoryOutlined style="color:#9370DB;" class="hover:cursor-pointer" />
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
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useAuthStore } from '@/stores/auth.ts';
import { useRouter } from 'vue-router';

export default defineComponent({
  setup() {
    const auth = useAuthStore();
    const router = useRouter();
    
    const toHomePage = () => {
      router.push('/');
    }

    const toChatPage = () => {
      router.push('/chat');
    }

    const handleLogout = () => {
      auth.clearToken();
      router.push('/');
    };

    const handleLogin = () => {
      router.push('/login');
    };

    return {
      auth,
      toHomePage,
      toChatPage,
      handleLogin,
      handleLogout,
    }
  }
})
</script>