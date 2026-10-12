/** GET /api/config：後端定義的各種上限。見 docs/api.md 的「設定」。 */
import { api } from './client'

export interface AlbumConfig {
  maxPhotoBytes: number
  maxVideoBytes: number
  maxUploadsPerHour: number
  uploadConcurrency: number
  maxBlessingLength: number
  uploadsOpen: boolean
  /** 管理員設定的 Kahoot! 連結，沒設是 null */
  kahootUrl: string | null
}

let cached: Promise<AlbumConfig> | null = null

/**
 * 同一次開啟只問一次。婚禮當天後端改了設定，賓客重新整理頁面就會拿到新的。
 * fresh 為 true 時重新問一次（例如 Kahoot! 連結隨時可能被管理員改）。失敗時不快取，下次再試。
 */
export function fetchConfig(fresh = false): Promise<AlbumConfig> {
  if (!cached || fresh) {
    cached = api<AlbumConfig>('/config').catch((e) => {
      cached = null
      throw e
    })
  }
  return cached
}

/** 管理員設定 Kahoot! 連結；傳空字串代表拿掉 */
export function setKahootUrl(url: string) {
  return api<{ kahootUrl: string | null }>('/settings/kahoot', { method: 'PUT', body: { url } })
}
