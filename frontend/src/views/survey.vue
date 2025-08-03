<template>
  <div class="flex">
    <SideBar></SideBar>
    <ProjectInfo></ProjectInfo>
    <Consent></Consent>
    <div class="h-screen w-full overflow-scroll">
      <div v-if="useSurvey.surveyShow" class="pt-8 space-y-4 pl-30 pr-30 pb-15">
        <h1 class="text-center text-2xl font-bold text-gray-800">Project Survey</h1>

        <div class="ml-auto flex flex-row justify-between w-1/3 text-xs text-gray-400">
          <p>Strongly Disagree</p> <p>Strongly Agree</p>
        </div>

        <div v-for="(q, index) in questions" :key="index" class="mb-2 grid grid-cols-3">
          <div class="col-span-2 text-gray-700">{{ q.text }}</div>
          <a-radio-group v-model:value="q.value" :options="plainOptions" />
        </div>

        <div class="text-gray-600 font-bold pt-6">Any other suggestion for improvment:</div>
        <a-textarea v-model:value="improvementSuggestion" :rows="5" />
        
        <div class="p-6 flex justify-end gap-3">
          <a-button @click="onSubmit" type="primary">Submit</a-button>
        </div>
      </div>

      <div v-else-if="useSurvey.surveyCompleted">
        <a-result title="Thanks for your participation!">
          <template #icon>
            <smile-twoTone two-tone-color="#9370DB"/>
          </template>
        </a-result>
      </div>
    </div>
    
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import SideBar from '@/components/SideBar.vue';
import { useAuthStore } from '@/stores/auth.ts';
import axios from "axios";
import { useSurveyStore } from '@/stores/survey';
import ProjectInfo from '@/components/ProjectInfo.vue';
import Consent from '@/components/Consent.vue';
import { message, Modal } from 'ant-design-vue';
import { onBeforeRouteLeave } from 'vue-router';

const auth = useAuthStore();
const useSurvey = useSurveyStore();
const plainOptions = [1,2,3,4,5];

const questions = ref([
  { key: "question1", value: null, text: "1. Are interactive elements well sized?" },
  { key: "question2", value: null, text: "2. Is the color scheme easy to view and read?" },
  { key: "question3", value: null, text: "3. Does the website render well in your browser?" },
  { key: "question4", value: null, text: "4. Is the website easy to use?" },
  { key: "question5", value: null, text: "5. Are functions seamlessly integrated?" },
  { key: "question6", value: null, text: "6. Does the website perform smoothly?" },
  { key: "question7", value: null, text: "7. Can the AI assistant understand and answer you accurately?" },
  { key: "question8", value: null, text: "8. Does the AI assistant stay focused on travel-related topics?" },
  { key: "question9", value: null, text: "9. Do the recommended scenic spots match your preferences?" },
  { key: "question10", value: null, text: "10. Are the recommendations helpful in finding the scenic spots you like?" },
  { key: "question11", value: null, text: "11. Does the site help you save time when planning your travels?" },
  { key: "question12", value: null, text: "12. Does the detailed spot information help you make a choice?" },
  { key: "question13", value: null, text: "13. Is the itinerary calendar helpful for planning your trip?" },
]);

const improvementSuggestion = ref<string>('');

const allEmpty = computed(() => {
  return questions.value.every(q => q.value === null) && improvementSuggestion.value === '';
})

const onSubmit = async () => {
  const allCompleted = questions.value.every(q => q.value);
  if (!allCompleted) {
    message.info('Please complete all questions.');
    return;
  }
  useSurvey.onSurveyCompleted();
  const ret = {} as {[key: string]: any};
  questions.value.forEach(q => ret[q.key] = q.value);
  if (improvementSuggestion.value) {
    ret["improvement_suggestion"] = improvementSuggestion.value;
  }
  await axios.post("/survey/save-survey", {user_id: auth.token, survey_res: ret});
}

onMounted(async () => {
  const res = await axios.post("/survey/consent-status", {user_id: auth.token});
  if (res.data["is_consented"]) {
    if (res.data["survey_completed"]) {
      useSurvey.onSurveyCompleted();
    } else {
      useSurvey.showSurvey();
    }
  } else {
    useSurvey.showProjectInfo();
  }
});

onBeforeRouteLeave(async (to, from) => {
  if (useSurvey.surveyShow && !allEmpty.value) {
    return new Promise((resolve) => {
      Modal.confirm({
        title: "Unsaved Changes",
        content: "Leave without submitting?",
        onOk: () => {
          useSurvey.surveyShow = false;
          resolve(true);
        },
        onCancel: () => resolve(false)
      });
    });
  } else {
    useSurvey.clear();
    return true;
  }
});

window.addEventListener('beforeunload', (e) => {
  // Have to use returnValue, otherwise doesn't work
  if (useSurvey.surveyShow && !allEmpty.value) {
    e.preventDefault();
    const confirmationMessage = '';
    e.returnValue = confirmationMessage;
    return confirmationMessage;
  }
});

</script>

<style>
.ant-radio-wrapper {
  margin-right: 35px !important;
  padding-bottom: 16px;
}
</style>