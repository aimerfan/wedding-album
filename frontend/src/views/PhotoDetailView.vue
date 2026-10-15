<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { deletePhoto, editPhoto, fetchPhoto, setFavorited, setLiked } from '@/api/photos'
import MarkPicker from '@/components/MarkPicker.vue'
import PhotoComments from '@/components/PhotoComments.vue'
import PhotoSwiper from '@/components/PhotoSwiper.vue'
import { useAlbumConfig } from '@/composables/useAlbumConfig'
import { PHOTO_TAGS, tagLabel } from '@/config/photoTags'
import {
  ensureLoaded,
  filterFromQuery,
  getPhotoList,
  loadMore,
  removePhoto,
  updatePhoto,
} from '@/stores/photoLists'
import { session } from '@/stores/session'
import type { Photo, PhotoTag } from '@/types/album'

const props = defineProps<{ photoId: string }>()
const route = useRoute()
const router = useRouter()
const albumConfig = useAlbumConfig()

/**
 * 左右滑動要在哪一串照片裡換張：由網址上的篩選條件決定（例如 ?uploader=me、?tag=banquet），
 * 跟列表頁用的是同一份快取，所以從哪裡點進來，就在那一串裡滑。
 */
const filter = computed(() => filterFromQuery(route.query))
const list = computed(() => getPhotoList(filter.value))

/** 直接打開分享連結、而那張不在列表已載入的範圍時，單獨抓這一張來顯示 */
const single = ref<Photo | null>(null)
const missing = ref(false)
const loadError = ref('')

const inList = computed(() => list.value.items.some((p) => p.id === props.photoId))
const photos = computed(() => (inList.value ? list.value.items : single.value ? [single.value] : []))

watch(
  () => props.photoId,
  async (id) => {
    if (inList.value) return
    missing.value = false
    loadError.value = ''
    await ensureLoaded(filter.value)
    if (list.value.items.some((p) => p.id === id)) return
    try {
      single.value = await fetchPhoto(id)
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) missing.value = true
      else loadError.value = e instanceof ApiError ? e.message : '載入失敗，請稍後再試'
    }
  },
  { immediate: true },
)

const index = computed(() => photos.value.findIndex((p) => p.id === props.photoId))
const photo = computed(() => photos.value[index.value])

// 滑到倒數第三張就先載下一頁，滑到底時通常已經接上了
watch(index, (i) => {
  const l = list.value
  if (inList.value && !l.done && i >= l.items.length - 3) loadMore(filter.value)
})

/** 「3 / 30+」：還有下一頁沒載時，總數後面加 + */
const counter = computed(() => {
  if (!inList.value) return ''
  const l = list.value
  return `${index.value + 1} / ${l.items.length}${l.done ? '' : '+'}`
})

const slides = computed(() =>
  photos.value.map((p) => ({
    key: p.id,
    photo: p,
    ratio: p.width / p.height,
    video: p.kind === 'video' ? p.url : undefined,
  })),
)

/** 滑到別張時換掉網址，返回鍵才會直接回相簿，而不是一張張倒退 */
const current = computed({
  get: () => index.value,
  set: (i) => {
    const next = photos.value[i]
    if (next) {
      router.replace({ name: 'photo-detail', params: { photoId: next.id }, query: route.query })
    }
  },
})

const takenLabel = computed(() => {
  const p = photo.value
  if (!p) return ''
  const d = new Date(p.uploadedAt)
  return (
    String(d.getMonth() + 1) +
    '/' +
    d.getDate() +
    ' · ' +
    String(d.getHours()).padStart(2, '0') +
    ':' +
    String(d.getMinutes()).padStart(2, '0') +
    ' · ' +
    tagLabel(p.tag)
  )
})

// --- 手機橫放：點一下照片收起／叫出按鈕與資訊條 ---------------------------
// 版面本身由 CSS 的 media query 切換，這裡只記「收起來了沒」。條件要跟 <style> 裡的一致

const LANDSCAPE = '(orientation: landscape) and (max-height: 500px)'
const landscapeQuery = window.matchMedia(LANDSCAPE)
const immersive = ref(false)

// 轉向時一律先顯示：直式時點過照片，轉成橫的不該一開始就什麼都看不到
function onOrientation() {
  immersive.value = false
}
onMounted(() => landscapeQuery.addEventListener('change', onOrientation))
onBeforeUnmount(() => landscapeQuery.removeEventListener('change', onOrientation))

/**
 * 點照片：像 IG 一樣把畫面左右三等分，點左邊上一張、點右邊下一張；
 * 點中間在橫放時收起／叫出按鈕與資訊條，直式時不做事。
 * 點在影片上是叫出播放控制，一律不處理；影片旁邊的黑邊照樣可以點左右換張。
 * 影片那張中間也不切換（見 <style> 的 .is-video：上方按鈕改成播放中收起）。
 */
function onStageClick(e: MouseEvent) {
  if ((e.target as Element).closest('video')) return
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const x = (e.clientX - rect.left) / rect.width
  const i = index.value
  if (x < 1 / 3) {
    if (i > 0) current.value = i - 1
  } else if (x > 2 / 3) {
    if (i < photos.value.length - 1) current.value = i + 1
  } else if (landscapeQuery.matches && photo.value?.kind !== 'video') {
    immersive.value = !immersive.value
  }
}

/**
 * 影片播放中，橫放時上方按鈕也收起來，畫面上只剩影片；暫停或播完再出現（一般影片 app 的習慣）。
 * play／pause 事件不會冒泡，所以在 .stage 上用 capture 接。
 * 換張時播放器整個被拿掉，不一定有 pause 事件，要自己歸零。
 */
const playing = ref(false)
watch(() => props.photoId, () => (playing.value = false))

function close() {
  if (window.history.state?.back) router.back()
  else router.push({ name: 'feed' })
}

// --- 按讚、收藏 -----------------------------------------------------------

/** 把更新後的照片換進所有列表（以及單獨抓來的那張），畫面上每個地方的數字才一致 */
function apply(p: Photo) {
  updatePhoto(p)
  if (single.value?.id === p.id) single.value = p
}

const actionError = ref('')
/** 同一張照片的請求還沒回來前，不接受下一次點擊，避免回應順序錯亂 */
const pending = new Set<string>()

/**
 * 先把畫面改掉（樂觀更新），按下去立刻有反應；再送給後端，以後端回傳的為準。
 * 失敗就改回原樣並顯示原因。
 */
async function toggle(change: (p: Photo) => Photo, send: (p: Photo) => Promise<Photo>) {
  const before = photo.value
  if (!before || pending.has(before.id)) return
  pending.add(before.id)
  actionError.value = ''
  const optimistic = change(before)
  apply(optimistic)
  try {
    apply(await send(optimistic))
  } catch (e) {
    apply(before)
    actionError.value = e instanceof ApiError ? e.message : '操作失敗，請稍後再試'
  } finally {
    pending.delete(before.id)
  }
}

function toggleLike() {
  toggle(
    (p) => ({ ...p, likedByMe: !p.likedByMe, likeCount: p.likeCount + (p.likedByMe ? -1 : 1) }),
    (p) => setLiked(p.id, p.likedByMe),
  )
}

// --- 刪除照片 -------------------------------------------------------------

const isMine = computed(() => !!photo.value && photo.value.uploader.id === session.guestId)
/** 上傳者刪自己的；管理員可刪任何一張。真正的權限由後端把關，這裡只決定要不要顯示選單 */
const canDelete = computed(() => isMine.value || session.isAdmin)
const deleteLabel = computed(() => {
  const label = photo.value?.kind === 'video' ? '刪除影片' : '刪除照片'
  return isMine.value ? label : label + '（管理員）'
})
const moreOpen = ref(false)
const deleting = ref(false)

// 換張時把選單、編輯中的說明收起來
watch(
  () => props.photoId,
  () => {
    moreOpen.value = false
    editing.value = false
  },
)

async function removeCurrent() {
  const target = photo.value
  if (!target || deleting.value) return
  const what = target.kind === 'video' ? '這支影片' : '這張照片'
  const question = isMine.value
    ? `確定要刪除${what}嗎？刪除後無法復原。`
    : `以管理員身分刪除「${target.uploader.nickname}」上傳的${what}？刪除後無法復原。`
  if (!window.confirm(question)) return

  deleting.value = true
  // 刪完要顯示同一串裡的下一張（沒有下一張就上一張）；這串只剩它的話就關掉
  const list = photos.value
  const i = list.findIndex((p) => p.id === target.id)
  const neighbor = list[i + 1] ?? list[i - 1]
  try {
    await deletePhoto(target.id)
    removePhoto(target.id)
    if (single.value?.id === target.id) single.value = null
    moreOpen.value = false
    if (neighbor) {
      router.replace({ name: 'photo-detail', params: { photoId: neighbor.id }, query: route.query })
    } else {
      close()
    }
  } catch (e) {
    actionError.value = e instanceof ApiError ? e.message : '刪除失敗，請稍後再試'
    moreOpen.value = false
  } finally {
    deleting.value = false
  }
}

// --- 說明與分類 -----------------------------------------------------------
// 上傳者可以改說明與分類；管理員可以改分類、刪掉說明，但不能替上傳者寫說明（後端也這樣把關）

const editing = ref(false)
const draftCaption = ref('')
const captionEl = ref<HTMLTextAreaElement>()
const draftTag = ref<PhotoTag>('banquet')
const saving = ref(false)
const editError = ref('')

const editLabel = computed(() => (isMine.value ? '編輯文字與分類' : '改分類（管理員）'))

function startEdit() {
  const p = photo.value
  if (!p) return
  draftCaption.value = p.caption ?? ''
  draftTag.value = p.tag
  editError.value = ''
  moreOpen.value = false
  editing.value = true
}

type PhotoChanges = Parameters<typeof editPhoto>[1]

/** 送出修改，成功就換掉畫面上的那張並收起編輯區。回傳有沒有成功 */
async function send(target: Photo, changes: PhotoChanges) {
  saving.value = true
  editError.value = ''
  try {
    apply(await editPhoto(target.id, changes))
    editing.value = false
    return true
  } catch (e) {
    editError.value = e instanceof ApiError ? e.message : '儲存失敗，請稍後再試'
    return false
  } finally {
    saving.value = false
  }
}

async function saveEdit() {
  const target = photo.value
  if (!target || saving.value) return
  const changes: PhotoChanges = {}
  if (draftTag.value !== target.tag) changes.tag = draftTag.value
  const caption = draftCaption.value.trim()
  if (isMine.value && caption !== (target.caption ?? '')) changes.caption = caption || null
  // 什麼都沒改就直接收起來，不必送
  if (Object.keys(changes).length === 0) {
    editing.value = false
    return
  }
  await send(target, changes)
}

async function removeCaption() {
  const target = photo.value
  if (!target || saving.value) return
  const question = isMine.value
    ? '確定要刪除這段文字嗎？'
    : `以管理員身分刪除「${target.uploader.nickname}」在這張寫的文字？`
  if (!window.confirm(question)) return
  moreOpen.value = false
  // 從選單刪的時候沒有編輯區，錯誤改顯示在按讚那一列下面
  if (!(await send(target, { caption: null })) && !editing.value) actionError.value = editError.value
}

/** 留言數變了（新增、刪除）：換進列表，回到相簿或下次打開時數字才對 */
function onCommentCount(count: number) {
  const p = photo.value
  if (p && p.commentCount !== count) apply({ ...p, commentCount: count })
}

function toggleFavorite() {
  toggle(
    (p) => ({ ...p, favoritedByMe: !p.favoritedByMe }),
    (p) => setFavorited(p.id, p.favoritedByMe),
  )
}
</script>

<template>
  <main
    v-if="photo"
    class="detail"
    :class="{
      immersive: (immersive || playing) && !moreOpen,
      'is-video': photo.kind === 'video',
    }"
  >
    <header class="bar">
      <button class="round" type="button" aria-label="關閉" @click="close">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
      <span class="counter">{{ counter }}</span>
      <!-- 只有上傳者與管理員有選單（說明、分類、刪除）；其他人留一塊空白，讓序號保持置中 -->
      <div v-if="canDelete" class="more">
        <button
          class="round"
          type="button"
          aria-label="更多"
          :aria-expanded="moreOpen"
          @click="moreOpen = !moreOpen"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="#fff"
            stroke-width="1.8"
            stroke-linecap="round"
          >
            <circle cx="5" cy="12" r="2" />
            <circle cx="12" cy="12" r="2" />
            <circle cx="19" cy="12" r="2" />
          </svg>
        </button>
        <div v-if="moreOpen" class="more-pop" role="menu">
          <!-- 編輯說明與分類只在直式做：橫放時面板只剩資訊條，放不下編輯表單（見 <style>） -->
          <button class="portrait-only" type="button" role="menuitem" @click="startEdit">
            {{ editLabel }}
          </button>
          <button
            v-if="!isMine && photo.caption"
            class="portrait-only"
            type="button"
            role="menuitem"
            :disabled="saving"
            @click="removeCaption"
          >
            刪除文字（管理員）
          </button>
          <button type="button" role="menuitem" :disabled="deleting" @click="removeCurrent">
            {{ deleting ? '刪除中…' : deleteLabel }}
          </button>
        </div>
      </div>
      <span v-else class="round-spacer" />
    </header>

    <div
      class="stage"
      @click="onStageClick"
      @play.capture="playing = true"
      @pause.capture="playing = false"
      @ended.capture="playing = false"
    >
      <PhotoSwiper v-model="current" :slides="slides" />
    </div>

    <section class="panel">
      <span class="grip" />

      <div class="uploader">
        <RouterLink
          class="who"
          :to="{ name: 'guest-photos', params: { guestId: photo.uploader.id } }"
          :aria-label="'看' + photo.uploader.nickname + '拍的所有照片'"
        >
          <span class="avatar">{{ photo.uploader.nickname[0] }}</span>
          <div class="who-text">
            <p class="name">{{ photo.uploader.nickname }}</p>
            <p class="meta">{{ takenLabel }}</p>
          </div>
          <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path d="M9 6l6 6-6 6" />
          </svg>
        </RouterLink>
        <button
          class="action"
          type="button"
          :aria-pressed="photo.favoritedByMe"
          :aria-label="photo.favoritedByMe ? '取消收藏' : '收藏'"
          @click="toggleFavorite"
        >
          <svg
            class="bookmark"
            :class="{ on: photo.favoritedByMe }"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linejoin="round"
          >
            <path d="M6 3h12v18l-6-4-6 4z" />
          </svg>
        </button>
        <button
          class="action"
          type="button"
          :aria-pressed="photo.likedByMe"
          :aria-label="photo.likedByMe ? '收回讚' : '按讚'"
          @click="toggleLike"
        >
          <svg
            class="heart"
            :class="{ on: photo.likedByMe }"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.8"
          >
            <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z" />
          </svg>
          <span class="likes">{{ photo.likeCount }}</span>
        </button>
      </div>
      <p v-if="actionError" class="action-error" role="alert">{{ actionError }}</p>

      <form v-if="editing" class="editor" @submit.prevent="saveEdit">
        <fieldset class="editor-tags" :disabled="saving">
          <legend>分類</legend>
          <div class="editor-tag-grid">
            <label
              v-for="t in PHOTO_TAGS"
              :key="t.id"
              class="editor-tag"
              :class="{ active: draftTag === t.id }"
            >
              <input v-model="draftTag" type="radio" name="detail-tag" :value="t.id" />
              {{ t.label }}
            </label>
          </div>
        </fieldset>
        <template v-if="isMine">
          <textarea
            ref="captionEl"
            v-model="draftCaption"
            class="editor-caption"
            :maxlength="albumConfig.maxCaptionLength"
            :disabled="saving"
            placeholder="想說點什麼…（選填）"
            rows="3"
            aria-label="想說的話"
          />
          <div class="editor-foot">
            <MarkPicker
              v-model="draftCaption"
              class="editor-marks"
              :target="captionEl"
              :max-length="albumConfig.maxCaptionLength"
            />
            <span class="editor-counter">
              {{ draftCaption.length }} / {{ albumConfig.maxCaptionLength }}
            </span>
          </div>
        </template>
        <p v-if="editError" class="action-error" role="alert">{{ editError }}</p>
        <div class="editor-actions">
          <button
            v-if="isMine && photo.caption"
            class="editor-delete"
            type="button"
            :disabled="saving"
            @click="removeCaption"
          >
            刪除文字
          </button>
          <button class="editor-cancel" type="button" :disabled="saving" @click="editing = false">
            取消
          </button>
          <button class="editor-save" type="submit" :disabled="saving">
            {{ saving ? '儲存中…' : '儲存' }}
          </button>
        </div>
      </form>

      <!-- 上傳者就在正上方，一看就知道是誰說的，不必再加名字或標籤 -->
      <div v-else-if="photo.caption" class="caption">
        <p class="caption-text">{{ photo.caption }}</p>
        <p v-if="photo.captionEditedAt" class="caption-edited">已編輯</p>
      </div>

      <button v-else-if="isMine" class="caption-add" type="button" @click="startEdit">
        ＋ 為這張說點什麼
      </button>

      <!-- key：換張時整個重來，不會短暫顯示上一張的留言 -->
      <PhotoComments :key="photo.id" :photo-id="photo.id" @count="onCommentCount" />
    </section>
  </main>

  <!-- 照片被刪掉或網址打錯時，不要只留一片空白 -->
  <main v-else-if="missing || loadError" class="detail missing">
    <p>{{ missing ? '找不到這張照片' : loadError }}</p>
    <button class="missing-back" type="button" @click="close">回相簿</button>
  </main>

  <main v-else class="detail missing">
    <p>載入中…</p>
  </main>
</template>

<style scoped>
.detail {
  height: var(--screen-h);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--c-dark-bg);
  color: var(--c-dark-ink);
  position: relative;
}

.missing {
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-size: 14px;
  color: var(--c-dark-ink-mute);
}

.missing-back {
  padding: 8px 20px;
  border: 1px solid var(--c-dark-line);
  border-radius: 18px;
  background: transparent;
  color: var(--c-dark-ink);
  font-size: 13px;
}

.bar {
  position: absolute;
  top: calc(var(--page-top) + 24px);
  left: 16px;
  right: 16px;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.round {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.round-spacer {
  width: 32px;
}

.more {
  position: relative;
}

.more-pop {
  position: absolute;
  top: 40px;
  right: 0;
  min-width: 160px;
  padding: 4px 0;
  border-radius: 10px;
  background: var(--c-card);
  box-shadow: var(--shadow-float);
}

.more-pop button {
  width: 100%;
  padding: 12px 16px;
  border: 0;
  background: transparent;
  text-align: left;
  font-size: 14px;
  color: var(--c-rose);
}

.round svg {
  width: 14px;
  height: 14px;
}

.counter {
  font-size: 11px;
  letter-spacing: 1px;
}

.stage {
  flex: 1;
  min-height: 0;
  padding: calc(var(--page-top) + 84px) 0 16px;
}

/* 資訊區固定貼底；說明太長時在面板內捲動，不把照片擠掉 */
.panel {
  flex-shrink: 0;
  max-height: calc(var(--screen-h) * 0.55);
  overflow-y: auto;
  background: var(--c-bg);
  color: var(--c-ink);
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  padding: 20px 20px calc(var(--safe-bottom) + 32px);
}

.grip {
  display: block;
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--c-line);
  margin: 0 auto 16px;
}

.uploader {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 18px;
  background: var(--c-bg-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-serif);
  font-size: 15px;
}

.who {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.chevron {
  width: 14px;
  height: 14px;
  color: var(--c-ink-mute);
}

.name {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.meta {
  margin: 1px 0 0;
  font-size: 10px;
  letter-spacing: 0.5px;
  color: var(--c-ink-mute);
}

.action {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px;
  border: 0;
  background: transparent;
  color: var(--c-ink);
}

/* 沒按過是空心，按過填滿 */
.heart,
.bookmark {
  width: 20px;
  height: 20px;
  fill: none;
  transition: transform 0.15s;
}

.heart {
  color: var(--c-rose);
}

.bookmark {
  color: var(--c-ink-soft);
}

.heart.on,
.bookmark.on {
  fill: currentColor;
}

.action:active .heart,
.action:active .bookmark {
  transform: scale(0.85);
}

.likes {
  min-width: 1.5em;
  font-size: 12px;
  text-align: left;
}

.action-error {
  margin: -6px 0 10px;
  font-size: 11px;
  color: var(--c-rose);
}

.caption {
  position: relative;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--c-bg-soft);
}

.caption-text {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 14px;
  line-height: 1.7;
  text-align: justify;
  /* 保留說明裡的換行 */
  white-space: pre-line;
}

.caption-edited {
  margin: 6px 0 0;
  font-size: 10px;
  color: var(--c-ink-mute);
  text-align: right;
}

.caption-add {
  width: 100%;
  padding: 12px 0;
  border: 1.5px dashed var(--c-line-strong);
  border-radius: 12px;
  background: transparent;
  font-size: 13px;
  letter-spacing: 1px;
  color: var(--c-ink-soft);
}

.editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--c-bg-soft);
}

.editor-tags {
  margin: 0;
  padding: 0;
  border: 0;
}

.editor-tags legend {
  margin-bottom: 8px;
  padding: 0;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.editor-tag-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

/* 單選用原生 radio 保留可存取性，外觀畫成 chip（同上傳頁） */
.editor-tag {
  padding: 7px 0;
  border-radius: 16px;
  border: 1px solid var(--c-line-strong);
  text-align: center;
  font-size: 13px;
  letter-spacing: 1px;
  color: var(--c-ink-soft);
  cursor: pointer;
}

.editor-tag input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.editor-tag.active {
  border-color: transparent;
  background: var(--c-rose);
  color: #fff;
}

.editor-tag:has(input:focus-visible) {
  outline: 2px solid var(--c-rose-soft);
  outline-offset: 2px;
}

.editor-caption {
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

.editor-caption:focus {
  outline: none;
  border-color: var(--c-rose-soft);
}

.editor-foot {
  margin-top: -6px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

/* 符號按鈕本身有留白，往左拉齊輸入框 */
.editor-marks {
  margin-left: -6px;
}

.editor-counter {
  font-size: 10px;
  color: var(--c-ink-mute);
}

.editor-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

/* 刪除放最左邊，跟儲存離遠一點，不容易誤按 */
.editor-delete {
  margin-right: auto;
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 12px;
  color: var(--c-rose);
}

.editor-cancel,
.editor-save {
  padding: 7px 18px;
  border-radius: 16px;
  font-size: 13px;
  letter-spacing: 1px;
}

.editor-cancel {
  border: 1px solid var(--c-line-strong);
  background: transparent;
  color: var(--c-ink-soft);
}

.editor-save {
  border: 0;
  background: var(--c-rose);
  color: #fff;
}

.editor-actions button:disabled {
  opacity: 0.5;
}

/*
 * 手機橫放：照片（影片）佔滿整個螢幕，上方按鈕與下方面板都浮在照片上，
 * 面板變成半透明的資訊條。點一下照片兩者一起收起來（.immersive），再點一下叫回來。
 * 限定高度 500px 以下，只有橫拿的手機會套用，平板橫放照舊；條件要跟 <script> 裡的 LANDSCAPE 一致。
 * 轉回直式就回到原本的版面，停在同一張（PhotoSwiper 會自己重新對齊）。
 */
@media (orientation: landscape) and (max-height: 500px) {
  .detail {
    background: var(--c-dark-stage);
  }

  /* 瀏海在左右兩側，按鈕要避開 */
  .bar {
    top: calc(var(--safe-top) + 12px);
    left: calc(var(--safe-left) + 16px);
    right: calc(var(--safe-right) + 16px);
  }

  .stage {
    padding: 0;
  }

  .bar,
  .panel {
    transition: opacity 0.2s;
  }

  .immersive .bar,
  .immersive .panel {
    opacity: 0;
    pointer-events: none;
  }

  .panel {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 5;
    max-height: none;
    overflow: visible;
    border-radius: 0;
    background: var(--c-dark-scrim);
    color: var(--c-dark-ink);
    padding: 10px calc(var(--safe-right) + 20px) calc(var(--safe-bottom) + 10px)
      calc(var(--safe-left) + 20px);
  }

  /*
   * 影片點一下是叫出播放控制，不切換；資訊條會蓋住控制列，所以不顯示。
   * 上方按鈕改成播放中收起（.immersive 由 playing 帶出來），暫停就回來
   */
  .is-video .panel {
    display: none;
  }

  /*
   * 資訊條只留上傳者那一列和說明兩行。留言、編輯表單、「為這張說點什麼」都要轉回直式才看得到：
   * 浮在照片上的資訊條放不下，也避免橫放時鍵盤把整個畫面蓋掉。
   * .comments 是 PhotoComments 的根元素，scoped 樣式管得到子元件的根
   */
  .grip,
  .comments,
  .editor,
  .caption-add,
  .caption-edited,
  .portrait-only {
    display: none;
  }

  .uploader {
    margin-bottom: 0;
  }

  .avatar {
    background: var(--c-dark-line);
  }

  .meta,
  .chevron {
    color: var(--c-dark-ink-mute);
  }

  .action,
  .bookmark {
    color: var(--c-dark-ink);
  }

  .action-error {
    margin: 6px 0 0;
  }

  /* 說明只留兩行，完整的要轉回直式看 */
  .caption {
    margin-top: 6px;
    padding: 0;
    background: transparent;
  }

  .caption-text {
    font-size: 13px;
    line-height: 1.6;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    overflow: hidden;
  }
}
</style>
