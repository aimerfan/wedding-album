<script setup lang="ts">
withDefaults(defineProps<{ color?: string; width?: number }>(), {
  color: 'var(--c-gold)',
  width: 80,
})
</script>

<template>
  <div class="deco">
    <span class="rule" :style="{ width: `${width}px`, background: color }" />
    <svg width="6" height="6" viewBox="0 0 6 6" aria-hidden="true">
      <path d="M3 0L6 3L3 6L0 3Z" :fill="color" />
    </svg>
    <span class="rule" :style="{ width: `${width}px`, background: color }" />
  </div>
</template>

<style scoped>
.deco {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.rule {
  height: 1px;
  opacity: 0.5;
}
</style>
