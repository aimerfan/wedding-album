<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { claimTransferCode } from '@/api/guests'
import { invalidateAll } from '@/stores/photoLists'
import { session, setGuestId, setProfile, setToken } from '@/stores/session'

/**
 * 在另一個瀏覽器或裝置打開「接續連結」的地方：/continue?code=XXXXXXXX
 * 用接續碼換一組 token，之後就是同一位賓客。不需要先加入相簿。
 */
const route = useRoute()
const router = useRouter()

const code = computed(() => (typeof route.query.code === 'string' ? route.query.code : ''))

type State = 'confirm' | 'working' | 'error'
// 這個瀏覽器已經是某位賓客時，先問要不要切換，不要默默換掉
const state = ref<State>(session.token ? 'confirm' : 'working')
const error = ref('')

async function claim() {
  if (!code.value) {
    state.value = 'error'
    error.value = '連結不完整，請在原本的裝置重新產生'
    return
  }
  state.value = 'working'
  try {
    const { token, guest } = await claimTransferCode(code.value)
    setToken(token)
    setGuestId(guest.id)
    setProfile(guest.nickname, guest.relation ?? '')
    // 換了身分，之前快取的「我上傳的」「收藏」都不再是自己的
    invalidateAll()
    router.replace({ name: 'feed' })
  } catch (e) {
    state.value = 'error'
    error.value = e instanceof ApiError ? e.message : '發生錯誤，請稍後再試'
  }
}

function keepCurrent() {
  router.replace({ name: 'feed' })
}

onMounted(() => {
  if (state.value === 'working') claim()
})
</script>

<template>
  <main class="continue">
    <h1>在這裡繼續</h1>

    <template v-if="state === 'confirm'">
      <p class="text">
        這個瀏覽器目前是「{{ session.nickname || '另一位賓客' }}」。<br />
        要改成連結裡的身分嗎？
      </p>
      <button class="primary" type="button" @click="claim">改成連結裡的身分</button>
      <button class="secondary" type="button" @click="keepCurrent">保持現在的身分</button>
    </template>

    <p v-else-if="state === 'working'" class="text">正在延續你的身分…</p>

    <template v-else>
      <p class="text error" role="alert">{{ error }}</p>
      <button class="secondary" type="button" @click="router.replace({ name: 'welcome' })">
        改用新身分加入
      </button>
    </template>
  </main>
</template>

<style scoped>
.continue {
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
