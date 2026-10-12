<script setup lang="ts">
import { ref } from 'vue'
import { setTextSize, TEXT_SIZES, textSize } from '@/stores/textSize'

/**
 * 選字體大小。歡迎頁用 compact（右上角一個「Aa」，點開才有選項），「我的」頁直接列出來。
 */
defineProps<{ compact?: boolean }>()

const open = ref(false)
</script>

<template>
  <div class="picker" :class="{ compact }">
    <button
      v-if="compact"
      class="aa"
      type="button"
      aria-label="字體大小"
      :aria-expanded="open"
      @click="open = !open"
    >
      <span class="aa-mark"><span class="aa-small">A</span><span class="aa-big">A</span></span>
    </button>

    <div v-if="!compact || open" class="options" role="radiogroup" aria-label="字體大小">
      <span v-if="!compact" class="label">字體大小</span>
      <button
        v-for="s in TEXT_SIZES"
        :key="s.id"
        type="button"
        role="radio"
        class="option"
        :class="[s.id, { active: textSize === s.id }]"
        :aria-checked="textSize === s.id"
        @click="setTextSize(s.id)"
      >
        {{ s.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.picker {
  position: relative;
}

.aa {
  width: 40px;
  height: 40px;
  padding: 0;
  border: 0;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.55);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: var(--c-ink);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 兩個 A 對齊底線，整組置中在圓裡；用系統的無襯線粗體，小尺寸才清楚 */
.aa-mark {
  display: flex;
  align-items: baseline;
  gap: 1px;
  line-height: 1;
  font-family: -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  font-weight: 700;
}

.aa-small {
  font-size: 12px;
}

.aa-big {
  font-size: 17px;
}

.options {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 歡迎頁：從「Aa」底下彈出來 */
.compact .options {
  position: absolute;
  top: 46px;
  right: 0;
  z-index: 10;
  padding: 6px;
  border-radius: 20px;
  background: var(--c-card);
  box-shadow: var(--shadow-raised);
}

.label {
  flex: 1;
  font-size: 13px;
  color: var(--c-ink-soft);
}

.option {
  min-width: 52px;
  height: 34px;
  padding: 0 12px;
  border: 1px solid var(--c-line-strong);
  border-radius: 17px;
  background: transparent;
  color: var(--c-ink-soft);
  white-space: nowrap;
}

/* 選項本身的字就照它代表的大小，一看就懂 */
.option.normal {
  font-size: 13px;
}

.option.large {
  font-size: 15px;
}

.option.xlarge {
  font-size: 17px;
}

.option.active {
  border-color: transparent;
  background: var(--c-rose);
  color: #fff;
}
</style>
