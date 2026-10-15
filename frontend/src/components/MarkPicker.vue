<script setup lang="ts">
import { nextTick } from 'vue'

/**
 * 輸入框旁的一排符號（♥ ♡ ✿）。照片上的文字、留言牆的祝福共用。
 * 插在游標的位置（有選取文字就取代），而不是一律加在最後；插完游標停在符號後面。
 */
const text = defineModel<string | undefined>({ required: true })
const props = defineProps<{
  /** 要插入的輸入框，用來讀游標位置、插完把焦點還回去 */
  target: HTMLTextAreaElement | null | undefined
  maxLength: number
}>()

const MARKS = ['♥', '♡', '✿']

async function insert(mark: string) {
  const el = props.target
  const current = text.value ?? ''
  // 還沒點過輸入框時沒有游標，就加在最後
  const start = el?.selectionStart ?? current.length
  const end = el?.selectionEnd ?? current.length
  const next = current.slice(0, start) + mark + current.slice(end)
  if (next.length > props.maxLength) return

  text.value = next
  await nextTick()
  if (el) {
    el.focus()
    el.setSelectionRange(start + mark.length, start + mark.length)
  }
}
</script>

<template>
  <!-- mousedown.prevent：按符號時輸入框不會失焦，游標位置與手機鍵盤都留著 -->
  <div class="marks" role="group" aria-label="插入符號">
    <button
      v-for="m in MARKS"
      :key="m"
      type="button"
      :aria-label="'插入 ' + m"
      @mousedown.prevent
      @click="insert(m)"
    >
      {{ m }}
    </button>
  </div>
</template>

<style scoped>
.marks {
  display: flex;
  gap: 4px;
}

/* 符號本身很小，按鈕做大一點，手指才按得到 */
.marks button {
  min-width: 32px;
  height: 28px;
  border: 0;
  background: transparent;
  font-size: 14px;
  color: var(--c-ink-mute);
  padding: 0;
}
</style>
