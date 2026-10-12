<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { becomeAdmin } from '@/api/guests'
import { session, setAdmin } from '@/stores/session'

/**
 * 開通管理員：/admin?code=<管理員代碼>
 * 要先加入相簿（路由會先導去歡迎頁，加入後再回來這裡）。管理員可以刪除任何照片與祝福。
 */
const route = useRoute()
const router = useRouter()

const state = ref<'working' | 'done' | 'error'>('working')
const error = ref('')

onMounted(async () => {
  const code = typeof route.query.code === 'string' ? route.query.code : ''
  if (!code) {
    state.value = 'error'
    error.value = '連結不完整，缺少管理員代碼'
    return
  }
  try {
    await becomeAdmin(code)
    setAdmin(true)
    state.value = 'done'
    // 把代碼從網址拿掉，免得截圖或分享畫面時不小心外流
    router.replace({ name: 'admin' })
  } catch (e) {
    state.value = 'error'
    error.value = e instanceof ApiError ? e.message : '開通失敗，請稍後再試'
  }
})
</script>

<template>
  <main class="admin">
    <h1>管理員</h1>

    <p v-if="state === 'working'" class="text">開通中…</p>

    <template v-else-if="state === 'done'">
      <p class="text">
        「{{ session.nickname }}」已經是管理員了。<br />
        在照片右上角的「⋯」、祝福右上角的「⋯」<br />
        可以刪除不適當的照片與祝福。
      </p>
      <button class="primary" type="button" @click="router.replace({ name: 'feed' })">
        回相簿
      </button>
    </template>

    <template v-else>
      <p class="text error" role="alert">{{ error }}</p>
      <button class="secondary" type="button" @click="router.replace({ name: 'feed' })">
        回相簿
      </button>
    </template>
  </main>
</template>

<style scoped>
.admin {
  min-height: 100dvh;
  padding: calc(var(--page-top) + 80px) 24px 40px;
  background: var(--c-bg);
  color: var(--c-ink);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;
}

h1 {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 22px;
  font-weight: 500;
  letter-spacing: 2px;
}

.text {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--c-ink-soft);
}

.text.error {
  color: var(--c-rose);
}

.primary,
.secondary {
  width: 100%;
  max-width: 320px;
  height: 46px;
  border-radius: 23px;
  font-size: 14px;
  letter-spacing: 2px;
}

.primary {
  border: 0;
  background: var(--c-rose);
  color: #fff;
  box-shadow: var(--shadow-rose);
}

.secondary {
  border: 1px solid var(--c-line-strong);
  background: transparent;
  color: var(--c-ink);
}
</style>
