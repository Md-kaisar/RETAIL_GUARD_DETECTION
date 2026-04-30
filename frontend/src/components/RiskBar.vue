<template>
  <div class="risk-bar">
    <div class="risk-bar-track">
      <div class="risk-bar-fill" :style="{ width: pct, background: color }" />
    </div>
    <span class="risk-label" :style="{ color }">{{ label }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ score: { type: Number, default: null } })
const pct = computed(() => props.score != null ? `${Math.round(props.score * 100)}%` : '0%')
const color = computed(() => {
  if (props.score == null) return '#5a6572'
  if (props.score >= 0.8) return '#ff4d6a'
  if (props.score >= 0.6) return '#ff8c42'
  if (props.score >= 0.3) return '#ffd166'
  return '#06d6a0'
})
const label = computed(() => props.score != null ? `${Math.round(props.score * 100)}%` : 'N/A')
</script>
