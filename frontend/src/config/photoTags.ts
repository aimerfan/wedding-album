import type { PhotoTag } from '@/types/album'

/** 照片分類，順序跟首頁的篩選 chips 一致。上傳頁與照片詳情改分類時共用 */
export const PHOTO_TAGS: { id: PhotoTag; label: string }[] = [
  { id: 'engagement', label: '訂婚・迎娶' },
  { id: 'banquet', label: '宴客' },
  { id: 'candid', label: '花絮' },
  { id: 'throwback', label: '那些年' },
]

export function tagLabel(tag: PhotoTag): string {
  return PHOTO_TAGS.find((t) => t.id === tag)?.label ?? tag
}
