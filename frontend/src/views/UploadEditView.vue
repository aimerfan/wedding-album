<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { wedding } from '@/config/wedding'
import { resetUploadFlow, session, uploadFlow } from '@/stores/session'

const router = useRouter()

const selected = computed(() =>
  uploadFlow.selectedIds
    .map((id) => uploadFlow.picked.find((p) => p.id === id))
    .filter((p) => Boolean(p)),
)

const count = computed(() => selected.value.length)

const nickname = computed(() => session.nickname || '賓客')
const initial = computed(() => nickname.value[0] ?? '賓')

const blessingLength = computed(() => uploadFlow.draft.blessing.length)

onMounted(() => {
  // 直接開這個網址（重新整理、分享連結）時沒有選到的檔案，退回第一步
  if (uploadFlow.picked.length === 0) router.replace({ name: 'upload' })
})

function addMore() {
  router.back()
}

function upload() {
  // TODO: 接後端上傳 API，帶 uploadFlow.draft 一起送
  resetUploadFlow()
  router.push({ name: 'feed' })
}

function skip() {
  uploadFlow.draft.blessing = ''
  upload()
}
</script>

<template>
  <main class="edit">
    <header class="head">
      <button class="back" type="button" @click="router.back()">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
        >
          <path d="M15 6l-6 6 6 6" />
        </svg>
        返回
      </button>
      <h1>留下祝福</h1>
      <button class="skip" type="button" @click="skip">跳過</button>
    </header>

    <section class="preview">
      <p class="preview-label">{{ count }} 個項目 · 將公開分享</p>
      <div class="preview-row">
        <div v-for="item in selected" :key="item!.id" class="thumb">
          <img :src="item!.previewUrl" alt="" />
          <span v-if="item!.isVideo" class="thumb-video">影片</span>
        </div>
        <button class="thumb add" type="button" aria-label="再選照片" @click="addMore">＋</button>
      </div>
    </section>

    <section class="block">
      <div class="identity">
        <span class="identity-avatar">{{ initial }}</span>
        <div class="identity-text">
          <p class="identity-label">以此暱稱發布</p>
          <p class="identity-name">{{ nickname }}</p>
        </div>
        <button class="identity-change" type="button" @click="router.push({ name: 'welcome' })">
          更改
        </button>
      </div>
    </section>

    <section class="block">
      <div class="card">
        <div class="card-head">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z" />
          </svg>
          <span>寫下你的祝福（選填）</span>
        </div>

        <textarea
          v-model="uploadFlow.draft.blessing"
          class="blessing"
          :maxlength="wedding.maxBlessingLength"
          placeholder="願你們的愛情&#10;如同今日的天氣&#10;晴朗、明亮、永遠溫暖"
          rows="4"
        />

        <div class="card-foot">
          <div class="marks">
            <button type="button" @click="uploadFlow.draft.blessing += '♥'">♥</button>
            <button type="button" @click="uploadFlow.draft.blessing += '♡'">♡</button>
            <button type="button" @click="uploadFlow.draft.blessing += '✿'">✿</button>
          </div>
          <span class="counter">{{ blessingLength }} / {{ wedding.maxBlessingLength }}</span>
        </div>
      </div>

      <div class="settings">
        <label class="setting">
          <span>允許其他賓客看到</span>
          <input v-model="uploadFlow.draft.visibleToGuests" type="checkbox" class="switch" />
        </label>
        <label class="setting last">
          <span>附加位置：{{ wedding.venue }}</span>
          <input v-model="uploadFlow.draft.attachLocation" type="checkbox" class="switch" />
        </label>
      </div>
    </section>

    <div class="submit-bar">
      <button class="submit" type="button" :disabled="count === 0" @click="upload">
        上 傳 {{ count }} 個 項 目
      </button>
    </div>
  </main>
</template>

<style scoped>
.edit {
  min-height: 100dvh;
  background: var(--c-bg);
  color: var(--c-ink);
  padding-bottom: 120px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(var(--page-top) + 24px) 16px 12px;
  border-bottom: 1px solid var(--c-line);
}

.head h1 {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 16px;
  font-weight: 500;
}

.back,
.skip {
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--c-ink-soft);
  min-width: 56px;
}

.back svg {
  width: 16px;
  height: 16px;
}

.skip {
  justify-content: flex-end;
  font-size: 13px;
  color: var(--c-ink-mute);
}

.preview {
  padding: 18px 16px 14px;
}

.preview-label {
  margin: 0 0 8px;
  font-size: 11px;
  letter-spacing: 1.5px;
  color: var(--c-ink-mute);
}

.preview-row {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
}

.preview-row::-webkit-scrollbar {
  display: none;
}

.thumb {
  position: relative;
  flex-shrink: 0;
  width: 64px;
  height: 80px;
  border-radius: 8px;
  border: 1px solid var(--c-line);
  overflow: hidden;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-video {
  position: absolute;
  bottom: 4px;
  right: 4px;
  padding: 1px 4px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.5);
  font-size: 8px;
  color: #fff;
}

.thumb.add {
  border: 1.5px dashed var(--c-ink-mute);
  background: transparent;
  color: var(--c-ink-mute);
  font-size: 22px;
  font-weight: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}

.block {
  padding: 0 16px;
  margin-bottom: 14px;
}

.identity {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
}

.identity-avatar {
  width: 30px;
  height: 30px;
  border-radius: 15px;
  background: var(--c-bg-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-serif);
  font-size: 13px;
}

.identity-text {
  flex: 1;
}

.identity-label {
  margin: 0;
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.identity-name {
  margin: 1px 0 0;
  font-size: 14px;
}

.identity-change {
  border: 0;
  background: transparent;
  font-size: 11px;
  color: var(--c-rose);
}

.card {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--c-rose);
}

.card-head svg {
  width: 14px;
  height: 14px;
}

.blessing {
  border: 0;
  padding: 0;
  resize: none;
  background: transparent;
  font-family: var(--f-serif);
  font-size: 15px;
  line-height: 1.7;
  color: var(--c-ink);
  caret-color: var(--c-rose);
  min-height: 96px;
}

.blessing:focus {
  outline: none;
}

.blessing::placeholder {
  color: var(--c-ink-mute);
  opacity: 0.55;
}

.card-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid var(--c-line);
}

.marks {
  display: flex;
  gap: 12px;
}

.marks button {
  border: 0;
  background: transparent;
  font-size: 14px;
  color: var(--c-ink-mute);
  padding: 0;
}

.counter {
  font-size: 10px;
  color: var(--c-ink-mute);
}

.settings {
  margin-top: 14px;
  border-radius: 12px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
  overflow: hidden;
}

.setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--c-line);
  font-size: 13px;
}

.setting.last {
  border-bottom: 0;
}

/* iOS 風格開關：用原生 checkbox 保留可存取性，外觀自己畫 */
.switch {
  appearance: none;
  width: 36px;
  height: 22px;
  border-radius: 11px;
  background: var(--c-bg-deep);
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;
}

.switch::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 9px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  transition: left 0.2s;
}

.switch:checked {
  background: var(--c-rose);
}

.switch:checked::after {
  left: 16px;
}

.submit-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px 16px calc(var(--safe-bottom) + 28px);
  background: linear-gradient(180deg, transparent, var(--c-bg) 30%);
}

.submit {
  width: 100%;
  height: 50px;
  border: 0;
  border-radius: 25px;
  background: var(--c-rose);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 4px;
  box-shadow: var(--shadow-rose);
}

.submit:disabled {
  opacity: 0.45;
  box-shadow: none;
  cursor: default;
}
</style>
