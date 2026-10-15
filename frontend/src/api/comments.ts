/** 照片下的留言。見 docs/api.md 的「留言」。 */
import type { Comment } from '@/types/album'
import { api } from './client'

/** 一張照片的所有留言，舊的在前。不分頁 */
export function fetchComments(photoId: string) {
  return api<{ items: Comment[] }>(`/photos/${encodeURIComponent(photoId)}/comments`)
}

export function createComment(photoId: string, text: string) {
  return api<Comment>(`/photos/${encodeURIComponent(photoId)}/comments`, {
    method: 'POST',
    body: { text },
  })
}

export function updateComment(id: string, text: string) {
  return api<Comment>('/comments/' + encodeURIComponent(id), { method: 'PATCH', body: { text } })
}

/** 作者刪自己的；管理員可刪任何一則 */
export function deleteComment(id: string) {
  return api<null>('/comments/' + encodeURIComponent(id), { method: 'DELETE' })
}
