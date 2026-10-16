<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { createBlessing, updateBlessing } from '@/api/blessings'
import { ApiError } from '@/api/client'
import MarkPicker from '@/components/MarkPicker.vue'
import ProfileSheet from '@/components/ProfileSheet.vue'
import { useAlbumConfig } from '@/composables/useAlbumConfig'
import { addBlessing, replaceBlessing } from '@/stores/blessingLists'
import { session } from '@/stores/session'
import type { Blessing } from '@/types/album'

/**
 * 寫祝福／修改祝福的底部面板。留言牆與「我的 → 我的祝福」共用。
 * 送出成功後自己更新祝福列表（新的放最上面、改過的換掉），再通知外面。
 */
const open = defineModel<boolean>({ required: true })
const props = defineProps<{
  /** 要修改的那則；null 代表寫新的 */
  editing: Blessing | null
}>()
const emit = defineEmits<{ saved: [blessing: Blessing, isNew: boolean] }>()

const config = useAlbumConfig()

const nickname = computed(() => session.nickname || '賓客')
/** 改暱稱：在這個面板上面再疊一層，不跳到歡迎頁（寫到一半的祝福才不會不見） */
const profileOpen = ref(false)

const draft = ref('')
const draftEl = ref<HTMLTextAreaElement>()
const sending = ref(false)
const sendError = ref('')
const canSend = computed(() => draft.value.trim().length > 0 && !sending.value)

// 每次打開都依「寫新的 / 改哪一則」重新帶入內容
watch(open, async (isOpen) => {
  if (!isOpen) return
  draft.value = props.editing?.text ?? ''
  sendError.value = ''
  await nextTick()
  draftEl.value?.focus()
})

function close() {
  open.value = false
}

async function send() {
  if (!canSend.value) return
  sending.value = true
  sendError.value = ''
  try {
    const text = draft.value.trim()
    const target = props.editing
    const saved = target ? await updateBlessing(target.id, text) : await createBlessing(text)
    if (target) replaceBlessing(saved)
    else addBlessing(saved)
    draft.value = ''
    open.value = false
    emit('saved', saved, !target)
  } catch (e) {
    sendError.value = e instanceof ApiError ? e.message : '送出失敗，請稍後再試'
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <Transition name="sheet">
    <div v-if="open" class="overlay" @click.self="close">
      <form
        class="sheet"
        role="dialog"
        :aria-label="editing ? '修改祝福' : '寫祝福'"
        @submit.prevent="send"
      >
        <span class="grip" />
        <div class="sheet-head">
          <button class="sheet-cancel" type="button" @click="close">取消</button>
          <h2>{{ editing ? '修 改 祝 福' : '寫 祝 福' }}</h2>
          <span class="sheet-spacer" />
        </div>

        <div v-if="!editing" class="identity">
          <span class="avatar">{{ nickname[0] }}</span>
          <p class="identity-name">以「{{ nickname }}」留言</p>
          <button class="identity-change" type="button" @click="profileOpen = true">
            更改
          </button>
        </div>

        <textarea
          ref="draftEl"
          v-model="draft"
          class="draft"
          :maxlength="config.maxBlessingLength"
          placeholder="想對新人說些什麼？"
          rows="5"
        />

        <p v-if="sendError" class="send-error" role="alert">{{ sendError }}</p>

        <div class="sheet-foot">
          <MarkPicker v-model="draft" :target="draftEl" :max-length="config.maxBlessingLength" />
          <span class="counter">{{ draft.length }} / {{ config.maxBlessingLength }}</span>
          <button class="send" type="submit" :disabled="!canSend">
            {{ sending ? '送 出 中 …' : editing ? '儲 存' : '送 出' }}
          </button>
        </div>
      </form>
    </div>
  </Transition>
  <ProfileSheet v-model="profileOpen" />
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  /* 要蓋過 AppTabBar（30） */
  z-index: 40;
  display: flex;
  align-items: flex-end;
  background: rgba(61, 46, 38, 0.35);
}

.sheet {
  width: 100%;
  padding: 12px 20px calc(var(--safe-bottom) + 20px);
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  background: var(--c-bg);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.grip {
  display: block;
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--c-line);
  margin: 0 auto;
}

.sheet-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sheet-head h2 {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 16px;
  font-weight: 500;
}

.sheet-cancel {
  border: 0;
  background: transparent;
  padding: 0;
  font-size: 13px;
  color: var(--c-ink-mute);
  min-width: 40px;
  text-align: left;
}

.sheet-spacer {
  min-width: 40px;
}

.identity {
  display: flex;
  align-items: center;
  gap: 10px;
}

.identity-name {
  flex: 1;
  margin: 0;
  font-size: 13px;
  color: var(--c-ink-soft);
}

.identity-change {
  border: 0;
  background: transparent;
  font-size: 11px;
  color: var(--c-rose);
}

.draft {
  padding: 14px 16px;
  border: 1px solid var(--c-line);
  border-radius: 12px;
  background: var(--c-card);
  resize: none;
  font-family: var(--f-serif);
  font-size: 15px;
  line-height: 1.7;
  color: var(--c-ink);
  caret-color: var(--c-rose);
}

.draft:focus {
  outline: none;
  border-color: var(--c-rose-soft);
}

.draft::placeholder {
  color: var(--c-ink-mute);
  opacity: 0.55;
}

.sheet-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.counter {
  margin-left: auto;
  margin-right: 16px;
  font-size: 10px;
  color: var(--c-ink-mute);
}

.send {
  height: 40px;
  padding: 0 28px;
  border: 0;
  border-radius: 20px;
  background: var(--c-rose);
  color: #fff;
  font-size: 13px;
  letter-spacing: 2px;
  box-shadow: var(--shadow-rose);
}

.send:disabled {
  opacity: 0.45;
  box-shadow: none;
  cursor: default;
}

.sheet-enter-active,
.sheet-leave-active {
  transition: background 0.25s;
}

.sheet-enter-active .sheet,
.sheet-leave-active .sheet {
  transition: transform 0.25s ease-out;
}

.sheet-enter-from,
.sheet-leave-to {
  background: transparent;
}

.sheet-enter-from .sheet,
.sheet-leave-to .sheet {
  transform: translateY(100%);
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

.send-error {
  margin: 0;
  font-size: 12px;
  color: var(--c-rose);
}
</style>
