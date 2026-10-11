<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ApiError } from '@/api/client'
import { updateMe } from '@/api/guests'
import { session, setProfile } from '@/stores/session'

/** 「我的」頁改暱稱與「與新人的關係」 */
const open = defineModel<boolean>({ required: true })

const nickname = ref('')
const relation = ref('')
const saving = ref(false)
const error = ref('')

const canSave = computed(() => nickname.value.trim().length > 0 && !saving.value)

// 每次打開都從目前的資料重新帶入，上次取消時改到一半的內容不留著
watch(open, (isOpen) => {
  if (!isOpen) return
  nickname.value = session.nickname
  relation.value = session.relation
  error.value = ''
})

async function save() {
  if (!canSave.value) return
  saving.value = true
  error.value = ''
  try {
    const { guest } = await updateMe(nickname.value.trim(), relation.value.trim())
    setProfile(guest.nickname, guest.relation ?? '')
    open.value = false
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : '儲存失敗，請稍後再試'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Transition name="sheet">
    <div v-if="open" class="overlay" @click.self="open = false">
      <form class="sheet" role="dialog" aria-label="編輯個人資料" @submit.prevent="save">
        <span class="grip" />
        <div class="sheet-head">
          <button class="cancel" type="button" @click="open = false">取消</button>
          <h2>編輯個人資料</h2>
          <span class="spacer" />
        </div>

        <label class="field">
          <span class="field-label">你的名字</span>
          <input
            v-model="nickname"
            type="text"
            class="field-input"
            autocomplete="nickname"
            enterkeyhint="done"
            maxlength="20"
          />
        </label>

        <label class="field">
          <span class="field-label">與新人的關係（選填）</span>
          <input
            v-model="relation"
            type="text"
            class="field-input"
            placeholder="例如：新娘的大學同學"
            enterkeyhint="done"
            maxlength="30"
          />
        </label>

        <p class="note">改名後，你之前上傳的照片和祝福也會顯示新的名字。</p>

        <p v-if="error" class="error" role="alert">{{ error }}</p>

        <button class="save" type="submit" :disabled="!canSave">
          {{ saving ? '儲 存 中 …' : '儲 存' }}
        </button>
      </form>
    </div>
  </Transition>
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
  color: var(--c-ink);
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  margin-bottom: 4px;
}

.sheet-head h2 {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 16px;
  font-weight: 500;
}

.cancel {
  min-width: 40px;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
  font-size: 13px;
  color: var(--c-ink-mute);
}

.spacer {
  min-width: 40px;
}

.field {
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field:focus-within {
  border-color: var(--c-rose-soft);
}

.field-label {
  font-size: 11px;
  letter-spacing: 1.5px;
  color: var(--c-ink-mute);
}

/* 16px 以上 iOS 點進輸入框時才不會自動放大畫面 */
.field-input {
  border: 0;
  padding: 0;
  background: transparent;
  font-family: var(--f-serif);
  font-size: 16px;
  color: var(--c-ink);
  caret-color: var(--c-rose);
}

.field-input:focus {
  outline: none;
}

.field-input::placeholder {
  color: var(--c-ink-mute);
  opacity: 0.55;
}

.note {
  margin: 0;
  font-size: 11px;
  color: var(--c-ink-mute);
}

.error {
  margin: 0;
  font-size: 12px;
  color: var(--c-rose);
}

.save {
  margin-top: 4px;
  height: 46px;
  border: 0;
  border-radius: 23px;
  background: var(--c-rose);
  color: #fff;
  font-size: 14px;
  letter-spacing: 2px;
  box-shadow: var(--shadow-rose);
}

.save:disabled {
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
</style>
