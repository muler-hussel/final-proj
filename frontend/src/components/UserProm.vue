<template>
  <div class="flex items-center p-4 bg-violet-50 h-fit rounded-l-2xl rounded-b-2xl w-fit ml-auto text-justify">
    <p class="text-gray-700">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">

defineProps<{
  message: string
}>()

</script>