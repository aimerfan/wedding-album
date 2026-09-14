<script setup lang="ts">
import { RouterLink } from 'vue-router'
import DecoDivider from '@/components/DecoDivider.vue'
</script>

<template>
  <main class="page">
    <h1>找不到這一頁</h1>
    <DecoDivider :width="40" />
    <p class="hint">它可能已經被收起來了</p>
    <RouterLink :to="{ name: 'feed' }" class="home">回到相簿</RouterLink>
  </main>
</template>

<style scoped>
.page {
  min-height: 100dvh;
  background: var(--c-bg);
  color: var(--c-ink);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 32px;
  text-align: center;
}

h1 {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 22px;
  font-weight: 500;
  letter-spacing: 1px;
}

.hint {
  margin: 0;
  font-size: 12px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.home {
  margin-top: 12px;
  padding: 12px 28px;
  border-radius: 24px;
  background: var(--c-rose);
  color: #fff;
  font-size: 13px;
  letter-spacing: 2px;
  box-shadow: var(--shadow-rose);
}
</style>
