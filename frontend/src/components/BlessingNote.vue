<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { session } from '@/stores/session'
import type { Blessing } from '@/types/album'
import { relativeTime } from '@/utils/time'

/**
 * 一則祝福，像一張便條紙。留言牆與「我的 → 我的祝福」共用。
 * 自己寫的祝福右上角有「⋯」，可以修改或刪除；管理員看別人的祝福只能刪除（不能替人改內容）。
 */
const props = defineProps<{
  blessing: Blessing
  /** 便條紙的傾斜方向，左右交錯 */
  tilt?: 'left' | 'right'
}>()

const emit = defineEmits<{ edit: [Blessing]; delete: [Blessing] }>()

const mine = computed(() => !!session.guestId && props.blessing.guest.id === session.guestId)
/** 真正的權限由後端把關，這裡只決定要不要顯示選單 */
const canDelete = computed(() => mine.value || session.isAdmin)

const menuOpen = ref(false)
const root = ref<HTMLElement>()

// 點選單以外的地方就關掉
function onDocumentClick(e: MouseEvent) {
  if (!root.value?.contains(e.target as Node)) menuOpen.value = false
}
watch(menuOpen, (open) => {
  if (open) document.addEventListener('click', onDocumentClick)
  else document.removeEventListener('click', onDocumentClick)
})
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))

function choose(action: 'edit' | 'delete') {
  menuOpen.value = false
  if (action === 'edit') emit('edit', props.blessing)
  else emit('delete', props.blessing)
}
</script>

<template>
  <li
    ref="root"
    class="note"
    :class="[tilt === 'right' ? 'tilt-right' : 'tilt-left', { raised: menuOpen }]"
  >
    <div class="note-head">
      <span class="avatar">{{ blessing.guest.nickname[0] }}</span>
      <div class="who">
        <p class="name">{{ blessing.guest.nickname }}</p>
        <p class="time">
          {{ relativeTime(blessing.createdAt) }}<span v-if="blessing.editedAt"> · 已編輯</span>
        </p>
      </div>

      <div v-if="canDelete" class="menu">
        <button
          class="menu-btn"
          type="button"
          aria-label="祝福選項"
          :aria-expanded="menuOpen"
          @click="menuOpen = !menuOpen"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <circle cx="5" cy="12" r="1.8" />
            <circle cx="12" cy="12" r="1.8" />
            <circle cx="19" cy="12" r="1.8" />
          </svg>
        </button>
        <div v-if="menuOpen" class="menu-pop" role="menu">
          <button v-if="mine" type="button" role="menuitem" @click="choose('edit')">修改</button>
          <button type="button" role="menuitem" class="danger" @click="choose('delete')">
            刪除
          </button>
        </div>
      </div>
      <svg v-else class="heart" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z" />
      </svg>
    </div>
    <p class="text">{{ blessing.text }}</p>
  </li>
</template>

<style scoped>
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

/*
 * 卡片有 transform（傾斜），會自成一個圖層，選單的 z-index 只在卡片裡面有效，
 * 蓋不過排在後面的卡片。所以選單打開時，把整張卡片提到上層。
 */
.raised {
  position: relative;
  z-index: 5;
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

.menu {
  position: relative;
}

.menu-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  border: 0;
  border-radius: 14px;
  background: transparent;
  color: var(--c-ink-mute);
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-btn svg {
  width: 16px;
  height: 16px;
}

.menu-pop {
  position: absolute;
  top: 30px;
  right: 0;
  z-index: 10;
  min-width: 96px;
  padding: 4px 0;
  border-radius: 10px;
  background: var(--c-card);
  box-shadow: var(--shadow-raised);
  display: flex;
  flex-direction: column;
}

.menu-pop button {
  padding: 10px 16px;
  border: 0;
  background: transparent;
  text-align: left;
  font-size: 13px;
  color: var(--c-ink);
}

.menu-pop .danger {
  color: var(--c-rose);
}

.text {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 14px;
  line-height: 1.7;
  text-align: justify;
  white-space: pre-line;
}
</style>
