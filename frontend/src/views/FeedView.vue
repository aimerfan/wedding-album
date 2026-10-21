<script lang="ts">
import ScriptHeart from '@/components/ScriptHeart.vue'
import { ref } from 'vue'

// 放在元件外面：從照片詳情返回首頁時，仍停在原本選的分類與搜尋
const activeChip = ref('all')
const searchOpen = ref(false)
/** 輸入框裡的字 */
const searchText = ref('')
/** 實際拿去搜尋的字：停止輸入一下才更新，不必每打一個字就問一次後端 */
const searchQuery = ref('')
</script>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { fetchStats, type PhotoFilter } from '@/api/photos'
import PhotoTile from '@/components/PhotoTile.vue'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { wedding } from '@/config/wedding'
import { ensureLoaded, filterToQuery, getPhotoList, loadMore, reload } from '@/stores/photoLists'
import type { AlbumStats } from '@/types/album'

type Chip = { id: string; label: string; filter: PhotoFilter }

/** 篩選交給後端（GET /api/photos 的參數），每個 chip 各自是一串快取的列表 */
const chips: Chip[] = [
  { id: 'all', label: '全部', filter: {} },
  { id: 'engagement', label: '訂婚・迎娶', filter: { tag: 'engagement' } },
  { id: 'banquet', label: '宴客', filter: { tag: 'banquet' } },
  { id: 'candid', label: '花絮', filter: { tag: 'candid' } },
  { id: 'throwback', label: '那些年', filter: { tag: 'throwback' } },
  { id: 'video', label: '影片', filter: { kind: 'video' } },
]

/** 分類與搜尋可以合併，例如「影片」＋「小慧」 */
const filter = computed<PhotoFilter>(() => {
  const chip = chips.find((c) => c.id === activeChip.value)!.filter
  return searchQuery.value ? { ...chip, q: searchQuery.value } : chip
})
const list = computed(() => getPhotoList(filter.value))

// --- 搜尋：比對上傳者的暱稱與「與新人的關係」（GET /api/photos?q=） ---------

const searchInput = ref<HTMLInputElement>()
let debounce: ReturnType<typeof setTimeout> | undefined

watch(searchText, (text) => {
  clearTimeout(debounce)
  debounce = setTimeout(() => (searchQuery.value = text.trim()), 300)
})
onBeforeUnmount(() => clearTimeout(debounce))

// 換了搜尋字或分類就載入那一串（已經載過的直接用快取）
watch(filter, (f) => ensureLoaded(f))

async function openSearch() {
  searchOpen.value = true
  await nextTick()
  searchInput.value?.focus()
}

/** 按 Enter 不等了，馬上搜尋，並收起鍵盤看結果 */
function submitSearch() {
  clearTimeout(debounce)
  searchQuery.value = searchText.value.trim()
  searchInput.value?.blur()
}

function closeSearch() {
  clearTimeout(debounce)
  searchText.value = ''
  searchQuery.value = ''
  searchOpen.value = false
}

const emptyMessage = computed(() => {
  if (searchQuery.value) return `找不到「${searchQuery.value}」上傳的照片`
  return activeChip.value === 'all' ? '還沒有照片，成為第一個分享回憶的人吧' : '這個分類還沒有照片'
})

// 兩欄瀑布流：依序左右分配。載入下一頁時只往後加，已經排好的不會跳動
const columnA = computed(() => list.value.items.filter((_, i) => i % 2 === 0))
const columnB = computed(() => list.value.items.filter((_, i) => i % 2 === 1))

const stats = ref<AlbumStats | null>(null)

function select(chip: Chip) {
  slide.value = ''
  activeChip.value = chip.id
}

// --- 左右滑動切換分類 -----------------------------------------------------
// 只在手指離開時判斷一次（不跟著手指移動），上下捲動完全交給瀏覽器。
// 從分類列、搜尋框開始的滑動不算（分類列自己會橫向捲動）；
// 從螢幕左右邊緣開始的也不算，那是 Android 的返回、iPhone Safari 的上一頁手勢。

const SWIPE_MIN = 45
const EDGE = 24
let touchStart: { x: number; y: number; t: number } | null = null

/** 這次換分類的動畫方向：滑動才有，點分類不動畫 */
const slide = ref<'' | 'from-right' | 'from-left'>('')

function onTouchStart(e: TouchEvent) {
  touchStart = null
  const t = e.touches[0]
  if (e.touches.length !== 1 || !t) return
  if ((e.target as Element).closest('.chips, .search')) return
  if (t.clientX < EDGE || t.clientX > window.innerWidth - EDGE) return
  touchStart = { x: t.clientX, y: t.clientY, t: e.timeStamp }
}

function onTouchCancel() {
  touchStart = null
}

function onTouchEnd(e: TouchEvent) {
  const start = touchStart
  touchStart = null
  const t = e.changedTouches[0]
  if (!start || !t) return
  const dx = t.clientX - start.x
  const dy = t.clientY - start.y
  // 要夠長、明顯是橫的、而且是一下甩過去的（慢慢拖比較像在看照片）
  if (Math.abs(dx) < SWIPE_MIN || Math.abs(dx) < Math.abs(dy) * 1.5) return
  if (e.timeStamp - start.t > 800) return
  const i = chips.findIndex((c) => c.id === activeChip.value)
  const next = chips[i + (dx < 0 ? 1 : -1)]
  if (!next) return
  slide.value = dx < 0 ? 'from-right' : 'from-left'
  activeChip.value = next.id
  // 換到新的分類就從頭看，不要停在上一個分類捲到的位置
  window.scrollTo({ top: 0 })
}

// 換了分類，分類列捲到讓它露出來（只捲分類列，不動整頁的上下位置）
const chipsEl = ref<HTMLElement>()
watch(activeChip, async (id) => {
  await nextTick()
  const box = chipsEl.value
  const el = box?.querySelector<HTMLElement>(`[data-chip="${id}"]`)
  if (!box || !el) return
  box.scrollTo({ left: el.offsetLeft - (box.clientWidth - el.clientWidth) / 2, behavior: 'smooth' })
})

async function more() {
  // 正在載入就不重複觸發；載完由那一次負責接著檢查
  if (list.value.loading) return false
  await loadMore(filter.value)
  return !list.value.done && !list.value.error
}

function retry() {
  reload(filter.value)
}

const sentinel = ref<HTMLElement>()
useInfiniteScroll(sentinel, more)

onMounted(() => {
  ensureLoaded(filter.value)
  fetchStats()
    .then((s) => (stats.value = s))
    .catch(() => {
      // 統計數字只是裝飾，拿不到就不顯示
    })
})

function ratioOf(p: { width: number; height: number }) {
  return `${p.width}/${p.height}`
}
</script>

<template>
  <main
    class="feed"
    @touchstart.passive="onTouchStart"
    @touchend.passive="onTouchEnd"
    @touchcancel.passive="onTouchCancel"
  >
    <header class="head">
      <div class="head-row">
        <div>
          <p class="date-en">{{ wedding.dateDisplayEn }}</p>
          <h1 class="names">
            {{ wedding.groomName }} <ScriptHeart class="amp" /> {{ wedding.brideName }}
          </h1>
          <p v-if="stats" class="stats">
            共 {{ stats.photoCount }} 張回憶 · {{ stats.guestCount }} 位賓客
          </p>
        </div>
        <button
          v-if="!searchOpen"
          class="search-toggle"
          type="button"
          aria-label="搜尋上傳者"
          @click="openSearch"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
          >
            <circle cx="11" cy="11" r="6.5" />
            <path d="M16 16l4.5 4.5" />
          </svg>
        </button>
      </div>

      <form v-if="searchOpen" class="search" role="search" @submit.prevent="submitSearch">
        <svg
          class="search-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
        >
          <circle cx="11" cy="11" r="6.5" />
          <path d="M16 16l4.5 4.5" />
        </svg>
        <input
          ref="searchInput"
          v-model="searchText"
          class="search-input"
          type="search"
          enterkeyhint="search"
          maxlength="30"
          placeholder="搜尋上傳者的名字或關係"
          aria-label="搜尋上傳者的名字或關係"
        />
        <button class="search-close" type="button" aria-label="關閉搜尋" @click="closeSearch">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        </button>
      </form>

      <div ref="chipsEl" class="chips">
        <button
          v-for="c in chips"
          :key="c.id"
          :data-chip="c.id"
          type="button"
          class="chip"
          :class="{ active: activeChip === c.id }"
          @click="select(c)"
        >
          {{ c.label }}
        </button>
      </div>
    </header>

    <!-- key：換分類時整塊重畫，滑動的進場動畫才會每次都播 -->
    <div :key="activeChip" class="masonry" :class="slide">
      <div class="column">
        <RouterLink
          v-for="p in columnA"
          :key="p.id"
          class="card"
          :to="{ name: 'photo-detail', params: { photoId: p.id }, query: filterToQuery(filter) }"
        >
          <PhotoTile :photo="p" :index="list.items.indexOf(p)" :ratio="ratioOf(p)" />
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
          :to="{ name: 'photo-detail', params: { photoId: p.id }, query: filterToQuery(filter) }"
        >
          <PhotoTile :photo="p" :index="list.items.indexOf(p)" :ratio="ratioOf(p)" />
          <div class="card-foot">
            <span class="avatar">{{ p.uploader.nickname[0] }}</span>
            {{ p.uploader.nickname }}
          </div>
        </RouterLink>
      </div>
    </div>

    <p v-if="list.loaded && list.items.length === 0" class="status">{{ emptyMessage }}</p>
    <p v-else-if="list.error" class="status">
      {{ list.error }}
      <button class="retry" type="button" @click="retry">重試</button>
    </p>
    <p v-else-if="list.loading" class="status">載入中…</p>

    <!-- 捲到這裡附近就載入下一頁 -->
    <div ref="sentinel" class="sentinel" />
  </main>
</template>

<style scoped>
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
  height: 1px;
}

.feed {
  background: var(--c-bg);
  min-height: var(--screen-h);
  /* 滑動切換的進場動畫會往旁邊超出一點，不能讓整頁變成可以左右捲 */
  overflow-x: clip;
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
  color: var(--c-rose);
}

.stats {
  margin: 4px 0 0;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.search-toggle {
  width: 36px;
  height: 36px;
  margin-top: 4px;
  border: 1px solid var(--c-line);
  border-radius: 18px;
  background: transparent;
  color: var(--c-ink-soft);
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-toggle svg {
  width: 18px;
  height: 18px;
}

.search {
  margin-top: 14px;
  height: 40px;
  padding: 0 4px 0 12px;
  border: 1px solid var(--c-line-strong);
  border-radius: 20px;
  background: var(--c-card);
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-icon {
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  color: var(--c-ink-mute);
}

/* 字體至少 16px：iPhone 對焦輸入框時才不會自動把畫面放大 */
.search-input {
  flex: 1;
  min-width: 0;
  border: 0;
  background: transparent;
  font: inherit;
  font-size: 16px;
  color: var(--c-ink);
  outline: none;
}

/* 自己有關閉鈕，不要瀏覽器內建的清除鈕 */
.search-input::-webkit-search-cancel-button {
  display: none;
}

.search-close {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 16px;
  background: transparent;
  color: var(--c-ink-mute);
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-close svg {
  width: 14px;
  height: 14px;
}



.chips {
  /* 讓分類按鈕的 offsetLeft 以這裡為準，換分類時才算得出要捲多少 */
  position: relative;
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

.masonry.from-right {
  animation: slide-from-right 0.25s ease-out;
}

.masonry.from-left {
  animation: slide-from-left 0.25s ease-out;
}

@keyframes slide-from-right {
  from {
    opacity: 0;
    transform: translateX(40px);
  }
}

@keyframes slide-from-left {
  from {
    opacity: 0;
    transform: translateX(-40px);
  }
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
