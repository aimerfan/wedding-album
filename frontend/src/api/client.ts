/**
 * 所有 API 呼叫都走這裡：帶上 token、把錯誤統一成 ApiError。
 * 規格見 docs/api.md。網址一律是相對路徑 /api/...，開發時由 Vite 轉給 Flask。
 */
import { session } from '@/stores/session'

export class ApiError extends Error {
  constructor(
    /** HTTP 狀態碼；連不上伺服器時是 0 */
    readonly status: number,
    /** 後端給的錯誤代碼，例如 invalid_event_code */
    readonly code: string,
    /** 可以直接顯示給賓客看的中文訊息 */
    message: string,
  ) {
    super(message)
  }
}

type Query = Record<string, string | number | undefined>

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  body?: unknown
  query?: Query
}

/** token 失效時要做的事（清掉身分、回歡迎頁），由 main.ts 註冊，避免這裡直接依賴 router */
let onUnauthorized: () => void = () => {}

export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler
}

function buildUrl(path: string, query?: Query) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== '') params.set(key, String(value))
  }
  const qs = params.toString()
  return '/api' + path + (qs ? '?' + qs : '')
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (session.token) headers.Authorization = 'Bearer ' + session.token
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'

  let res: Response
  try {
    res = await fetch(buildUrl(path, options.query), {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(0, 'network_error', '網路連線不穩，請稍後再試')
  }

  const data = await res.json().catch(() => null)

  if (!res.ok) {
    const error = data?.error
    const apiError = new ApiError(
      res.status,
      error?.code ?? 'unknown_error',
      error?.message ?? '發生錯誤，請稍後再試',
    )
    // 帶了 token 卻被拒絕：token 已失效（例如開發時重建了資料庫），要重新加入
    if (res.status === 401 && session.token) onUnauthorized()
    throw apiError
  }

  return data as T
}
