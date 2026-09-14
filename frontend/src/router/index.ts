import { createRouter, createWebHistory } from 'vue-router'
import TabLayout from '@/layouts/TabLayout.vue'
import FeedView from '@/views/FeedView.vue'
import { session } from '@/stores/session'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // 有底部 tab bar 的四個主畫面
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
      ],
    },

    // 全螢幕畫面（沒有 tab bar）
    { path: '/welcome', name: 'welcome', component: () => import('@/views/WelcomeView.vue') },
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
  scrollBehavior: () => ({ top: 0 }),
})

/**
 * 還沒留下暱稱的賓客一律先進歡迎頁。
 * 這不是驗證，只是要有個稱呼掛在照片和祝福上。
 */
router.beforeEach((to) => {
  if (to.name === 'welcome') return true
  if (!session.nickname) return { name: 'welcome' }
  return true
})

export default router
