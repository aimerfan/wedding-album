import { reactive } from 'vue'
import { ApiError } from '@/api/client'
import { fetchPhotos, type PhotoFilter } from '@/api/photos'
import type { Photo, PhotoTag } from '@/types/album'

/**
 * 依篩選條件快取的照片列表。
 *
 * 首頁、賓客照片頁、「我的」各自載入一串照片；點進照片詳情後要在「同一串」裡左右滑，
 * 所以列表放在這裡共用，詳情頁用同樣的篩選條件拿到同一份，滑到尾端時接著往下載。
 * 回到列表頁時資料還在，不必重新載入。
 */
export interface PhotoList {
  items: Photo[]
  nextCursor: string | null
  /** 已經載過第一頁 */
  loaded: boolean
  /** 沒有下一頁了 */
  done: boolean
  loading: boolean
  error: string
  /** 內容已經過時（例如收藏有變），下次顯示時要從頭重新載入 */
  stale: boolean
}

const lists = new Map<string, { state: PhotoList; filter: PhotoFilter }>()

/** 篩選條件 → 快取的 key。欄位排序固定，同樣的條件一定得到同一個 key */
function keyOf(filter: PhotoFilter): string {
  return (Object.keys(filter) as (keyof PhotoFilter)[])
    .filter((k) => filter[k])
    .sort()
    .map((k) => `${k}=${filter[k]}`)
    .join('&')
}

function entry(filter: PhotoFilter) {
  const key = keyOf(filter)
  let found = lists.get(key)
  if (!found) {
    found = {
      filter,
      state: reactive<PhotoList>({
        items: [],
        nextCursor: null,
        loaded: false,
        done: false,
        loading: false,
        error: '',
        stale: false,
      }),
    }
    lists.set(key, found)
  }
  return found
}

export function getPhotoList(filter: PhotoFilter): PhotoList {
  return entry(filter).state
}

/** 載入下一頁。正在載入或已經沒有下一頁時什麼都不做，可以放心重複呼叫 */
export async function loadMore(filter: PhotoFilter) {
  const { state } = entry(filter)
  if (state.loading || state.done) return

  state.loading = true
  state.error = ''
  try {
    const page = await fetchPhotos(filter, state.nextCursor)
    // 保險：同一張不要出現兩次（例如重新整理與載入下一頁同時發生）
    const seen = new Set(state.items.map((p) => p.id))
    state.items.push(...page.items.filter((p) => !seen.has(p.id)))
    state.nextCursor = page.nextCursor
    state.done = page.nextCursor === null
    state.loaded = true
  } catch (e) {
    state.error = e instanceof ApiError ? e.message : '載入失敗，請稍後再試'
  } finally {
    state.loading = false
  }
}

/** 第一次進來才載入；之前載過就沿用，回到列表時不會閃一下又重來。過時了才重新載入 */
export function ensureLoaded(filter: PhotoFilter) {
  const { state } = entry(filter)
  if (state.stale) return reload(filter)
  if (!state.loaded) return loadMore(filter)
}

/** 從頭重新載入，例如上傳完照片之後 */
export async function reload(filter: PhotoFilter) {
  const { state } = entry(filter)
  state.items = []
  state.nextCursor = null
  state.loaded = false
  state.done = false
  state.stale = false
  await loadMore(filter)
}

/**
 * 網址 query ⇄ 篩選條件。從列表點進照片詳情時把條件帶在網址上（例如 ?uploader=me），
 * 詳情頁才知道要在哪一串照片裡左右滑；重新整理或分享連結時也不會遺失。
 */
const TAGS: PhotoTag[] = ['engagement', 'welcome', 'ceremony', 'banquet']

export function filterFromQuery(query: Record<string, unknown>): PhotoFilter {
  const pick = (k: string) => (typeof query[k] === 'string' ? (query[k] as string) : undefined)
  const filter: PhotoFilter = {}
  const tag = pick('tag')
  if (tag && (TAGS as string[]).includes(tag)) filter.tag = tag as PhotoTag
  if (pick('kind') === 'video' || pick('kind') === 'photo') filter.kind = pick('kind') as 'video'
  if (pick('date') === 'today') filter.date = 'today'
  const uploader = pick('uploader')
  if (uploader) filter.uploader = uploader
  if (pick('favorited') === 'true') filter.favorited = 'true'
  return filter
}

export function filterToQuery(filter: PhotoFilter): Record<string, string> {
  const query: Record<string, string> = {}
  for (const [k, v] of Object.entries(filter)) if (v) query[k] = v
  return query
}

/**
 * 讓所有列表下次顯示時重新載入，例如剛上傳完照片。
 * 只重設狀態、不換掉物件，畫面上正在用的列表會跟著更新。
 */
export function invalidateAll() {
  for (const { state } of lists.values()) {
    state.items = []
    state.nextCursor = null
    state.loaded = false
    state.done = false
    state.error = ''
  }
}

/**
 * 某張照片變了（按讚、收藏），把每一串列表裡的那張都換成新的，回到列表時數字才對。
 *
 * 收藏的列表要增減照片，但不在這裡立刻動：從「收藏」點進照片詳情後取消收藏，
 * 正在看的那張突然消失會很怪。所以只標記成過時，回到收藏頁時再重新載入。
 */
export function updatePhoto(photo: Photo) {
  for (const [key, { state }] of lists) {
    const i = state.items.findIndex((p) => p.id === photo.id)
    if (i >= 0) {
      if (state.items[i]!.favoritedByMe !== photo.favoritedByMe && key.includes('favorited=true')) {
        state.stale = true
      }
      state.items[i] = photo
    } else if (photo.favoritedByMe && key.includes('favorited=true')) {
      state.stale = true
    }
  }
}

/** 照片被刪了：從每一串列表拿掉 */
export function removePhoto(id: string) {
  for (const { state } of lists.values()) {
    const i = state.items.findIndex((p) => p.id === id)
    if (i >= 0) state.items.splice(i, 1)
  }
}
