<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ApiError } from '@/api/client'
import { createComment, deleteComment, fetchComments, updateComment } from '@/api/comments'
import MarkPicker from '@/components/MarkPicker.vue'
import { useAlbumConfig } from '@/composables/useAlbumConfig'
import { session } from '@/stores/session'
import type { Comment } from '@/types/album'
import { relativeTime } from '@/utils/time'

/**
 * 照片詳情下方的留言區：列表（舊的在前）、留言框、改刪自己的留言。
 * 管理員看別人的留言只能刪除（不能替人改內容）。真正的權限由後端把關，這裡只決定要不要顯示按鈕。
 */
const props = defineProps<{ photoId: string }>()
/** 留言數變了，讓照片詳情把照片上的 commentCount 換掉 */
const emit = defineEmits<{ count: [count: number] }>()

const config = useAlbumConfig()

const items = ref<Comment[]>([])
const loading = ref(true)
const loadError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    items.value = (await fetchComments(props.photoId)).items
  } catch (e) {
    loadError.value = e instanceof ApiError ? e.message : '留言載入失敗'
  } finally {
    loading.value = false
  }
}
onMounted(load)

// 載入完就以實際筆數為準（別人剛留的言也算進來），之後新增、刪除也跟著更新
watch([() => items.value.length, loading], ([n, isLoading]) => {
  if (!isLoading && !loadError.value) emit('count', n)
})

const isMine = (c: Comment) => !!session.guestId && c.guest.id === session.guestId

// --- 留言 -----------------------------------------------------------------

const draft = ref('')
const draftEl = ref<HTMLTextAreaElement>()
const sending = ref(false)
const sendError = ref('')
const canSend = computed(() => draft.value.trim().length > 0 && !sending.value)

async function send() {
  if (!canSend.value) return
  sending.value = true
  sendError.value = ''
  try {
    items.value = [...items.value, await createComment(props.photoId, draft.value.trim())]
    draft.value = ''
  } catch (e) {
    sendError.value = e instanceof ApiError ? e.message : '送出失敗，請稍後再試'
  } finally {
    sending.value = false
  }
}

// --- 修改、刪除 -----------------------------------------------------------

const editingId = ref('')
const editDraft = ref('')
/** 寫在 v-for 裡的 ref 會是陣列；一次只會編輯一則，所以最多一個 */
const editEl = ref<HTMLTextAreaElement[]>([])
/** 正在改或刪的那一則，按鈕先停用，避免連按 */
const busyId = ref('')
const itemError = ref<{ id: string; message: string } | null>(null)

function startEdit(c: Comment) {
  editingId.value = c.id
  editDraft.value = c.text
  itemError.value = null
}

function replace(updated: Comment) {
  items.value = items.value.map((c) => (c.id === updated.id ? updated : c))
}

async function saveEdit(c: Comment) {
  const text = editDraft.value.trim()
  if (!text || busyId.value) return
  if (text === c.text) {
    editingId.value = ''
    return
  }
  busyId.value = c.id
  itemError.value = null
  try {
    replace(await updateComment(c.id, text))
    editingId.value = ''
  } catch (e) {
    itemError.value = { id: c.id, message: e instanceof ApiError ? e.message : '儲存失敗' }
  } finally {
    busyId.value = ''
  }
}

async function remove(c: Comment) {
  if (busyId.value) return
  const question = isMine(c)
    ? '確定要刪除這則留言嗎？'
    : `以管理員身分刪除「${c.guest.nickname}」的留言？`
  if (!window.confirm(question)) return
  busyId.value = c.id
  itemError.value = null
  try {
    await deleteComment(c.id)
    items.value = items.value.filter((x) => x.id !== c.id)
  } catch (e) {
    itemError.value = { id: c.id, message: e instanceof ApiError ? e.message : '刪除失敗' }
  } finally {
    busyId.value = ''
  }
}
</script>

<template>
  <section class="comments" aria-label="留言">
    <h3 class="title">
      留言<span v-if="items.length" class="title-count"> · {{ items.length }}</span>
    </h3>

    <p v-if="loading" class="hint">載入中…</p>
    <p v-else-if="loadError" class="hint error" role="alert">
      {{ loadError }}
      <button class="link" type="button" @click="load">重試</button>
    </p>
    <p v-else-if="items.length === 0" class="hint">還沒有人留言，來說第一句吧</p>

    <ul v-if="items.length" class="list">
      <li v-for="c in items" :key="c.id" class="item">
        <span class="avatar">{{ c.guest.nickname[0] }}</span>
        <div class="body">
          <p class="meta">
            <span class="name">{{ c.guest.nickname }}</span>
            {{ relativeTime(c.createdAt) }}<span v-if="c.editedAt"> · 已編輯</span>
          </p>

          <form v-if="editingId === c.id" class="edit" @submit.prevent="saveEdit(c)">
            <textarea
              ref="editEl"
              v-model="editDraft"
              class="input"
              :maxlength="config.maxCommentLength"
              :disabled="busyId === c.id"
              rows="2"
              aria-label="修改留言"
            />
            <div class="foot">
              <MarkPicker
                v-model="editDraft"
                class="marks"
                :target="editEl[0]"
                :max-length="config.maxCommentLength"
              />
              <button class="link" type="button" @click="editingId = ''">取消</button>
              <button
                class="send"
                type="submit"
                :disabled="!editDraft.trim() || busyId === c.id"
              >
                儲存
              </button>
            </div>
          </form>
          <p v-else class="text">{{ c.text }}</p>

          <div v-if="editingId !== c.id && (isMine(c) || session.isAdmin)" class="actions">
            <button
              v-if="isMine(c)"
              class="link"
              type="button"
              :disabled="busyId === c.id"
              @click="startEdit(c)"
            >
              編輯
            </button>
            <button class="link" type="button" :disabled="busyId === c.id" @click="remove(c)">
              {{ isMine(c) ? '刪除' : '刪除（管理員）' }}
            </button>
          </div>
          <p v-if="itemError?.id === c.id" class="hint error" role="alert">
            {{ itemError.message }}
          </p>
        </div>
      </li>
    </ul>

    <form class="composer" @submit.prevent="send">
      <textarea
        ref="draftEl"
        v-model="draft"
        class="input"
        :maxlength="config.maxCommentLength"
        :disabled="sending"
        placeholder="留言給這張照片…"
        rows="2"
        aria-label="留言"
      />
      <p v-if="sendError" class="hint error" role="alert">{{ sendError }}</p>
      <div class="foot">
        <MarkPicker
          v-model="draft"
          class="marks"
          :target="draftEl"
          :max-length="config.maxCommentLength"
        />
        <span class="counter">{{ draft.length }} / {{ config.maxCommentLength }}</span>
        <button class="send" type="submit" :disabled="!canSend">
          {{ sending ? '送出中…' : '送出' }}
        </button>
      </div>
    </form>
  </section>
</template>

<style scoped>
.comments {
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid var(--c-line);
}

.title {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 1.5px;
  color: var(--c-ink-soft);
}

.title-count {
  color: var(--c-ink-mute);
}

.hint {
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--c-ink-mute);
}

.hint.error {
  color: var(--c-rose);
}

.list {
  margin: 0 0 12px;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.item {
  display: flex;
  gap: 10px;
}

.avatar {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 14px;
  background: var(--c-bg-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-serif);
  font-size: 12px;
}

.body {
  flex: 1;
  min-width: 0;
}

.meta {
  margin: 0;
  font-size: 10px;
  color: var(--c-ink-mute);
}

.name {
  margin-right: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--c-ink);
}

.text {
  margin: 2px 0 0;
  font-size: 14px;
  line-height: 1.6;
  /* 保留換行，長網址也不會撐破版面 */
  white-space: pre-line;
  overflow-wrap: anywhere;
}

.actions {
  display: flex;
  gap: 14px;
  margin-top: 2px;
}

.link {
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 11px;
  color: var(--c-ink-mute);
}

.link:disabled {
  opacity: 0.5;
}

.edit {
  margin-top: 4px;
}

.input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--c-line);
  border-radius: 10px;
  resize: none;
  background: var(--c-card);
  font-family: var(--f-serif);
  font-size: 14px;
  line-height: 1.6;
  color: var(--c-ink);
  caret-color: var(--c-rose);
}

.input:focus {
  outline: none;
  border-color: var(--c-rose-soft);
}

.input::placeholder {
  color: var(--c-ink-mute);
  opacity: 0.7;
}

.foot {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
}

/* 符號按鈕本身有留白，往左拉齊輸入框 */
.marks {
  margin-left: -6px;
  margin-right: auto;
}

.counter {
  font-size: 10px;
  color: var(--c-ink-mute);
}

.send {
  padding: 6px 18px;
  border: 0;
  border-radius: 16px;
  background: var(--c-rose);
  color: #fff;
  font-size: 13px;
  letter-spacing: 1px;
}

.send:disabled {
  opacity: 0.45;
}
</style>
