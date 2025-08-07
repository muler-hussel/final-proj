<template>
  <div class="flex">
    <SideBar></SideBar>
    <div class="min-h-screen w-full flex items-center justify-center flex-col">
      <div class="w-full sm:w-3/4 md:w-1/2 lg:w-1/3 flex flex-col 
        sm:p-8 md:p-12 lg:p-15 border border-gray-200 rounded-lg shadow-sm mx-auto"
      > 
        <div class="text-2xl flex justify-center gap-2">
          <h1 class="font-semibold text-indigo-900 mb-2 text-center">Login to </h1>
          <span class="text-gradient font-bold">YOURT</span><span class="-ml-2 font-semibold text-indigo-900">ravel</span>
        </div>
        <p class="mb-10 text-center text-gray-500 text-sm">Enter your user name to login</p>
        <a-textarea v-model:value="userName"  placeholder="User Name" :auto-size="{ minRows: 2 }" />
        <p class="mt-4 ml-2 text-xs text-violet-400">Don't have an account? Automatically registered upon logging in</p>
        <a-button 
          class="mt-10 w-full mx-auto block" 
          type="primary"
          @click="handleLogin"
          :disabled="userName === ''"
        >Login</a-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';
import { useRouter } from 'vue-router';
import SideBar from '@/components/SideBar.vue';
import { useAuthStore } from '@/stores/auth.ts';
import axios from "axios";
import { useUserSessionsStore } from '@/stores/userSessions.ts';

export default defineComponent({
  components: {
    SideBar,
  },
  setup() {
    const userName = ref<string>('');
    const auth = useAuthStore();
    const router = useRouter();
    const userSessions = useUserSessionsStore();

    const handleLogin = async () => {
      const res = await axios.post('/login', {userName: userName.value});
      auth.setToken(res.data);
      const redirect = router.currentRoute.value.query.redirect as string;
      if (redirect) {
        router.push(redirect);
      } else {
        router.push('/');
      }
      await userSessions.initialize();
    };

    return {
      userName,
      handleLogin,
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

.error-border {
  border-color: #ff4d4f;
}
.error-text {
  color: #ff4d4f;
  font-size: 12px;
}
</style>