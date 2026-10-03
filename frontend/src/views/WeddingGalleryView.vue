<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import PhotoSwiper from '@/components/PhotoSwiper.vue'
import PhotoTile from '@/components/PhotoTile.vue'
import { weddingCollections } from '@/mock/sample'

/** 婚紗集是新人自己的照片，僅供觀賞，不提供下載 */
const activeCollection = ref(weddingCollections[0]?.id ?? '')

const route = useRoute()
const router = useRouter()

// 雜誌排版裡的四張，依閱讀順序。真的照片接上後改成 collection.photos
const spread = [
  { key: '01', index: 3, ratio: 3 / 2 },
  { key: '02', index: 5, ratio: 3 / 4 },
  { key: '03', index: 6, ratio: 1 },
  { key: '04', index: 7, ratio: 1 },
]

/**
 * 放大檢視記在網址上（?photo=2），手機的返回鍵／返回手勢才會先關掉檢視，
 * 而不是直接離開婚紗集。
 */
const viewing = computed(() => {
  const n = Number(route.query.photo)
  return Number.isInteger(n) && n >= 1 && n <= spread.length ? n - 1 : null
})

const current = computed({
  get: () => viewing.value ?? 0,
  set: (i) => router.replace({ query: { photo: String(i + 1) } }),
})

let openedHere = false

function open(i: number) {
  openedHere = true
  router.push({ query: { photo: String(i + 1) } })
}

function close() {
  // 直接開帶 ?photo 的網址時沒有上一頁可退，改成拿掉參數
  if (openedHere) router.back()
  else router.replace({ query: {} })
  openedHere = false
}
</script>

<template>
  <main class="gallery">
    <section class="hero">
      <PhotoTile :index="2" ratio="auto" class="hero-photo" />
      <div class="hero-scrim" />

      <div class="hero-bar">
        <RouterLink :to="{ name: 'feed' }" class="back">← 相簿</RouterLink>
        <span class="notice">僅供觀賞 · 無法下載</span>
      </div>

      <div class="hero-text">
        <p class="kicker">OUR PRE-WEDDING</p>
        <h1>婚 紗 集</h1>
        <p class="caption">{{ weddingCollections[0]?.caption }}</p>
      </div>
    </section>

    <div class="chips">
      <button
        v-for="c in weddingCollections"
        :key="c.id"
        type="button"
        class="chip"
        :class="{ active: activeCollection === c.id }"
        @click="activeCollection = c.id"
      >
        {{ c.title }}
      </button>
    </div>

    <!-- 雜誌式排版：一張大圖 + 一直一橫的組合 -->
    <div class="spread">
      <button class="frame wide" type="button" aria-label="放大第 1 張" @click="open(0)">
        <PhotoTile :index="3" ratio="3/2" />
        <span class="plate">01 · Hill Path</span>
      </button>

      <div class="pair">
        <button class="frame tall" type="button" aria-label="放大第 2 張" @click="open(1)">
          <PhotoTile :index="5" ratio="auto" label="02 · Wildflowers" class="fill" />
        </button>
        <div class="stack">
          <button class="frame" type="button" aria-label="放大第 3 張" @click="open(2)">
            <PhotoTile :index="6" ratio="1/1" label="03" />
          </button>
          <button class="frame" type="button" aria-label="放大第 4 張" @click="open(3)">
            <PhotoTile :index="7" ratio="1/1" label="04" />
          </button>
        </div>
      </div>
    </div>

    <Transition name="fade">
      <!-- 長按選單會出現「儲存影像」，婚紗集不開放下載，一併擋掉 -->
      <div
        v-if="viewing !== null"
        class="viewer"
        role="dialog"
        aria-label="婚紗照"
        @contextmenu.prevent
      >
        <header class="viewer-bar">
          <button class="round" type="button" aria-label="關閉" @click="close">
            <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
          <span class="viewer-counter">{{ current + 1 }} / {{ spread.length }}</span>
          <span class="round-spacer" />
        </header>

        <div class="viewer-stage">
          <PhotoSwiper v-model="current" :slides="spread" />
        </div>
      </div>
    </Transition>
  </main>
</template>

<style scoped>
.gallery {
  min-height: 100dvh;
  background: var(--c-dark-bg);
  color: var(--c-dark-ink);
}

.hero {
  position: relative;
  height: 380px;
  overflow: hidden;
}

.hero-photo {
  height: 100%;
}

.hero-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(0, 0, 0, 0.4) 0%,
    transparent 30%,
    transparent 60%,
    rgba(61, 46, 38, 0.95) 100%
  );
}

.hero-bar {
  position: absolute;
  top: calc(var(--page-top) + 24px);
  left: 20px;
  right: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back {
  font-size: 14px;
  opacity: 0.9;
}

.notice {
  padding: 4px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  font-size: 9px;
  letter-spacing: 1.5px;
}

.hero-text {
  position: absolute;
  left: 20px;
  right: 20px;
  bottom: 32px;
}

.kicker {
  margin: 0;
  font-family: var(--f-display);
  font-style: italic;
  font-size: 12px;
  letter-spacing: 4px;
  color: var(--c-gold);
  /* 金色壓在漸層中段對比偏弱，補一層陰影墊底 */
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.55);
}

.hero-text h1 {
  margin: 6px 0 0;
  font-family: var(--f-serif);
  font-size: 30px;
  font-weight: 500;
  letter-spacing: 2px;
}

.caption {
  margin: 6px 0 0;
  font-size: 11px;
  letter-spacing: 1px;
  opacity: 0.7;
}

.chips {
  display: flex;
  gap: 8px;
  padding: 20px 16px 12px;
  overflow-x: auto;
  scrollbar-width: none;
}

.chips::-webkit-scrollbar {
  display: none;
}

.chip {
  flex-shrink: 0;
  padding: 7px 14px;
  border-radius: 14px;
  border: 1px solid var(--c-dark-line);
  background: transparent;
  color: var(--c-dark-ink-mute);
  font-size: 11px;
  letter-spacing: 1px;
  white-space: nowrap;
}

.chip.active {
  background: #fff;
  border-color: transparent;
  color: var(--c-ink);
}

.spread {
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.frame {
  position: relative;
  display: block;
  width: 100%;
  padding: 0;
  border: 0;
  background: none;
  border-radius: 8px;
  overflow: hidden;
}

.pair {
  display: flex;
  gap: 8px;
}

.tall {
  flex: 1;
  min-width: 0;
}

/*
 * 直幅那張要跟右邊兩張方圖等高。3/4 的比例比兩張方圖疊起來矮，
 * 照比例放會在下方留白、圓角落在空白處，所以改成撐滿整格（圖片 cover 裁切）。
 */
.fill {
  height: 100%;
}

.stack {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.plate {
  position: absolute;
  right: 12px;
  bottom: 10px;
  font-family: var(--f-display);
  font-style: italic;
  font-size: 14px;
  color: #fff;
  text-shadow: 0 1px 4px rgba(0, 0, 0, 0.6);
}
.viewer {
  position: fixed;
  inset: 0;
  /* 要蓋過 AppTabBar（30） */
  z-index: 40;
  display: flex;
  flex-direction: column;
  background: var(--c-dark-bg);
  -webkit-touch-callout: none;
  user-select: none;
}

.viewer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(var(--page-top) + 24px) 16px 0;
}

.round,
.round-spacer {
  width: 32px;
  height: 32px;
}

.round {
  border: 0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.round svg {
  width: 14px;
  height: 14px;
}

.viewer-counter {
  font-size: 11px;
  letter-spacing: 1px;
}

.viewer-stage {
  flex: 1;
  min-height: 0;
  padding: 16px 0 calc(var(--safe-bottom) + 32px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
