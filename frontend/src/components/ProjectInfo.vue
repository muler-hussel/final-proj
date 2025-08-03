<template>
  <a-modal
    v-model:open="useSurvey.projectInfoOpen"
    width="100%"
    wrap-class-name="full-modal"
  > 
    <template #footer>
      <a-button key="cancel" @click="handelCancel">cancel</a-button>
      <a-button key="submit" type="primary" @click="useSurvey.onProjectInfoConfirm">Have Read Information Sheet</a-button>
    </template>
    <div class="absolute top-0 right-0 p-16">
      <img src="@/assets/bristollogo.png" alt="Logo" class="h-20 w-auto">
    </div>
    <div class="text-center space-y-3 pt-8">
      <h1 class="text-2xl font-bold text-gray-800">Study Information Sheet</h1>
      <p class="text-lg font-semibold text-gray-700">MSc Individual Project (COMSM3201)</p>
      <div class="text-gray-600 space-x-4">
        <span>Contact Name: Zhu Xuefei</span>
        <span>Email: ft24227@bristol.ac.uk</span>
        <span>Date: Aug 03 2025</span>
      </div>
    </div>
    <div class="p-30 text-lg">
      Dear Participant,<br><br>
      I am a student in Computer Science at the University of Bristol, currently developing a travelling website as part of our final project. To evaluate the project, we are engaging participants to try to understand usability of the website. This data collection will take place using questionnaires of the use of our designs. By engaging potential users in the initial design activities of these interactive prototypes, we hope to ensure that our designs are both useful and usable.
      <br><br>
      <b>Participation</b><br><br>
      Participants should be over 18 and should be able to provide written consent on the form provided.<br>
      Participation in this study is voluntary. If you decide to take part, you will be asked to provide written consent. You are free to withdraw during the study at any time and without having to give a reason.<br><br>
      <b>Risks and Disadvantages</b><br><br>
      There are no known risks associated with completion of the questionnaires, the interviews, or the observations of the use of the device. <br><br>
      <b>Data management and Confidentiality</b><br><br>
      No personally identifying information will be recorded on the questionnaires, interviews, or observations. Any personal information recorded as part of the consent process will be kept strictly confidential by the development teams and the lecturing staff. Any final write-ups of the data gathered will not include any information that can be linked directly to you. <br>
      All data will be stored so that your name is not associated with it (using an arbitrary participant number) and no photographs, audio recordings, or video recordings will be made. All data will be handled confidentially and anonymously. The data collected from this study will be used in a coursework submission to the University of Bristol. Results from the research will be presented in accordance with rules for anonymity such that the results cannot be traced to individual participants.<br>
      If you have any questions about the management of your data please do not hesitate to ask.<br><br>
      <b>Right to Withdraw</b><br><br>
      <b>You are free to withdraw from the study at any time without penalty and without losing any advertised benefits.</b> Withdrawal from the study will not affect your academic status or your access to services at the University of Bristol. If you withdraw, all of your non-anonymised data held by the student will be deleted from the study and destroyed. Please note that data can only be withdrawn up until the point that the data is anonymised; after this time your data cannot be identified. In addition, you are free to not answer specific questions in the interviews or on the questionnaire. <br>
      Your continued participation should be as informed as your initial consent, so you should feel free to ask for clarification or new information throughout your participation. If you have further questions concerning matters related to this research, please contact us by emailing both the Lecturer and the Group using the details given at the top of the document. <br><br>
      <b>Questions</b><br><br>
      If you have any questions concerning the study, please feel free to ask at any point; you are also free to contact us with the details provided above if you have questions at a later time.<br>
      This study has been approved on ethical grounds by the University of Bristol Faculty of Engineering Ethics Board.<br>
      Any questions regarding your rights as a participant may be addressed to that committee through the Faculty Ethics Officer (<a href="http://www.bris.ac.uk/red/support/governance/ethics/ethics.html">http://www.bris.ac.uk/red/support/governance/ethics/ethics.html</a>). Please note that you are free to withdraw from participation at any time. 
      <br><br>
      Thank you for your interest and cooperation. If you would like more information about the research project, please feel free to make contact.
      <br><br>
      Yours faithfully,
      <br><br>
      Zhu Xuefei

    </div>
  </a-modal>
</template>

<script lang="ts">
import { useSurveyStore } from '@/stores/survey';
import { defineComponent } from 'vue';
import { useRouter } from 'vue-router';

export default defineComponent({
  setup() {
    const useSurvey = useSurveyStore();
    const router = useRouter();

    const handelCancel = () => {
      useSurvey.onProjectInfoCancel();
      router.push('/');
    }
    return {
      useSurvey,
      handelCancel,
    }
  }
})
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