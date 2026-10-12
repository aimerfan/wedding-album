<script setup lang="ts">
import type { InstallGuideKind } from '@/composables/usePlatform'

/**
 * 「加到主畫面」的說明卡片。歡迎頁（加入前）與「我的」頁共用。
 *
 * iPhone 上，從主畫面打開的網頁 app 跟 Safari 的資料是分開的：先在 Safari 加入、再加到主畫面，
 * 從主畫面打開會變成另一位賓客。所以歡迎頁在加入「之前」就引導，從主畫面打開後再加入。
 */
defineProps<{ kind: Exclude<InstallGuideKind, null> }>()
defineEmits<{ close: [] }>()
</script>

<template>
  <section class="guide" aria-label="加到主畫面">
    <button class="close" type="button" aria-label="關閉" @click="$emit('close')">×</button>

    <template v-if="kind === 'in-app'">
      <p class="title">請改用瀏覽器開啟</p>
      <p class="text">
        你現在是在 LINE 或 Instagram 裡面開啟的，這裡沒辦法加到主畫面，
        之後也不容易再找到這個相簿。
      </p>
      <ol class="steps">
        <li>點右上角（或右下角）的 <b>⋯</b> 或 <b>分享</b></li>
        <li>選 <b>用 Safari 開啟</b>（Android 是 <b>用瀏覽器開啟</b>）</li>
        <li>在瀏覽器裡再照著提示加到主畫面</li>
      </ol>
    </template>

    <template v-else-if="kind === 'ios-safari'">
      <p class="title">建議先加到主畫面再進入</p>
      <p class="text">之後從主畫面一點就能打開，像 app 一樣全螢幕，不用再掃 QR code。</p>
      <ol class="steps">
        <li>
          點畫面下方的分享按鈕
          <svg class="share" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-label="分享圖示">
            <path d="M12 3v12M8 7l4-4 4 4" />
            <path d="M6 11H5a1 1 0 00-1 1v8a1 1 0 001 1h14a1 1 0 001-1v-8a1 1 0 00-1-1h-1" />
          </svg>
        </li>
        <li>往下滑，選 <b>加入主畫面</b></li>
        <li>點右上角的 <b>新增</b>，再從主畫面打開「婚禮相簿」</li>
      </ol>
      <p class="hint">
        已經在這裡加入過也沒關係：在「我的」頁複製接續碼，到主畫面打開的相簿裡輸入，就能延續身分。
      </p>
    </template>

    <template v-else>
      <p class="title">加到主畫面</p>
      <p class="text">之後從主畫面一點就能打開，像 app 一樣全螢幕。</p>
      <ol class="steps">
        <li>點瀏覽器右上角的 <b>⋮</b></li>
        <li>選 <b>加到主畫面</b> 或 <b>安裝應用程式</b></li>
      </ol>
    </template>
  </section>
</template>

<style scoped>
.guide {
  position: relative;
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
  color: var(--c-ink);
  text-align: left;
}

.close {
  position: absolute;
  top: 6px;
  right: 8px;
  width: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 20px;
  line-height: 1;
  color: var(--c-ink-mute);
}

.title {
  margin: 0 28px 6px 0;
  font-family: var(--f-serif);
  font-size: 15px;
  font-weight: 500;
}

.text {
  margin: 0;
  font-size: 12px;
  line-height: 1.7;
  color: var(--c-ink-soft);
}

.steps {
  margin: 10px 0 0;
  padding-left: 20px;
  font-size: 13px;
  line-height: 2;
}

.steps b {
  color: var(--c-rose);
  font-weight: 500;
}

.share {
  width: 18px;
  height: 18px;
  vertical-align: -3px;
  color: #007aff; /* iOS 系統藍，跟 Safari 上的按鈕同色，比較好認 */
}

.hint {
  margin: 10px 0 0;
  padding-top: 10px;
  border-top: 1px solid var(--c-line);
  font-size: 11px;
  line-height: 1.7;
  color: var(--c-ink-mute);
}
</style>
