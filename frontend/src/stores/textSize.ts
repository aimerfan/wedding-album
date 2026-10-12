import { ref } from 'vue'

/**
 * 字體大小：標準／大／特大。給長輩用的。
 *
 * iPhone 的 Safari 不會跟著系統的字體設定放大網頁，設計稿又有不少 10～11px 的小字，
 * 所以讓賓客自己選。用 CSS zoom 讓整個畫面等比例放大，排版會跟著重排，不會超出螢幕。
 * 選擇只存在這支手機上。
 */
export type TextSize = 'normal' | 'large' | 'xlarge'

export const TEXT_SIZES: { id: TextSize; label: string; zoom: number }[] = [
  { id: 'normal', label: '標準', zoom: 1 },
  { id: 'large', label: '大', zoom: 1.15 },
  { id: 'xlarge', label: '特大', zoom: 1.3 },
]

const KEY = 'wedding-album:text-size'

function read(): TextSize {
  try {
    const v = localStorage.getItem(KEY)
    if (v === 'large' || v === 'xlarge') return v
  } catch {
    // 無痕模式等情況讀不到，就用標準
  }
  return 'normal'
}

export const textSize = ref<TextSize>(read())

function apply(size: TextSize) {
  const zoom = TEXT_SIZES.find((s) => s.id === size)!.zoom
  // 放大倍率給 CSS 用：佔滿螢幕高度的畫面要除回去，不然放大後會超出螢幕（見 base.css）
  document.documentElement.style.setProperty('--text-zoom', String(zoom))
  document.documentElement.style.zoom = zoom === 1 ? '' : String(zoom)
}

export function setTextSize(size: TextSize) {
  textSize.value = size
  apply(size)
  try {
    if (size === 'normal') localStorage.removeItem(KEY)
    else localStorage.setItem(KEY, size)
  } catch {
    // 存不了就只在這次有效
  }
}

/** main.ts 啟動時呼叫，畫面一出來就是使用者選的大小 */
export function applySavedTextSize() {
  apply(textSize.value)
}
