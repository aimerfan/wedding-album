<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { joinAlbum, updateMe } from '@/api/guests'
import PhotoTile from '@/components/PhotoTile.vue'
import DecoDivider from '@/components/DecoDivider.vue'
import { wedding } from '@/config/wedding'
import { session, setProfile, setToken } from '@/stores/session'

const route = useRoute()
const router = useRouter()

// 從上傳頁按「更改」回來、或 token 失效重新加入時，帶入原本填的內容
const name = ref(session.nickname)
const relation = ref(session.relation)

const submitting = ref(false)
const error = ref('')

async function enter() {
  const nickname = name.value.trim()
  if (!nickname || submitting.value) return

  if (!session.token && !session.eventCode) {
    error.value = '請用手機掃描婚禮會場的 QR code 進入'
    return
  }

  submitting.value = true
  error.value = ''
  try {
    // 已經加入過（從上傳頁按「更改」回來）就只改資料，不要變成另一位新賓客
    const { guest } = session.token
      ? await updateMe(nickname, relation.value.trim())
      : await joinAlbum(session.eventCode, nickname, relation.value.trim()).then((r) => {
          setToken(r.token)
          return r
        })
    setProfile(guest.nickname, guest.relation ?? '')

    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    // 只接受站內路徑，避免被帶去別的網站
    router.replace(redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : { name: 'feed' })
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : '發生錯誤，請稍後再試'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="welcome">
    <div class="hero">
      <PhotoTile :index="0" ratio="auto" class="hero-photo" />
      <div class="hero-fade" />
      <p class="kicker">{{ wedding.kicker }}</p>
    </div>

    <div class="content">
      <h1 class="names">
        {{ wedding.groomName }} <span class="amp">&amp;</span> {{ wedding.brideName }}
      </h1>

      <DecoDivider />

      <p class="date">{{ wedding.dateDisplay }}</p>

      <p class="intro">
        歡迎你來到我們的婚禮<br />
        請留下你的名字<br />
        一起記錄這個值得收藏的日子
      </p>

      <label class="field">
        <span class="field-label">你的名字</span>
        <input
          v-model="name"
          type="text"
          class="field-input"
          placeholder="小慧"
          autocomplete="nickname"
          enterkeyhint="go"
          maxlength="20"
          @keyup.enter="enter"
        />
      </label>

      <label class="field">
        <span class="field-label">與新人的關係（選填）</span>
        <input
          v-model="relation"
          type="text"
          class="field-input"
          placeholder="例如：新娘的大學同學"
          enterkeyhint="go"
          maxlength="30"
          @keyup.enter="enter"
        />
      </label>

      <p v-if="error" class="error" role="alert">{{ error }}</p>

      <button class="enter" type="button" :disabled="!name.trim() || submitting" @click="enter">
        {{ submitting ? '進 入 中 …' : '進 入 相 簿' }}
      </button>

      <p class="consent">進入後即代表同意分享你拍攝的回憶</p>
    </div>
  </main>
</template>

<style scoped>
.welcome {
  min-height: 100dvh;
  background: var(--c-bg);
  color: var(--c-ink);
}

.hero {
  position: relative;
  height: 380px;
  overflow: hidden;
}

.hero-photo {
  height: 100%;
}

/* 相片底部漸隱到頁面底色 */
.hero-fade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 0%, transparent 50%, var(--c-bg) 100%);
}

.kicker {
  position: absolute;
  top: calc(var(--safe-top) + 32px);
  left: 0;
  right: 0;
  margin: 0;
  text-align: center;
  color: #fff;
  font-family: var(--f-display);
  font-style: italic;
  font-size: 13px;
  letter-spacing: 4px;
}

.content {
  /* 往上疊到 hero 的漸隱區，維持設計稿的重疊感 */
  margin-top: -100px;
  position: relative;
  padding: 0 28px calc(var(--safe-bottom) + 32px);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.names {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 30px;
  font-weight: 500;
  letter-spacing: 1px;
  line-height: 1.1;
  white-space: nowrap;
}

.amp {
  font-family: var(--f-display);
  font-style: italic;
  color: var(--c-rose);
  margin: 0 4px;
}

.date {
  margin: 0;
  font-family: var(--f-display);
  font-style: italic;
  font-size: 15px;
  letter-spacing: 3px;
  color: var(--c-ink-soft);
}

.intro {
  margin: 18px 0 0;
  padding: 0 16px;
  text-align: center;
  font-size: 13px;
  line-height: 1.8;
  color: var(--c-ink-soft);
}

.field {
  margin-top: 14px;
  width: 100%;
  background: var(--c-card);
  border: 1px solid var(--c-line);
  border-radius: 14px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 11px;
  letter-spacing: 1.5px;
  color: var(--c-ink-mute);
}

.field-input {
  border: 0;
  padding: 0;
  background: transparent;
  font-family: var(--f-serif);
  font-size: 18px;
  color: var(--c-ink);
  caret-color: var(--c-rose);
}

.field-input:focus {
  outline: none;
}

.field-input::placeholder {
  color: var(--c-ink-mute);
  opacity: 0.5;
}

.enter {
  margin-top: 6px;
  width: 100%;
  height: 52px;
  border: 0;
  border-radius: 26px;
  background: var(--c-rose);
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 4px;
  box-shadow: var(--shadow-rose);
  transition: opacity 0.2s;
}

.enter:disabled {
  opacity: 0.45;
  box-shadow: none;
  cursor: default;
}

.consent {
  margin: 0;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.error {
  margin: 0;
  font-size: 13px;
  text-align: center;
  color: var(--c-rose);
}
</style>
