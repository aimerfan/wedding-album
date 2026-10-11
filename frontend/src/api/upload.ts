/**
 * 上傳照片：POST /api/photos，一個請求一個檔案。見 docs/api.md 的「上傳」。
 *
 * 用 XMLHttpRequest 而不是 fetch：fetch 拿不到上傳進度，每張照片就沒辦法有自己的進度條。
 */
import { session } from '@/stores/session'
import type { Photo, PhotoTag } from '@/types/album'
import { ApiError, toApiError } from './client'

export function uploadPhoto(
  file: File,
  tag: PhotoTag,
  /** 0–100 */
  onProgress: (percent: number) => void,
): Promise<Photo> {
  return new Promise((resolve, reject) => {
    const form = new FormData()
    form.append('file', file)
    form.append('tag', tag)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', '/api/photos')
    if (session.token) xhr.setRequestHeader('Authorization', 'Bearer ' + session.token)
    xhr.responseType = 'json'

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve(xhr.response as Photo)
      else reject(toApiError(xhr.status, xhr.response))
    }
    xhr.onerror = () => reject(new ApiError(0, 'network_error', '網路連線不穩，請稍後再試'))

    xhr.send(form)
  })
}
