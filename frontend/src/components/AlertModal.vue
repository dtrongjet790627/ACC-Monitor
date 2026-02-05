<template>
  <Teleport to="body">
    <!-- Full screen black flash overlay -->
    <div
      v-if="showFlash"
      class="flash-overlay"
      :class="{ active: flashActive }"
    ></div>

    <!-- Alert Modal -->
    <Transition name="alert-modal">
      <div v-if="visible" class="alert-modal-overlay" @click.self="handleClose">
        <div class="alert-modal-container">
          <!-- Terminal Header -->
          <div class="terminal-header">
            <div class="terminal-title">
              <span class="terminal-icon">[!]</span>
              <span class="terminal-text">CRITICAL ALERT</span>
            </div>
            <div class="terminal-controls">
              <span class="control-dot"></span>
              <span class="blink-cursor">_</span>
            </div>
          </div>

          <!-- Terminal Content -->
          <div class="terminal-content">
            <!-- Alert Type -->
            <div class="alert-line">
              <span class="line-prefix">&gt;</span>
              <span class="line-label">TYPE:</span>
              <span class="line-value type-critical">{{ typeText }}</span>
            </div>

            <!-- Server Name -->
            <div class="alert-line">
              <span class="line-prefix">&gt;</span>
              <span class="line-label">SERVER:</span>
              <span class="line-value server-name">{{ serverName }}</span>
            </div>

            <!-- IP Address -->
            <div class="alert-line">
              <span class="line-prefix">&gt;</span>
              <span class="line-label">IP:</span>
              <span class="line-value">{{ serverIp }}</span>
            </div>

            <!-- Timestamp -->
            <div class="alert-line">
              <span class="line-prefix">&gt;</span>
              <span class="line-label">TIME:</span>
              <span class="line-value">{{ timestamp }}</span>
            </div>

            <!-- Divider -->
            <div class="terminal-divider"></div>

            <!-- Message with typing effect -->
            <div class="alert-message">
              <span class="message-prefix">&gt;&gt;</span>
              <span class="message-text" ref="messageEl">{{ displayedMessage }}</span>
              <span class="typing-cursor" v-if="isTyping">|</span>
            </div>
          </div>

          <!-- Terminal Footer -->
          <div class="terminal-footer">
            <button class="terminal-btn" @click="handleClose">
              <span class="btn-prefix">[</span>
              <span class="btn-text">ACKNOWLEDGE</span>
              <span class="btn-suffix">]</span>
            </button>
            <div class="footer-info">
              <span class="info-text">PRESS ENTER OR CLICK TO DISMISS</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  alert: {
    type: Object,
    default: () => ({
      type: 'error',
      serverName: 'Unknown',
      serverIp: '0.0.0.0',
      message: 'Server error detected',
      timestamp: new Date().toISOString()
    })
  }
})

const emit = defineEmits(['close'])

// Typing effect state
const displayedMessage = ref('')
const isTyping = ref(false)
const messageEl = ref(null)

// Flash effect state
const showFlash = ref(false)
const flashActive = ref(false)
let flashCount = 0
let flashInterval = null

// Computed properties
const typeText = computed(() => {
  const typeMap = {
    error: 'CRITICAL ERROR',
    warning: 'WARNING',
    info: 'INFORMATION'
  }
  return typeMap[props.alert?.type] || 'CRITICAL ERROR'
})

const serverName = computed(() => props.alert?.serverName || 'Unknown')
const serverIp = computed(() => props.alert?.serverIp || '0.0.0.0')
const timestamp = computed(() => {
  if (!props.alert?.timestamp) return new Date().toLocaleString()
  const date = new Date(props.alert.timestamp)
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
})
const fullMessage = computed(() => props.alert?.message || 'Server error detected')

// Typing effect function
function startTypingEffect() {
  displayedMessage.value = ''
  isTyping.value = true

  let charIndex = 0
  const message = fullMessage.value
  const typingSpeed = 50 // 50ms per character

  const typeChar = () => {
    if (charIndex < message.length) {
      displayedMessage.value += message[charIndex]
      charIndex++
      setTimeout(typeChar, typingSpeed)
    } else {
      isTyping.value = false
    }
  }

  typeChar()
}

// Flash effect function
function triggerFlashEffect() {
  showFlash.value = true
  flashCount = 0

  const doFlash = () => {
    if (flashCount < 4) { // 2 full flashes = 4 toggles
      flashActive.value = !flashActive.value
      flashCount++
      flashInterval = setTimeout(doFlash, 100)
    } else {
      showFlash.value = false
      flashActive.value = false
    }
  }

  doFlash()
}

// Handle close
function handleClose() {
  emit('close')
}

// Keyboard handler
function handleKeydown(e) {
  if (props.visible && (e.key === 'Enter' || e.key === 'Escape')) {
    handleClose()
  }
}

// Watch for visibility changes
watch(() => props.visible, (newVal) => {
  if (newVal) {
    triggerFlashEffect()
    setTimeout(startTypingEffect, 300) // Start typing after flash
  } else {
    displayedMessage.value = ''
    isTyping.value = false
    if (flashInterval) {
      clearTimeout(flashInterval)
      flashInterval = null
    }
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (flashInterval) {
    clearTimeout(flashInterval)
  }
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

$alert-red: #ff3333;
$alert-bg: #0a0a0a;
$terminal-green: #00d4aa;

// Full screen flash overlay
.flash-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #000;
  z-index: 10000;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.05s ease;

  &.active {
    opacity: 1;
  }
}

// Modal overlay
.alert-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

// Modal container - Terminal style
.alert-modal-container {
  width: 90%;
  max-width: 600px;
  background: $alert-bg;
  border: 2px solid $alert-red;
  box-shadow:
    0 0 30px rgba($alert-red, 0.5),
    0 0 60px rgba($alert-red, 0.3),
    inset 0 0 20px rgba($alert-red, 0.1);
  font-family: $font-mono;
  animation: alertPulse 2s ease-in-out infinite;
}

@keyframes alertPulse {
  0%, 100% {
    box-shadow:
      0 0 30px rgba($alert-red, 0.5),
      0 0 60px rgba($alert-red, 0.3),
      inset 0 0 20px rgba($alert-red, 0.1);
  }
  50% {
    box-shadow:
      0 0 40px rgba($alert-red, 0.7),
      0 0 80px rgba($alert-red, 0.4),
      inset 0 0 30px rgba($alert-red, 0.15);
  }
}

// Terminal header
.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: linear-gradient(90deg, rgba($alert-red, 0.2) 0%, rgba($alert-red, 0.1) 100%);
  border-bottom: 1px solid rgba($alert-red, 0.4);
}

.terminal-title {
  display: flex;
  align-items: center;
  gap: 10px;

  .terminal-icon {
    color: $alert-red;
    font-weight: bold;
    font-size: 16px;
    animation: iconBlink 0.5s ease-in-out infinite;
  }

  .terminal-text {
    color: $alert-red;
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 2px;
    text-shadow: 0 0 10px rgba($alert-red, 0.5);
  }
}

@keyframes iconBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.terminal-controls {
  display: flex;
  align-items: center;
  gap: 8px;

  .control-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: $alert-red;
    box-shadow: 0 0 8px $alert-red;
    animation: dotPulse 1s ease-in-out infinite;
  }

  .blink-cursor {
    color: $alert-red;
    font-size: 14px;
    animation: cursorBlink 0.8s ease-in-out infinite;
  }
}

@keyframes dotPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.8; }
}

@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

// Terminal content
.terminal-content {
  padding: 20px;
}

.alert-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-size: 13px;

  .line-prefix {
    color: $alert-red;
    font-weight: bold;
  }

  .line-label {
    color: rgba(255, 255, 255, 0.5);
    min-width: 70px;
  }

  .line-value {
    color: rgba(255, 255, 255, 0.9);

    &.type-critical {
      color: $alert-red;
      font-weight: bold;
      text-shadow: 0 0 8px rgba($alert-red, 0.5);
    }

    &.server-name {
      color: $terminal-green;
      font-weight: bold;
      text-shadow: 0 0 8px rgba($terminal-green, 0.5);
    }
  }
}

.terminal-divider {
  height: 1px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba($alert-red, 0.4) 20%,
    rgba($alert-red, 0.6) 50%,
    rgba($alert-red, 0.4) 80%,
    transparent 100%);
  margin: 15px 0;
}

.alert-message {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 15px;
  background: rgba($alert-red, 0.1);
  border: 1px solid rgba($alert-red, 0.3);
  border-radius: 4px;
  min-height: 60px;

  .message-prefix {
    color: $alert-red;
    font-weight: bold;
    flex-shrink: 0;
  }

  .message-text {
    color: $alert-red;
    font-size: 14px;
    line-height: 1.5;
    text-shadow: 0 0 5px rgba($alert-red, 0.3);
  }

  .typing-cursor {
    color: $alert-red;
    font-weight: bold;
    animation: typingCursor 0.5s ease-in-out infinite;
  }
}

@keyframes typingCursor {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

// Terminal footer
.terminal-footer {
  padding: 15px 20px;
  background: rgba(0, 0, 0, 0.5);
  border-top: 1px solid rgba($alert-red, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.terminal-btn {
  background: transparent;
  border: 1px solid $alert-red;
  padding: 10px 20px;
  cursor: pointer;
  font-family: $font-mono;
  font-size: 12px;
  letter-spacing: 1px;
  transition: all 0.2s ease;

  .btn-prefix, .btn-suffix {
    color: rgba($alert-red, 0.6);
  }

  .btn-text {
    color: $alert-red;
    font-weight: bold;
  }

  &:hover {
    background: rgba($alert-red, 0.2);
    box-shadow: 0 0 15px rgba($alert-red, 0.4);

    .btn-prefix, .btn-suffix, .btn-text {
      color: #fff;
    }
  }

  &:active {
    transform: scale(0.98);
  }
}

.footer-info {
  .info-text {
    color: rgba(255, 255, 255, 0.3);
    font-size: 10px;
    letter-spacing: 1px;
  }
}

// Transition animations
.alert-modal-enter-active {
  animation: modalEnter 0.3s ease-out;
}

.alert-modal-leave-active {
  animation: modalLeave 0.2s ease-in;
}

@keyframes modalEnter {
  0% {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes modalLeave {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

// CRT effect on modal
.alert-modal-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.1) 2px,
    rgba(0, 0, 0, 0.1) 4px
  );
  pointer-events: none;
  z-index: 10;
}
</style>
