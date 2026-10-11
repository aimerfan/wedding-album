<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { deleteBlessing } from '@/api/blessings'
import { ApiError } from '@/api/client'
import { ensureGuestId } from '@/api/guests'
import { fetchStats } from '@/api/photos'
import BlessingComposer from '@/components/BlessingComposer.vue'
import BlessingNote from '@/components/BlessingNote.vue'
import DecoDivider from '@/components/DecoDivider.vue'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import {
  ensureBlessingsLoaded,
  getBlessingList,
  loadMoreBlessings,
  reloadBlessings,
  removeBlessing,
} from '@/stores/blessingLists'
import type { AlbumStats, Blessing } from '@/types/album'

/** 留言牆：GET /api/blessings，新的在上 */
const ALL = {}
const wall = getBlessingList(ALL)
const stats = ref<AlbumStats | null>(null)

const sentinel = ref<HTMLElement>()
useInfiniteScroll(sentinel, async () => {
  if (wall.loading) return false
  await loadMoreBlessings(ALL)
  return !wall.done && !wall.error
})

function refreshStats() {
  fetchStats()
    .then((s) => (stats.value = s))
    .catch(() => {
      // 標題的數字只是裝飾，拿不到就不顯示
    })
}

onMounted(() => {
  ensureBlessingsLoaded(ALL)
  refreshStats()
  // 要知道自己是誰，自己的祝福才會出現「修改、刪除」
  ensureGuestId().catch(() => {})
})

// --- 寫祝福 / 修改祝福 -----------------------------------------------------

const composing = ref(false)
/** 正在修改哪一則；null 代表寫新的 */
const editing = ref<Blessing | null>(null)

function openComposer(target: Blessing | null = null) {
  editing.value = target
  composing.value = true
}

function onSaved(_blessing: Blessing, isNew: boolean) {
  if (!isNew) return
  refreshStats()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function remove(blessing: Blessing) {
  if (!window.confirm('確定要刪除這則祝福嗎？刪除後無法復原。')) return
  try {
    await deleteBlessing(blessing.id)
    removeBlessing(blessing.id)
    refreshStats()
  } catch (e) {
    window.alert(e instanceof ApiError ? e.message : '刪除失敗，請稍後再試')
  }
}
</script>

<template>
  <main class="blessings">
    <header class="head">
      <div class="head-row">
        <RouterLink :to="{ name: 'feed' }" class="back">← 相簿</RouterLink>
        <span class="kicker">BLESSINGS</span>
        <span class="spacer" />
      </div>

      <div class="title-block">
        <h1>祝 福 留 言</h1>
        <DecoDivider :width="40" />
        <p v-if="stats" class="summary">
          {{ stats.blessingGuestCount }} 位賓客留下了 {{ stats.blessingCount }} 則祝福
        </p>
      </div>
    </header>

    <ul class="list">
      <BlessingNote
        v-for="(b, i) in wall.items"
        :key="b.id"
        :blessing="b"
        :tilt="i % 2 === 0 ? 'left' : 'right'"
        @edit="openComposer"
        @delete="remove"
      />
    </ul>

    <p v-if="wall.loaded && wall.items.length === 0" class="status">
      還沒有人留言，寫下第一則祝福吧
    </p>
    <p v-else-if="wall.error" class="status">
      {{ wall.error }}
      <button class="retry" type="button" @click="reloadBlessings(ALL)">重試</button>
    </p>
    <p v-else-if="wall.loading" class="status">載入中…</p>

    <div ref="sentinel" class="sentinel" />

    <button class="fab" type="button" @click="openComposer()">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
      >
        <path d="M12 19l7-7 3 3-7 7-3-3z" />
        <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" />
      </svg>
      寫祝福
    </button>

    <BlessingComposer v-model="composing" :editing="editing" @saved="onSaved" />
  </main>
</template>

<style scoped>
.blessings {
  min-height: 100dvh;
  background: var(--c-bg);
  color: var(--c-ink);
}

.head {
  padding: calc(var(--page-top) + 24px) 20px 14px;
}

.head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.back {
  font-size: 14px;
  color: var(--c-ink-soft);
}

.kicker {
  font-size: 12px;
  letter-spacing: 2px;
  color: var(--c-gold);
}

.spacer {
  width: 30px;
}

.title-block {
  margin-top: 16px;
  text-align: center;
}

.title-block h1 {
  margin: 0 0 4px;
  font-family: var(--f-serif);
  font-size: 24px;
  font-weight: 500;
  letter-spacing: 1px;
}

.summary {
  margin: 8px 0 0;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.list {
  margin: 0;
  padding: 8px 16px;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status {
  margin: 24px 0;
  text-align: center;
  font-size: 13px;
  color: var(--c-ink-mute);
}

.retry {
  margin-left: 8px;
  padding: 4px 12px;
  border: 1px solid var(--c-line-strong);
  border-radius: 12px;
  background: transparent;
  font-size: 12px;
  color: var(--c-ink);
}

.sentinel {
  height: 80px;
}

.fab {
  position: fixed;
  right: 20px;
  bottom: calc(var(--page-bottom) + 20px);
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 18px;
  border: 0;
  border-radius: 24px;
  background: var(--c-ink);
  color: #fff;
  font-size: 12px;
  letter-spacing: 1px;
  box-shadow: var(--shadow-float);
}

.fab svg {
  width: 14px;
  height: 14px;
}
</style>
