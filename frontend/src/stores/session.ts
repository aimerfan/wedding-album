import { reactive } from 'vue'
import type { UploadDraft } from '@/types/album'

/**
 * 跨頁共用的一點點狀態。目前只有「賓客暱稱」與「上傳流程」兩件事，
 * 用 reactive 就夠了，還不需要 Pinia。之後狀態變複雜再換。
 */

const NICKNAME_KEY = 'wedding-album:nickname'

function readNickname(): string {
  try {
    return localStorage.getItem(NICKNAME_KEY) ?? ''
  } catch {
    // 無痕模式或封鎖 site data 時 localStorage 會直接 throw
    return ''
  }
}

export const session = reactive({
  /** 賓客自己輸入的暱稱，這個 app 沒有帳號密碼 */
  nickname: readNickname(),
})

export function setNickname(name: string) {
  session.nickname = name
  try {
    localStorage.setItem(NICKNAME_KEY, name)
  } catch {
    // 存不進去也無所謂，只是下次要重打
  }
}

/** 使用者從系統選取器挑到的檔案 */
export interface PickedMedia {
  id: string
  file: File
  /** createObjectURL 產生的預覽網址，用完要 revoke */
  previewUrl: string
  isVideo: boolean
}

/**
 * 上傳流程：選照片（第一步）→ 寫祝福（第二步）。
 * 檔案放在這裡而不是各自的元件裡，否則離開選擇頁時 object URL 會被回收，
 * 第二步就拿不到預覽了。
 */
export const uploadFlow = reactive({
  picked: [] as PickedMedia[],
  selectedIds: [] as string[],
  draft: {
    blessing: '',
    visibleToGuests: true,
    attachLocation: false,
  } as UploadDraft,
})

function revokePicked() {
  for (const p of uploadFlow.picked) URL.revokeObjectURL(p.previewUrl)
}

export function setPicked(items: PickedMedia[]) {
  revokePicked()
  uploadFlow.picked = items
}

export function resetUploadFlow() {
  revokePicked()
  uploadFlow.picked = []
  uploadFlow.selectedIds = []
  uploadFlow.draft = { blessing: '', visibleToGuests: true, attachLocation: false }
}
