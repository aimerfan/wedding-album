/**
 * 假資料 —— 只為了讓畫面能照設計稿長出來。
 * 後端 API 接上後整個資料夾刪掉。
 *
 * 相片的 url / thumbnailUrl 刻意留空字串，PhotoTile 會退回設計稿的漸層佔位圖，
 * 等真的有圖再填。
 */
import type { AlbumStats, Blessing, Guest, Photo, WeddingCollection } from '@/types/album'

const guests: Record<string, Guest> = {
  hui: { id: 'g1', nickname: '小慧', relation: '新娘的大學同學' },
  kai: { id: 'g2', nickname: '阿凱' },
  ting: { id: 'g3', nickname: '婷婷' },
  ming: { id: 'g4', nickname: '志明' },
  ling: { id: 'g5', nickname: '美玲阿姨' },
  hong: { id: 'g6', nickname: '建宏' },
  ying: { id: 'g7', nickname: '佳穎' },
  hao: { id: 'g8', nickname: '俊豪' },
}

/** 目前登入（輸入暱稱）的賓客 */
export const currentGuest = guests.hui

function photo(
  id: string,
  uploader: Guest,
  width: number,
  height: number,
  extra: Partial<Photo> = {},
): Photo {
  return {
    id,
    kind: 'photo',
    url: '',
    thumbnailUrl: '',
    width,
    height,
    uploader,
    uploadedAt: '2026-10-17T18:42:00+08:00',
    likeCount: 0,
    likedByMe: false,
    favoritedByMe: false,
    tags: ['banquet'],
    ...extra,
  }
}

export const feedPhotos: Photo[] = [
  photo('p1', guests.hui, 3, 4, { tags: ['welcome'] }),
  photo('p2', guests.kai, 4, 5, {
    likeCount: 12,
    location: '婚宴會館',
    blessing:
      '俊鴻是我大學最好的兄弟，一路看著他追到鈺婷。今天看到你們穿上禮服，眼淚差點掉下來。祝你們白頭偕老！',
  }),
  photo('p3', guests.ting, 1, 1, { tags: ['ceremony'] }),
  photo('p4', guests.ming, 4, 3, { tags: ['ceremony'] }),
  photo('p5', guests.ling, 3, 4, { kind: 'video', durationSeconds: 24 }),
  photo('p6', guests.hong, 4, 5),
  photo('p7', guests.ying, 1, 1),
  photo('p8', guests.hao, 3, 4),
]

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

/** 我的個人頁：我上傳的照片 */
export const myPhotos: Photo[] = [
  photo('m1', currentGuest, 1, 1),
  photo('m2', currentGuest, 1, 1),
  photo('m3', currentGuest, 1, 1),
  photo('m4', currentGuest, 1, 1),
  photo('m5', currentGuest, 1, 1),
  photo('m6', currentGuest, 1, 1),
]

export const myStats = { uploaded: 12, favorited: 8, likesReceived: 24, blessings: 1 }
