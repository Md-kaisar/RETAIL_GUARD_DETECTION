import { reactive } from 'vue'

const toasts = reactive([])
let nextId = 0

export function useToast() {
  function show(message, type = 'info', duration = 4000) {
    const id = ++nextId
    toasts.push({ id, message, type })
    setTimeout(() => {
      const i = toasts.findIndex(t => t.id === id)
      if (i !== -1) toasts.splice(i, 1)
    }, duration)
  }
  return {
    success: (msg) => show(msg, 'success'),
    error: (msg) => show(msg, 'error'),
    info: (msg) => show(msg, 'info'),
  }
}

export { toasts }
