import { reactive } from 'vue'
import type { AlbumConfig } from '@/api/config'
import type { MediaKind, PhotoTag, UploadDraft } from '@/types/album'

/**
 * 跨頁共用的一點點狀態。目前只有「賓客資料」與「上傳流程」兩件事，
 * 用 reactive 就夠了，還不需要 Pinia。之後狀態變複雜再換。
 */

const NICKNAME_KEY = 'wedding-album:nickname'
const RELATION_KEY = 'wedding-album:relation'
const TOKEN_KEY = 'wedding-album:token'
const GUEST_ID_KEY = 'wedding-album:guest-id'
const ADMIN_KEY = 'wedding-album:admin'
const EVENT_CODE_KEY = 'wedding-album:event-code'

function read(key: string): string {
  try {
    return localStorage.getItem(key) ?? ''
  } catch {
    // 無痕模式或封鎖 site data 時 localStorage 會直接 throw
    return ''
  }
}

function write(key: string, value: string) {
  try {
    if (value) localStorage.setItem(key, value)
    else localStorage.removeItem(key)
  } catch {
    // 存不進去也無所謂，只是下次要重新加入
  }
}

/**
 * 活動碼來自會場 QR code 的網址（?code=...），第一次打開時記下來，之後加入相簿要用。
 * 開發時沒有 QR code，用後端開發模式的預設值 "dev"。
 * /admin?code= 是管理員代碼，不是活動碼，不能記下來。
 *
 * 還沒加入的人會被導到 /welcome?redirect=/?code=...，活動碼包在 redirect 裡。
 * iPhone 加到主畫面時可能用的是這個網址，所以 redirect 裡的也要認得。
 * 規則要跟 index.html 裡挑 manifest 的那段一致。
 */
function codeFromUrl(path: string, search: string): string | null {
  if (path === '/admin') return null
  const params = new URLSearchParams(search)
  const code = params.get('code')
  if (code) return code
  const redirect = params.get('redirect') ?? ''
  if (!redirect.startsWith('/') || redirect.startsWith('//')) return null
  const inner = new URL(redirect, window.location.origin)
  return codeFromUrl(inner.pathname, inner.search)
}

function initialEventCode(): string {
  const fromUrl = codeFromUrl(window.location.pathname, window.location.search)
  if (fromUrl) {
    write(EVENT_CODE_KEY, fromUrl)
    return fromUrl
  }
  return read(EVENT_CODE_KEY) || (import.meta.env.DEV ? 'dev' : '')
}

export const session = reactive({
  /** 後端發的身分代號。有它才算加入了相簿，見 docs/api.md 的「身分」 */
  token: read(TOKEN_KEY),
  /** 自己的賓客 id，用來判斷哪些祝福是自己寫的（才顯示修改、刪除） */
  guestId: read(GUEST_ID_KEY),
  /** 管理員可以刪除任何照片與祝福。以後端 /api/me 的 isAdmin 為準，這裡只是記一份 */
  isAdmin: read(ADMIN_KEY) === '1',
  eventCode: initialEventCode(),
  /** 賓客自己輸入的暱稱，這個 app 沒有帳號密碼 */
  nickname: read(NICKNAME_KEY),
  /** 與新人的關係，選填，例如「新娘的大學同學」 */
  relation: read(RELATION_KEY),
})

/** 暱稱與關係以後端回傳的為準，這裡只是存一份在手機上，畫面不必每次都問後端 */
export function setProfile(nickname: string, relation: string) {
  session.nickname = nickname
  session.relation = relation
  write(NICKNAME_KEY, nickname)
  write(RELATION_KEY, relation)
}

export function setToken(token: string) {
  session.token = token
  write(TOKEN_KEY, token)
}

export function setGuestId(id: string) {
  session.guestId = id
  write(GUEST_ID_KEY, id)
}

export function setAdmin(isAdmin: boolean) {
  session.isAdmin = isAdmin
  write(ADMIN_KEY, isAdmin ? '1' : '')
}

/** token 失效時清掉身分。暱稱留著，重新加入時歡迎頁可以直接帶入 */
export function clearToken() {
  session.token = ''
  session.guestId = ''
  session.isAdmin = false
  write(TOKEN_KEY, '')
  write(GUEST_ID_KEY, '')
  write(ADMIN_KEY, '')
}

/** 使用者從系統選取器挑到的檔案 */
export interface PickedMedia {
  id: string
  file: File
  kind: MediaKind
  /** createObjectURL 產生的預覽網址，用完要 revoke */
  previewUrl: string
}

/**
 * 只用來決定預覽怎麼畫、套哪個上限；真正是照片還是影片由後端看檔案內容判斷。
 * 有些 Android 的選取器不給 type，再看副檔名。
 */
export function kindOf(file: File): MediaKind {
  if (file.type.startsWith('video/')) return 'video'
  return /\.(mov|mp4|m4v)$/i.test(file.name) ? 'video' : 'photo'
}

/** 「3 張照片、1 支影片」。只有一種時只說那一種 */
export function describeMedia(items: { kind: MediaKind }[]): string {
  const videos = items.filter((m) => m.kind === 'video').length
  const photos = items.length - videos
  return [photos && `${photos} 張照片`, videos && `${videos} 支影片`].filter(Boolean).join('、')
}

/** 檔案太大傳不了時，給賓客一條出路：之後再私下給新人 */
export const TOO_LARGE_HINT = '可以等婚禮過後再分享給新人唷 ♥'

/**
 * 超過單檔上限時要顯示的原因，沒超過回傳空字串。選取頁與上傳頁共用，
 * 文字跟後端的 file_too_large 一致。
 */
export function sizeProblem(
  item: { kind: MediaKind; file: File },
  limits: Pick<AlbumConfig, 'maxPhotoBytes' | 'maxVideoBytes'>,
): string {
  const isVideo = item.kind === 'video'
  const limit = isVideo ? limits.maxVideoBytes : limits.maxPhotoBytes
  if (item.file.size <= limit) return ''
  const mb = Math.floor(limit / 1024 / 1024)
  return `${isVideo ? '影片' : '照片'}太大了，單檔上限 ${mb} MB，${TOO_LARGE_HINT}`
}

/**
 * 上傳流程：選照片（第一步）→ 分類與想說的話（第二步）。
 * 檔案放在這裡而不是各自的元件裡，否則離開選擇頁時 object URL 會被回收，
 * 第二步就拿不到預覽了。
 */
export const uploadFlow = reactive({
  picked: [] as PickedMedia[],
  selectedIds: [] as string[],
  draft: emptyDraft(),
  /** 剛傳完一批、還有沒傳的回到選取頁時，告訴賓客剛剛傳了什麼（例如「3 張照片」）。顯示過就清掉 */
  uploadedSummary: '',
})

function emptyDraft(): UploadDraft {
  return { tag: 'banquet', tags: {}, captions: {} }
}

function revokePicked() {
  for (const p of uploadFlow.picked) URL.revokeObjectURL(p.previewUrl)
}

/** 每個選到的檔案一個 id。不用檔名：同一批裡可能有同名的檔案 */
let pickedSeq = 0

/**
 * 不比 lastModified：有些手機每次叫出選取器都會重新產生檔案，同一張照片的時間會不一樣。
 * 檔名與大小都相同的兩張不同照片幾乎不會出現
 */
function isSameFile(a: File, b: File) {
  return a.name === b.name && a.size === b.size
}

/** 選取器選完（含「再選」）：接在已選的後面，同一個檔案選第二次就略過。回傳實際加進來的 */
export function addPicked(files: File[]): PickedMedia[] {
  const added = files
    .filter((file) => !uploadFlow.picked.some((p) => isSameFile(p.file, file)))
    .map((file) => ({
      id: `m${++pickedSeq}`,
      file,
      kind: kindOf(file),
      previewUrl: URL.createObjectURL(file),
    }))
  uploadFlow.picked = [...uploadFlow.picked, ...added]
  return added
}

/** 上傳頁拿掉的那一個，按「復原」時連同位置、寫好的文字與分類放回去 */
export interface RemovedPick {
  item: PickedMedia
  pickedIndex: number
  selectedIndex: number
  tag?: PhotoTag
  caption?: string
}

/**
 * 上傳頁按「✕」拿掉一個選錯的：整個從待選區移除，不只是取消勾選，
 * 不然傳完這批會被當成「還沒傳的」，又回到選取頁。
 * 預覽網址先不回收，復原時還要用；確定不復原時交給 discardRemoved
 */
export function removePicked(id: string): RemovedPick | null {
  const pickedIndex = uploadFlow.picked.findIndex((p) => p.id === id)
  if (pickedIndex < 0) return null
  const { tags, captions } = uploadFlow.draft
  const removed: RemovedPick = {
    item: uploadFlow.picked[pickedIndex]!,
    pickedIndex,
    selectedIndex: uploadFlow.selectedIds.indexOf(id),
    tag: tags[id],
    caption: captions[id],
  }
  uploadFlow.picked = uploadFlow.picked.filter((p) => p.id !== id)
  uploadFlow.selectedIds = uploadFlow.selectedIds.filter((x) => x !== id)
  delete tags[id]
  delete captions[id]
  return removed
}

export function restoreRemoved({ item, pickedIndex, selectedIndex, tag, caption }: RemovedPick) {
  const picked = [...uploadFlow.picked]
  picked.splice(pickedIndex, 0, item)
  uploadFlow.picked = picked
  if (selectedIndex >= 0) {
    const selected = [...uploadFlow.selectedIds]
    selected.splice(selectedIndex, 0, item.id)
    uploadFlow.selectedIds = selected
  }
  if (tag) uploadFlow.draft.tags[item.id] = tag
  if (caption !== undefined) uploadFlow.draft.captions[item.id] = caption
}

export function discardRemoved(removed: RemovedPick) {
  URL.revokeObjectURL(removed.item.previewUrl)
}

/** 清空待選區時拿走的內容，按「復原」時放回去 */
export interface PickedSnapshot {
  picked: PickedMedia[]
  selectedIds: string[]
}

/** 清空待選區。預覽網址先不回收，復原時還要用；確定不復原時交給 discardPicked */
export function takePicked(): PickedSnapshot {
  const snapshot = { picked: uploadFlow.picked, selectedIds: uploadFlow.selectedIds }
  uploadFlow.picked = []
  uploadFlow.selectedIds = []
  return snapshot
}

export function restorePicked(snapshot: PickedSnapshot) {
  uploadFlow.picked = snapshot.picked
  uploadFlow.selectedIds = snapshot.selectedIds
}

export function discardPicked(snapshot: PickedSnapshot) {
  for (const p of snapshot.picked) URL.revokeObjectURL(p.previewUrl)
}

/**
 * 一批傳完：拿掉傳好的與傳不了的（太大），沒勾的留在待選區給下一批，並預設勾起前 limit 個。
 * 預設分類留著，同一次多半是同一類；留下來的那些已經寫好的說明、分類也留著。回傳還剩幾個
 */
export function finishBatch(canUpload: (item: PickedMedia) => boolean, limit: number): number {
  const sent = new Set(uploadFlow.selectedIds)
  const keep = uploadFlow.picked.filter((p) => !sent.has(p.id) && canUpload(p))
  for (const p of uploadFlow.picked) if (!keep.includes(p)) URL.revokeObjectURL(p.previewUrl)

  uploadFlow.uploadedSummary = describeMedia(uploadFlow.picked.filter((p) => sent.has(p.id)))
  uploadFlow.picked = keep
  uploadFlow.selectedIds = keep.slice(0, limit).map((p) => p.id)
  const ids = new Set(keep.map((p) => p.id))
  const only = <T>(record: Record<string, T>) =>
    Object.fromEntries(Object.entries(record).filter(([id]) => ids.has(id)))
  uploadFlow.draft = {
    tag: uploadFlow.draft.tag,
    tags: only(uploadFlow.draft.tags),
    captions: only(uploadFlow.draft.captions),
  }
  return keep.length
}

export function resetUploadFlow() {
  revokePicked()
  uploadFlow.picked = []
  uploadFlow.selectedIds = []
  uploadFlow.draft = emptyDraft()
  uploadFlow.uploadedSummary = ''
}
