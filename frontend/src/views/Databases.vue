<template>
  <div class="dashboard-container">
    <!-- Top Status Bar -->
    <header class="top-status-bar">
      <div class="status-left">
        <button class="back-btn" @click="$router.push('/')">
          <span class="bracket">[</span>
          <span class="arrow">&lt;</span>
          <span class="bracket">]</span>
        </button>
        <div class="system-title">
          <span class="title-bracket">[</span>
          <span class="title-icon">&#9671;</span>
          <span class="title-text">DATABASE MONITOR</span>
          <span class="title-icon">&#9671;</span>
          <span class="title-bracket">]</span>
        </div>
        <div class="status-group">
          <div class="status-item">
            <span class="stat-label">TOTAL</span>
            <span class="stat-value">{{ databases.length }}</span>
          </div>
          <div class="status-item online">
            <span class="stat-label">NORMAL</span>
            <span class="stat-value">{{ normalCount }}</span>
          </div>
          <div class="status-item warning" v-if="warningCount > 0">
            <span class="stat-label">WARNING</span>
            <span class="stat-value">{{ warningCount }}</span>
          </div>
          <div class="status-item critical" v-if="criticalCount > 0">
            <span class="stat-label">CRITICAL</span>
            <span class="stat-value">{{ criticalCount }}</span>
          </div>
        </div>
      </div>
      <div class="status-center">
        <div class="realtime-indicator">
          <span class="indicator-dot" :class="{ active: !loading }"></span>
          <span class="indicator-text">{{ loading ? 'SCANNING' : 'LIVE' }}</span>
        </div>
      </div>
      <div class="status-right">
        <div class="refresh-info">
          <span class="refresh-label">INTERVAL:</span>
          <span class="refresh-value">60s</span>
        </div>
        <button class="refresh-btn" @click="fetchDatabases" :disabled="loading">
          <span class="bracket">[</span>
          <span :class="{ 'spin': loading }">&#8635;</span>
          <span class="bracket">]</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="main-content">
      <!-- Left: Database Cards Grid - Server Rack Cabinet -->
      <div class="servers-section">
        <!-- Cabinet frame decorations -->
        <div class="cabinet-frame">
          <div class="cabinet-top">
            <div class="handle-left"></div>
            <div class="cabinet-label">RACK UNIT // DB-MONITOR</div>
            <div class="handle-right"></div>
          </div>
          <div class="cabinet-rail-left">
            <div class="rail-led" :class="{ active: !loading }"></div>
            <div class="rail-led warning" :class="{ active: warningCount > 0 }"></div>
            <div class="rail-led error" :class="{ active: criticalCount > 0 }"></div>
            <div class="rail-screw"></div>
            <div class="rail-screw"></div>
          </div>
          <div class="cabinet-rail-right">
            <div class="vent-slots">
              <span></span><span></span><span></span><span></span><span></span>
            </div>
            <div class="rail-screw"></div>
            <div class="rail-screw"></div>
          </div>
        </div>
        <!-- Database cards grid -->
        <div class="servers-grid">
          <DatabaseCardCompact
            v-for="dbItem in databases"
            :key="dbItem.server_id"
            :database="dbItem"
          />
        </div>
      </div>

      <!-- Right: Guardian Panel -->
      <div class="guardian-section">
        <!-- Pixel Face -->
        <div class="face-panel">
          <PixelFace :is-online="!loading" />
        </div>

        <!-- Database Alert Log -->
        <div class="log-panel">
          <DatabaseLog :alerts="alertsList" :max-entries="30" />
        </div>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading && databases.length === 0" class="loading-overlay">
      <div class="loading-text">SCANNING DATABASES<span class="loading-dots"></span></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import DatabaseCardCompact from '@/components/DatabaseCardCompact.vue'
import PixelFace from '@/components/PixelFace.vue'
import DatabaseLog from '@/components/DatabaseLog.vue'

const API_BASE = '/api'
const databases = ref([])
const alertsList = ref([])
const loading = ref(false)
let refreshInterval = null

// Computed counts
const normalCount = computed(() => databases.value.filter(d => d.status === 'normal').length)
const warningCount = computed(() => databases.value.filter(d => d.status === 'warning').length)
const criticalCount = computed(() => databases.value.filter(d => d.status === 'critical').length)

// Fetch databases from API
async function fetchDatabases() {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE}/databases`, { timeout: 30000 })
    if (response.data && response.data.data) {
      databases.value = response.data.data
    }
  } catch (error) {
    console.error('[Databases] Failed to fetch databases:', error)
  } finally {
    loading.value = false
  }
}

// Fetch database alerts
async function fetchAlerts() {
  try {
    const response = await axios.get(`${API_BASE}/oracle-ops/alerts`, {
      params: { page: 1, page_size: 50 },
      timeout: 30000
    })
    if (response.data && response.data.data && response.data.data.records) {
      alertsList.value = response.data.data.records
    }
  } catch (error) {
    console.error('[Databases] Failed to fetch alerts:', error)
  }
}

onMounted(() => {
  fetchDatabases()
  fetchAlerts()
  refreshInterval = setInterval(() => {
    fetchDatabases()
    fetchAlerts()
  }, 60000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

// Cybercore Color System
$cyber-cyan: #00d4aa;
$cyber-cyan-glow: #00ffcc;
$cyber-yellow: #ffcc00;
$cyber-red: #ff3333;

.dashboard-container {
  position: relative;
  z-index: 10;
  height: 100vh;
  padding: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: transparent;
}

// ============================================
// Top Status Bar
// ============================================
.top-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(0, 0, 0, 0.85);
  border-bottom: 2px solid rgba($cyber-cyan, 0.45);
  font-family: $font-mono;
  flex-shrink: 0;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba($cyber-cyan, 0.6) 20%, $cyber-cyan 50%, rgba($cyber-cyan, 0.6) 80%, transparent 100%);
    box-shadow: 0 0 20px rgba($cyber-cyan, 0.4);
  }
}

.status-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  background: none;
  border: 1px solid rgba($cyber-cyan, 0.3);
  color: $cyber-cyan;
  padding: 6px 12px;
  cursor: pointer;
  font-family: $font-mono;
  font-size: 14px;
  transition: all 0.2s;

  &:hover {
    background: rgba($cyber-cyan, 0.1);
    border-color: $cyber-cyan;
    box-shadow: 0 0 10px rgba($cyber-cyan, 0.3);
  }

  .bracket { opacity: 0.5; }
}

.system-title {
  font-size: 22px;
  letter-spacing: 4px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 8px;

  .title-bracket {
    color: rgba($cyber-cyan, 0.5);
    font-size: 26px;
  }

  .title-icon {
    color: $cyber-cyan;
    font-size: 10px;
    animation: title-pulse 2s ease-in-out infinite;
  }

  .title-text {
    color: $cyber-cyan;
    text-shadow:
      0 0 10px rgba($cyber-cyan, 0.6),
      0 0 20px rgba($cyber-cyan, 0.4),
      0 0 30px rgba($cyber-cyan, 0.2);
  }
}

@keyframes title-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: rgba($cyber-cyan, 0.08);
  border: 1px solid rgba($cyber-cyan, 0.3);
  border-radius: 4px;

  .stat-label {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.5);
    letter-spacing: 1px;
  }

  .stat-value {
    font-size: 18px;
    font-weight: bold;
    color: $cyber-cyan;
    text-shadow: 0 0 8px rgba($cyber-cyan, 0.5);
  }

  &.online {
    background: rgba($cyber-cyan, 0.1);
    border-color: rgba($cyber-cyan, 0.4);
  }

  &.warning {
    background: rgba($cyber-yellow, 0.1);
    border-color: rgba($cyber-yellow, 0.4);
    .stat-value { color: $cyber-yellow; text-shadow: 0 0 8px rgba($cyber-yellow, 0.5); }
  }

  &.critical {
    background: rgba($cyber-red, 0.1);
    border-color: rgba($cyber-red, 0.4);
    .stat-value { color: $cyber-red; text-shadow: 0 0 8px rgba($cyber-red, 0.5); }
  }
}

.status-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.realtime-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba($cyber-cyan, 0.3);
  border-radius: 20px;

  .indicator-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #666;
    transition: all 0.3s ease;

    &.active {
      background: $cyber-cyan;
      box-shadow: 0 0 10px $cyber-cyan;
      animation: pulse-dot 1.5s ease-in-out infinite;
    }
  }

  .indicator-text {
    font-size: 12px;
    font-weight: bold;
    letter-spacing: 2px;
    color: rgba(255, 255, 255, 0.7);
  }
}

@keyframes pulse-dot {
  0%, 100% { box-shadow: 0 0 10px $cyber-cyan; }
  50% { box-shadow: 0 0 20px $cyber-cyan, 0 0 30px rgba($cyber-cyan, 0.5); }
}

.status-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.refresh-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;

  .refresh-label {
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 1px;
  }

  .refresh-value {
    color: $cyber-cyan;
    font-weight: bold;
  }
}

.refresh-btn {
  background: none;
  border: 1px solid rgba($cyber-cyan, 0.3);
  color: $cyber-cyan;
  padding: 6px 12px;
  cursor: pointer;
  font-family: $font-mono;
  font-size: 16px;
  transition: all 0.2s;

  &:hover { background: rgba($cyber-cyan, 0.1); box-shadow: 0 0 10px rgba($cyber-cyan, 0.3); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }

  .bracket { opacity: 0.5; font-size: 14px; }
  .spin { display: inline-block; animation: spin 1s linear infinite; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ============================================
// Main Content - Left/Right Split
// ============================================
.main-content {
  flex: 1;
  display: flex;
  padding: 24px;
  gap: 24px;
  overflow: hidden;
  height: calc(100vh - 80px);
  background: transparent;
}

// ============================================
// Left: Database Cards Section (70%)
// ============================================
.servers-section {
  flex: 7;
  min-width: 0;
  position: relative;
  overflow: visible;
  margin: 8px 0;

  background:
    repeating-linear-gradient(90deg, transparent 0px, transparent 1px, rgba(255, 255, 255, 0.008) 1px, rgba(255, 255, 255, 0.008) 2px),
    repeating-linear-gradient(0deg, transparent 0px, transparent 3px, rgba(0, 212, 170, 0.012) 3px, rgba(0, 212, 170, 0.012) 4px),
    radial-gradient(circle at 10% 20%, rgba(0, 212, 170, 0.025) 0%, transparent 20%),
    radial-gradient(circle at 90% 80%, rgba(0, 212, 170, 0.025) 0%, transparent 20%),
    radial-gradient(circle at 50% 50%, rgba(0, 212, 170, 0.015) 0%, transparent 40%),
    linear-gradient(180deg, rgba(15, 18, 22, 0.88) 0%, rgba(10, 12, 16, 0.85) 50%, rgba(8, 10, 14, 0.88) 100%);
  border-radius: 8px;
  border: 1px solid rgba($cyber-cyan, 0.3);

  box-shadow:
    0 0 0 2px rgba(40, 40, 45, 0.7),
    0 0 0 4px rgba(25, 25, 30, 0.75),
    0 0 25px rgba($cyber-cyan, 0.15),
    0 0 50px rgba($cyber-cyan, 0.08),
    0 8px 32px rgba(0, 0, 0, 0.5),
    0 16px 48px rgba(0, 0, 0, 0.35),
    inset 0 0 60px rgba(0, 0, 0, 0.3),
    inset 0 0 30px rgba(0, 212, 170, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

// Rack Cabinet Top Panel
.servers-section::before {
  content: '';
  position: absolute;
  top: -20px; left: 10px; right: 10px;
  height: 20px;
  pointer-events: none;
  z-index: 10;
  background:
    repeating-linear-gradient(90deg, transparent 0px, transparent 4px, rgba(10, 15, 15, 0.92) 4px, rgba(10, 15, 15, 0.92) 6px),
    linear-gradient(90deg, transparent 0%, transparent 20%, rgba(0, 212, 170, 0.1) 50%, transparent 80%, transparent 100%),
    linear-gradient(180deg, rgba(35, 38, 42, 0.95) 0%, rgba(28, 30, 34, 0.95) 40%, rgba(22, 24, 28, 0.95) 100%);
  border-radius: 6px 6px 0 0;
  box-shadow:
    0 -2px 8px rgba(0, 0, 0, 0.4),
    inset 0 2px 4px rgba(60, 60, 65, 0.15),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3),
    0 -1px 10px rgba(0, 212, 170, 0.08);
  border-top: 1px solid rgba(0, 212, 170, 0.2);
  border-left: 1px solid rgba(60, 60, 65, 0.3);
  border-right: 1px solid rgba(60, 60, 65, 0.3);
}

// Rack Cabinet Bottom Panel
.servers-section::after {
  content: '';
  position: absolute;
  bottom: -24px; left: 10px; right: 10px;
  height: 24px;
  pointer-events: none;
  z-index: 10;
  background:
    radial-gradient(ellipse 20px 8px at 60px 16px, rgba(20, 22, 25, 0.95) 0%, transparent 100%),
    radial-gradient(ellipse 20px 8px at calc(100% - 60px) 16px, rgba(20, 22, 25, 0.95) 0%, transparent 100%),
    repeating-linear-gradient(90deg, transparent 0px, transparent 4px, rgba(10, 15, 15, 0.92) 4px, rgba(10, 15, 15, 0.92) 6px),
    linear-gradient(90deg, transparent 0%, transparent 30%, rgba(0, 212, 170, 0.08) 50%, transparent 70%, transparent 100%),
    linear-gradient(0deg, rgba(22, 24, 28, 0.95) 0%, rgba(28, 30, 34, 0.95) 60%, rgba(35, 38, 42, 0.95) 100%);
  border-radius: 0 0 6px 6px;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.5),
    inset 0 -2px 4px rgba(60, 60, 65, 0.1),
    inset 0 2px 4px rgba(0, 0, 0, 0.3),
    0 2px 10px rgba(0, 212, 170, 0.06);
  border-bottom: 1px solid rgba(0, 212, 170, 0.15);
  border-left: 1px solid rgba(50, 50, 55, 0.3);
  border-right: 1px solid rgba(50, 50, 55, 0.3);
}

// Database Cards Grid - 3x2 layout
.servers-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 28px 24px;
  padding: 32px 48px 40px 48px;
  height: 100%;
  align-content: center;
  position: relative;
  z-index: 5;

  // Inner rack structure
  &::before {
    content: '';
    position: absolute;
    top: 8px; left: 18px; right: 18px; bottom: 8px;
    pointer-events: none;
    z-index: 0;
    border-radius: 4px;

    background:
      linear-gradient(90deg, rgba(25, 28, 32, 0.95) 0px, rgba(35, 38, 42, 0.95) 2px, rgba(45, 48, 52, 0.95) 4px, rgba(35, 38, 42, 0.95) 6px, rgba(28, 31, 35, 0.95) 8px, transparent 14px),
      repeating-linear-gradient(0deg, transparent 0px, transparent 20px, rgba(0, 212, 170, 0.08) 20px, rgba(8, 12, 14, 0.9) 22px, rgba(0, 212, 170, 0.08) 24px, transparent 24px, transparent 44px),
      linear-gradient(270deg, rgba(25, 28, 32, 0.95) 0px, rgba(35, 38, 42, 0.95) 2px, rgba(45, 48, 52, 0.95) 4px, rgba(35, 38, 42, 0.95) 6px, rgba(28, 31, 35, 0.95) 8px, transparent 14px),
      repeating-linear-gradient(0deg, transparent 0px, transparent 20px, rgba(0, 212, 170, 0.08) 20px, rgba(8, 12, 14, 0.9) 22px, rgba(0, 212, 170, 0.08) 24px, transparent 24px, transparent 44px),
      repeating-linear-gradient(0deg, transparent 0%, transparent calc(50% - 2px), rgba(0, 212, 170, 0.04) calc(50% - 2px), rgba(35, 40, 45, 0.6) 50%, rgba(0, 212, 170, 0.04) calc(50% + 2px), transparent calc(50% + 2px), transparent 100%),
      linear-gradient(180deg, rgba(0, 0, 0, 0.15) 0%, rgba(0, 0, 0, 0.05) 20%, transparent 50%, rgba(0, 0, 0, 0.05) 80%, rgba(0, 0, 0, 0.15) 100%);
    background-size: 14px 100%, 10px 44px, 14px 100%, 10px 44px, 100% 100%, 100% 100%;
    background-position: left top, 2px top, right top, calc(100% - 2px) top, center center, center center;
    background-repeat: no-repeat, repeat-y, no-repeat, repeat-y, no-repeat, no-repeat;

    box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.3), inset 0 0 80px rgba(0, 0, 0, 0.15), inset 0 0 20px rgba(0, 212, 170, 0.02);
  }

  &::after {
    content: '';
    position: absolute;
    top: 8px; left: 32px; right: 32px; bottom: 8px;
    pointer-events: none;
    z-index: 1;
    background: radial-gradient(circle at center, transparent 1px, rgba(0, 212, 170, 0.015) 1px, rgba(0, 0, 0, 0.03) 2px, transparent 2px);
    background-size: 8px 8px;
    opacity: 0.6;
  }
}

// ============================================
// Cabinet Frame Decorations
// ============================================
.cabinet-frame {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  pointer-events: none;
  z-index: 8;
}

.cabinet-top {
  position: absolute;
  top: 8px; left: 50px; right: 50px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  opacity: 0.7;
  background:
    repeating-linear-gradient(90deg, transparent 0px, transparent 1px, rgba(255, 255, 255, 0.015) 1px, rgba(255, 255, 255, 0.015) 2px),
    linear-gradient(180deg, rgba(50, 55, 60, 0.85) 0%, rgba(38, 42, 48, 0.9) 50%, rgba(28, 32, 38, 0.9) 100%);
  border-radius: 4px;
  border: 1px solid rgba(0, 212, 170, 0.2);
  box-shadow: inset 0 1px 0 rgba(100, 105, 110, 0.15), 0 2px 8px rgba(0, 0, 0, 0.3), 0 0 15px rgba(0, 212, 170, 0.05);
}

.handle-left, .handle-right {
  width: 32px; height: 8px;
  background: linear-gradient(180deg, rgba(70, 75, 80, 0.95) 0%, rgba(50, 55, 60, 0.95) 40%, rgba(35, 40, 45, 0.95) 100%);
  border-radius: 2px;
  border: 1px solid rgba(0, 212, 170, 0.15);
  box-shadow: inset 0 1px 0 rgba(100, 105, 110, 0.25), 0 1px 3px rgba(0, 0, 0, 0.4), 0 0 6px rgba(0, 212, 170, 0.08);
}

.cabinet-label {
  font-family: $font-mono;
  font-size: 9px;
  letter-spacing: 2px;
  color: rgba($cyber-cyan, 0.6);
  text-shadow: 0 0 8px rgba($cyber-cyan, 0.3);
}

.cabinet-rail-left {
  position: absolute;
  left: 16px; top: 60px; bottom: 60px;
  width: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  opacity: 0.65;
  background:
    repeating-linear-gradient(180deg, transparent 0px, transparent 1px, rgba(255, 255, 255, 0.02) 1px, rgba(255, 255, 255, 0.02) 2px),
    linear-gradient(90deg, rgba(40, 45, 50, 0.7) 0%, rgba(30, 35, 40, 0.85) 50%, rgba(40, 45, 50, 0.7) 100%);
  border-radius: 3px;
  border: 1px solid rgba(0, 212, 170, 0.12);
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3), 0 0 8px rgba(0, 212, 170, 0.05);
}

.rail-led {
  width: 6px; height: 6px; border-radius: 50%;
  background: #1a1a1e;
  border: 1px solid rgba(40, 40, 45, 0.6);
  transition: all 0.3s ease;

  &.active {
    background: $cyber-cyan;
    box-shadow: 0 0 8px $cyber-cyan, 0 0 12px rgba($cyber-cyan, 0.5);
    animation: led-pulse 2s ease-in-out infinite;
  }

  &.warning.active {
    background: $cyber-yellow;
    box-shadow: 0 0 8px $cyber-yellow, 0 0 12px rgba($cyber-yellow, 0.5);
    animation: led-blink-fast 0.5s ease-in-out infinite;
  }

  &.error.active {
    background: $cyber-red;
    box-shadow: 0 0 8px $cyber-red, 0 0 12px rgba($cyber-red, 0.5);
    animation: led-blink-fast 0.3s ease-in-out infinite;
  }
}

@keyframes led-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes led-blink-fast {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.rail-screw {
  width: 8px; height: 8px; border-radius: 50%;
  opacity: 0.6;
  background: linear-gradient(135deg, rgba(70, 75, 80, 0.95) 0%, rgba(55, 60, 65, 0.95) 30%, rgba(40, 45, 50, 0.95) 70%, rgba(55, 60, 65, 0.95) 100%);
  border: 1px solid rgba(0, 212, 170, 0.1);
  margin-top: auto;
  box-shadow: 0 0 4px rgba(0, 212, 170, 0.05);

  &:last-child { margin-top: 8px; margin-bottom: 0; }

  &::after {
    content: '';
    display: block;
    width: 5px; height: 1px;
    background: rgba(15, 20, 25, 0.85);
    margin: 3px auto 0;
  }
}

.cabinet-rail-right {
  position: absolute;
  right: 16px; top: 60px; bottom: 60px;
  width: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  opacity: 0.65;
  background:
    repeating-linear-gradient(180deg, transparent 0px, transparent 1px, rgba(255, 255, 255, 0.02) 1px, rgba(255, 255, 255, 0.02) 2px),
    linear-gradient(270deg, rgba(40, 45, 50, 0.7) 0%, rgba(30, 35, 40, 0.85) 50%, rgba(40, 45, 50, 0.7) 100%);
  border-radius: 3px;
  border: 1px solid rgba(0, 212, 170, 0.12);
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.3), 0 0 8px rgba(0, 212, 170, 0.05);
}

.vent-slots {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-top: 4px;

  span {
    width: 14px; height: 2px;
    background: rgba(0, 0, 0, 0.6);
    border-radius: 1px;
    box-shadow: inset 0 1px 0 rgba(0, 0, 0, 0.3), 0 1px 0 rgba(0, 212, 170, 0.03);
  }
}

// ============================================
// Right: Guardian Section (30%)
// ============================================
.guardian-section {
  flex: 3;
  min-width: 280px;
  max-width: 360px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
  min-height: 0;
  background: transparent;
}

.face-panel {
  height: 280px;
  flex-shrink: 0;
}

.log-panel {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

// ============================================
// Loading Overlay
// ============================================
.loading-overlay {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  z-index: 100;
}

.loading-text {
  font-family: $font-terminal;
  font-size: 16px;
  color: $neon-green;
  letter-spacing: 3px;
  text-shadow: 0 0 15px rgba($neon-green, 0.5);
}

.loading-dots::after {
  content: '';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0% { content: ''; }
  25% { content: '.'; }
  50% { content: '..'; }
  75% { content: '...'; }
  100% { content: ''; }
}

// ============================================
// Responsive
// ============================================
@media (max-width: 1400px) {
  .servers-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 20px 18px;
    padding: 28px 36px 36px 36px;
  }

  .guardian-section {
    min-width: 260px;
    max-width: 320px;
  }
}

@media (max-width: 1200px) {
  .main-content {
    flex-direction: column;
    overflow-y: auto;
  }

  .servers-section {
    flex: none;
    height: auto;
    min-height: 500px;
  }

  .guardian-section {
    flex: none;
    max-width: none;
    min-width: 0;
    flex-direction: row;
    height: 350px;
  }

  .face-panel {
    height: 100%;
    width: 300px;
    flex-shrink: 0;
  }

  .log-panel {
    flex: 1;
    height: 100%;
  }
}

@media (max-width: 768px) {
  .servers-grid {
    grid-template-columns: repeat(2, 1fr);
    grid-template-rows: auto;
  }

  .top-status-bar {
    padding: 12px 16px;
    flex-wrap: wrap;
    gap: 8px;
  }

  .system-title {
    font-size: 16px;
    .title-bracket { font-size: 20px; }
  }

  .status-group {
    display: none;
  }

  .guardian-section {
    flex-direction: column;
    height: auto;
  }

  .face-panel {
    width: 100%;
    height: 200px;
  }

  .log-panel {
    height: 300px;
  }
}
</style>
