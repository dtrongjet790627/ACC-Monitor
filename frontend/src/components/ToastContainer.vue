<template>
  <Teleport to="body">
    <div class="cyber-toast">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="cyber-toast-item"
          :class="[`cyber-toast-item--${toast.type}`]"
        >
          <span class="cyber-toast-icon">{{ getIcon(toast.type) }}</span>
          <span class="cyber-toast-message">{{ toast.message }}</span>
          <button class="cyber-toast-close" @click="removeToast(toast.id)">x</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, provide } from 'vue'

const toasts = ref([])

function addToast(options) {
  const toast = {
    id: Date.now() + Math.random(),
    type: options.type || 'info',
    message: options.message,
    duration: options.duration || 3000
  }

  toasts.value.push(toast)

  if (toast.duration > 0) {
    setTimeout(() => {
      removeToast(toast.id)
    }, toast.duration)
  }
}

function removeToast(id) {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

function getIcon(type) {
  const icons = {
    success: '[OK]',
    warning: '[!]',
    error: '[X]',
    info: '[i]'
  }
  return icons[type] || icons.info
}

// 提供给全局使用
provide('toast', {
  success: (message, duration) => addToast({ type: 'success', message, duration }),
  warning: (message, duration) => addToast({ type: 'warning', message, duration }),
  error: (message, duration) => addToast({ type: 'error', message, duration }),
  info: (message, duration) => addToast({ type: 'info', message, duration })
})

// 暴露给外部使用
defineExpose({
  success: (message, duration) => addToast({ type: 'success', message, duration }),
  warning: (message, duration) => addToast({ type: 'warning', message, duration }),
  error: (message, duration) => addToast({ type: 'error', message, duration }),
  info: (message, duration) => addToast({ type: 'info', message, duration })
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.toast-move {
  transition: transform 0.3s ease;
}
</style>
