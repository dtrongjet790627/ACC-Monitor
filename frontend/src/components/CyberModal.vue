<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="cyber-modal-overlay" @click.self="handleClose">
        <div class="cyber-modal-content" :style="{ width: width }">
          <!-- 扫描线效果 -->
          <div class="scan-line"></div>

          <!-- 边角装饰 -->
          <div class="corner top-left"></div>
          <div class="corner top-right"></div>
          <div class="corner bottom-left"></div>
          <div class="corner bottom-right"></div>

          <!-- 头部 -->
          <div class="cyber-modal-header">
            <h3 class="cyber-modal-title">
              <slot name="title">{{ title }}</slot>
            </h3>
            <button class="cyber-modal-close" @click="handleClose">X</button>
          </div>

          <!-- 内容区 -->
          <div class="cyber-modal-body">
            <slot></slot>
          </div>

          <!-- 底部按钮 -->
          <div v-if="$slots.footer || showFooter" class="cyber-modal-footer">
            <slot name="footer">
              <button class="cyber-btn cyber-btn--ghost" @click="handleClose">
                CANCEL
              </button>
              <button class="cyber-btn cyber-btn--primary" @click="handleConfirm">
                CONFIRM
              </button>
            </slot>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'SYSTEM MESSAGE'
  },
  width: {
    type: String,
    default: '500px'
  },
  showFooter: {
    type: Boolean,
    default: true
  },
  closeOnClickOverlay: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'confirm', 'close'])

function handleClose() {
  if (props.closeOnClickOverlay) {
    emit('update:modelValue', false)
    emit('close')
  }
}

function handleConfirm() {
  emit('confirm')
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;

  .cyber-modal-content {
    transition: all 0.3s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .cyber-modal-content {
    transform: translateY(-20px) scale(0.95);
    opacity: 0;
  }
}

.cyber-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(4px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cyber-modal-content {
  position: relative;
  background: linear-gradient(135deg, rgba(5, 5, 20, 0.98) 0%, rgba(10, 10, 30, 0.98) 100%);
  border: 2px solid transparent;
  border-image: linear-gradient(135deg, $neon-cyan, $neon-purple) 1;
  max-width: 90vw;
  max-height: 90vh;
  overflow: hidden;
  box-shadow:
    0 0 50px rgba($neon-cyan, 0.3),
    0 0 100px rgba($neon-purple, 0.2),
    0 20px 60px rgba(0, 0, 0, 0.8);

  .scan-line {
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, transparent, $neon-cyan, $neon-purple, transparent);
    animation: modalScan 3s linear infinite;
    z-index: 10;
  }

  .corner {
    position: absolute;
    width: 20px;
    height: 20px;
    border: 2px solid $neon-cyan;
    z-index: 5;

    &.top-left {
      top: -1px;
      left: -1px;
      border-right: none;
      border-bottom: none;
    }

    &.top-right {
      top: -1px;
      right: -1px;
      border-left: none;
      border-bottom: none;
    }

    &.bottom-left {
      bottom: -1px;
      left: -1px;
      border-right: none;
      border-top: none;
    }

    &.bottom-right {
      bottom: -1px;
      right: -1px;
      border-left: none;
      border-top: none;
    }
  }
}

@keyframes modalScan {
  0% { left: -100%; }
  100% { left: 100%; }
}

.cyber-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 25px;
  background: linear-gradient(90deg, rgba($neon-cyan, 0.1), rgba($neon-purple, 0.1));
  border-bottom: 1px solid rgba($neon-cyan, 0.3);
}

.cyber-modal-title {
  font-size: 16px;
  font-weight: 400;
  text-transform: uppercase;
  letter-spacing: 3px;
  color: $neon-cyan;
  text-shadow: 0 0 10px rgba($neon-cyan, 0.5);
}

.cyber-modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba($neon-red, 0.5);
  color: $neon-red;
  font-family: $font-mono;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba($neon-red, 0.2);
    box-shadow: 0 0 20px rgba($neon-red, 0.5);
  }
}

.cyber-modal-body {
  padding: 25px;
  color: $text-secondary;
  line-height: 1.8;
  max-height: 60vh;
  overflow-y: auto;
}

.cyber-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 25px;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba($neon-cyan, 0.2);
}
</style>
