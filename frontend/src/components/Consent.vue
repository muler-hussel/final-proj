<template>
  <a-modal
    v-model:open="useSurvey.consentOpen"
    width="100%"
    wrap-class-name="full-modal"
    @cancel="handelCancel"
  >
    <template #footer>
      <a-button key="cancel" @click="handelCancel">cancel</a-button>
      <a-button key="submit" type="primary" @click="handleSubmit">Submit</a-button>
    </template>

    <div class="absolute top-0 right-0 p-16">
      <img src="@/assets/bristollogo.png" alt="Logo" class="h-20 w-auto">
    </div>

    <div class="text-center space-y-3 pt-16">
      <h1 class="text-2xl font-bold text-gray-800">PARTICIPANT CONSENT FORM</h1>
      <p class="font-semibold text-gray-800">Please answer the following questions to the best of your knowledge</p>
    </div>
    
    <div class="p-30 text-lg space-y-4 text-gray-800">
      <h3 class="font-bold">HAVE YOU:</h3>
      <div class="pl-8 pr-10 space-y-2">
        <div class="flex flex-row items-center justify-between">
          <p>Been given information explaining about the study?</p>
          <a-radio-group v-model:value="value1" :options="plainOptions" />
        </div>
        <div class="flex flex-row items-center justify-between">
          <p>Had an opportunity to ask questions and discuss this study?</p>
          <a-radio-group v-model:value="value2" :options="plainOptions" />
        </div>
        <div class="flex flex-row items-center justify-between">
          <p>Received satisfactory answers to all questions you asked?</p>
          <a-radio-group v-model:value="value3" :options="plainOptions" />
        </div>
        <div class="flex flex-row items-center justify-between">
          <p>Received enough information about the study for you to make a decision about your participation?</p>
          <a-radio-group v-model:value="value4" :options="plainOptions" />
        </div>
        <div class="flex flex-row items-center justify-between">
          <p>Ascertained that you don’t have any known condition that prevents you from taking part in this study?</p>
          <a-radio-group v-model:value="value5" :options="plainOptions" />
        </div>
      </div>
      <h3 class="font-bold">DO YOU UNDERSTAND:</h3>
      <div>That you are free to withdraw from the study and free to withdraw your data prior to final consent</div>
      <div class="pl-8 pr-10 space-y-2">
        <div class="flex flex-row items-center justify-between">
          <p>At any time?</p>
          <a-radio-group v-model:value="value6" :options="plainOptions" />
        </div>
        <div class="flex flex-row items-center justify-between">
          <p>Without having to give a reason for withdrawing?</p>
          <a-radio-group v-model:value="value7" :options="plainOptions" />
        </div>
      </div>
    </div>

    <div class="text-xl text-center font-bold text-gray-800">I hereby fully and freely consent to my participation in this study</div>
    <div class="pl-30 pr-30 pt-8 text-lg">
      I understand the nature and purpose of the procedures involved in this study. These have been communicated to me on the information sheet accompanying this form.<br><br>
      I understand and acknowledge that the investigation is designed to promote scientific knowledge and that the University of Bristol will use the data I provide for no purpose other than teaching and research. <br><br>
      I understand the data I provide will be anonymous. No link will be made between my name or other identifying information and my study data. <br><br>
      I understand that the University of Bristol may use the data collected for this study in a future research project but that the conditions on this form under which I have provided the data will still apply. <br><br>
      I agree to the University of Bristol keeping and processing the data I have provided during the course of this study. I understand that this data will be used only for the purpose(s) set out in the information sheet, and my consent is conditional upon the University complying with its duties and obligations under GDPR.
      <div class="pt-8 flex space-x-4">
        <p>Participant’s signature:</p>
        <a-input v-model:value="signature" style="width: 200px" />
      </div>
      <div class="pt-8 flex space-x-4">
        <p>Date:</p>
        <button v-if="!signedDate" @click="fillDate" class="w-40 border-b border-gray-400 hover:cursor-pointer">
        </button>
        <span v-else class="border-b border-gray-400 px-2">
          {{ signedDate }}
        </span>
      </div>
      <div class="pt-8 flex space-x-4">
        <p>Name in BLOCK Letters:</p>
        <a-input v-model:value="blockName" style="width: 200px" />
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { useSurveyStore } from '@/stores/survey';
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import { useRouter } from 'vue-router';

const useSurvey = useSurveyStore();
const plainOptions = ['Yes', 'No'];
const router = useRouter();

const value1 = ref<string>('');
const value2 = ref<string>('');
const value3 = ref<string>('');
const value4 = ref<string>('');
const value5 = ref<string>('');
const value6 = ref<string>('');
const value7 = ref<string>('');
const signature = ref<string>('');
const blockName = ref<string>('');
const signedDate = ref('');

const fillDate = () => {
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, '0');
  const dd = String(today.getDate()).padStart(2, '0');
  signedDate.value = `${yyyy}-${mm}-${dd}`;
}

const handleSubmit = async () => {
  const values = [value1, value2, value3, value4, value5, value6, value7];

  const allYes = values.every(v => v.value === 'Yes');
  const hasSignature = signature.value.trim() !== '';
  const hasDate = signedDate.value.trim() !== '';
  const isValidBlockName = /^[A-Z]+$/.test(blockName.value.trim());

  if (!allYes) {
    message.info('All questions must be answered "Yes".');
    return;
  }

  if (!hasSignature || !hasDate) {
    message.info('Signature and date are required.');
    return;
  }

  if (!isValidBlockName) {
    message.info('Block name must be all uppercase letters.');
    return;
  }
  const consentHash = await generateConsentHash({
    value1: value1.value,
    value2: value2.value,
    value3: value3.value,
    value4: value4.value,
    value5: value5.value,
    value6: value6.value,
    value7: value7.value,
    signature: signature.value.trim(),
    block_name: blockName.value.trim(),
    signed_at: signedDate.value});
  await useSurvey.onConsentConfirm(consentHash);
}

const handelCancel = () => {
  useSurvey.onConsentCancel();
  router.push('/');
}

async function generateConsentHash(data: {
  value1: string
  value2: string
  value3: string
  value4: string
  value5: string
  value6: string
  value7: string
  signature: string
  block_name: string
  signed_at: string
}): Promise<string> {
  const payload = JSON.stringify(data, Object.keys(data).sort());
  const encoder = new TextEncoder();
  const dataBuffer = encoder.encode(payload);
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  return hashHex;
}
    
</script>

<style>
.full-modal {
  .ant-modal {
    max-width: 100%;
    top: 0;
    padding-bottom: 0;
    margin: 0;
    overflow: hidden;
  }
  .ant-modal-content {
    display: flex;
    flex-direction: column;
    height: calc(100vh);
    overflow: scroll;
  }
  .ant-modal-body {
    flex: 1;
  }
}
</style>