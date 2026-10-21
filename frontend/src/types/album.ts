/**
 * 相簿領域型別，對應 docs/api.md 的「資料形狀」。規格改了這裡要跟著改。
 */

export type GuestId = string
export type PhotoId = string
export type BlessingId = string
export type CommentId = string

/** 賓客。這個 app 不做帳號密碼，賓客只留暱稱。 */
export interface Guest {
  id: GuestId
  nickname: string
  /** 與新人的關係，例如「新娘的大學同學」 */
  relation?: string
}

export type MediaKind = 'photo' | 'video'

/** 相片分類，對應首頁的篩選 chips */
export type PhotoTag = 'engagement' | 'banquet' | 'candid' | 'throwback'

export interface Photo {
  id: PhotoId
  kind: MediaKind
  /**
   * 原檔網址。照片可能是 HEIC，只用在下載與匯出，不要拿來顯示；
   * 影片則是拿來播放的檔案（MP4 或 MOV，不轉檔）
   */
  url: string
  /** 長邊 1600px 的 JPEG（影片是封面）。照片詳情等放大檢視用這個 */
  displayUrl: string
  /** 長邊 480px 的 JPEG（影片是封面）。列表一律用這個 */
  thumbnailUrl: string
  width: number
  height: number
  /** 影片長度（秒，到小數一位），kind 為 'video' 時才有 */
  durationSeconds?: number | null
  uploader: Guest
  /** ISO 8601 */
  uploadedAt: string
  /** ISO 8601，EXIF 取得，可能沒有 */
  takenAt?: string | null
  likeCount: number
  /** 照片下的留言數 */
  commentCount: number
  /** 目前這位賓客按過讚沒 */
  likedByMe: boolean
  favoritedByMe: boolean
  tag: PhotoTag
  /** 只給新人看：只有上傳者與管理員（新人與家人）看得到，不出現在相簿裡 */
  private: boolean
  /** 上傳者對這張照片的說明，選填 */
  caption: string | null
  /** 說明最後一次修改的時間，沒改過是 null。用來標示「已編輯」 */
  captionEditedAt: string | null
}

/** 列表類 API 的分頁回應，見 docs/api.md 的「分頁」 */
export interface Page<T> {
  items: T[]
  nextCursor: string | null
}

/** 照片下的留言。任何賓客都能留；照片上的文字（caption）是上傳者寫的，不是留言 */
export interface Comment {
  id: CommentId
  photoId: PhotoId
  guest: Guest
  text: string
  /** ISO 8601 */
  createdAt: string
  /** 最後一次修改的時間，沒改過是 null。用來標示「已編輯」 */
  editedAt: string | null
}

/** 留言牆上的祝福。照片上的文字是 Photo.caption，不是祝福 */
export interface Blessing {
  id: BlessingId
  guest: Guest
  text: string
  /** ISO 8601 */
  createdAt: string
  /** 最後一次修改的時間，沒改過是 null。用來標示「已編輯」 */
  editedAt?: string | null
}

/**
 * 婚紗照。新人自己的照片，婚紗集不分系列，就是一串。
 * 僅供觀賞：只有顯示用與縮圖，沒有原檔網址、上傳者與讚。
 */
export interface WeddingPhoto {
  id: string
  displayUrl: string
  thumbnailUrl: string
  width: number
  height: number
}

/** PhotoTile 顯示一張圖需要的欄位，賓客照片與婚紗照都符合。影片會多一個角標 */
export type TileImage = Pick<Photo, 'displayUrl' | 'thumbnailUrl'> &
  Partial<Pick<Photo, 'kind' | 'durationSeconds' | 'caption' | 'private'>>

/** 首頁頂部的統計數字 */
export interface AlbumStats {
  photoCount: number
  guestCount: number
  blessingCount: number
  /** 留過祝福的人數（含預先匯入的），留言牆標題用 */
  blessingGuestCount: number
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

/** 上傳流程第二步（分類與說明）收集到的設定。key 都是 PickedMedia.id */
export interface UploadDraft {
  /** 這批照片預設是哪個環節拍的。多數賓客只參加宴客，預設 'banquet' */
  tag: PhotoTag
  /** 個別改過分類的；沒有的就跟著預設 */
  tags: Record<string, PhotoTag>
  /** 這批照片預設是不是只給新人看。預設公開 */
  private: boolean
  /** 個別改過公開與否的；沒有的就跟著預設 */
  privates: Record<string, boolean>
  /** 每張的說明，選填 */
  captions: Record<string, string>
}
