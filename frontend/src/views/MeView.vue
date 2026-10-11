<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { fetchMe, type MyStats } from '@/api/guests'
import ContinueSheet from '@/components/ContinueSheet.vue'
import PhotoTile from '@/components/PhotoTile.vue'
import ProfileSheet from '@/components/ProfileSheet.vue'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { ensureLoaded, getPhotoList, loadMore } from '@/stores/photoLists'
import { session, setProfile } from '@/stores/session'

const nickname = computed(() => session.nickname || '賓客')
const initial = computed(() => nickname.value[0] ?? '賓')

/** 「我上傳的」= GET /api/photos?uploader=me；點進照片詳情時帶同樣的條件，左右滑只在自己的照片之間 */
const MINE = { uploader: 'me' }
const uploaded = getPhotoList(MINE)

const stats = ref<MyStats>({ uploaded: 0, favorited: 0, likesReceived: 0, blessings: 0 })

/** 設計稿的第 4 個 tab 原本標「收藏」，收藏收進這裡當分頁 */
const tabs = [
  { id: 'uploaded', label: '我上傳的', stat: 'uploaded' },
  { id: 'favorites', label: '收藏', stat: 'favorited' },
  { id: 'blessings', label: '我的祝福', stat: 'blessings' },
] as const

const activeTab = ref<(typeof tabs)[number]['id']>('uploaded')

const continueOpen = ref(false)
const profileOpen = ref(false)

const sentinel = ref<HTMLElement>()
useInfiniteScroll(sentinel, async () => {
  if (uploaded.loading) return false
  await loadMore(MINE)
  return !uploaded.done && !uploaded.error
})

onMounted(() => {
  ensureLoaded(MINE)
  fetchMe()
    .then((me) => {
      stats.value = me.stats
      // 以後端為準，例如在別的裝置改過名字
      setProfile(me.guest.nickname, me.guest.relation ?? '')
    })
    .catch(() => {
      // 統計數字拿不到就先顯示 0，不擋住整頁
    })
})
</script>

<template>
  <main class="me">
    <div class="backdrop" />

    <button class="qr" type="button" aria-label="在其他裝置繼續" @click="continueOpen = true">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <path d="M14 14h3v3M21 14v3M14 21h3M21 18v3" />
      </svg>
    </button>

    <ContinueSheet v-model="continueOpen" />
    <ProfileSheet v-model="profileOpen" />

    <header class="profile">
      <span class="avatar">{{ initial }}</span>
      <div class="name-row">
        <h1 class="name">{{ nickname }}</h1>
        <button class="edit" type="button" aria-label="編輯個人資料" @click="profileOpen = true">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M12 20h9" />
            <path d="M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4 12.5-12.5z" />
          </svg>
        </button>
      </div>
      <p v-if="session.relation" class="relation">{{ session.relation }}</p>

      <div class="stats">
        <div class="stat">
          <p class="stat-n">{{ stats.uploaded }}</p>
          <p class="stat-l">已上傳</p>
        </div>
        <span class="stat-sep" />
        <div class="stat">
          <p class="stat-n">{{ stats.favorited }}</p>
          <p class="stat-l">收藏</p>
        </div>
        <span class="stat-sep" />
        <div class="stat">
          <p class="stat-n">{{ stats.likesReceived }}</p>
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
        {{ t.label }} <span class="tab-n">{{ stats[t.stat] }}</span>
      </button>
    </nav>

    <template v-if="activeTab === 'uploaded'">
      <div class="grid">
        <RouterLink
          v-for="(p, i) in uploaded.items"
          :key="p.id"
          class="cell"
          :to="{ name: 'photo-detail', params: { photoId: p.id }, query: MINE }"
        >
          <PhotoTile :photo="p" :index="i * 3" ratio="1/1" />
        </RouterLink>
      </div>
      <p v-if="uploaded.error" class="empty">{{ uploaded.error }}</p>
      <p v-else-if="uploaded.loaded && uploaded.items.length === 0" class="empty">
        你還沒有上傳照片
      </p>
      <div ref="sentinel" />
    </template>

    <!-- TODO: 第五步（收藏、祝福）的 API 做好之後接上 -->
    <p v-else class="empty">即將推出</p>
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
  padding: 0;
  color: var(--c-ink);
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

/* 筆的按鈕放名字右邊，名字本身仍置中：左邊用等寬的空白抵銷 */
.name-row {
  margin-top: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.name-row::before {
  content: '';
  width: 28px;
}

.edit {
  width: 28px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: 14px;
  background: transparent;
  color: var(--c-ink-mute);
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit svg {
  width: 14px;
  height: 14px;
}

.name {
  margin: 0;
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

.empty {
  margin: 32px 0;
  text-align: center;
  font-size: 13px;
  color: var(--c-ink-mute);
}

.cell {
  border-radius: 6px;
  overflow: hidden;
}
</style>
