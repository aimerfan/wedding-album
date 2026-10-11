/** 祝福留言的 API。見 docs/api.md 的「祝福」。 */
import type { Blessing, Page } from '@/types/album'
import { api } from './client'

export interface BlessingFilter {
  /** 只列自己的（「我的 → 我的祝福」） */
  guest?: 'me'
}

export function fetchBlessings(filter: BlessingFilter, cursor?: string | null, limit = 30) {
  return api<Page<Blessing>>('/blessings', {
    query: { ...filter, cursor: cursor ?? undefined, limit },
  })
}

/** photoId 只能是自己上傳的照片；不帶就是留言牆上的獨立祝福 */
export function createBlessing(text: string, photoId?: string) {
  return api<Blessing>('/blessings', { method: 'POST', body: { text, photoId } })
}

export function updateBlessing(id: string, text: string) {
  return api<Blessing>('/blessings/' + encodeURIComponent(id), {
    method: 'PATCH',
    body: { text },
  })
}

export function deleteBlessing(id: string) {
  return api<null>('/blessings/' + encodeURIComponent(id), { method: 'DELETE' })
}
