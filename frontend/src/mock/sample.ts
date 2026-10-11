/**
 * 假資料 —— 只為了讓還沒接上 API 的畫面能照設計稿長出來。
 * 每接上一個畫面就刪掉對應的部分，全部接完後整個資料夾刪掉。
 *
 * 目前還在用的：婚紗集（WeddingGalleryView）。
 */
import type { WeddingCollection } from '@/types/album'

export const weddingCollections: WeddingCollection[] = [
  {
    id: 'w1',
    title: '陽明山外景',
    caption: '陽明山 · 2026 春末 · 共 24 張',
    coverUrl: '',
    photos: [],
  },
  { id: 'w2', title: '棚拍經典', coverUrl: '', photos: [] },
  { id: 'w3', title: '海邊夕陽', coverUrl: '', photos: [] },
]
