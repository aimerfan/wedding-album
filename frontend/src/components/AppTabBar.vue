<script setup lang="ts">
import { RouterLink } from 'vue-router'

/**
 * 底部 tab bar。
 * 設計稿裡第 4 個 tab 標「收藏」卻連到祝福留言牆 —— 那是 prototype 的接線筆誤。
 * 這裡定為「祝福」，收藏收進「我的」頁的分頁。
 */
const tabs = [
  { to: { name: 'feed' }, label: '相簿' },
  { to: { name: 'upload' }, label: '上傳' },
  { to: { name: 'wedding' }, label: '婚紗集' },
  { to: { name: 'blessings' }, label: '祝福' },
  { to: { name: 'me' }, label: '我的' },
] as const
</script>

<template>
  <nav class="tabbar">
    <RouterLink v-for="tab in tabs" :key="tab.label" :to="tab.to" class="tab">
      <svg
        v-if="tab.label === '相簿'"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect x="3" y="3" width="18" height="18" rx="2.5" />
        <circle cx="9" cy="9" r="1.5" />
        <path d="M21 16l-5-5L5 21" />
      </svg>
      <svg
        v-else-if="tab.label === '上傳'"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M12 4v14M5 11l7-7 7 7" />
        <path d="M4 21h16" />
      </svg>
      <svg
        v-else-if="tab.label === '婚紗集'"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z" />
      </svg>
      <svg
        v-else-if="tab.label === '祝福'"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path
          d="M21 11.5a8.4 8.4 0 01-9 8.3 9 9 0 01-3.4-.6L3 21l1.9-5.1A8.2 8.2 0 014 11.5 8.4 8.4 0 0112.5 3 8.4 8.4 0 0121 11.5z"
        />
      </svg>
      <svg
        v-else
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6" />
      </svg>
      <span>{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 30;
  display: flex;
  justify-content: space-around;
  align-items: flex-start;
  height: calc(var(--tabbar-height) + var(--safe-bottom));
  padding-top: 8px;
  padding-bottom: var(--safe-bottom);
  background: rgba(255, 252, 247, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 0.5px solid var(--c-line-strong);
}

.tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  min-width: 44px;
  font-size: 9px;
  letter-spacing: 0.3px;
  color: var(--c-ink-mute);
}

.tab svg {
  width: 20px;
  height: 20px;
}

/* Vue Router 會在 active 的連結加上這個 class */
.tab.router-link-exact-active {
  color: var(--c-rose);
}
</style>
