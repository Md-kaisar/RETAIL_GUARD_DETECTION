<template>
  <span :class="['badge', colorClass]">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ status: String, type: { type: String, default: 'transaction' } })

const colorClass = computed(() => {
  const map = {
    flagged: 'badge-red', fraud: 'badge-red',
    cleared: 'badge-green', resolved: 'badge-green',
    pending: 'badge-yellow',
    unscored: 'badge-gray',
    open: 'badge-blue', new: 'badge-red',
    in_progress: 'badge-orange',
    acknowledged: 'badge-yellow',
    closed: 'badge-gray',
    FRAUD: 'badge-red', SUSPICIOUS: 'badge-orange', ANOMALY: 'badge-yellow',
    admin: 'badge-red', analyst: 'badge-blue', investigator: 'badge-orange',
  }
  return map[props.status] || 'badge-gray'
})
const label = computed(() => props.status?.replace(/_/g, ' ') || '—')
</script>
