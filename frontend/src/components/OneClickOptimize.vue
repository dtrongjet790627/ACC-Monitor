<template>
  <div class="optimize-container">
    <button
      class="optimize-btn"
      :class="{ 'is-loading': isLoading, 'is-disabled': isDisabled, 'is-typing': isTyping }"
      :disabled="isLoading || isDisabled"
      @click="handleClick"
    >
      <div class="btn-background"></div>
      <div class="btn-glow"></div>
      <div class="btn-content">
        <span v-if="!isLoading" class="btn-icon">{{ icon }}</span>
        <span v-else class="btn-spinner"></span>
        <span class="btn-text">
          <span v-if="isTyping" class="typewriter-text">{{ displayText }}</span>
          <span v-else-if="isLoading">{{ progressText }}</span>
          <span v-else>{{ text }}</span>
        </span>
        <span v-if="isTyping || (!isLoading && !isTyping)" class="cursor">_</span>
      </div>
      <!-- 执行进度条 -->
      <div v-if="isLoading" class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        <div class="progress-glow"></div>
      </div>
      <div class="btn-particles">
        <span v-for="i in 6" :key="i" class="particle"></span>
      </div>
    </button>

    <!-- 确认弹窗 -->
    <CyberModal
      v-model="showConfirmModal"
      :title="confirmTitle"
      width="450px"
      @confirm="executeOptimize"
      @close="showConfirmModal = false"
    >
      <div class="confirm-content">
        <div class="confirm-icon warning">[!]</div>
        <p class="confirm-message">{{ confirmMessage }}</p>
        <div class="confirm-details" v-if="details">
          <div v-for="(item, index) in details" :key="index" class="detail-item">
            <span class="detail-label">{{ item.label }}:</span>
            <span class="detail-value">{{ item.value }}</span>
          </div>
        </div>
      </div>
    </CyberModal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import CyberModal from './CyberModal.vue'

const props = defineProps({
  text: {
    type: String,
    default: 'ONE-CLICK OPTIMIZE'
  },
  icon: {
    type: String,
    default: '[>]'
  },
  confirmTitle: {
    type: String,
    default: 'CONFIRM OPERATION'
  },
  confirmMessage: {
    type: String,
    default: 'Are you sure you want to execute this operation?'
  },
  details: {
    type: Array,
    default: null
  },
  requireConfirm: {
    type: Boolean,
    default: true
  },
  isDisabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['execute', 'success', 'error'])

const isLoading = ref(false)
const isTyping = ref(false)
const showConfirmModal = ref(false)
const displayText = ref('')
const progress = ref(0)

// Progress text with percentage
const progressText = computed(() => {
  const progressStages = [
    'INITIALIZING...',
    'SCANNING SERVERS...',
    'CLEARING TEMP FILES...',
    'ANALYZING DATABASE...',
    'OPTIMIZING...',
    'COMPLETING...'
  ]
  const stageIndex = Math.min(Math.floor(progress.value / 20), progressStages.length - 1)
  return `${progressStages[stageIndex]} [${progress.value}%]`
})

// Typewriter effect
async function typewriterEffect(text) {
  isTyping.value = true
  displayText.value = ''
  for (let i = 0; i < text.length; i++) {
    displayText.value += text[i]
    await new Promise(resolve => setTimeout(resolve, 50))
  }
  await new Promise(resolve => setTimeout(resolve, 300))
  isTyping.value = false
}

function handleClick() {
  if (props.requireConfirm) {
    typewriterEffect('CONFIRM?').then(() => {
      showConfirmModal.value = true
    })
  } else {
    executeOptimize()
  }
}

async function executeOptimize() {
  showConfirmModal.value = false
  isLoading.value = true
  progress.value = 0

  try {
    emit('execute')
    // Animate progress
    const progressInterval = setInterval(() => {
      if (progress.value < 100) {
        progress.value += Math.random() * 15 + 5
        if (progress.value > 100) progress.value = 100
      }
    }, 300)

    // Simulate operation delay
    await new Promise(resolve => setTimeout(resolve, 2500))

    clearInterval(progressInterval)
    progress.value = 100
    await new Promise(resolve => setTimeout(resolve, 300))

    emit('success')
  } catch (error) {
    emit('error', error)
  } finally {
    isLoading.value = false
    progress.value = 0
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.optimize-container {
  display: inline-block;
}

.optimize-btn {
  position: relative;
  padding: 16px 32px;
  background: transparent;
  border: 2px solid $neon-cyan;
  color: $neon-cyan;
  font-family: $font-mono;
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 3px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
  clip-path: polygon(15px 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%, 0 15px);

  .btn-background {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba($neon-cyan, 0.1), rgba($neon-purple, 0.1));
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .btn-glow {
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba($neon-cyan, 0.3) 0%, transparent 50%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .btn-content {
    position: relative;
    display: flex;
    align-items: center;
    gap: 12px;
    z-index: 2;
  }

  .btn-icon {
    font-size: 18px;
    transition: transform 0.3s ease;
  }

  .btn-spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba($neon-cyan, 0.3);
    border-top-color: $neon-cyan;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  // Typewriter cursor
  .cursor {
    animation: cursorBlink 0.8s step-end infinite;
    font-weight: bold;
    margin-left: 2px;
  }

  @keyframes cursorBlink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }

  // Progress bar
  .progress-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: rgba(0, 0, 0, 0.5);
    overflow: hidden;

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, $neon-cyan, $neon-green);
      transition: width 0.3s ease;
      position: relative;
    }

    .progress-glow {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.5),
        transparent
      );
      animation: progressGlowMove 1s linear infinite;
    }
  }

  @keyframes progressGlowMove {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  &.is-typing {
    .btn-text {
      color: $neon-green;
    }
  }

  .btn-particles {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;

    .particle {
      position: absolute;
      width: 4px;
      height: 4px;
      background: $neon-cyan;
      border-radius: 50%;
      opacity: 0;
      box-shadow: 0 0 10px $neon-cyan;

      @for $i from 1 through 6 {
        &:nth-child(#{$i}) {
          top: random(100) * 1%;
          left: random(100) * 1%;
          animation-delay: $i * 0.1s;
        }
      }
    }
  }

  &:hover:not(.is-loading):not(.is-disabled) {
    border-color: $neon-cyan;
    box-shadow: $glow-cyan;
    text-shadow: 0 0 10px $neon-cyan;

    .btn-background {
      opacity: 1;
    }

    .btn-glow {
      opacity: 1;
      animation: glowPulse 2s ease-in-out infinite;
    }

    .btn-icon {
      transform: translateX(5px);
    }

    .btn-particles .particle {
      animation: particleFloat 1s ease-out infinite;
    }
  }

  &:active:not(.is-loading):not(.is-disabled) {
    transform: scale(0.98);
  }

  &.is-loading {
    border-color: rgba($neon-cyan, 0.5);
    color: rgba($neon-cyan, 0.7);
    cursor: wait;
  }

  &.is-disabled {
    border-color: rgba($text-secondary, 0.3);
    color: rgba($text-secondary, 0.5);
    cursor: not-allowed;
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes glowPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes particleFloat {
  0% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateY(-30px) scale(0);
  }
}

.confirm-content {
  text-align: center;
  padding: 20px 0;
}

.confirm-icon {
  font-size: 48px;
  margin-bottom: 20px;

  &.warning {
    color: $neon-orange;
    text-shadow: $glow-orange;
    animation: iconPulse 1s ease-in-out infinite;
  }
}

@keyframes iconPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.confirm-message {
  font-size: 15px;
  color: $text-primary;
  margin-bottom: 20px;
  line-height: 1.6;
}

.confirm-details {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba($neon-cyan, 0.2);
  padding: 15px;
  text-align: left;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba($neon-cyan, 0.1);

  &:last-child {
    border-bottom: none;
  }
}

.detail-label {
  color: $text-secondary;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.detail-value {
  color: $neon-cyan;
  font-size: 13px;
  text-shadow: 0 0 5px rgba($neon-cyan, 0.5);
}
</style>
