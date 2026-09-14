<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import PhotoTile from '@/components/PhotoTile.vue'
import { currentGuest, myPhotos, myStats } from '@/mock/sample'
import { session } from '@/stores/session'

const nickname = computed(() => session.nickname || currentGuest.nickname)
const initial = computed(() => nickname.value[0] ?? '賓')

/** 設計稿的第 4 個 tab 原本標「收藏」，收藏收進這裡當分頁 */
const tabs = [
  { id: 'uploaded', label: '我上傳的', count: myStats.uploaded },
  { id: 'favorites', label: '收藏', count: myStats.favorited },
  { id: 'blessings', label: '我的祝福', count: myStats.blessings },
] as const

const activeTab = ref<(typeof tabs)[number]['id']>('uploaded')
</script>

<template>
  <main class="me">
    <div class="backdrop" />

    <RouterLink :to="{ name: 'feed' }" class="qr" aria-label="分享 QR Code">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <path d="M14 14h3v3M21 14v3M14 21h3M21 18v3" />
      </svg>
    </RouterLink>

    <header class="profile">
      <span class="avatar">{{ initial }}</span>
      <h1 class="name">{{ nickname }}</h1>
      <p class="relation">{{ currentGuest.relation }}</p>

      <div class="stats">
        <div class="stat">
          <p class="stat-n">{{ myStats.uploaded }}</p>
          <p class="stat-l">已上傳</p>
        </div>
        <span class="stat-sep" />
        <div class="stat">
          <p class="stat-n">{{ myStats.favorited }}</p>
          <p class="stat-l">收藏</p>
        </div>
        <span class="stat-sep" />
        <div class="stat">
          <p class="stat-n">{{ myStats.likesReceived }}</p>
          <p class="stat-l">收到的讚</p>
        </div>
      </div>
    </header>

    <nav class="tabs">
      <button
        v-for="t in tabs"
        :key="t.id"
        type="button"
        class="tab"
        :class="{ active: activeTab === t.id }"
        @click="activeTab = t.id"
      >
        {{ t.label }} <span class="tab-n">{{ t.count }}</span>
      </button>
    </nav>

    <div class="grid">
      <RouterLink
        v-for="(p, i) in myPhotos"
        :key="p.id"
        class="cell"
        :to="{ name: 'photo-detail', params: { photoId: p.id } }"
      >
        <PhotoTile :photo="p" :index="i * 3" ratio="1/1" />
      </RouterLink>
    </div>
  </main>
</template>

<style scoped>
.me {
  position: relative;
  min-height: 100dvh;
  background: var(--c-bg);
  color: var(--c-ink);
}

.backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 200px;
  background: linear-gradient(180deg, var(--c-bg-soft) 0%, var(--c-bg) 100%);
}

.qr {
  position: absolute;
  top: calc(var(--page-top) + 28px);
  right: 20px;
  z-index: 5;
  width: 36px;
  height: 36px;
  border-radius: 18px;
  background: var(--c-card);
  border: 1px solid var(--c-line);
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr svg {
  width: 16px;
  height: 16px;
}

.profile {
  position: relative;
  padding-top: calc(var(--page-top) + 48px);
  text-align: center;
}

.avatar {
  width: 76px;
  height: 76px;
  border-radius: 38px;
  margin: 0 auto;
  background: var(--c-card);
  border: 2px solid var(--c-bg);
  box-shadow: var(--shadow-raised);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-serif);
  font-size: 32px;
}

.name {
  margin: 12px 0 0;
  font-family: var(--f-serif);
  font-size: 20px;
  font-weight: 500;
  letter-spacing: 1px;
}

.relation {
  margin: 2px 0 0;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.stats {
  margin: 18px 20px 0;
  padding: 14px 0;
  border-radius: 14px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
  display: flex;
  justify-content: space-around;
}

.stat {
  flex: 1;
  text-align: center;
}

.stat-sep {
  width: 1px;
  background: var(--c-line);
}

.stat-n {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 22px;
  font-weight: 500;
}

.stat-l {
  margin: 2px 0 0;
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.tabs {
  margin-top: 20px;
  padding: 0 20px;
  display: flex;
  gap: 20px;
  border-bottom: 1px solid var(--c-line);
}

.tab {
  position: relative;
  padding: 0 0 10px;
  border: 0;
  background: transparent;
  font-size: 13px;
  color: var(--c-ink-mute);
}

.tab.active {
  color: var(--c-ink);
  font-weight: 500;
}

.tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--c-rose);
}

.tab-n {
  font-size: 10px;
  color: var(--c-ink-mute);
}

.grid {
  padding: 12px 16px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
}

.cell {
  border-radius: 6px;
  overflow: hidden;
}
</style>
