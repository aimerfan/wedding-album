/**
 * 假資料 —— 只為了讓還沒接上 API 的畫面能照設計稿長出來。
 * 每接上一個畫面就刪掉對應的部分，全部接完後整個資料夾刪掉。
 *
 * 目前還在用的：祝福留言（BlessingsView）、婚紗集（WeddingGalleryView）。
 */
import type { AlbumStats, Blessing, Guest, WeddingCollection } from '@/types/album'

const guests: Record<string, Guest> = {
  kai: { id: 'g2', nickname: '阿凱' },
  ming: { id: 'g4', nickname: '志明' },
  ling: { id: 'g5', nickname: '美玲阿姨' },
  ying: { id: 'g7', nickname: '佳穎' },
}

/** 祝福留言頁標題下的「32 位賓客留下了 47 則祝福」 */
export const stats: AlbumStats = { photoCount: 247, guestCount: 32, blessingCount: 47 }

export const blessings: Blessing[] = [
  {
    id: 'b1',
    guest: guests.kai,
    text: '俊鴻是我大學最好的兄弟，一路看著他追到鈺婷。今天看到你們穿上禮服，眼淚差點掉下來。祝你們白頭偕老！',
    createdAt: '2026-10-17T19:30:00+08:00',
    photoId: 'p2',
  },
  {
    id: 'b2',
    guest: guests.ling,
    text: '從小看著婷婷長大，今天看到她當新娘真的好美。願你們的婚姻甜甜蜜蜜，早生貴子。',
    createdAt: '2026-10-17T19:18:00+08:00',
  },
  { id: 'b3', guest: guests.ming, text: '恭喜恭喜！', createdAt: '2026-10-17T18:52:00+08:00' },
  {
    id: 'b4',
    guest: guests.ying,
    text: '兩個人在一起的樣子真好看。 ♥',
    createdAt: '2026-10-17T18:30:00+08:00',
  },
]

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
