import { reactive } from 'vue'
import { fetchBlessings, type BlessingFilter } from '@/api/blessings'
import { ApiError } from '@/api/client'
import type { Blessing } from '@/types/album'

/**
 * 祝福列表：留言牆（全部）與「我的祝福」（guest=me）各一份。
 * 在其中一邊新增、修改、刪除，另一邊也跟著更新，不必重新載入。
 */
export interface BlessingList {
  items: Blessing[]
  nextCursor: string | null
  loaded: boolean
  done: boolean
  loading: boolean
  error: string
}

const lists = new Map<string, { state: BlessingList; filter: BlessingFilter }>()

function entry(filter: BlessingFilter) {
  const key = filter.guest ?? 'all'
  let found = lists.get(key)
  if (!found) {
    found = {
      filter,
      state: reactive<BlessingList>({
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

export function getBlessingList(filter: BlessingFilter): BlessingList {
  return entry(filter).state
}

export async function loadMoreBlessings(filter: BlessingFilter) {
  const { state } = entry(filter)
  if (state.loading || state.done) return
  state.loading = true
  state.error = ''
  try {
    const page = await fetchBlessings(filter, state.nextCursor)
    const seen = new Set(state.items.map((b) => b.id))
    state.items.push(...page.items.filter((b) => !seen.has(b.id)))
    state.nextCursor = page.nextCursor
    state.done = page.nextCursor === null
    state.loaded = true
  } catch (e) {
    state.error = e instanceof ApiError ? e.message : '載入失敗，請稍後再試'
  } finally {
    state.loading = false
  }
}

export function ensureBlessingsLoaded(filter: BlessingFilter) {
  if (!entry(filter).state.loaded) return loadMoreBlessings(filter)
}

export async function reloadBlessings(filter: BlessingFilter) {
  const { state } = entry(filter)
  Object.assign(state, { items: [], nextCursor: null, loaded: false, done: false })
  await loadMoreBlessings(filter)
}

/** 新寫的祝福放到每個已載入列表的最上面（留言牆新的在上） */
export function addBlessing(blessing: Blessing) {
  for (const { state } of lists.values()) {
    if (state.loaded && !state.items.some((b) => b.id === blessing.id)) state.items.unshift(blessing)
  }
}

export function replaceBlessing(blessing: Blessing) {
  for (const { state } of lists.values()) {
    const i = state.items.findIndex((b) => b.id === blessing.id)
    if (i >= 0) state.items[i] = blessing
  }
}

export function removeBlessing(id: string) {
  for (const { state } of lists.values()) {
    const i = state.items.findIndex((b) => b.id === id)
    if (i >= 0) state.items.splice(i, 1)
  }
}
