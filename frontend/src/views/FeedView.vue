<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import PhotoTile from '@/components/PhotoTile.vue'
import { wedding } from '@/config/wedding'
import { feedPhotos, stats } from '@/mock/sample'
import type { PhotoTag } from '@/types/album'

type Filter = { id: string; label: string; tag?: PhotoTag; videoOnly?: boolean; today?: boolean }

const filters: Filter[] = [
  { id: 'all', label: '全部' },
  { id: 'today', label: '今天', today: true },
  { id: 'welcome', label: '迎賓', tag: 'welcome' },
  { id: 'ceremony', label: '儀式', tag: 'ceremony' },
  { id: 'banquet', label: '宴客', tag: 'banquet' },
  { id: 'video', label: '影片', videoOnly: true },
]

const activeFilter = ref('all')

const visible = computed(() => {
  const f = filters.find((x) => x.id === activeFilter.value)
  if (!f || f.id === 'all') return feedPhotos
  if (f.videoOnly) return feedPhotos.filter((p) => p.kind === 'video')
  if (f.tag) return feedPhotos.filter((p) => p.tags.includes(f.tag!))
  return feedPhotos
})

// 兩欄瀑布流：依序左右分配
const columnA = computed(() => visible.value.filter((_, i) => i % 2 === 0))
const columnB = computed(() => visible.value.filter((_, i) => i % 2 === 1))

function ratioOf(p: { width: number; height: number }) {
  return `${p.width}/${p.height}`
}

function duration(seconds?: number) {
  if (!seconds) return ''
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}
</script>

<template>
  <main class="feed">
    <header class="head">
      <div class="head-row">
        <div>
          <p class="date-en">{{ wedding.dateDisplayEn }}</p>
          <h1 class="names">
            {{ wedding.groomName }} <span class="amp">&amp;</span> {{ wedding.brideName }}
          </h1>
          <p class="stats">共 {{ stats.photoCount }} 張回憶 · {{ stats.guestCount }} 位賓客</p>
        </div>
        <button class="icon-btn" type="button" aria-label="搜尋">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.6"
            stroke-linecap="round"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="M16 16l5 5" />
          </svg>
        </button>
      </div>

      <div class="chips">
        <button
          v-for="f in filters"
          :key="f.id"
          type="button"
          class="chip"
          :class="{ active: activeFilter === f.id }"
          @click="activeFilter = f.id"
        >
          {{ f.label }}
        </button>
      </div>
    </header>

    <div class="masonry">
      <div class="column">
        <RouterLink
          v-for="p in columnA"
          :key="p.id"
          class="card"
          :to="{ name: 'photo-detail', params: { photoId: p.id } }"
        >
          <PhotoTile :photo="p" :index="feedPhotos.indexOf(p)" :ratio="ratioOf(p)">
            <span v-if="p.kind === 'video'" class="video-badge">
              <svg viewBox="0 0 12 12" fill="#fff"><path d="M3 2v8l7-4z" /></svg>
              {{ duration(p.durationSeconds) }}
            </span>
          </PhotoTile>
          <div class="card-foot">
            <span class="avatar">{{ p.uploader.nickname[0] }}</span>
            {{ p.uploader.nickname }}
          </div>
        </RouterLink>
      </div>
      <div class="column">
        <RouterLink
          v-for="p in columnB"
          :key="p.id"
          class="card"
          :to="{ name: 'photo-detail', params: { photoId: p.id } }"
        >
          <PhotoTile :photo="p" :index="feedPhotos.indexOf(p)" :ratio="ratioOf(p)">
            <span v-if="p.kind === 'video'" class="video-badge">
              <svg viewBox="0 0 12 12" fill="#fff"><path d="M3 2v8l7-4z" /></svg>
              {{ duration(p.durationSeconds) }}
            </span>
          </PhotoTile>
          <div class="card-foot">
            <span class="avatar">{{ p.uploader.nickname[0] }}</span>
            {{ p.uploader.nickname }}
          </div>
        </RouterLink>
      </div>
    </div>
  </main>
</template>

<style scoped>
.feed {
  background: var(--c-bg);
  min-height: 100dvh;
}

.head {
  padding: calc(var(--page-top) + 24px) 20px 16px;
}

.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.date-en {
  margin: 0;
  font-family: var(--f-display);
  font-style: italic;
  font-size: 12px;
  letter-spacing: 3px;
  color: var(--c-gold);
}

.names {
  margin: 4px 0 0;
  font-family: var(--f-serif);
  font-size: 26px;
  font-weight: 500;
  letter-spacing: 1px;
}

.amp {
  font-family: var(--f-display);
  font-style: italic;
  color: var(--c-rose);
}

.stats {
  margin: 4px 0 0;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.icon-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 18px;
  background: var(--c-card);
  border: 1px solid var(--c-line);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-ink);
}

.icon-btn svg {
  width: 16px;
  height: 16px;
}

.chips {
  margin-top: 18px;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  /* 隱藏水平捲軸，手機上用手勢滑 */
  scrollbar-width: none;
}

.chips::-webkit-scrollbar {
  display: none;
}

.chip {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 14px;
  border: 1px solid var(--c-line);
  background: transparent;
  color: var(--c-ink-soft);
  font-size: 11px;
  letter-spacing: 1px;
  white-space: nowrap;
}

.chip.active {
  background: var(--c-ink);
  border-color: transparent;
  color: var(--c-bg);
}

.masonry {
  padding: 0 16px;
  display: flex;
  gap: 10px;
}

.column {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  /* 兩欄等寬，內容才不會把欄位撐開 */
  min-width: 0;
}

.card {
  border-radius: 12px;
  overflow: hidden;
  background: var(--c-card);
  box-shadow: var(--shadow-card);
}

.video-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.5);
  font-size: 9px;
  color: #fff;
}

.video-badge svg {
  width: 9px;
  height: 9px;
}

.card-foot {
  padding: 8px 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--c-ink-soft);
}

.avatar {
  width: 16px;
  height: 16px;
  border-radius: 8px;
  background: var(--c-bg-deep);
  color: var(--c-ink);
  font-family: var(--f-serif);
  font-size: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
