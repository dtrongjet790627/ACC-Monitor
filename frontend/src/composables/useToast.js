import { inject } from 'vue'

export function useToast() {
  const toast = inject('toast')

  if (!toast) {
    // 如果没有注入toast，返回console版本作为fallback
    return {
      success: (message) => console.log('[Toast Success]', message),
      warning: (message) => console.warn('[Toast Warning]', message),
      error: (message) => console.error('[Toast Error]', message),
      info: (message) => console.info('[Toast Info]', message)
    }
  }

  return toast
}
