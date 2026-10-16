<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { fetchConfig } from '@/api/config'
import { uploadWithRetry } from '@/api/upload'
import MarkPicker from '@/components/MarkPicker.vue'
import AppToast, { type Toast } from '@/components/AppToast.vue'
import MediaLightbox from '@/components/MediaLightbox.vue'
import MediaPreview from '@/components/MediaPreview.vue'
import ProfileSheet from '@/components/ProfileSheet.vue'
import { FALLBACK, useAlbumConfig } from '@/composables/useAlbumConfig'
import { PHOTO_TAGS } from '@/config/photoTags'
import { invalidateAll } from '@/stores/photoLists'
import { wedding } from '@/config/wedding'
import {
  describeMedia,
  discardRemoved,
  finishBatch,
  removePicked,
  resetUploadFlow,
  restoreRemoved,
  sizeProblem,
  session,
  uploadFlow,
  type PickedMedia,
  type RemovedPick,
} from '@/stores/session'
import type { PhotoTag, UploadStatus } from '@/types/album'

const router = useRouter()
const albumConfig = useAlbumConfig()

const selected = computed(() =>
  uploadFlow.selectedIds
    .map((id) => uploadFlow.picked.find((p) => p.id === id))
    .filter((p): p is PickedMedia => Boolean(p)),
)

const count = computed(() => selected.value.length)
const summary = computed(() => describeMedia(selected.value))
const hasVideo = computed(() => selected.value.some((p) => p.kind === 'video'))

const nickname = computed(() => session.nickname || '賓客')
const initial = computed(() => nickname.value[0] ?? '賓')

// --- 每張的分類與說明 -----------------------------------------------------
// 多數人一次選的是同一類，所以上面先選一個預設，套用到每一張；個別改過的就不再跟著預設

function tagOf(item: PickedMedia): PhotoTag {
  return uploadFlow.draft.tags[item.id] ?? uploadFlow.draft.tag
}

function setTag(item: PickedMedia, tag: PhotoTag) {
  // 改回跟預設一樣，就當成沒改過，之後換預設時會跟著換
  if (tag === uploadFlow.draft.tag) delete uploadFlow.draft.tags[item.id]
  else uploadFlow.draft.tags[item.id] = tag
}

/**
 * 符號只出現在正在輸入的那一張下面：一次最多 30 張，每張都放一排太擠。
 * 失焦時不收起來，按符號、捲動畫面時才不會一閃一閃
 */
const typingId = ref('')
const typingEl = ref<HTMLTextAreaElement | null>(null)

function startTyping(item: PickedMedia, event: FocusEvent) {
  typingId.value = item.id
  typingEl.value = event.target as HTMLTextAreaElement
}

/** 改暱稱：就地打開面板，不跳到歡迎頁（跳過去會丟下這頁選好的東西） */
const profileOpen = ref(false)

// --- 放大看、拿掉選錯的 ---------------------------------------------------

/** 正在放大看的那一張 */
const zoomed = ref<PickedMedia | null>(null)

// 拿掉不跳確認（選錯好幾張時每張都要多按一次很煩），改成幾秒內可以「復原」

const toast = ref<Toast | null>(null)
let toastTimer = 0
/** 剛拿掉的那一個，提示還在時可以放回去。連續拿掉時只能復原最後一個 */
let removed: RemovedPick | null = null

function remove(item: PickedMedia) {
  // 先收掉上一個提示（上一個就不能復原了），再拿掉這一個：順序反過來的話，
  // 拿掉最後一個時 hideToast 會以為全部拿光了而直接回選取頁
  hideToast()
  const snapshot = removePicked(item.id)
  if (!snapshot) return
  if (typingId.value === item.id) typingId.value = ''
  removed = snapshot
  const what = item.kind === 'video' ? '1 支影片' : '1 張照片'
  toast.value = { text: `已拿掉 ${what}`, action: { label: '復原', run: undo } }
  toastTimer = window.setTimeout(hideToast, 5000)
}

function undo() {
  if (!removed) return
  restoreRemoved(removed)
  removed = null
  hideToast()
}

function hideToast() {
  window.clearTimeout(toastTimer)
  toast.value = null
  // 提示消失就不能復原了，預覽可以回收
  if (removed) discardRemoved(removed)
  removed = null
  // 全部拿掉了（又沒有復原）就回選取頁重選，不要停在一個空的頁面
  if (uploadFlow.selectedIds.length === 0 && !leaving) router.back()
}

/** 離開這頁時只回收，不要再導頁 */
let leaving = false
onBeforeUnmount(() => {
  leaving = true
  hideToast()
})

/** 跟預設不同的有幾張，提示賓客「換預設不會動到這些」 */
const customTagCount = computed(() => selected.value.filter((p) => p.id in uploadFlow.draft.tags).length)

onMounted(() => {
  // 直接開這個網址（重新整理、分享連結）時沒有選到的檔案，退回第一步
  if (uploadFlow.picked.length === 0) router.replace({ name: 'upload' })
})

function addMore() {
  router.back()
}

// --- 上傳 -----------------------------------------------------------------

interface Task {
  status: UploadStatus
  /** 0–100 */
  progress: number
  errorMessage?: string
  /** 失敗後正在等著自動重試 */
  retrying?: boolean
}

/** 每張照片的上傳狀態，key 是 PickedMedia.id */
const tasks = reactive<Record<string, Task>>({})
const retrying = computed(() => selected.value.some((p) => tasks[p.id]?.retrying))
const running = ref(false)

const failedCount = computed(
  () => selected.value.filter((p) => tasks[p.id]?.status === 'failed').length,
)
const doneCount = computed(
  () => selected.value.filter((p) => tasks[p.id]?.status === 'succeeded').length,
)

/** 失敗的原因通常都一樣（例如截止上傳、網路斷了），顯示第一個就好 */
const failedMessage = computed(() => {
  if (running.value || failedCount.value === 0) return ''
  const first = selected.value.find((p) => tasks[p.id]?.status === 'failed')
  const reason = first ? tasks[first.id]?.errorMessage : ''
  return `有 ${failedCount.value} 個檔案沒有傳成功：${reason}`
})

const submitLabel = computed(() => {
  if (running.value) return `上 傳 中 ${doneCount.value} / ${count.value}`
  if (failedCount.value > 0) return `重 試 ${failedCount.value} 個`
  return `上 傳 ${summary.value}`
})

/**
 * 在手機上先讀影片長度。超過上限就不必傳了：影片動輒上百 MB，傳完才被後端拒絕太浪費。
 * 讀不到（例如這支手機解不開這種格式）就回 null，交給後端判斷。
 */
function readDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const video = document.createElement('video')
    const url = URL.createObjectURL(file)
    const done = (value: number | null) => {
      URL.revokeObjectURL(url)
      video.removeAttribute('src')
      resolve(value)
    }
    video.preload = 'metadata'
    video.muted = true
    video.onloadedmetadata = () => done(Number.isFinite(video.duration) ? video.duration : null)
    video.onerror = () => done(null)
    setTimeout(() => done(null), 5000)
    video.src = url
  })
}

function formatSeconds(seconds: number) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (!m) return `${s} 秒`
  return s ? `${m} 分 ${s} 秒` : `${m} 分鐘`
}

/** 傳之前先在手機上擋掉的情況，回傳要顯示的原因；沒問題回傳空字串 */
async function precheck(item: PickedMedia, config: typeof FALLBACK): Promise<string> {
  // 選取頁已經擋過一次；這裡再檢查是因為後端設定可能在那之後才載入
  const tooLarge = sizeProblem(item, config)
  if (tooLarge) return tooLarge
  if (item.kind === 'video') {
    const seconds = await readDuration(item.file)
    // 跟後端一樣留一秒誤差
    if (seconds !== null && seconds > config.maxVideoSeconds + 1) {
      return `影片太長了，請剪到 ${formatSeconds(config.maxVideoSeconds)}以內再上傳`
    }
  }
  return ''
}

async function upload() {
  if (running.value) return
  running.value = true

  const config = await fetchConfig().catch(() => FALLBACK)
  // 已經傳成功的不重傳；按「重試」時只會跑失敗的那幾張
  const pending = selected.value.filter((p) => tasks[p.id]?.status !== 'succeeded')
  for (const item of pending) tasks[item.id] = { status: 'pending', progress: 0 }
  // 照片、影片各排各的隊：影片一次只傳一支，不會卡住後面的照片
  const photoQueue = pending.filter((p) => p.kind !== 'video')
  const videoQueue = pending.filter((p) => p.kind === 'video')

  // 碰到「截止上傳」「傳太多」這種後面每張都會失敗的錯誤，就不再送了
  let stopReason = ''

  async function worker(queue: PickedMedia[]) {
    for (let item = queue.shift(); item; item = queue.shift()) {
      const task = tasks[item.id]!
      if (stopReason) {
        Object.assign(task, { status: 'failed', errorMessage: stopReason })
        continue
      }
      // 先在手機上擋掉太大、太長的檔案，不必浪費流量傳到一半才被拒絕
      const problem = await precheck(item, config)
      if (problem) {
        Object.assign(task, { status: 'failed', errorMessage: problem })
        continue
      }

      task.status = 'uploading'
      try {
        await uploadWithRetry(
          item.file,
          // 分類與說明在送出的那一刻才讀：排隊等著的那幾張，上傳中還來得及改
          { tag: tagOf(item), caption: uploadFlow.draft.captions[item.id] ?? '' },
          (percent) => {
            task.progress = percent
            if (percent > 0) task.retrying = false
          },
          () => (task.retrying = true),
        )
        Object.assign(task, { status: 'succeeded', progress: 100, retrying: false })
      } catch (e) {
        const message = e instanceof ApiError ? e.message : '上傳失敗，請稍後再試'
        Object.assign(task, { status: 'failed', errorMessage: message, retrying: false })
        if (e instanceof ApiError && [401, 403, 429].includes(e.status)) stopReason = message
      }
    }
  }

  // 同時傳幾個由後端設定決定，不要一次全送：會互搶網路，每個都變慢
  const pool = (queue: PickedMedia[], size: number) =>
    Array.from({ length: Math.max(1, size) }, () => worker(queue))
  await Promise.all([
    ...pool(photoQueue, config.uploadConcurrency),
    ...pool(videoQueue, config.videoUploadConcurrency),
  ])
  running.value = false

  if (doneCount.value > 0) invalidateAll()
  if (failedCount.value === 0) finish()
}

function finish() {
  // 還有沒勾的（例如一次選超過上限）就回選取頁接著傳下一批，都傳完才回首頁
  const left = finishBatch((p) => sizeProblem(p, albumConfig) === '', wedding.maxUploadCount)
  if (left > 0) {
    router.back()
    return
  }
  resetUploadFlow()
  router.push({ name: 'feed' })
}

// 傳到一半離開會中斷上傳，先確認
onBeforeRouteLeave(() => {
  if (!running.value) return true
  return window.confirm('還在上傳中，離開會中斷上傳。確定要離開嗎？')
})
</script>

<template>
  <main class="edit">
    <header class="head">
      <button class="back" type="button" @click="router.back()">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
        >
          <path d="M15 6l-6 6 6 6" />
        </svg>
        返回
      </button>
      <h1>上傳照片影片</h1>
      <!-- 讓標題保持置中 -->
      <span class="head-spacer" />
    </header>

    <section class="block intro">
      <div class="identity">
        <span class="identity-avatar">{{ initial }}</span>
        <div class="identity-text">
          <p class="identity-label">以此暱稱發布</p>
          <p class="identity-name">{{ nickname }}</p>
        </div>
        <!-- 上傳中先停用：上傳的請求已經帶著目前的身分送出了 -->
        <button
          class="identity-change"
          type="button"
          :disabled="running"
          @click="profileOpen = true"
        >
          更改
        </button>
      </div>

      <fieldset class="settings" :disabled="running">
        <legend class="settings-label">這些大多是在哪個環節拍的？</legend>
        <div class="tags">
          <label
            v-for="t in PHOTO_TAGS"
            :key="t.id"
            class="tag"
            :class="{ active: uploadFlow.draft.tag === t.id }"
          >
            <input v-model="uploadFlow.draft.tag" type="radio" name="tag" :value="t.id" />
            {{ t.label }}
          </label>
        </div>
        <p class="settings-hint">
          {{
            customTagCount > 0
              ? `另有 ${customTagCount} 個已個別改過分類，不會跟著換`
              : '不一樣的可以在下面個別改'
          }}
        </p>
      </fieldset>
    </section>

    <section class="items">
      <p class="items-label">{{ summary }} · 將公開分享</p>
      <ul class="item-list">
        <li v-for="item in selected" :key="item.id" class="item">
          <button
            class="thumb"
            type="button"
            :aria-label="item.kind === 'video' ? '放大看這支影片' : '放大看這張照片'"
            @click="zoomed = item"
          >
            <MediaPreview :item="item" />
            <template v-if="tasks[item.id]">
              <span
                v-if="tasks[item.id]!.status === 'uploading' || tasks[item.id]!.status === 'pending'"
                class="thumb-progress"
                :style="{ width: tasks[item.id]!.progress + '%' }"
              />
              <span v-else-if="tasks[item.id]!.status === 'succeeded'" class="thumb-badge ok">
                ✓
              </span>
              <span v-else class="thumb-badge fail" :title="tasks[item.id]!.errorMessage">!</span>
            </template>
          </button>
          <!-- 傳好的就不能再改：要改請到照片詳情 -->
          <fieldset
            class="item-fields"
            :disabled="running || tasks[item.id]?.status === 'succeeded'"
          >
            <span class="item-tag" :class="{ custom: item.id in uploadFlow.draft.tags }">
              <select
                :value="tagOf(item)"
                aria-label="分類"
                @change="setTag(item, ($event.target as HTMLSelectElement).value as PhotoTag)"
              >
                <option v-for="t in PHOTO_TAGS" :key="t.id" :value="t.id">{{ t.label }}</option>
              </select>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 9l6 6 6-6" />
              </svg>
            </span>
            <textarea
              v-model="uploadFlow.draft.captions[item.id]"
              class="item-caption"
              :maxlength="albumConfig.maxCaptionLength"
              placeholder="想說點什麼…（選填）"
              rows="2"
              aria-label="想說的話"
              @focus="startTyping(item, $event)"
            />
            <MarkPicker
              v-if="typingId === item.id"
              v-model="uploadFlow.draft.captions[item.id]"
              class="item-marks"
              :target="typingEl"
              :max-length="albumConfig.maxCaptionLength"
            />
          </fieldset>
          <!-- 傳好的已經在相簿裡了，要刪請到照片詳情 -->
          <button
            v-if="!running && tasks[item.id]?.status !== 'succeeded'"
            class="item-remove"
            type="button"
            :aria-label="item.kind === 'video' ? '不傳這支影片' : '不傳這張照片'"
            @click="remove(item)"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </li>
      </ul>
      <button v-if="!running" class="add" type="button" @click="addMore">＋ 再選照片或影片</button>

      <p v-if="hasVideo" class="video-hint">影片比較大，上傳時請停留在這一頁，也不要關掉螢幕。</p>
      <p v-if="retrying" class="video-hint">現在上傳的人比較多，稍等一下會自動重新上傳…</p>
      <p v-if="failedMessage" class="upload-error" role="alert">
        {{ failedMessage }}
        <!-- 壞掉的檔案怎麼重試都不會成功，給一條出路 -->
        <button v-if="doneCount > 0" class="give-up" type="button" @click="finish">
          略過失敗的，回相簿
        </button>
      </p>
    </section>

    <MediaLightbox v-model="zoomed" />
    <ProfileSheet v-model="profileOpen" />
    <AppToast :toast="toast" />

    <div class="submit-bar">
      <button class="submit" type="button" :disabled="count === 0 || running" @click="upload">
        {{ submitLabel }}
      </button>
    </div>
  </main>
</template>

<style scoped>
.edit {
  min-height: var(--screen-h);
  background: var(--c-bg);
  color: var(--c-ink);
  padding-bottom: 120px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(var(--page-top) + 24px) 16px 12px;
  border-bottom: 1px solid var(--c-line);
}

.head h1 {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 16px;
  font-weight: 500;
}

.back {
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--c-ink-soft);
  min-width: 56px;
}

.head-spacer {
  min-width: 56px;
}

.back svg {
  width: 16px;
  height: 16px;
}

.intro {
  padding-top: 18px;
}

.items {
  padding: 0 16px;
}

.items-label {
  margin: 0 0 8px;
  font-size: 11px;
  letter-spacing: 1.5px;
  color: var(--c-ink-mute);
}

.item-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.item {
  position: relative;
  display: flex;
  gap: 12px;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
}

.item-fields {
  flex: 1;
  min-width: 0;
  margin: 0;
  /* 右上角留給「✕」 */
  padding: 0 28px 0 0;
  border: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* 原生下拉選單：手機上會叫出系統的選擇器，比自己畫的好按。外觀畫成小 chip */
.item-tag {
  position: relative;
  align-self: flex-start;
  color: var(--c-ink-soft);
}

.item-tag select {
  padding: 3px 26px 3px 12px;
  border-radius: 12px;
  border: 1px solid var(--c-line-strong);
  background: transparent;
  appearance: none;
  font: inherit;
  font-size: 12px;
  letter-spacing: 1px;
  color: inherit;
}

.item-tag svg {
  position: absolute;
  right: 9px;
  top: 50%;
  width: 11px;
  height: 11px;
  transform: translateY(-50%);
  pointer-events: none;
}

/* 個別改過、跟預設不同的，標出來 */
.item-tag.custom {
  color: var(--c-rose);
}

.item-tag.custom select {
  border-color: var(--c-rose);
}

.item-caption {
  width: 100%;
  border: 0;
  padding: 0;
  resize: none;
  background: transparent;
  font-family: var(--f-serif);
  font-size: 14px;
  line-height: 1.6;
  color: var(--c-ink);
  caret-color: var(--c-rose);
}

.item-caption:focus {
  outline: none;
}

.item-caption::placeholder {
  color: var(--c-ink-mute);
  opacity: 0.7;
}

/* 圖示很小，按鈕做大一點，手指才按得到 */
.item-remove {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 0;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--c-ink-mute);
}

.item-remove svg {
  width: 14px;
  height: 14px;
}

/* 符號按鈕本身有留白，往左拉齊輸入框的文字 */
.item-marks {
  margin-left: -9px;
}

/* 上傳中（或這張已經傳好）不能再改：整塊變淡，一看就知道按不了 */
.item-fields:disabled,
.settings:disabled {
  opacity: 0.5;
}

.settings:disabled .tag {
  cursor: default;
}

.add {
  width: 100%;
  margin-top: 10px;
  padding: 12px 0;
  border: 1.5px dashed var(--c-line-strong);
  border-radius: 12px;
  background: transparent;
  font-size: 13px;
  letter-spacing: 1px;
  color: var(--c-ink-soft);
}

.thumb {
  position: relative;
  flex-shrink: 0;
  width: 64px;
  height: 80px;
  border-radius: 8px;
  border: 1px solid var(--c-line);
  overflow: hidden;
  /* 點縮圖放大看 */
  padding: 0;
  background: transparent;
  cursor: zoom-in;
}

/* 上傳進度：沿著縮圖底部長出來的一條線 */
.thumb-progress {
  position: absolute;
  left: 0;
  bottom: 0;
  height: 3px;
  background: var(--c-rose);
  transition: width 0.2s;
}

.thumb-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 18px;
  height: 18px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #fff;
}

.thumb-badge.ok {
  background: var(--c-rose);
}

.thumb-badge.fail {
  background: var(--c-ink);
}

.video-hint {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--c-ink-mute);
}

.upload-error {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--c-rose);
}

.give-up {
  margin-left: 6px;
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 12px;
  color: var(--c-ink-soft);
  text-decoration: underline;
}

.block {
  padding: 0 16px;
  margin-bottom: 14px;
}

.identity {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
}

.identity-avatar {
  width: 30px;
  height: 30px;
  border-radius: 15px;
  background: var(--c-bg-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-serif);
  font-size: 13px;
}

.identity-text {
  flex: 1;
}

.identity-label {
  margin: 0;
  font-size: 10px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.identity-name {
  margin: 1px 0 0;
  font-size: 14px;
}

.identity-change {
  border: 0;
  background: transparent;
  font-size: 11px;
  color: var(--c-rose);
}

.identity-change:disabled {
  opacity: 0.4;
}

.settings {
  margin: 14px 0 0;
  padding: 12px 16px 14px;
  border-radius: 12px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
}

.settings-label {
  float: left;
  width: 100%;
  margin-bottom: 10px;
  padding: 0;
  font-size: 13px;
}

/* 四個選項排一列太擠（「訂婚・迎娶」放不下），排成兩欄 */
.tags {
  clear: both;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

/* 單選用原生 radio 保留可存取性，外觀畫成 chip */
.tag {
  flex: 1;
  padding: 8px 0;
  border-radius: 16px;
  border: 1px solid var(--c-line-strong);
  text-align: center;
  font-size: 13px;
  letter-spacing: 1px;
  color: var(--c-ink-soft);
  cursor: pointer;
}

.tag input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.tag.active {
  border-color: transparent;
  background: var(--c-rose);
  color: #fff;
}

.settings-hint {
  margin: 10px 0 0;
  font-size: 11px;
  color: var(--c-ink-mute);
}

.tag:has(input:focus-visible) {
  outline: 2px solid var(--c-rose-soft);
  outline-offset: 2px;
}

.submit-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px 16px calc(var(--safe-bottom) + 28px);
  background: linear-gradient(180deg, transparent, var(--c-bg) 30%);
}

.submit {
  width: 100%;
  height: 50px;
  border: 0;
  border-radius: 25px;
  background: var(--c-rose);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 4px;
  box-shadow: var(--shadow-rose);
}

.submit:disabled {
  opacity: 0.45;
  box-shadow: none;
  cursor: default;
}
</style>
