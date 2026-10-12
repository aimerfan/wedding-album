<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '@/api/client'
import { joinAlbum, signInWithTransferCode, updateMe } from '@/api/guests'
import DecoDivider from '@/components/DecoDivider.vue'
import InstallGuide from '@/components/InstallGuide.vue'
import PhotoTile from '@/components/PhotoTile.vue'
import TextSizePicker from '@/components/TextSizePicker.vue'
import { installGuideKind } from '@/composables/usePlatform'
import { wedding } from '@/config/wedding'
import { session, setAdmin, setGuestId, setProfile, setToken } from '@/stores/session'

const route = useRoute()
const router = useRouter()

// 從上傳頁按「更改」回來、或 token 失效重新加入時，帶入原本填的內容
const name = ref(session.nickname)
const relation = ref(session.relation)

const submitting = ref(false)
const error = ref('')

// --- 加到主畫面的引導 -----------------------------------------------------
// 只在 iPhone Safari 與 LINE／IG 內建瀏覽器顯示：iPhone 上 Safari 與主畫面的資料是分開的，
// 要在「加入之前」引導，才不會一個人變成兩位賓客。Android 沒有這個問題，引導放在「我的」頁就好。

const GUIDE_DISMISSED_KEY = 'wedding-album:install-guide-dismissed'
const kind = installGuideKind()
const showGuide = ref((kind === 'ios-safari' || kind === 'in-app') && !readDismissed())

function readDismissed() {
  try {
    return localStorage.getItem(GUIDE_DISMISSED_KEY) === '1'
  } catch {
    return false
  }
}

function dismissGuide() {
  showGuide.value = false
  try {
    localStorage.setItem(GUIDE_DISMISSED_KEY, '1')
  } catch {
    // 存不了就下次再顯示一次，沒關係
  }
}

// --- 已經加入過：輸入接續碼 -----------------------------------------------
// 從主畫面打開的 app 沒有網址列，貼不了接續連結，所以讓人直接輸入 8 碼接續碼

const showCodeInput = ref(false)
const transferCode = ref('')
const claiming = ref(false)
const codeError = ref('')

async function useTransferCode() {
  const code = transferCode.value.trim()
  if (!code || claiming.value) return
  claiming.value = true
  codeError.value = ''
  try {
    await signInWithTransferCode(code)
    router.replace({ name: 'feed' })
  } catch (e) {
    codeError.value = e instanceof ApiError ? e.message : '發生錯誤，請稍後再試'
  } finally {
    claiming.value = false
  }
}

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
          setAdmin(false) // 新加入的賓客一定不是管理員
          return r
        })
    setProfile(guest.nickname, guest.relation ?? '')
    setGuestId(guest.id)

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
      <!-- 長輩一進來就看得到：右上角的「Aa」可以把字放大 -->
      <TextSizePicker compact class="text-size" />
    </div>

    <div class="content">
      <h1 class="names">
        {{ wedding.groomName }} <span class="amp">&amp;</span> {{ wedding.brideName }}
      </h1>

      <DecoDivider />

      <p class="date">{{ wedding.dateDisplay }}</p>

      <InstallGuide v-if="showGuide && kind" :kind="kind" class="guide" @close="dismissGuide" />

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

      <button
        v-if="!showCodeInput"
        class="have-code"
        type="button"
        @click="showCodeInput = true"
      >
        已經加入過？輸入接續碼
      </button>
      <form v-else class="code-form" @submit.prevent="useTransferCode">
        <p class="code-hint">在原本的裝置打開「我的」→ 右上角圖示，複製 8 碼接續碼貼在這裡</p>
        <div class="code-row">
          <input
            v-model="transferCode"
            class="code-input"
            type="text"
            inputmode="text"
            autocapitalize="characters"
            autocomplete="off"
            spellcheck="false"
            maxlength="12"
            placeholder="例如 7Q2K9MPX"
            aria-label="接續碼"
          />
          <button class="code-submit" type="submit" :disabled="!transferCode.trim() || claiming">
            {{ claiming ? '…' : '繼續' }}
          </button>
        </div>
        <p v-if="codeError" class="error" role="alert">{{ codeError }}</p>
      </form>
    </div>
  </main>
</template>

<style scoped>
.welcome {
  min-height: var(--screen-h);
  background: var(--c-bg);
  color: var(--c-ink);
}

/*
 * 大圖跟著螢幕高度縮：螢幕矮或還有瀏覽器網址列時，「進入相簿」才不會被擠到畫面外。
 * 最高 380px（設計稿），最矮 220px（名字以上至少留一點圖）
 */
.hero {
  position: relative;
  height: clamp(220px, var(--screen-h) - 470px, 380px);
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

.text-size {
  position: absolute;
  top: calc(var(--safe-top) + 20px);
  right: 16px;
  z-index: 5;
}

.kicker {
  position: absolute;
  top: calc(var(--safe-top) + 32px);
  /* 左右讓出右上角「Aa」的寬度，字放大時才不會疊在一起 */
  left: 60px;
  right: 60px;
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

.guide {
  width: 100%;
}

.have-code {
  padding: 4px 8px;
  border: 0;
  background: transparent;
  font-size: 12px;
  color: var(--c-ink-mute);
  text-decoration: underline;
}

.code-form {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.code-hint {
  margin: 0;
  font-size: 11px;
  line-height: 1.6;
  text-align: center;
  color: var(--c-ink-mute);
}

.code-row {
  display: flex;
  gap: 8px;
}

/* 16px 以上 iOS 點進輸入框時才不會自動放大畫面 */
.code-input {
  flex: 1;
  min-width: 0;
  padding: 10px 14px;
  border: 1px solid var(--c-line);
  border-radius: 12px;
  background: var(--c-card);
  font-family: ui-monospace, 'SF Mono', monospace;
  font-size: 16px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--c-ink);
}

.code-input:focus {
  outline: none;
  border-color: var(--c-rose-soft);
}

.code-submit {
  padding: 0 18px;
  border: 0;
  border-radius: 12px;
  background: var(--c-ink);
  color: #fff;
  font-size: 13px;
}

.code-submit:disabled {
  opacity: 0.45;
}

.error {
  margin: 0;
  font-size: 13px;
  text-align: center;
  color: var(--c-rose);
}
</style>
