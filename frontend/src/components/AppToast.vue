<script setup lang="ts">
/**
 * 短暫提示，浮在底部按鈕列的上方，可以帶一個動作（例如「復原」）。
 * 幾秒後消失由外面決定（外面還要在消失時回收資料），這裡只負責畫。選取頁與上傳頁共用。
 */
export interface Toast {
  text: string
  action?: { label: string; run: () => void }
}

defineProps<{ toast: Toast | null }>()
</script>

<template>
  <Transition name="toast">
    <div v-if="toast" class="toast" role="status">
      <span>{{ toast.text }}</span>
      <button v-if="toast.action" type="button" @click="toast.action.run">
        {{ toast.action.label }}
      </button>
    </div>
  </Transition>
</template>

<style scoped>
/* 浮在底部「下一步」「上傳」那條的上方 */
.toast {
  position: fixed;
  left: 16px;
  right: 16px;
  bottom: calc(var(--safe-bottom) + 92px);
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 14px;
  background: var(--c-ink);
  box-shadow: 0 12px 32px rgba(61, 46, 38, 0.25);
  font-size: 13px;
  line-height: 1.6;
  color: var(--c-bg);
}

.toast span {
  flex: 1;
}

.toast button {
  flex-shrink: 0;
  padding: 4px 4px;
  border: 0;
  background: transparent;
  font-size: 13px;
  font-weight: 500;
  color: var(--c-rose-soft);
}

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity 0.2s,
    transform 0.2s;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
