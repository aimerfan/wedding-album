/** 身分相關的 API。見 docs/api.md 的「身分」。 */
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
