<script setup lang="ts">
/**
 * 新人名字中間的手寫風愛心，一筆畫成：左邊拖一點尾巴，右邊收一個往回捲的小圈。
 * 取代原本 Cormorant 斜體的「&」：那個字型的 & 是花體，很多人認不出來。
 * 大小跟著字級（1em），顏色跟著 currentColor。
 */
</script>

<template>
  <svg
    class="heart"
    viewBox="0 0 48 38"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    role="img"
    aria-label="愛"
  >
    <path
      d="M3 31C8 30 14 30 21 34 12 27 4.5 19 6.5 11 8.5 3.5 18 3 21.5 11.5 25 3 35.5 3.5 37 11.5 38.5 20 30 27 21 34 25 30.5 31 26 37 25.5 41 25 43 28 40.5 29.5"
    />
  </svg>
</template>

<style scoped>
.heart {
  display: inline-block;
  width: 1.25em;
  height: 1em;
  margin: 0 0.1em;
  /* 跟中文字的視覺中線對齊 */
  vertical-align: -0.12em;
  overflow: visible;
  /* 稍微往左傾，比較像隨手畫的 */
  transform: rotate(-8deg);
}
</style>
