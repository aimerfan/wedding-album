<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppTabBar from '@/components/AppTabBar.vue'
</script>

<template>
  <div class="shell">
    <RouterView />
    <AppTabBar />
  </div>
</template>

<style scoped>
.shell {
  min-height: 100dvh;
  /* 讓內容不被 tab bar 蓋住 */
  padding-bottom: var(--page-bottom);
}
</style>
