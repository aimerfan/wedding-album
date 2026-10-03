<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import DecoDivider from '@/components/DecoDivider.vue'
import { wedding } from '@/config/wedding'
import { blessings as sampleBlessings, stats } from '@/mock/sample'
import { session } from '@/stores/session'
import type { Blessing } from '@/types/album'

const router = useRouter()

// 複製一份，送出的新祝福才能插進列表而不動到 mock 本身
const blessings = ref<Blessing[]>([...sampleBlessings])

const nickname = computed(() => session.nickname || '賓客')

const composing = ref(false)
const draft = ref('')
const draftEl = ref<HTMLTextAreaElement>()
const canSend = computed(() => draft.value.trim().length > 0)

async function openComposer() {
  composing.value = true
  await nextTick()
  draftEl.value?.focus()
}

function closeComposer() {
  composing.value = false
}

function send() {
  if (!canSend.value) return
  // TODO: 接後端 API。現在只插在本頁列表最上面，重新整理就會消失
  blessings.value.unshift({
    id: 'local-' + Date.now(),
    guest: { id: 'me', nickname: nickname.value },
    text: draft.value.trim(),
    createdAt: new Date().toISOString(),
  })
  draft.value = ''
  composing.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

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

    <button class="fab" type="button" @click="openComposer">
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

    <Transition name="sheet">
      <div v-if="composing" class="backdrop" @click.self="closeComposer">
        <form class="sheet" role="dialog" aria-label="寫祝福" @submit.prevent="send">
          <span class="grip" />
          <div class="sheet-head">
            <button class="sheet-cancel" type="button" @click="closeComposer">取消</button>
            <h2>寫 祝 福</h2>
            <span class="sheet-spacer" />
          </div>

          <div class="identity">
            <span class="avatar">{{ nickname[0] }}</span>
            <p class="identity-name">以「{{ nickname }}」留言</p>
            <button class="identity-change" type="button" @click="router.push({ name: 'welcome' })">
              更改
            </button>
          </div>

          <textarea
            ref="draftEl"
            v-model="draft"
            class="draft"
            :maxlength="wedding.maxBlessingLength"
            placeholder="想對新人說些什麼？"
            rows="5"
          />

          <div class="sheet-foot">
            <span class="counter">{{ draft.length }} / {{ wedding.maxBlessingLength }}</span>
            <button class="send" type="submit" :disabled="!canSend">送 出</button>
          </div>
        </form>
      </div>
    </Transition>
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
.backdrop {
  position: fixed;
  inset: 0;
  /* 要蓋過 AppTabBar（30） */
  z-index: 40;
  display: flex;
  align-items: flex-end;
  background: rgba(61, 46, 38, 0.35);
}

.sheet {
  width: 100%;
  padding: 12px 20px calc(var(--safe-bottom) + 20px);
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  background: var(--c-bg);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.grip {
  display: block;
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--c-line);
  margin: 0 auto;
}

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sheet-head h2 {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 16px;
  font-weight: 500;
}

.sheet-cancel {
  border: 0;
  background: transparent;
  padding: 0;
  font-size: 13px;
  color: var(--c-ink-mute);
  min-width: 40px;
  text-align: left;
}

.sheet-spacer {
  min-width: 40px;
}

.identity {
  display: flex;
  align-items: center;
  gap: 10px;
}

.identity-name {
  flex: 1;
  margin: 0;
  font-size: 13px;
  color: var(--c-ink-soft);
}

.identity-change {
  border: 0;
  background: transparent;
  font-size: 11px;
  color: var(--c-rose);
}

.draft {
  padding: 14px 16px;
  border: 1px solid var(--c-line);
  border-radius: 12px;
  background: var(--c-card);
  resize: none;
  font-family: var(--f-serif);
  font-size: 15px;
  line-height: 1.7;
  color: var(--c-ink);
  caret-color: var(--c-rose);
}

.draft:focus {
  outline: none;
  border-color: var(--c-rose-soft);
}

.draft::placeholder {
  color: var(--c-ink-mute);
  opacity: 0.55;
}

.sheet-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.counter {
  font-size: 10px;
  color: var(--c-ink-mute);
}

.send {
  height: 40px;
  padding: 0 28px;
  border: 0;
  border-radius: 20px;
  background: var(--c-rose);
  color: #fff;
  font-size: 13px;
  letter-spacing: 2px;
  box-shadow: var(--shadow-rose);
}

.send:disabled {
  opacity: 0.45;
  box-shadow: none;
  cursor: default;
}

.sheet-enter-active,
.sheet-leave-active {
  transition: background 0.25s;
}

.sheet-enter-active .sheet,
.sheet-leave-active .sheet {
  transition: transform 0.25s ease-out;
}

.sheet-enter-from,
.sheet-leave-to {
  background: transparent;
}

.sheet-enter-from .sheet,
.sheet-leave-to .sheet {
  transform: translateY(100%);
}
</style>
