<script setup lang="ts">
import { computed, ref, watch } from 'vue'

/**
 * 「在其他裝置繼續」：產生一條一次性連結，在別的瀏覽器或電腦打開就是同一位賓客。
 * 見 docs/api.md 的「換瀏覽器或換裝置」。
 */
const open = defineModel<boolean>({ required: true })

const link = ref('')
const expiresAt = ref<Date | null>(null)
const copied = ref(false)

const canShare = typeof navigator !== 'undefined' && 'share' in navigator

const expiresLabel = computed(() => {
  const d = expiresAt.value
  if (!d) return ''
  return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
})

// 每次打開都重新產生，舊的就不必擔心外流
watch(open, (isOpen) => {
  if (isOpen) generate()
})

function generate() {
  // TODO: 接後端 API（POST /api/me/transfer-codes）。現在是假的接續碼，打開也不會有作用
  const code = Math.random().toString(36).slice(2, 8).toUpperCase()
  link.value = `${window.location.origin}/continue?code=${code}`
  expiresAt.value = new Date(Date.now() + 30 * 60 * 1000)
  copied.value = false
}

async function copy() {
  try {
    await navigator.clipboard.writeText(link.value)
    copied.value = true
  } catch {
    // 沒有剪貼簿權限時，至少讓使用者能手動選取
    copied.value = false
  }
}

async function share() {
  try {
    await navigator.share({ title: '婚禮相簿', url: link.value })
  } catch {
    // 使用者取消分享也會 throw，不用處理
  }
}
</script>

<template>
  <Transition name="sheet">
    <div v-if="open" class="overlay" @click.self="open = false">
      <section class="sheet" role="dialog" aria-label="在其他裝置繼續">
        <span class="grip" />
        <h2>在其他裝置繼續</h2>
        <p class="intro">
          想換瀏覽器，或回家用電腦上傳照片？<br />
          在那邊打開這條連結，就會延續你現在的身分。
        </p>

        <!-- user-select: all，點一下就整串選起來，沒有剪貼簿權限時也能手動複製 -->
        <p class="link">{{ link }}</p>
        <p class="note">{{ expiresLabel }} 前有效，只能使用一次。請不要傳給別人。</p>

        <div class="actions">
          <button class="primary" type="button" @click="copy">
            {{ copied ? '已複製' : '複製連結' }}
          </button>
          <button v-if="canShare" class="secondary" type="button" @click="share">分享</button>
        </div>

        <button class="close" type="button" @click="open = false">關閉</button>
      </section>
    </div>
  </Transition>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  /* 要蓋過 AppTabBar（30） */
  z-index: 40;
  display: flex;
  align-items: flex-end;
  background: rgba(61, 46, 38, 0.35);
}

.sheet {
  width: 100%;
  padding: 12px 20px calc(var(--safe-bottom) + 20px);
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  background: var(--c-bg);
  color: var(--c-ink);
  text-align: center;
}

.grip {
  display: block;
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--c-line);
  margin: 0 auto 16px;
}

h2 {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 1px;
}

.intro {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.8;
  color: var(--c-ink-soft);
}

.link {
  margin: 16px 0 0;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--c-line);
  background: var(--c-card);
  font-family: ui-monospace, 'SF Mono', monospace;
  font-size: 12px;
  word-break: break-all;
  user-select: all;
}

.note {
  margin: 8px 0 0;
  font-size: 11px;
  color: var(--c-ink-mute);
}

.actions {
  margin-top: 18px;
  display: flex;
  gap: 10px;
}

.primary,
.secondary {
  flex: 1;
  height: 44px;
  border-radius: 22px;
  font-size: 13px;
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

.close {
  margin-top: 12px;
  border: 0;
  background: transparent;
  font-size: 13px;
  color: var(--c-ink-mute);
}

.sheet-enter-active,
.sheet-leave-active {
  transition: background 0.25s;
}

.sheet-enter-active .sheet,
.sheet-leave-active .sheet {
  transition: transform 0.25s ease-out;
}

.sheet-enter-from,
.sheet-leave-to {
  background: transparent;
}

.sheet-enter-from .sheet,
.sheet-leave-to .sheet {
  transform: translateY(100%);
}
</style>
