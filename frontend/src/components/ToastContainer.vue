<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div v-for="t in toasts" :key="t.id" :class="['toast', t.type]">
        <span class="toast-icon">{{ icons[t.type] }}</span>
        {{ t.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { toasts } from '@/utils/toast'
const icons = { success: '✓', error: '✕', info: 'ℹ' }
</script>

<style scoped>
.toast-leave-active { transition: all 0.2s ease; }
.toast-leave-to { opacity: 0; transform: translateX(100%); }
.toast-icon { font-weight: 700; }
</style>
