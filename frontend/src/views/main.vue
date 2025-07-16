<template>
  <div class="flex">
    <SideBar></SideBar>
    <div class="h-screen w-full text-gray-800 flex flex-col items-center px-4 overflow-y-auto">
      <header>
        <div class="text-3xl flex justify-center gap-2 pt-20">
          <RocketTwoTone two-tone-color="#8A54FF" />
          <span class="text-gradient font-bold">YOURT</span><span class="-ml-2">ravel</span>
        </div>
      </header>

      <section class="mt-15 w-full max-w-2xl">
        <a-textarea 
          v-model:value="prompt"
          placeholder="Tell me anything about the trip you want"
          :auto-size="{ minRows: 4, maxRows: 7}"
          class="shadow-lg shadow-violet-300/20"
        />
        <div class="flex justify-end mt-3 gap-x-5 items-center">
          <a-popover>
            <template #content>
              <p>Skips all clarification questions.</p>
              <p>Create your trip with any infomation.</p>
            </template>
            <a-switch v-model:checked="easyPlan" size="small" />
            <span class="text-sm text-gray-500 ml-2">Easy Plan</span>
          </a-popover>
          <a-button @click="submitPrompt" :disabled="prompt === ''">Submit</a-button>
        </div>
      </section>

      <section class="mt-12">
        <div class="flex gap-x-4 justify-center mb-6 hover:cursor-pointer text-gradient text-xl font-medium">
          <h2>What you may want </h2>
          <p>|</p>
          <SyncOutlined style="color:#9370DB;"/>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 ml-2 mr-2">
          <a-card 
            v-for="(card, idx) in cardData"
            :key="idx"
            class="hover:shadow hover:shadow-indigo-500/30 hover:scale-105 ease-in-out transition hover:cursor-pointer"
            @click="hadleCardClick(card)"
          >
            <template #title>
              <p>🫧 {{ card.title }}</p>
            </template>
            <p>{{ card.description }}</p>
          </a-card>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue';
import SideBar from '@/components/SideBar.vue';
import { useRouter } from 'vue-router';
import { useFirstPromStore } from '@/stores/firstPrompt';
import { useAuthStore } from '@/stores/auth';

export default defineComponent({
  components: {
    SideBar,
  },
  setup() {
    const prompt = ref<string>('');
    const easyPlan = ref<boolean>(false);
    const router = useRouter();
    const cardData = [
      {
        title: "Hidden Gems",
        description: "Find secret gardens and offbeat attractions in Kyoto."
      },
      {
        title: "Top Towns and Cities",
        description: "Best cities in Italy for history, landscapes, and food."
      },
      {
        title: "Plan My Escape",
        description: "4-day Paris trip: mix of landmarks, hidden gems, and food."
      },
      {
        title: "Vegetarian Delights",
        description: "Vegetarian-friendly restaurants in Austin with great ambiance."
      },
      {
        title: "Perfect February Beaches",
        description: "Beaches with ideal February weather and vibes."
      },
      {
        title: "5 Days, Zero Regrets",
        description: "Epic 5-day Iceland itinerary with adventure highlights."
      }
    ]
    const firstPromptStore = useFirstPromStore()
    const auth = useAuthStore();
    
    const submitPrompt = async () => {
      router.push("/chat/new");
      firstPromptStore.firstPromptData = {
        isEasyPlan: easyPlan.value,
        user_input: prompt.value
      }
    };
    
    const hadleCardClick = (card: any) => {
      prompt.value = card.description
    }

    onMounted(() => {
      auth.initialize();
    });
    
    return {
      easyPlan,
      cardData,
      prompt,
      submitPrompt,
      hadleCardClick,
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