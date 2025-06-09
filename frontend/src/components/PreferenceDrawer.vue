<template>
  <a-drawer title="Your Preference" :open="drawer.isOpen" @close="drawer.onClose()" class="flex flex-col">
    <div class="flex flex-col h-full">
      <div class="flex flex-row items-center justify-between mb-6">
        <p class="font-semibold">Adults</p>
        <a-input-number id="inputNumber" v-model:value="adult" :min="0" :max="100" />
        <p class="font-semibold">Children</p>
        <a-input-number id="inputNumber" v-model:value="child" :min="0" :max="100" />
      </div>

      <p class="font-semibold mb-2">Destination</p>
      <a-input v-model:value="value" placeholder="Type in any areas, countries, cities" />

      <p class="font-semibold mb-2 mt-6">Pick your time</p>
      <a-range-picker v-model:value="value3" :disabled-date="disabledDate" />

      <p class="font-semibold mt-6">Type of attractions</p>
      <p class="mb-2 text-sm mt-1 text-gray-400">You can type in any types not available</p>
      <a-select
        v-model:value="type"
        mode="tags"
        style="width: 100%"
        placeholder="Choose types you want"
        :options="options"
        @change="addType"
      ></a-select>

      <div class="flex flex-col grow mt-6 mb-6">
        <p class="font-semibold mb-2">Anything else</p>
        <a-textarea
          v-model:value="value2"
          placeholder="I'd like to have picnic. | A hike. | Somewhere relaxing."
          :auto-size="{ minRows: 2, maxRows: 7 }"
        />
      </div>
      <div class="flex flex-col gap-y-2">
        <div class="bg-gradient-to-r from-[#4c64db] to-[#a84adf] h-8 rounded-md leading-8 text-center
          hover:cursor-pointer hover:shadow hover:shadow-indigo-500">
          <p class="text-white">Consult AI With Choice</p>
        </div>
        <a-button type="primary">Save Choice</a-button>
        <a-button>Create Trip</a-button>
      </div>
    </div>
  </a-drawer>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';
import { useDrawerStore } from '@/stores/drawer.ts';
import dayjs, { Dayjs } from 'dayjs';

export default defineComponent({
  setup() {
    const drawer = useDrawerStore();
    const adult = ref<number>(1);
    const child = ref<number>(0);
    const value3 = ref<[Dayjs, Dayjs]>();

    const disabledDate = (current: Dayjs) => {
      // Can not select days before today and today
      return current && current < dayjs().endOf('day');
    };

    const addType = (value: string) => {
      console.log(`selected ${value}`);
    };
    const type = ref([]);
    const options = [{value:'Bustling cities'},{value:'Scenic landscapes'},{value:'Cultural heritage sites'},{value:'Coastal areas'}];

    return {
      drawer,
      adult,
      child,
      value3,
      disabledDate,
      addType,
      type,
      options,
    }
  }
})
</script>