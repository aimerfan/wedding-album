<script setup lang="ts">
import { useRegisterSW } from 'virtual:pwa-register/vue'

// registerType 是 autoUpdate，新版 Service Worker 會自己接手，
// 這裡只負責提示使用者「已經換新版了」跟「可以離線使用了」。
const { offlineReady, needRefresh, updateServiceWorker } = useRegisterSW()

function close() {
  offlineReady.value = false
  needRefresh.value = false
}
</script>

<template>
  <div v-if="offlineReady || needRefresh" class="pwa-toast" role="status" aria-live="polite">
    <span>{{ offlineReady ? '已可離線使用' : '有新版本' }}</span>
    <button v-if="needRefresh" type="button" @click="updateServiceWorker(true)">重新載入</button>
    <button type="button" @click="close">關閉</button>
  </div>
</template>

<style scoped>
.pwa-toast {
  position: fixed;
  left: 50%;
  bottom: calc(1rem + env(safe-area-inset-bottom));
  transform: translateX(-50%);
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 999px;
  background: #1a1a1a;
  color: #fff;
  font-size: 0.875rem;
  box-shadow: 0 4px 16px rgb(0 0 0 / 0.2);
}

.pwa-toast button {
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
}
</style>
