<template>
  <div class="database-log">
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
        <span class="header-text">DATABASE ALERTS</span>
        <span class="header-bracket">]</span>
      </div>
      <div class="header-right">
        <span class="live-indicator"></span>
        <span class="live-text">LIVE</span>
      </div>
    </div>

    <!-- Alert table -->
    <div class="log-entries" ref="logContainer"
         @mouseenter="isHovering = true"
         @mouseleave="isHovering = false">
      <!-- Empty state -->
      <div v-if="displayAlerts.length === 0" class="empty-state">
        <span class="empty-icon">&gt;_</span>
        <span class="empty-text">No database alerts...</span>
        <span class="empty-cursor"></span>
      </div>
      <template v-else>
        <div
          v-for="(alert, index) in displayAlerts"
          :key="alert.id || (alert.triggered_at + '-' + alert.message)"
          class="log-entry"
          :class="[alert.severity?.toLowerCase() || 'info', { 'expanded': hoveredIndex === index }]"
          @mouseenter="hoveredIndex = index"
          @mouseleave="hoveredIndex = -1"
        >
          <span class="log-line-number">{{ String(index + 1).padStart(2, '0') }}</span>
          <span class="log-severity" :class="alert.severity?.toLowerCase() || 'info'">
            [{{ (alert.severity || 'INFO').toUpperCase() }}]
          </span>
          <span class="log-server">{{ alert.server_name || alert.server_id || '--' }}</span>
          <span class="log-message">
            <span class="message-text">{{ alert.message }}</span>
          </span>
          <!-- Expanded detail panel on hover -->
          <div v-if="hoveredIndex === index" class="log-detail">
            <div class="detail-row">
              <span class="detail-label">SEVERITY:</span>
              <span class="detail-value" :class="alert.severity?.toLowerCase()">{{ (alert.severity || 'INFO').toUpperCase() }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">SERVER:</span>
              <span class="detail-value">{{ alert.server_name || alert.server_id || '--' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">TYPE:</span>
              <span class="detail-value">{{ alert.alert_type || '--' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">MESSAGE:</span>
              <span class="detail-value full-message">{{ alert.message }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">TRIGGERED:</span>
              <span class="detail-value">{{ formatTime(alert.triggered_at) }}</span>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Command line -->
    <div class="command-line">
      <span class="prompt-symbol">oracle@db-monitor</span>
      <span class="prompt-separator">:</span>
      <span class="prompt-path">~</span>
      <span class="prompt-char">$</span>
      <span class="cursor"></span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  alerts: {
    type: Array,
    default: () => []
  },
  maxEntries: {
    type: Number,
    default: 30
  }
})

const logContainer = ref(null)
const hoveredIndex = ref(-1)
const isHovering = ref(false)
let scrollInterval = null

const displayAlerts = computed(() => {
  return props.alerts.slice(0, props.maxEntries)
})

function formatTime(ts) {
  if (!ts) return '--'
  try {
    const d = new Date(ts)
    if (isNaN(d.getTime())) return ts
    return d.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return ts
  }
}

// Auto-scroll
function startAutoScroll() {
  scrollInterval = setInterval(() => {
    if (!isHovering.value && logContainer.value) {
      const el = logContainer.value
      const maxScroll = el.scrollHeight - el.clientHeight
      if (maxScroll > 0) {
        if (el.scrollTop >= maxScroll) {
          el.scrollTop = 0
        } else {
          el.scrollTop += 2
        }
      }
    }
  }, 100)
}

function stopAutoScroll() {
  if (scrollInterval) {
    clearInterval(scrollInterval)
    scrollInterval = null
  }
}

onMounted(() => {
  startAutoScroll()
})

onUnmounted(() => {
  stopAutoScroll()
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

.database-log {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(8, 10, 14, 0.92);
  border: 1px solid rgba($cyber-cyan, 0.4);
  border-radius: 8px;
  font-family: $font-mono;
  overflow: hidden;

  box-shadow:
    0 0 8px rgba($cyber-cyan, 0.25),
    0 0 15px rgba($cyber-cyan, 0.12),
    0 4px 20px rgba(0, 0, 0, 0.45),
    inset 0 0 25px rgba(0, 0, 0, 0.15);
}

// Corner Decorations
.corner-decoration {
  position: absolute;
  width: 16px;
  height: 16px;
  border: 2px solid $cyber-cyan;
  box-shadow: 0 0 6px rgba($cyber-cyan, 0.5);
  z-index: 15;

  &.top-left { top: 4px; left: 4px; border-right: none; border-bottom: none; }
  &.top-right { top: 4px; right: 4px; border-left: none; border-bottom: none; }
  &.bottom-left { bottom: 4px; left: 4px; border-right: none; border-top: none; }
  &.bottom-right { bottom: 4px; right: 4px; border-left: none; border-top: none; }
}

// CRT Scanlines
.scanlines {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 0, 0, 0.04) 2px, rgba(0, 0, 0, 0.04) 4px);
  pointer-events: none;
  z-index: 10;
  opacity: 0.3;
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

  .header-bracket { color: rgba($cyber-cyan, 0.5); }

  .header-icon {
    color: $cyber-cyan;
    text-shadow: 0 0 10px $cyber-cyan;
    animation: blink 1s step-end infinite;
  }

  .header-text {
    color: $cyber-cyan;
    font-weight: bold;
    text-shadow: 0 0 10px rgba($cyber-cyan, 0.6), 0 0 20px rgba($cyber-cyan, 0.3);
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .live-indicator {
    width: 8px; height: 8px; border-radius: 50%;
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
  0%, 100% { box-shadow: 0 0 10px $cyber-cyan; opacity: 1; }
  50% { box-shadow: 0 0 20px $cyber-cyan, 0 0 30px rgba($cyber-cyan, 0.5); opacity: 0.8; }
}

.log-entries {
  position: relative;
  z-index: 5;
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;

  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.3); }
  &::-webkit-scrollbar-thumb {
    background: rgba($cyber-cyan, 0.4);
    border-radius: 3px;
    &:hover { background: rgba($cyber-cyan, 0.6); }
  }
}

.log-entry {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 16px;
  font-size: 11px;
  line-height: 1.4;
  border-left: 2px solid transparent;
  transition: background 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
  flex-wrap: wrap;
  position: relative;

  &:hover { background: rgba($cyber-cyan, 0.05); }

  &.expanded {
    background: rgba($cyber-cyan, 0.08);
    white-space: normal;
    .log-message .message-text {
      white-space: normal;
      overflow: visible;
      text-overflow: unset;
    }
  }

  &.critical, &.error {
    border-left-color: $cyber-red;
    background: rgba($cyber-red, 0.05);
    &.expanded { background: rgba($cyber-red, 0.08); }
  }

  &.warning {
    border-left-color: $cyber-yellow;
    background: rgba($cyber-yellow, 0.03);
    &.expanded { background: rgba($cyber-yellow, 0.06); }
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

  .log-severity {
    flex-shrink: 0;
    font-weight: bold;
    min-width: 80px;

    &.critical, &.error {
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

  .log-server {
    color: rgba($cyber-cyan, 0.7);
    flex-shrink: 0;
    min-width: 80px;
    font-size: 10px;
    text-shadow: 0 0 5px rgba($cyber-cyan, 0.3);
  }

  .log-message {
    color: rgba(255, 255, 255, 0.85);
    flex: 1;
    overflow: hidden;
    display: flex;
    align-items: center;
    min-width: 0;

    .message-text {
      display: inline-block;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 100%;
    }
  }

  // Expanded detail panel
  .log-detail {
    width: 100%;
    padding: 6px 0 4px 30px;
    animation: detailFadeIn 0.2s ease-out;

    .detail-row {
      display: flex;
      gap: 8px;
      font-size: 10px;
      padding: 2px 0;
    }

    .detail-label {
      color: rgba($cyber-cyan, 0.5);
      min-width: 70px;
      flex-shrink: 0;
      font-weight: bold;
      letter-spacing: 0.5px;
    }

    .detail-value {
      color: rgba(255, 255, 255, 0.7);

      &.warning { color: $cyber-yellow; }
      &.critical, &.error { color: $cyber-red; }
      &.info { color: $cyber-blue; }
    }

    .full-message {
      white-space: pre-wrap;
      word-break: break-all;
    }
  }
}

@keyframes detailFadeIn {
  0% { opacity: 0; transform: translateY(-4px); }
  100% { opacity: 1; transform: translateY(0); }
}

// Empty state
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 100%;
  padding: 24px 16px;
  font-family: $font-mono;

  .empty-icon {
    color: rgba($cyber-cyan, 0.5);
    font-size: 14px;
    text-shadow: 0 0 8px rgba($cyber-cyan, 0.3);
  }

  .empty-text {
    color: rgba($cyber-cyan, 0.45);
    font-size: 12px;
    letter-spacing: 1.5px;
    text-shadow: 0 0 6px rgba($cyber-cyan, 0.2);
  }

  .empty-cursor {
    display: inline-block;
    width: 8px; height: 14px;
    background: rgba($cyber-cyan, 0.5);
    animation: cursorBlink 1s step-end infinite;
    box-shadow: 0 0 6px rgba($cyber-cyan, 0.3);
  }
}

@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
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

  .prompt-separator { color: rgba(255, 255, 255, 0.5); }

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
    width: 10px; height: 16px;
    background: $cyber-cyan;
    box-shadow: 0 0 10px $cyber-cyan;
    animation: cursorBlink 1s step-end infinite;
  }
}
</style>
