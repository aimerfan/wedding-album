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

/** 第一次進來才載入；之前載過就沿用，回到列表時不會閃一下又重來 */
export function ensureLoaded(filter: PhotoFilter) {
  const { state } = entry(filter)
  if (!state.loaded) return loadMore(filter)
}

/** 從頭重新載入，例如上傳完照片之後 */
export async function reload(filter: PhotoFilter) {
  const { state } = entry(filter)
  state.items = []
  state.nextCursor = null
  state.loaded = false
  state.done = false
  await loadMore(filter)
}

/**
 * 網址 query ⇄ 篩選條件。從列表點進照片詳情時把條件帶在網址上（例如 ?uploader=me），
 * 詳情頁才知道要在哪一串照片裡左右滑；重新整理或分享連結時也不會遺失。
 */
const TAGS: PhotoTag[] = ['welcome', 'ceremony', 'banquet']

export function filterFromQuery(query: Record<string, unknown>): PhotoFilter {
  const pick = (k: string) => (typeof query[k] === 'string' ? (query[k] as string) : undefined)
  const filter: PhotoFilter = {}
  const tag = pick('tag')
  if (tag && (TAGS as string[]).includes(tag)) filter.tag = tag as PhotoTag
  if (pick('kind') === 'video' || pick('kind') === 'photo') filter.kind = pick('kind') as 'video'
  if (pick('date') === 'today') filter.date = 'today'
  const uploader = pick('uploader')
  if (uploader) filter.uploader = uploader
  return filter
}

export function filterToQuery(filter: PhotoFilter): Record<string, string> {
  const query: Record<string, string> = {}
  for (const [k, v] of Object.entries(filter)) if (v) query[k] = v
  return query
}
