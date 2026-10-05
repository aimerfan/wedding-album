<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import PhotoSwiper from '@/components/PhotoSwiper.vue'
import { feedPhotos, myPhotos, stats } from '@/mock/sample'

const props = defineProps<{ photoId: string }>()
const router = useRouter()

/**
 * 左右滑動要在哪一串照片裡換張：從「我的」點進來就只在我上傳的之間滑。
 * 假資料階段用 id 判斷；接上 API 後改成依網址上的篩選條件（例如 ?uploader=me）向後端要列表。
 */
const list = computed(() =>
  myPhotos.some((p) => p.id === props.photoId) ? myPhotos : feedPhotos,
)

const index = computed(() => list.value.findIndex((p) => p.id === props.photoId))
const photo = computed(() => list.value[index.value])

/** 「3 / 247」的序號；首頁那串的總數是全相簿的張數 */
const position = computed(() => (index.value >= 0 ? index.value + 1 : 1))
const total = computed(() => (list.value === feedPhotos ? stats.photoCount : list.value.length))

const slides = computed(() =>
  list.value.map((p) => ({ key: p.id, photo: p, ratio: p.width / p.height })),
)

/** 滑到別張時換掉網址，返回鍵才會直接回相簿，而不是一張張倒退 */
const current = computed({
  get: () => index.value,
  set: (i) => {
    const next = list.value[i]
    if (next) router.replace({ name: 'photo-detail', params: { photoId: next.id } })
  },
})

const takenLabel = computed(() => {
  const p = photo.value
  if (!p) return ''
  const d = new Date(p.uploadedAt)
  const time =
    String(d.getMonth() + 1) +
    '/' +
    d.getDate() +
    ' · ' +
    String(d.getHours()).padStart(2, '0') +
    ':' +
    String(d.getMinutes()).padStart(2, '0')
  return p.location ? time + ' · ' + p.location : time
})

function close() {
  if (window.history.state?.back) router.back()
  else router.push({ name: 'feed' })
}
</script>

<template>
  <main v-if="photo" class="detail">
    <header class="bar">
      <button class="round" type="button" aria-label="關閉" @click="close">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
      <span class="counter">{{ position }} / {{ total }}</span>
      <button class="round" type="button" aria-label="更多">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="#fff"
          stroke-width="1.8"
          stroke-linecap="round"
        >
          <circle cx="5" cy="12" r="2" />
          <circle cx="12" cy="12" r="2" />
          <circle cx="19" cy="12" r="2" />
        </svg>
      </button>
    </header>

    <div class="stage">
      <PhotoSwiper v-model="current" :slides="slides" />
    </div>

    <section class="panel">
      <span class="grip" />

      <div class="uploader">
        <span class="avatar">{{ photo.uploader.nickname[0] }}</span>
        <div class="who">
          <p class="name">{{ photo.uploader.nickname }}</p>
          <p class="meta">{{ takenLabel }}</p>
        </div>
        <svg class="heart" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M12 21s-7-5-7-11a4 4 0 017-2.5A4 4 0 0119 10c0 6-7 11-7 11z" />
        </svg>
        <span class="likes">{{ photo.likeCount }}</span>
      </div>

      <div v-if="photo.blessing" class="blessing">
        <span class="blessing-tag">來自{{ photo.uploader.nickname }}的祝福</span>
        <p class="blessing-text">{{ photo.blessing }}</p>
      </div>
    </section>
  </main>

  <!-- 照片被刪掉或網址打錯時，不要只留一片空白 -->
  <main v-else class="detail missing">
    <p>找不到這張照片</p>
    <button class="missing-back" type="button" @click="close">回相簿</button>
  </main>
</template>

<style scoped>
.detail {
  height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--c-dark-bg);
  color: var(--c-dark-ink);
  position: relative;
}

.missing {
  align-items: center;
  justify-content: center;
  gap: 16px;
  font-size: 14px;
  color: var(--c-dark-ink-mute);
}

.missing-back {
  padding: 8px 20px;
  border: 1px solid var(--c-dark-line);
  border-radius: 18px;
  background: transparent;
  color: var(--c-dark-ink);
  font-size: 13px;
}

.bar {
  position: absolute;
  top: calc(var(--page-top) + 24px);
  left: 16px;
  right: 16px;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.round {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.round svg {
  width: 14px;
  height: 14px;
}

.counter {
  font-size: 11px;
  letter-spacing: 1px;
}

.stage {
  flex: 1;
  min-height: 0;
  padding: calc(var(--page-top) + 84px) 0 16px;
}

/* 留言區固定貼底；祝福太長時在面板內捲動，不把照片擠掉 */
.panel {
  flex-shrink: 0;
  max-height: 55dvh;
  overflow-y: auto;
  background: var(--c-bg);
  color: var(--c-ink);
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  padding: 20px 20px calc(var(--safe-bottom) + 32px);
}

.grip {
  display: block;
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: var(--c-line);
  margin: 0 auto 16px;
}

.uploader {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 18px;
  background: var(--c-bg-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-serif);
  font-size: 15px;
}

.who {
  flex: 1;
}

.name {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.meta {
  margin: 1px 0 0;
  font-size: 10px;
  letter-spacing: 0.5px;
  color: var(--c-ink-mute);
}

.heart {
  width: 18px;
  height: 18px;
  color: var(--c-rose);
}

.likes {
  font-size: 12px;
}

.blessing {
  position: relative;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--c-bg-soft);
}

/* 標籤壓在卡片上緣，用底色蓋住邊框做出缺口 */
.blessing-tag {
  position: absolute;
  top: -8px;
  left: 16px;
  padding: 0 8px;
  background: var(--c-bg-soft);
  font-size: 10px;
  letter-spacing: 1.5px;
  color: var(--c-rose);
}

.blessing-text {
  margin: 0;
  font-family: var(--f-serif);
  font-size: 14px;
  line-height: 1.7;
  text-align: justify;
}
</style>
