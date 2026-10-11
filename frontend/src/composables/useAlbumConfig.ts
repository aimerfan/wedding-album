import { reactive } from 'vue'
import { fetchConfig, type AlbumConfig } from '@/api/config'

/** 拿不到後端設定時的保底值，跟後端預設一致 */
const FALLBACK: AlbumConfig = {
  maxPhotoBytes: 30 * 1024 * 1024,
  maxVideoBytes: 200 * 1024 * 1024,
  maxUploadsPerHour: 300,
  uploadConcurrency: 3,
  maxBlessingLength: 200,
  uploadsOpen: true,
}

/**
 * 後端定義的各種上限（GET /api/config），畫面上直接綁這個。
 * 一開始先用保底值，後端回來後自動換成真的；上限只在後端設定一份。
 */
export function useAlbumConfig(): AlbumConfig {
  const config = reactive({ ...FALLBACK })
  fetchConfig()
    .then((c) => Object.assign(config, c))
    .catch(() => {
      // 拿不到就沿用保底值，不擋住畫面
    })
  return config
}
