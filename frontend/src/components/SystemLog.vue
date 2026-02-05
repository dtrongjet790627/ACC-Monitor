<template>
  <div class="system-log">
    <!-- Corner Decorations -->
    <div class="corner-decoration top-left"></div>
    <div class="corner-decoration top-right"></div>
    <div class="corner-decoration bottom-left"></div>
    <div class="corner-decoration bottom-right"></div>

    <!-- Scanlines Effect -->
    <div class="scanlines"></div>

    <!-- Header -->
    <div class="log-header">
      <div class="header-left">
        <span class="header-bracket">[</span>
        <span class="header-icon">></span>
        <span class="header-text">SYSTEM LOG</span>
        <span class="header-bracket">]</span>
      </div>
      <div class="header-right">
        <span class="live-indicator"></span>
        <span class="live-text">LIVE</span>
      </div>
    </div>

    <!-- Log entries -->
    <div class="log-entries" ref="logContainer">
      <TransitionGroup name="log-entry">
        <div
          v-for="(log, index) in displayLogs"
          :key="log.time + '-' + log.message"
          class="log-entry"
          :class="[log.level, { 'typing': index === 0 && isNewEntry }]"
        >
          <span class="log-line-number">{{ String(index + 1).padStart(2, '0') }}</span>
          <span class="log-time">{{ log.time }}</span>
          <span class="log-level" :class="log.level">[{{ log.level.toUpperCase() }}]</span>
          <span class="log-message">
            <span class="message-text" :class="{ 'typewriter': index === 0 && isNewEntry }">{{ log.message }}</span>
          </span>
        </div>
      </TransitionGroup>
    </div>

    <!-- Command line -->
    <div class="command-line">
      <span class="prompt-symbol">root@monitor</span>
      <span class="prompt-separator">:</span>
      <span class="prompt-path">~</span>
      <span class="prompt-char">$</span>
      <span class="cursor"></span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  },
  maxEntries: {
    type: Number,
    default: 8
  }
})

const logContainer = ref(null)
const isNewEntry = ref(false)
const previousLogCount = ref(0)

// Default demo logs if none provided
const defaultLogs = [
  { time: '13:46:01', level: 'critical', message: 'IPS_EPS: Connection timeout detected' },
  { time: '13:45:30', level: 'warning', message: 'SMT_EPS: High CPU usage (78%)' },
  { time: '13:45:00', level: 'info', message: 'DP_EPS: Service health check passed' },
  { time: '13:44:30', level: 'info', message: 'System monitoring initialized' },
  { time: '13:44:00', level: 'info', message: 'All services synchronized' },
  { time: '13:43:30', level: 'warning', message: 'C_EPS: Memory usage at 72%' },
  { time: '13:43:00', level: 'info', message: 'Database connection pool healthy' },
  { time: '13:42:30', level: 'info', message: 'Backup process completed' }
]

const displayLogs = computed(() => {
  const logs = props.logs.length > 0 ? props.logs : defaultLogs
  return logs.slice(0, props.maxEntries)
})

// Watch for new logs and trigger typing animation
watch(() => props.logs.length, (newCount, oldCount) => {
  if (newCount > oldCount) {
    isNewEntry.value = true
    // Reset typing state after animation completes
    setTimeout(() => {
      isNewEntry.value = false
    }, 1500)
  }
  previousLogCount.value = newCount
})

// Auto-scroll to top when new logs arrive (since newest is at top)
function scrollToTop() {
  if (logContainer.value) {
    logContainer.value.scrollTop = 0
  }
}

watch(displayLogs, () => {
  nextTick(() => {
    scrollToTop()
  })
})

onMounted(() => {
  previousLogCount.value = props.logs.length
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

// Cybercore Color System
$cyber-cyan: #00d4aa;
$cyber-cyan-glow: #00ffcc;
$cyber-yellow: #ffcc00;
$cyber-red: #ff3333;
$cyber-blue: #3b82f6;
$void-900: #0a0a0f;
$void-800: #12121a;

.system-log {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(10, 10, 15, 0.8);
  border: 1px solid rgba($cyber-cyan, 0.4);
  border-radius: 8px;
  font-family: $font-mono;
  overflow: hidden;
  backdrop-filter: blur(10px);

  // Multi-layer neon glow - matching card style
  box-shadow:
    0 0 5px rgba($cyber-cyan, 0.2),
    0 0 10px rgba($cyber-cyan, 0.1),
    0 4px 20px rgba(0, 0, 0, 0.5),
    inset 0 0 30px rgba(0, 0, 0, 0.3);
}

// Corner Decorations - Cyberpunk Style
.corner-decoration {
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid $cyber-cyan;
  box-shadow: 0 0 6px rgba($cyber-cyan, 0.5);
  z-index: 15;

  &.top-left {
    top: 4px;
    left: 4px;
    border-right: none;
    border-bottom: none;
  }

  &.top-right {
    top: 4px;
    right: 4px;
    border-left: none;
    border-bottom: none;
  }

  &.bottom-left {
    bottom: 4px;
    left: 4px;
    border-right: none;
    border-top: none;
  }

  &.bottom-right {
    bottom: 4px;
    right: 4px;
    border-left: none;
    border-top: none;
  }
}

// CRT Scanlines
.scanlines {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.08) 2px,
    rgba(0, 0, 0, 0.08) 4px
  );
  pointer-events: none;
  z-index: 10;
  opacity: 0.5;
}

.log-header {
  position: relative;
  z-index: 5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: linear-gradient(180deg, rgba($cyber-cyan, 0.15), rgba($cyber-cyan, 0.05));
  border-bottom: 1px solid rgba($cyber-cyan, 0.4);
  box-shadow: 0 0 15px rgba($cyber-cyan, 0.1);

  .header-left {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    letter-spacing: 2px;
  }

  .header-bracket {
    color: rgba($cyber-cyan, 0.5);
  }

  .header-icon {
    color: $cyber-cyan;
    text-shadow: 0 0 10px $cyber-cyan;
    animation: blink 1s step-end infinite;
  }

  .header-text {
    color: $cyber-cyan;
    font-weight: bold;
    text-shadow:
      0 0 10px rgba($cyber-cyan, 0.6),
      0 0 20px rgba($cyber-cyan, 0.3);
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .live-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: $cyber-cyan;
    box-shadow: 0 0 10px $cyber-cyan;
    animation: pulse-live 1.5s ease-in-out infinite;
  }

  .live-text {
    font-size: 10px;
    color: $cyber-cyan;
    letter-spacing: 2px;
    text-shadow: 0 0 5px rgba($cyber-cyan, 0.5);
  }
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

@keyframes pulse-live {
  0%, 100% {
    box-shadow: 0 0 10px $cyber-cyan;
    opacity: 1;
  }
  50% {
    box-shadow: 0 0 20px $cyber-cyan, 0 0 30px rgba($cyber-cyan, 0.5);
    opacity: 0.8;
  }
}

.log-entries {
  position: relative;
  z-index: 5;
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.3);
  }

  &::-webkit-scrollbar-thumb {
    background: rgba($cyber-cyan, 0.4);
    border-radius: 3px;

    &:hover {
      background: rgba($cyber-cyan, 0.6);
    }
  }
}

// Transition group animations
.log-entry-enter-active {
  animation: slideIn 0.4s ease-out;
}

.log-entry-leave-active {
  animation: fadeOut 0.3s ease-out;
}

.log-entry-move {
  transition: transform 0.3s ease;
}

@keyframes slideIn {
  0% {
    opacity: 0;
    transform: translateX(-20px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes fadeOut {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

.log-entry {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 16px;
  font-size: 11px;
  line-height: 1.4;
  border-left: 2px solid transparent;
  transition: background 0.2s ease;

  &:hover {
    background: rgba($cyber-cyan, 0.05);
  }

  &.critical {
    border-left-color: $cyber-red;
    background: rgba($cyber-red, 0.05);

    &.typing {
      animation: criticalPulse 0.5s ease-in-out 3;
    }
  }

  &.warning {
    border-left-color: $cyber-yellow;
    background: rgba($cyber-yellow, 0.03);

    &.typing {
      animation: warningPulse 0.5s ease-in-out 2;
    }
  }

  &.info {
    border-left-color: rgba($cyber-cyan, 0.4);
  }

  .log-line-number {
    color: rgba($cyber-cyan, 0.4);
    flex-shrink: 0;
    min-width: 20px;
    text-align: right;
    font-size: 10px;
  }

  .log-time {
    color: rgba($cyber-cyan, 0.7);
    flex-shrink: 0;
    min-width: 65px;
    text-shadow: 0 0 5px rgba($cyber-cyan, 0.3);
  }

  .log-level {
    flex-shrink: 0;
    font-weight: bold;
    min-width: 80px;

    &.critical {
      color: $cyber-red;
      text-shadow: 0 0 8px rgba($cyber-red, 0.6);
    }

    &.warning {
      color: $cyber-yellow;
      text-shadow: 0 0 8px rgba($cyber-yellow, 0.6);
    }

    &.info {
      color: $cyber-blue;
      text-shadow: 0 0 5px rgba($cyber-blue, 0.4);
    }
  }

  .log-message {
    color: rgba(255, 255, 255, 0.85);
    flex: 1;
    word-break: break-word;
    overflow: hidden;

    .message-text {
      display: inline;

      &.typewriter {
        animation: typewriter 1s steps(40, end);
        overflow: hidden;
        white-space: nowrap;
        display: inline-block;
        max-width: 100%;
      }
    }
  }
}

// Typewriter animation
@keyframes typewriter {
  0% {
    max-width: 0;
    opacity: 0.7;
  }
  10% {
    opacity: 1;
  }
  100% {
    max-width: 100%;
    opacity: 1;
  }
}

// Pulse animations for alerts
@keyframes criticalPulse {
  0%, 100% {
    background: rgba($cyber-red, 0.05);
    border-left-color: $cyber-red;
  }
  50% {
    background: rgba($cyber-red, 0.15);
    border-left-color: lighten($cyber-red, 10%);
  }
}

@keyframes warningPulse {
  0%, 100% {
    background: rgba($cyber-yellow, 0.03);
    border-left-color: $cyber-yellow;
  }
  50% {
    background: rgba($cyber-yellow, 0.1);
    border-left-color: lighten($cyber-yellow, 10%);
  }
}

.command-line {
  position: relative;
  z-index: 5;
  padding: 12px 16px;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.5));
  border-top: 1px solid rgba($cyber-cyan, 0.3);
  display: flex;
  align-items: center;
  gap: 0;
  font-size: 12px;
  box-shadow: 0 -5px 15px rgba(0, 0, 0, 0.2);

  .prompt-symbol {
    color: $cyber-cyan;
    text-shadow: 0 0 8px rgba($cyber-cyan, 0.5);
  }

  .prompt-separator {
    color: rgba(255, 255, 255, 0.5);
  }

  .prompt-path {
    color: $cyber-blue;
    text-shadow: 0 0 5px rgba($cyber-blue, 0.4);
  }

  .prompt-char {
    color: rgba(255, 255, 255, 0.7);
    margin-left: 2px;
    margin-right: 8px;
  }

  .cursor {
    width: 10px;
    height: 16px;
    background: $cyber-cyan;
    box-shadow: 0 0 10px $cyber-cyan;
    animation: cursorBlink 1s step-end infinite;
  }
}

@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
