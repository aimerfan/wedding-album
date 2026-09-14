/**
 * 相簿領域型別。
 * 後端 API 定案後，這裡會是前後端的共同契約，改動請同步兩邊。
 */

export type GuestId = string
export type PhotoId = string
export type BlessingId = string

/** 賓客。這個 app 不做帳號密碼，賓客只留暱稱。 */
export interface Guest {
  id: GuestId
  nickname: string
  /** 與新人的關係，例如「新娘的大學同學」 */
  relation?: string
}

export type MediaKind = 'photo' | 'video'

/** 相片分類，對應首頁的篩選 chips */
export type PhotoTag = 'welcome' | 'ceremony' | 'banquet'

export interface Photo {
  id: PhotoId
  kind: MediaKind
  /** 原圖網址 */
  url: string
  /** 縮圖網址。列表一律用這個，不要載原圖 */
  thumbnailUrl: string
  width: number
  height: number
  /** 影片長度（秒），kind 為 'video' 時才有 */
  durationSeconds?: number
  uploader: Guest
  /** ISO 8601 */
  uploadedAt: string
  /** ISO 8601，EXIF 取得，可能沒有 */
  takenAt?: string
  /** 上傳時附的祝福語 */
  blessing?: string
  location?: string
  likeCount: number
  /** 目前這位賓客按過讚沒 */
  likedByMe: boolean
  favoritedByMe: boolean
  tags: PhotoTag[]
}

/** 祝福留言。附在照片上的會帶 photoId，留言牆上的獨立留言則沒有。 */
export interface Blessing {
  id: BlessingId
  guest: Guest
  text: string
  /** ISO 8601 */
  createdAt: string
  photoId?: PhotoId
}

/** 婚紗集的一個系列，例如「陽明山外景」。僅供觀賞，不開放下載。 */
export interface WeddingCollection {
  id: string
  title: string
  /** 例如「陽明山 · 2026 春末 · 共 24 張」 */
  caption?: string
  coverUrl: string
  photos: Photo[]
}

/** 首頁頂部的統計數字 */
export interface AlbumStats {
  photoCount: number
  guestCount: number
  blessingCount: number
}

export type UploadStatus = 'pending' | 'uploading' | 'succeeded' | 'failed'

export interface UploadTask {
  /** 前端自己產生的暫時 id，上傳成功後才會拿到伺服器的 PhotoId */
  localId: string
  file: File
  status: UploadStatus
  /** 0–100 */
  progress: number
  errorMessage?: string
  photoId?: PhotoId
}

/** 上傳流程第二步（寫祝福）收集到的設定 */
export interface UploadDraft {
  blessing: string
  /** 允許其他賓客看到 */
  visibleToGuests: boolean
  /** 附加拍攝位置 */
  attachLocation: boolean
}
