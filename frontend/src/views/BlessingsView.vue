<script setup lang="ts">
import { RouterLink } from 'vue-router'
import DecoDivider from '@/components/DecoDivider.vue'
import { blessings, stats } from '@/mock/sample'

/** 把 ISO 時間轉成「剛剛 / 12 分鐘前 / 1 小時前」 */
function relativeTime(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diffMs / 60000)
  if (minutes < 1) return '剛剛'
  if (minutes < 60) return minutes + ' 分鐘前'
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return hours + ' 小時前'
  return Math.floor(hours / 24) + ' 天前'
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
        <p class="summary">{{ stats.guestCount }} 位賓客留下了 {{ stats.blessingCount }} 則祝福</p>
      </div>
    </header>

    <ul class="list">
      <li
        v-for="(b, i) in blessings"
        :key="b.id"
        class="note"
        :class="i % 2 === 0 ? 'tilt-left' : 'tilt-right'"
      >
        <div class="note-head">
          <span class="avatar">{{ b.guest.nickname[0] }}</span>
          <div class="who">
            <p class="name">{{ b.guest.nickname }}</p>
            <p class="time">{{ relativeTime(b.createdAt) }}</p>
          </div>
          <svg class="heart" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z" />
          </svg>
        </div>
        <p class="text">{{ b.text }}</p>
      </li>
    </ul>

    <button class="fab" type="button">
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

/* 便條紙般的輕微傾斜，左右交錯 */
.note {
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--c-bg-soft);
}

.note:nth-child(even) {
  background: var(--c-bg-deep);
}

.tilt-left {
  transform: rotate(-0.4deg);
}

.tilt-right {
  transform: rotate(0.4deg);
}

.note-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 14px;
  background: var(--c-card);
  border: 1px solid var(--c-line);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-serif);
  font-size: 13px;
}

.who {
  flex: 1;
}

.name {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
}

.time {
  margin: 0;
  font-size: 10px;
  letter-spacing: 0.5px;
  color: var(--c-ink-mute);
}

.heart {
  width: 14px;
  height: 14px;
  color: var(--c-rose);
  opacity: 0.6;
}

.text {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 14px;
  line-height: 1.7;
  text-align: justify;
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
