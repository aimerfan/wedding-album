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

export default router
