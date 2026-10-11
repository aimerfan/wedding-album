<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import PhotoTile from '@/components/PhotoTile.vue'
import { useInfiniteScroll } from '@/composables/useInfiniteScroll'
import { ensureLoaded, getPhotoList, loadMore } from '@/stores/photoLists'

/** 某位賓客拍的所有照片。從照片詳情點上傳者進來。對應 GET /api/photos?uploader=<guestId> */
const props = defineProps<{ guestId: string }>()
const router = useRouter()

const filter = computed(() => ({ uploader: props.guestId }))
const list = computed(() => getPhotoList(filter.value))
const photos = computed(() => list.value.items)
// 賓客資料直接取第一張照片上的上傳者，不必另外要
const guest = computed(() => photos.value[0]?.uploader)

watch(filter, (f) => ensureLoaded(f), { immediate: true })

const sentinel = ref<HTMLElement>()
useInfiniteScroll(sentinel, async () => {
  if (list.value.loading) return false
  await loadMore(filter.value)
  return !list.value.done && !list.value.error
})

function back() {
  if (window.history.state?.back) router.back()
  else router.push({ name: 'feed' })
}
</script>

<template>
  <main class="guest">
    <header class="head">
      <button class="back" type="button" @click="back">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
        >
          <path d="M15 6l-6 6 6 6" />
        </svg>
        返回
      </button>
    </header>

    <template v-if="guest">
      <section class="profile">
        <span class="avatar">{{ guest.nickname[0] }}</span>
        <h1 class="name">{{ guest.nickname }}</h1>
        <p v-if="guest.relation" class="relation">{{ guest.relation }}</p>
        <p class="count">拍了 {{ photos.length }}{{ list.done ? '' : '+' }} 張照片</p>
      </section>

      <div class="grid">
        <RouterLink
          v-for="(p, i) in photos"
          :key="p.id"
          class="cell"
          :to="{ name: 'photo-detail', params: { photoId: p.id }, query: { uploader: guestId } }"
        >
          <PhotoTile :photo="p" :index="i" ratio="1/1" />
        </RouterLink>
      </div>
    </template>

    <p v-else-if="list.error" class="empty">{{ list.error }}</p>
    <p v-else-if="list.loaded" class="empty">找不到這位賓客的照片</p>
    <p v-else class="empty">載入中…</p>

    <div ref="sentinel" />
  </main>
</template>

<style scoped>
.guest {
  min-height: 100dvh;
  background: var(--c-bg);
  color: var(--c-ink);
}

.head {
  padding: calc(var(--page-top) + 24px) 16px 0;
}

.back {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 14px;
  color: var(--c-ink-soft);
}

.back svg {
  width: 16px;
  height: 16px;
}

.profile {
  padding-top: 12px;
  text-align: center;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 32px;
  margin: 0 auto;
  background: var(--c-card);
  border: 2px solid var(--c-bg);
  box-shadow: var(--shadow-raised);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--f-serif);
  font-size: 26px;
}

.name {
  margin: 10px 0 0;
  font-family: var(--f-serif);
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 1px;
}

.relation {
  margin: 2px 0 0;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--c-ink-mute);
}

.count {
  margin: 8px 0 0;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--c-ink-soft);
}

.grid {
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
}

.cell {
  border-radius: 6px;
  overflow: hidden;
}

.empty {
  margin-top: 80px;
  text-align: center;
  font-size: 13px;
  color: var(--c-ink-mute);
}
</style>
