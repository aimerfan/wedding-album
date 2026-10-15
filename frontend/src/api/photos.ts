/** 相簿相關的 API。見 docs/api.md 的「相簿」。 */
import type { AlbumStats, Page, Photo, PhotoTag } from '@/types/album'
import { api } from './client'

/** GET /api/photos 的篩選條件，都可以不帶 */
export interface PhotoFilter {
  tag?: PhotoTag
  kind?: 'photo' | 'video'
  date?: 'today'
  /** 'me' 或某位賓客的 id */
  uploader?: string
  /** 只列我收藏的（「我的 → 收藏」） */
  favorited?: 'true'
}

export function fetchPhotos(filter: PhotoFilter, cursor?: string | null, limit = 30) {
  return api<Page<Photo>>('/photos', {
    query: { ...filter, cursor: cursor ?? undefined, limit },
  })
}

export function fetchPhoto(id: string) {
  return api<Photo>('/photos/' + encodeURIComponent(id))
}

export function fetchStats() {
  return api<AlbumStats>('/stats')
}

const photoPath = (id: string, action: string) => `/photos/${encodeURIComponent(id)}/${action}`

/** 按讚 / 收回讚。用 PUT / DELETE，重複按、網路重送都安全。回傳更新後的照片 */
export function setLiked(id: string, liked: boolean) {
  return api<Photo>(photoPath(id, 'like'), { method: liked ? 'PUT' : 'DELETE' })
}

/** 收藏 / 取消收藏。收藏是私人的，只有自己看得到 */
export function setFavorited(id: string, favorited: boolean) {
  return api<Photo>(photoPath(id, 'favorite'), { method: favorited ? 'PUT' : 'DELETE' })
}

/** 改分類或說明，沒帶的欄位不變。caption 傳 null 是刪掉說明。回傳更新後的照片 */
export function editPhoto(id: string, changes: { tag?: PhotoTag; caption?: string | null }) {
  return api<Photo>('/photos/' + encodeURIComponent(id), { method: 'PATCH', body: changes })
}

/** 刪除照片：上傳者刪自己的，管理員可刪任何一張 */
export function deletePhoto(id: string) {
  return api<null>('/photos/' + encodeURIComponent(id), { method: 'DELETE' })
}
