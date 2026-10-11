import { createApp } from 'vue'

import App from './App.vue'
import { setUnauthorizedHandler } from './api/client'
import router from './router'
import { clearToken } from './stores/session'
import './assets/base.css'

// token 失效（例如開發時重建了資料庫）：清掉身分，回歡迎頁重新加入
setUnauthorizedHandler(() => {
  clearToken()
  router.replace({ name: 'welcome' })
})

createApp(App).use(router).mount('#app')
