/** 把 ISO 時間轉成「剛剛 / 12 分鐘前 / 1 小時前」。祝福與留言共用 */
export function relativeTime(iso: string) {
  const diffMs = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diffMs / 60000)
  if (minutes < 1) return '剛剛'
  if (minutes < 60) return minutes + ' 分鐘前'
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return hours + ' 小時前'
  return Math.floor(hours / 24) + ' 天前'
}
