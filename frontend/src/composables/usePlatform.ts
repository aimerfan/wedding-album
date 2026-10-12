/**
 * 判斷賓客是用什麼開這個網站，決定要不要、以及怎麼引導「加到主畫面」。
 *
 * 全部靠 User-Agent 猜，不保證百分之百準：判斷錯了最多是多顯示或少顯示一張提示卡，
 * 不會擋住任何功能。
 */

const ua = typeof navigator === 'undefined' ? '' : navigator.userAgent

/** iPhone、iPad（新的 iPad 會假裝自己是 Mac，用「Mac + 觸控」認出來） */
export const isIOS =
  /iPhone|iPad|iPod/.test(ua) ||
  (/Macintosh/.test(ua) && typeof navigator !== 'undefined' && navigator.maxTouchPoints > 1)

export const isAndroid = /Android/.test(ua)

/**
 * App 內建的瀏覽器（LINE、Instagram、Facebook、Messenger、微信）。
 * 台灣很多人用 LINE 掃 QR code，會在 LINE 裡打開；這些內建瀏覽器沒辦法加到主畫面。
 */
export const isInAppBrowser = /Line\/|Instagram|FBAN|FBAV|FB_IAB|Messenger|MicroMessenger/i.test(ua)

/** 已經是從主畫面打開的（不是在瀏覽器分頁裡） */
export function isStandalone(): boolean {
  if (typeof window === 'undefined') return false
  // iOS Safari 自己的旗標；其他瀏覽器看 display-mode
  const iosStandalone = (navigator as Navigator & { standalone?: boolean }).standalone === true
  return iosStandalone || window.matchMedia('(display-mode: standalone)').matches
}

export type InstallGuideKind = 'ios-safari' | 'in-app' | 'android' | null

/** 該顯示哪一種「加到主畫面」的說明；不需要（已經裝了、或是電腦）就回傳 null */
export function installGuideKind(): InstallGuideKind {
  if (isStandalone()) return null
  if (isInAppBrowser && (isIOS || isAndroid)) return 'in-app'
  if (isIOS) return 'ios-safari'
  if (isAndroid) return 'android'
  return null
}
