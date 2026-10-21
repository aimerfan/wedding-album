/** 身分相關的 API。見 docs/api.md 的「身分」。 */
import { invalidateAll } from '@/stores/photoLists'
import { session, setAdmin, setGuestId, setProfile, setToken } from '@/stores/session'
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
  return api<{ guest: Guest; isAdmin: boolean; stats: MyStats }>('/me')
}

/**
 * 確定手機上記得自己的賓客 id。這個功能加上之前就已經加入的賓客沒有存 id，
 * 問一次後端補上。已經有了就什麼都不做。
 */
export async function ensureGuestId() {
  if (!session.token || session.guestId) return
  const me = await fetchMe()
  setGuestId(me.guest.id)
  setAdmin(me.isAdmin)
  setProfile(me.guest.nickname, me.guest.relation ?? '')
}

/** 產生接續碼。完整連結由前端組：前後端可能不同網域，後端不知道前端的網址 */
export function createTransferCode() {
  return api<{ code: string; expiresAt: string }>('/me/transfer-codes', { method: 'POST' })
}

/** 管理員替別人產生接續碼：對方原本的裝置不見了，自己產生不了時用 */
export function createTransferCodeFor(guestId: string) {
  return api<{ code: string; expiresAt: string }>(
    `/guests/${encodeURIComponent(guestId)}/transfer-codes`,
    { method: 'POST' },
  )
}

/** 在這個裝置用接續碼換一組新的 token。原本的裝置不會被登出 */
export function claimTransferCode(code: string) {
  return api<JoinResult>('/guests/claim', { method: 'POST', body: { transferCode: code } })
}

/** 用管理員代碼把自己開通成管理員（/admin?code=…） */
export function becomeAdmin(code: string) {
  return api<{ guest: Guest; isAdmin: boolean }>('/me/admin', {
    method: 'POST',
    body: { adminCode: code },
  })
}

/**
 * 用接續碼換成那位賓客：/continue 連結與歡迎頁的「輸入接續碼」共用。
 * 失敗時丟出 ApiError，呼叫的地方自己顯示訊息。
 */
export async function signInWithTransferCode(code: string) {
  const { token, guest } = await claimTransferCode(code)
  setToken(token)
  setGuestId(guest.id)
  // 換了身分，管理員狀態不能沿用；新身分若是管理員，進「我的」頁時會從後端補上
  setAdmin(false)
  setProfile(guest.nickname, guest.relation ?? '')
  // 之前快取的「我上傳的」「收藏」都不再是自己的
  invalidateAll()
  return guest
}
