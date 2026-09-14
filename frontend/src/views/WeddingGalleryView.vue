<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import PhotoTile from '@/components/PhotoTile.vue'
import { weddingCollections } from '@/mock/sample'

/** 婚紗集是新人自己的照片，僅供觀賞，不提供下載 */
const activeCollection = ref(weddingCollections[0]?.id ?? '')
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
      <div class="frame wide">
        <PhotoTile :index="3" ratio="3/2" />
        <span class="plate">01 · Hill Path</span>
      </div>

      <div class="pair">
        <div class="frame tall">
          <PhotoTile :index="5" ratio="3/4" label="02 · Wildflowers" />
        </div>
        <div class="stack">
          <div class="frame">
            <PhotoTile :index="6" ratio="1/1" label="03" />
          </div>
          <div class="frame">
            <PhotoTile :index="7" ratio="1/1" label="04" />
          </div>
        </div>
      </div>
    </div>
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
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.frame {
  position: relative;
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
</style>
