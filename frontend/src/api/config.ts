/** GET /api/config：後端定義的各種上限。見 docs/api.md 的「設定」。 */
import { api } from './client'

export interface AlbumConfig {
  maxPhotoBytes: number
  maxVideoBytes: number
  maxUploadsPerHour: number
  uploadConcurrency: number
  maxBlessingLength: number
  uploadsOpen: boolean
}

let cached: Promise<AlbumConfig> | null = null

/**
 * 同一次開啟只問一次。婚禮當天後端改了設定，賓客重新整理頁面就會拿到新的。
 * 失敗時不快取，下次再試。
 */
export function fetchConfig(): Promise<AlbumConfig> {
  if (!cached) {
    cached = api<AlbumConfig>('/config').catch((e) => {
      cached = null
      throw e
    })
  }
  return cached
}
