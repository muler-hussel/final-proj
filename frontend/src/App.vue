<script setup lang="ts">
  import { ConfigProvider } from 'ant-design-vue';
</script>

<template>
  <ConfigProvider 
    :theme="{
      token: {
        colorPrimary: '#9370DB'
      }
    }"
    
  >
    <router-view />
  </ConfigProvider>
</template>

<style scoped>

</style>
