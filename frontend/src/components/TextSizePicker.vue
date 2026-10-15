<script setup lang="ts">
import { setTextSize, TEXT_SIZES, textSize } from '@/stores/textSize'

/**
 * 選字體大小，三個選項直接列出來。歡迎頁與「我的」頁共用，歡迎頁換成比較口語的說明。
 */
const { label = '字體大小' } = defineProps<{ label?: string }>()
</script>

<template>
  <div class="options" role="radiogroup" aria-label="字體大小">
    <span class="label">
      <span class="aa" aria-hidden="true"><span class="aa-small">A</span>A</span>
      {{ label }}
    </span>
    <span class="choices">
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
    </span>
  </div>
</template>

<style scoped>
/* 字放到大或特大時一行放不下：說明不折行，按鈕整組換到下一行 */
.options {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 6px;
}

/* 分段按鈕：三格包在同一條裡，一看就知道是「三選一」，也跟一般的文字段落分得開 */
.choices {
  display: flex;
  gap: 2px;
  padding: 3px;
  border-radius: 20px;
  background: var(--c-bg-deep);
}

.label {
  flex: 1;
  display: flex;
  align-items: baseline;
  gap: 6px;
  white-space: nowrap;
  font-size: 13px;
  color: var(--c-ink-soft);
}

/* 「Aa」圖示：一大一小兩個 A，一眼就知道跟字的大小有關 */
.aa {
  font-family: -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
  font-size: 16px;
  font-weight: 700;
  line-height: 1;
  color: var(--c-ink);
}

.aa-small {
  font-size: 11px;
}

.option {
  min-width: 52px;
  height: 32px;
  padding: 0 12px;
  border: 0;
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
  background: var(--c-rose);
  color: #fff;
}
</style>
