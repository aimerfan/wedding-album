<script setup lang="ts">
import { computed } from 'vue'
import type { Photo } from '@/types/album'

/**
 * 相片格。還沒有真實圖檔時，退回設計稿的柔和漸層佔位圖。
 * 等後端接上、photo.thumbnailUrl 有值就會自動換成真圖。
 */
const props = withDefaults(
  defineProps<{
    photo?: Photo
    /** 沒有 photo 時用來挑漸層色 */
    index?: number
    /** CSS aspect-ratio，例如 '4/5'；'auto' 表示由外層控制高度 */
    ratio?: string
    label?: string
  }>(),
  { ratio: '4/5', index: 0 },
)

// 設計稿的 10 組佔位漸層
const GRADIENTS: [string, string][] = [
  ['#E8D4C8', '#C9A48E'],
  ['#D4B8A8', '#A88876'],
  ['#EAD9C5', '#C2A179'],
  ['#D9C2B0', '#A88562'],
  ['#E5D0BE', '#B8967A'],
  ['#DBC5B2', '#9C7E68'],
  ['#EFDFC9', '#C49E7C'],
  ['#E0CAB8', '#A8836A'],
  ['#E8D8C5', '#BC9778'],
  ['#D6BCA9', '#9D7B62'],
]

const src = computed(() => props.photo?.thumbnailUrl || '')

const gradient = computed(() => {
  const [a, b] = GRADIENTS[(props.index ?? 0) % GRADIENTS.length]
  return `linear-gradient(135deg, ${a} 0%, ${b} 100%)`
})

const aspectRatio = computed(() => (props.ratio === 'auto' ? undefined : props.ratio))
</script>

<template>
  <div class="tile" :style="{ aspectRatio, background: src ? undefined : gradient }">
    <img v-if="src" :src="src" :alt="photo?.blessing ?? ''" loading="lazy" decoding="async" />
    <div v-else class="texture" />
    <span v-if="label" class="label">{{ label }}</span>
    <slot />
  </div>
</template>

<style scoped>
.tile {
  position: relative;
  width: 100%;
  overflow: hidden;
}

.tile img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 佔位圖上的細斜紋，讓色塊不會太死 */
.texture {
  position: absolute;
  inset: 0;
  opacity: 0.25;
  background-image: repeating-linear-gradient(
    45deg,
    transparent 0 14px,
    rgba(255, 255, 255, 0.08) 14px 15px
  );
}

.label {
  position: absolute;
  bottom: 8px;
  left: 10px;
  font-family: ui-monospace, 'SF Mono', monospace;
  font-size: 9px;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.7);
}
</style>
