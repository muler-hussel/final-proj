<template>
  <div class="flex items-center p-4 bg-violet-50 h-fit rounded-l-2xl rounded-b-2xl w-fit ml-auto text-justify">
    <p class="text-gray-700">{{ content }}</p>
  </div>
</template>

<script setup lang="ts">

defineProps<{
  content: string | null
}>()

</script>