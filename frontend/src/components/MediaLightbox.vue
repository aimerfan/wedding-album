<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'
import type { PickedMedia } from '@/stores/session'

/**
 * 上傳前把選到的照片、影片放大來看：縮圖太小，寫文字時常常認不出是哪一張。
 * 點背景或右上角關閉；影片可以直接播。
 */
const item = defineModel<PickedMedia | null>({ required: true })

function close() {
  item.value = null
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}

// 開著的時候背後的頁面不要跟著捲
watch(
  item,
  (open) => {
    document.body.style.overflow = open ? 'hidden' : ''
    if (open) document.addEventListener('keydown', onKey)
    else document.removeEventListener('keydown', onKey)
  },
  { immediate: true },
)
onBeforeUnmount(() => {
  document.body.style.overflow = ''
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="item" class="lightbox" role="dialog" aria-label="放大預覽" @click.self="close">
      <button class="close" type="button" aria-label="關閉" @click="close">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
      <video
        v-if="item.kind === 'video'"
        class="media"
        :src="item.previewUrl"
        controls
        playsinline
        preload="metadata"
      />
      <img v-else class="media" :src="item.previewUrl" alt="" @click="close" />
    </div>
  </Teleport>
</template>

<style scoped>
.lightbox {
  position: fixed;
  inset: 0;
  /* 要蓋過上傳頁底部的按鈕列 */
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: calc(var(--page-top) + 64px) 12px calc(var(--safe-bottom) + 24px);
  background: var(--c-dark-bg);
}

.media {
  display: block;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.close {
  position: absolute;
  top: calc(var(--page-top) + 24px);
  right: 16px;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
}

.close svg {
  width: 14px;
  height: 14px;
}
</style>
