import { onBeforeUnmount, onMounted, type Ref } from 'vue'

/**
 * 捲到接近底部時呼叫 onReach，用來載入下一頁。
 * 在列表最後放一個空的元素當「哨兵」，它進入畫面就代表快到底了。
 *
 * onReach 載完後回傳「還有沒有下一頁」。還有的話會再檢查一次：一頁的照片太少、
 * 哨兵還在畫面裡時，瀏覽器不會再通知，要自己接著載。沒有了（或載入失敗）就停，不會一直重試。
 */
export function useInfiniteScroll(
  sentinel: Ref<HTMLElement | undefined>,
  onReach: () => Promise<boolean>,
) {
  let observer: IntersectionObserver | undefined

  function recheck() {
    // 重新 observe 會立刻回報一次目前是否在畫面裡
    if (!observer || !sentinel.value) return
    observer.unobserve(sentinel.value)
    observer.observe(sentinel.value)
  }

  onMounted(() => {
    // 提早 600px 開始載，使用者滑到底時下一頁通常已經出來了
    observer = new IntersectionObserver(
      async (entries) => {
        if (!entries.some((e) => e.isIntersecting)) return
        if (await onReach()) recheck()
      },
      { rootMargin: '600px 0px' },
    )
    if (sentinel.value) observer.observe(sentinel.value)
  })

  onBeforeUnmount(() => observer?.disconnect())
}
