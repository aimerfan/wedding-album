/** 身分相關的 API。見 docs/api.md 的「身分」。 */
import { session, setGuestId, setProfile } from '@/stores/session'
import type { Guest } from '@/types/album'
import { api } from './client'

export interface JoinResult {
  token: string
  guest: Guest
}

export function joinAlbum(eventCode: string, nickname: string, relation: string) {
  return api<JoinResult>('/guests', {
    method: 'POST',
    body: { eventCode, nickname, relation },
  })
}

export function updateMe(nickname: string, relation: string) {
  // relation 傳空字串代表清除
  return api<{ guest: Guest }>('/me', { method: 'PATCH', body: { nickname, relation } })
}

export interface MyStats {
  uploaded: number
  favorited: number
  likesReceived: number
  blessings: number
}

export function fetchMe() {
  return api<{ guest: Guest; stats: MyStats }>('/me')
}

/**
 * 確定手機上記得自己的賓客 id。這個功能加上之前就已經加入的賓客沒有存 id，
 * 問一次後端補上。已經有了就什麼都不做。
 */
export async function ensureGuestId() {
  if (!session.token || session.guestId) return
  const me = await fetchMe()
  setGuestId(me.guest.id)
  setProfile(me.guest.nickname, me.guest.relation ?? '')
}

/** 產生接續碼。完整連結由前端組：前後端可能不同網域，後端不知道前端的網址 */
export function createTransferCode() {
  return api<{ code: string; expiresAt: string }>('/me/transfer-codes', { method: 'POST' })
}

/** 在這個裝置用接續碼換一組新的 token。原本的裝置不會被登出 */
export function claimTransferCode(code: string) {
  return api<JoinResult>('/guests/claim', { method: 'POST', body: { transferCode: code } })
}
