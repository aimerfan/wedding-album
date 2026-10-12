/** 婚紗集的 API。見 docs/api.md 的「婚紗集」。 */
import type { WeddingPhoto } from '@/types/album'
import { api } from './client'

/** 所有婚紗照，依匯入時的檔名排好。只有幾十張，一次全部回傳、不分頁 */
export function fetchWeddingPhotos() {
  return api<{ items: WeddingPhoto[] }>('/wedding-photos')
}
