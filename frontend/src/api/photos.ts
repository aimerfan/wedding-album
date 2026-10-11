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
