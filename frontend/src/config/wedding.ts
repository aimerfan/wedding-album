/**
 * 婚禮基本資料。設計稿裡寫死的名字與日期都集中在這裡，換人換日期只改這個檔。
 */
export const wedding = {
  groomName: '俊鴻',
  brideName: '鈺婷',
  /** ISO 日期 */
  date: '2026-10-17',
  /** 歡迎頁的大字日期 */
  dateDisplay: '2026 · 10 · 17',
  /** 首頁與婚紗集的英文日期標 */
  dateDisplayEn: 'OCT · 17 · 2026',
  /** 歡迎頁頂部的裝飾字 */
  kicker: 'OUR WEDDING · 2026',
  venue: '婚宴會館',
  /** 單次上傳張數上限 */
  maxUploadCount: 30,
  /** 祝福語字數上限 */
  maxBlessingLength: 200,
} as const
