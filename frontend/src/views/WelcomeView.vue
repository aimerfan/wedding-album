<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import PhotoTile from '@/components/PhotoTile.vue'
import DecoDivider from '@/components/DecoDivider.vue'
import { wedding } from '@/config/wedding'
import { setNickname } from '@/stores/session'

const router = useRouter()
const name = ref('')

function enter() {
  const trimmed = name.value.trim()
  if (!trimmed) return
  setNickname(trimmed)
  router.push({ name: 'feed' })
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

      <button class="enter" type="button" :disabled="!name.trim()" @click="enter">
        進 入 相 簿
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
</style>
