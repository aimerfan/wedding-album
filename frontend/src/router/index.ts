import { createRouter, createWebHistory } from 'vue-router'
import TabLayout from '@/layouts/TabLayout.vue'
import FeedView from '@/views/FeedView.vue'
import { session } from '@/stores/session'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // 有底部 tab bar 的畫面：四個主畫面，加上從相簿點進去的賓客照片頁
    {
      path: '/',
      component: TabLayout,
      children: [
        { path: '', name: 'feed', component: FeedView },
        {
          path: 'wedding',
          name: 'wedding',
          component: () => import('@/views/WeddingGalleryView.vue'),
        },
        {
          path: 'blessings',
          name: 'blessings',
          component: () => import('@/views/BlessingsView.vue'),
        },
        { path: 'me', name: 'me', component: () => import('@/views/MeView.vue') },
        {
          path: 'guests/:guestId',
          name: 'guest-photos',
          component: () => import('@/views/GuestPhotosView.vue'),
          props: true,
        },
      ],
    },

    // 全螢幕畫面（沒有 tab bar）
    { path: '/welcome', name: 'welcome', component: () => import('@/views/WelcomeView.vue') },
    // 接續連結：在另一個裝置延續同一位賓客，不需要先加入相簿
    { path: '/continue', name: 'continue', component: () => import('@/views/ContinueView.vue') },
    // 開通管理員：要先加入相簿（沒加入會先導去歡迎頁，加入後帶回來）
    { path: '/admin', name: 'admin', component: () => import('@/views/AdminView.vue') },
    { path: '/upload', name: 'upload', component: () => import('@/views/UploadPickerView.vue') },
    {
      path: '/upload/edit',
      name: 'upload-edit',
      component: () => import('@/views/UploadEditView.vue'),
    },
    {
      path: '/photos/:photoId',
      name: 'photo-detail',
      component: () => import('@/views/PhotoDetailView.vue'),
      props: true,
    },

    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
  // 按返回時回到離開前的捲動位置（例如從照片詳情回首頁）；
  // 同一頁只改 query（例如婚紗集的 ?photo=）時留在原位；其餘換頁從頂端開始
  scrollBehavior: (to, from, savedPosition) =>
    savedPosition ?? (to.path === from.path ? false : { top: 0 }),
})

/**
 * 還沒加入相簿（沒有 token）的賓客一律先進歡迎頁。
 * 加入之後原本要去的網址記在 redirect，加入完再帶過去（例如分享出去的照片連結）。
 */
router.beforeEach((to) => {
  if (to.name === 'welcome' || to.name === 'continue') return true
  if (!session.token) {
    return to.fullPath === '/'
      ? { name: 'welcome' }
      : { name: 'welcome', query: { redirect: to.fullPath } }
  }
  return true
})

/**
 * 畫面方向：只有照片詳情與婚紗集的放大檢視（/wedding?photo=…）可以跟著手機轉，其他頁固定直式。
 * manifest 不鎖方向（鎖了詳情頁就轉不過來），改成每次換頁時用 screen.orientation 鎖／解鎖。
 * 只有 Android 安裝到主畫面的 app 鎖得住；iPhone、桌機、一般瀏覽器分頁的 lock() 會被拒絕，
 * 這時就不鎖，照瀏覽器原本的行為（iPhone 其他頁也能轉，這是接受的取捨）。
 */
type LockableOrientation = ScreenOrientation & {
  lock?: (orientation: 'portrait') => Promise<void>
}

router.afterEach((to) => {
  try {
    const o = window.screen?.orientation as LockableOrientation | undefined
    if (!o) return
    const viewing = to.name === 'photo-detail' || (to.name === 'wedding' && !!to.query.photo)
    if (viewing) o.unlock?.()
    else o.lock?.('portrait')?.catch(() => {})
  } catch {
    // 不支援的瀏覽器可能直接丟例外，方向鎖不到不影響使用
  }
})

export default router
