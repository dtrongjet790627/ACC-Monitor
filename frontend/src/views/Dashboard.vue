<template>
  <div class="dashboard-container">
    <!-- Top Status Bar - Enlarged -->
    <header class="top-status-bar">
      <div class="status-left">
        <div class="system-title">
          <span class="title-bracket">[</span>
          <span class="title-icon">&#9632;</span>
          <span class="title-text">SYSTEM MONITOR</span>
          <span class="title-icon">&#9632;</span>
          <span class="title-bracket">]</span>
        </div>
        <div class="status-group">
          <div class="status-item">
            <span class="stat-label">TOTAL</span>
            <span class="stat-value">{{ monitorStore.totalServers }}</span>
          </div>
          <div class="status-item online">
            <span class="stat-label">ONLINE</span>
            <span class="stat-value">{{ onlineServers }}</span>
          </div>
          <div class="status-item warning" v-if="monitorStore.warningServers > 0">
            <span class="stat-label">WARNING</span>
            <span class="stat-value">{{ monitorStore.warningServers }}</span>
          </div>
          <div class="status-item critical" v-if="monitorStore.criticalServers > 0">
            <span class="stat-label">CRITICAL</span>
            <span class="stat-value">{{ monitorStore.criticalServers }}</span>
          </div>
        </div>
      </div>
      <div class="status-center">
        <div class="realtime-indicator">
          <span class="indicator-dot" :class="{ active: wsConnected }"></span>
          <span class="indicator-text">{{ wsConnected ? 'LIVE' : 'OFFLINE' }}</span>
        </div>
      </div>
      <div class="status-right">
        <div class="incident-info" v-if="lastIncident">
          <span class="incident-label">LAST INCIDENT:</span>
          <span class="incident-value">{{ lastIncident.time }} {{ lastIncident.server }}</span>
        </div>
        <div class="uptime-info">
          <span class="uptime-label">UPTIME:</span>
          <span class="uptime-value">{{ uptimeDays }} DAYS</span>
        </div>
        <div class="ping-info">
          <span class="ping-label">AVG PING</span>
          <span class="ping-value">{{ avgPing }}ms</span>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="main-content">
      <!-- Left: Server Cards Grid -->
      <div class="servers-section">
        <div class="servers-grid">
          <ServerCardCompact
            v-for="server in monitorStore.servers"
            :key="server.id"
            :server="server"
            @click="handleServerClick"
          />
        </div>
      </div>

      <!-- Right: Guardian Panel -->
      <div class="guardian-section">
        <!-- Pixel Face -->
        <div class="face-panel">
          <PixelFace :is-online="wsConnected" />
        </div>

        <!-- System Log -->
        <div class="log-panel">
          <SystemLog :logs="systemLogs" :max-entries="8" />
        </div>
      </div>
    </div>

    <!-- Server Detail Modal -->
    <CyberModal
      v-model="showServerModal"
      :title="'[' + (selectedServer?.name || '') + '] // SERVER DETAILS'"
      width="600px"
      :show-footer="false"
    >
      <div v-if="selectedServer" class="server-detail">
        <div class="detail-section">
          <h4>> BASIC INFORMATION</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <span class="label">$ IP:</span>
              <span class="value">{{ selectedServer.ip }}</span>
            </div>
            <div class="detail-item">
              <span class="label">$ STATUS:</span>
              <span class="value" :class="'status-' + selectedServer.status">
                {{ selectedServer.status.toUpperCase() }}
              </span>
            </div>
            <div class="detail-item">
              <span class="label">$ CPU:</span>
              <span class="value">{{ selectedServer.cpuUsage }}%</span>
            </div>
            <div class="detail-item">
              <span class="label">$ MEM:</span>
              <span class="value">{{ selectedServer.memoryUsage }}%</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>> PROCESSES</h4>
          <div class="process-list">
            <div
              v-for="(process, index) in selectedServer.processes"
              :key="index"
              class="process-item"
            >
              <span class="process-prefix">>></span>
              <span class="process-name">{{ process.name }}</span>
              <span class="process-status" :class="process.status">
                {{ process.status.toUpperCase() }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </CyberModal>

    <!-- Critical Alert Modal -->
    <AlertModal
      :visible="showAlertModal"
      :alert="currentAlert"
      @close="handleAlertClose"
    />

    <!-- CRT Signal Interference Effect -->
    <div class="crt-interference" :class="{ active: showInterference }"></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import ServerCardCompact from '@/components/ServerCardCompact.vue'
import PixelFace from '@/components/PixelFace.vue'
import SystemLog from '@/components/SystemLog.vue'
import CyberModal from '@/components/CyberModal.vue'
import AlertModal from '@/components/AlertModal.vue'

const monitorStore = useMonitorStore()

// Alert modal state
const showAlertModal = ref(false)
const currentAlert = ref(null)
const alertQueue = ref([])
const previousServerStates = ref({})

// CRT interference effect state
const showInterference = ref(false)
let interferenceInterval = null

// WebSocket connection status
const wsConnected = computed(() => monitorStore.wsConnected)

// Online servers count
const onlineServers = computed(() => {
  const servers = monitorStore.servers
  if (!servers || servers.length === 0) return 0
  return servers.filter(s => s.status === 'normal').length
})

// Last incident data
const lastIncident = computed(() => {
  const alerts = monitorStore.alerts
  if (alerts && alerts.length > 0) {
    const latest = alerts[0]
    return {
      time: new Date(latest.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false }),
      server: latest.serverName || 'Unknown'
    }
  }
  return { time: '02-03 13:46', server: 'IPS_EPS' }
})

// Uptime in days
const uptimeDays = ref(145)

// Average ping
const avgPing = computed(() => {
  const servers = monitorStore.servers
  if (!servers || servers.length === 0) return 28
  const total = servers.reduce((sum, s) => sum + (s.ping || 0), 0)
  return Math.round(total / servers.length)
})

// System logs
const systemLogs = computed(() => {
  const alerts = monitorStore.alerts || []
  return alerts.slice(0, 8).map(alert => ({
    time: new Date(alert.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }),
    level: alert.level === 'error' ? 'critical' : alert.level,
    message: `${alert.serverName}: ${alert.message}`
  }))
})

// Server detail modal
const showServerModal = ref(false)
const selectedServer = ref(null)

function handleServerClick(server) {
  selectedServer.value = server
  showServerModal.value = true
}

// Handle alert modal close
function handleAlertClose() {
  showAlertModal.value = false
  currentAlert.value = null

  // Process next alert in queue
  setTimeout(() => {
    if (alertQueue.value.length > 0) {
      const nextAlert = alertQueue.value.shift()
      showCriticalAlert(nextAlert)
    }
  }, 500)
}

// Show critical alert modal
function showCriticalAlert(alert) {
  currentAlert.value = alert
  showAlertModal.value = true
}

// Trigger CRT interference effect randomly
function startInterferenceEffect() {
  interferenceInterval = setInterval(() => {
    // 5% chance to trigger interference
    if (Math.random() < 0.05) {
      showInterference.value = true
      setTimeout(() => {
        showInterference.value = false
      }, 100 + Math.random() * 200)
    }
  }, 3000)
}

// Watch for server status changes to trigger alerts
watch(() => monitorStore.servers, (newServers) => {
  if (!newServers || newServers.length === 0) return

  newServers.forEach(server => {
    const prevState = previousServerStates.value[server.id]

    // Check if server just became error state
    if (server.status === 'error' && prevState !== 'error') {
      const alert = {
        type: 'error',
        serverName: server.name,
        serverIp: server.ip,
        message: `Server ${server.name} (${server.ip}) has entered CRITICAL state. Immediate attention required. CPU: ${server.cpuUsage}%, MEM: ${server.memoryUsage}%`,
        timestamp: new Date().toISOString()
      }

      // If no alert showing, show immediately; otherwise queue it
      if (!showAlertModal.value) {
        showCriticalAlert(alert)
      } else {
        alertQueue.value.push(alert)
      }
    }

    // Update previous state
    previousServerStates.value[server.id] = server.status
  })
}, { deep: true })

onMounted(() => {
  // Start auto refresh
  monitorStore.startAutoRefresh(30000)

  // Initialize previous states
  if (monitorStore.servers) {
    monitorStore.servers.forEach(server => {
      previousServerStates.value[server.id] = server.status
    })
  }

  // Start CRT interference effect
  startInterferenceEffect()

  // Simulate connection
  setTimeout(() => {
    monitorStore.wsConnected = true
  }, 1500)
})

onUnmounted(() => {
  monitorStore.stopAutoRefresh()
  if (interferenceInterval) {
    clearInterval(interferenceInterval)
  }
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
  min-height: 100vh;
  padding: 0;
  display: flex;
  flex-direction: column;
}

// Top Status Bar - ENLARGED
.top-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(0, 0, 0, 0.95);
  border-bottom: 2px solid rgba($cyber-cyan, 0.4);
  font-family: $font-mono;
  flex-shrink: 0;
  position: relative;

  // Glow effect on bottom border
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg,
      transparent 0%,
      rgba($cyber-cyan, 0.6) 20%,
      $cyber-cyan 50%,
      rgba($cyber-cyan, 0.6) 80%,
      transparent 100%);
    box-shadow: 0 0 20px rgba($cyber-cyan, 0.4);
  }
}

.status-left {
  display: flex;
  align-items: center;
  gap: 32px;
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

    .stat-value {
      color: $cyber-yellow;
      text-shadow: 0 0 8px rgba($cyber-yellow, 0.5);
    }
  }

  &.critical {
    background: rgba($cyber-red, 0.1);
    border-color: rgba($cyber-red, 0.4);

    .stat-value {
      color: $cyber-red;
      text-shadow: 0 0 8px rgba($cyber-red, 0.5);
    }
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
    width: 10px;
    height: 10px;
    border-radius: 50%;
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
  gap: 24px;
}

.incident-info, .uptime-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;

  span:first-child {
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 1px;
  }

  span:last-child {
    color: $cyber-cyan;
    font-weight: bold;
  }
}

.ping-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
  background: rgba($cyber-cyan, 0.1);
  border: 1px solid rgba($cyber-cyan, 0.4);
  border-radius: 4px;

  .ping-label {
    font-size: 9px;
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 1px;
  }

  .ping-value {
    font-size: 16px;
    font-weight: bold;
    color: $cyber-cyan;
    text-shadow: 0 0 10px rgba($cyber-cyan, 0.6);
  }
}

// Main Content
.main-content {
  flex: 1;
  display: flex;
  padding: 24px;
  gap: 24px;
  overflow: hidden;
  height: calc(100vh - 80px);
}

// Left: Servers Section (70%) - Server Rack / Control Room Cabinet
.servers-section {
  flex: 7;
  min-width: 0;
  position: relative;
  overflow: hidden;

  // Server Rack Cabinet Background
  background:
    // Metal mesh/grille pattern (hexagonal holes)
    radial-gradient(circle at center, transparent 2px, rgba(0, 0, 0, 0.15) 2px, rgba(0, 0, 0, 0.15) 3px, transparent 3px),
    // Subtle vertical rack rail lines
    repeating-linear-gradient(90deg,
      transparent 0px,
      transparent 48px,
      rgba(40, 40, 45, 0.4) 48px,
      rgba(40, 40, 45, 0.4) 50px,
      transparent 50px,
      transparent 98px,
      rgba(40, 40, 45, 0.4) 98px,
      rgba(40, 40, 45, 0.4) 100px
    ),
    // Horizontal rack unit lines
    repeating-linear-gradient(0deg,
      transparent 0px,
      transparent 23px,
      rgba(30, 30, 35, 0.3) 23px,
      rgba(30, 30, 35, 0.3) 24px
    ),
    // Main cabinet gradient
    linear-gradient(180deg,
      rgba(18, 18, 22, 0.85) 0%,
      rgba(12, 12, 16, 0.9) 30%,
      rgba(8, 8, 12, 0.92) 70%,
      rgba(5, 5, 8, 0.85) 100%
    );
  background-size:
    12px 12px,
    100px 100%,
    100% 24px,
    100% 100%;
  border-radius: 6px;
  border: 2px solid rgba(50, 50, 55, 0.6);
  box-shadow:
    // Outer cabinet frame shadow
    0 0 30px rgba(0, 0, 0, 0.5),
    0 10px 40px rgba(0, 0, 0, 0.4),
    // Inner depth shadow
    inset 0 0 80px rgba(0, 0, 0, 0.5),
    inset 0 0 120px rgba(0, 0, 0, 0.3),
    // Subtle cyan glow from monitors
    inset 0 0 60px rgba(0, 212, 170, 0.03);

  // Rack Frame Rails (Left & Right)
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 6px;
    pointer-events: none;
    z-index: 1;
    // Frame rails on sides
    background:
      // Left rail
      linear-gradient(90deg,
        rgba(35, 35, 40, 0.8) 0px,
        rgba(45, 45, 50, 0.6) 4px,
        rgba(25, 25, 30, 0.9) 8px,
        transparent 12px
      ),
      // Right rail
      linear-gradient(270deg,
        rgba(35, 35, 40, 0.8) 0px,
        rgba(45, 45, 50, 0.6) 4px,
        rgba(25, 25, 30, 0.9) 8px,
        transparent 12px
      ),
      // Top frame
      linear-gradient(180deg,
        rgba(40, 40, 45, 0.7) 0px,
        rgba(30, 30, 35, 0.5) 3px,
        rgba(20, 20, 25, 0.8) 6px,
        transparent 10px
      ),
      // Bottom frame
      linear-gradient(0deg,
        rgba(25, 25, 30, 0.8) 0px,
        rgba(35, 35, 40, 0.5) 3px,
        rgba(20, 20, 25, 0.7) 6px,
        transparent 10px
      );
    background-size:
      12px 100%,
      12px 100%,
      100% 10px,
      100% 10px;
    background-position:
      left top,
      right top,
      top left,
      bottom left;
    background-repeat:
      no-repeat;
    box-shadow:
      // Inner frame depth
      inset 6px 0 12px rgba(0, 0, 0, 0.3),
      inset -6px 0 12px rgba(0, 0, 0, 0.3),
      inset 0 6px 12px rgba(0, 0, 0, 0.25),
      inset 0 -6px 12px rgba(0, 0, 0, 0.25);
  }

  // Top edge highlight (cabinet edge reflection)
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 15px;
    right: 15px;
    height: 1px;
    background: linear-gradient(90deg,
      transparent 0%,
      rgba(80, 80, 85, 0.4) 15%,
      rgba(100, 100, 105, 0.5) 50%,
      rgba(80, 80, 85, 0.4) 85%,
      transparent 100%);
    z-index: 2;
  }
}

// Server Cards Grid - 4x2 layout with space for monitor stands
.servers-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 28px 24px; // More vertical gap for stands
  padding: 24px 28px 32px 28px; // Extra bottom padding for stands
  height: 100%;
  align-content: center;
  position: relative;
  z-index: 5;
}

// Right: Guardian Section (30%)
.guardian-section {
  flex: 3;
  min-width: 280px;
  max-width: 360px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.face-panel {
  height: 280px;
  flex-shrink: 0;
}

.log-panel {
  flex: 1;
  min-height: 200px;
}

// Server Detail Modal
.server-detail {
  .detail-section {
    margin-bottom: 25px;

    &:last-child {
      margin-bottom: 0;
    }

    h4 {
      font-size: 12px;
      color: $cyber-cyan;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-bottom: 15px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba($cyber-cyan, 0.3);
      text-shadow: 0 0 10px rgba($cyber-cyan, 0.5);
      font-family: $font-mono;
      position: relative;

      &::after {
        content: '';
        position: absolute;
        bottom: -1px;
        left: 0;
        width: 60px;
        height: 2px;
        background: $cyber-cyan;
      }
    }
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 15px;
  }

  .detail-item {
    display: flex;
    justify-content: space-between;
    padding: 12px 16px;
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba($cyber-cyan, 0.2);
    position: relative;
    overflow: hidden;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 3px;
      height: 100%;
      background: $cyber-cyan;
      opacity: 0.6;
    }

    .label {
      color: $text-secondary;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
      font-family: $font-mono;
    }

    .value {
      color: $cyber-cyan;
      font-size: 13px;
      font-family: $font-mono;

      &.status-normal { color: $cyber-cyan; text-shadow: 0 0 10px rgba($cyber-cyan, 0.5); }
      &.status-warning { color: $cyber-yellow; text-shadow: 0 0 10px rgba($cyber-yellow, 0.5); }
      &.status-error { color: $cyber-red; text-shadow: 0 0 10px rgba($cyber-red, 0.5); }
    }
  }

  .process-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .process-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 18px;
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba($cyber-cyan, 0.2);
    transition: all 0.3s ease;

    &:hover {
      border-color: rgba($cyber-cyan, 0.5);
      background: rgba($cyber-cyan, 0.05);
    }

    .process-prefix {
      color: $cyber-cyan;
      font-size: 12px;
      font-family: $font-mono;
      opacity: 0.7;
    }

    .process-name {
      flex: 1;
      color: $text-secondary;
      font-size: 13px;
      font-family: $font-mono;
    }

    .process-status {
      font-size: 11px;
      text-transform: uppercase;
      font-weight: bold;
      letter-spacing: 1px;
      padding: 5px 14px;
      font-family: $font-mono;

      &.running {
        color: $cyber-cyan;
        background: rgba($cyber-cyan, 0.15);
        border: 1px solid rgba($cyber-cyan, 0.4);
        text-shadow: 0 0 5px rgba($cyber-cyan, 0.5);
      }

      &.stopped {
        color: $cyber-red;
        background: rgba($cyber-red, 0.15);
        border: 1px solid rgba($cyber-red, 0.4);
        text-shadow: 0 0 5px rgba($cyber-red, 0.5);
      }

      &.slow, &.warning {
        color: $cyber-yellow;
        background: rgba($cyber-yellow, 0.15);
        border: 1px solid rgba($cyber-yellow, 0.4);
        text-shadow: 0 0 5px rgba($cyber-yellow, 0.5);
      }
    }
  }
}

// Responsive
@media (max-width: 1600px) {
  .servers-grid {
    gap: 24px 20px;
    padding: 20px 24px 28px 24px;
  }

  .system-title {
    font-size: 18px;
    letter-spacing: 3px;
  }
}

@media (max-width: 1400px) {
  .servers-grid {
    padding: 18px 20px 26px 20px;
    gap: 22px 18px;
  }

  .guardian-section {
    min-width: 260px;
    max-width: 320px;
  }

  .status-group {
    gap: 8px;
  }

  .status-item {
    padding: 6px 12px;

    .stat-value {
      font-size: 14px;
    }
  }
}

@media (max-width: 1200px) {
  .main-content {
    padding: 16px;
    gap: 20px;
  }

  .servers-grid {
    padding: 16px 18px 24px 18px;
    gap: 20px 16px;
  }

  .guardian-section {
    min-width: 240px;
    max-width: 300px;
    gap: 16px;
  }

  .top-status-bar {
    padding: 12px 20px;
  }

  .system-title {
    font-size: 16px;
  }
}

@media (max-width: 1000px) {
  .main-content {
    flex-direction: column;
    height: auto;
    overflow-y: auto;
  }

  .servers-section {
    flex: none;
    min-height: 500px;
  }

  .servers-grid {
    padding: 16px 16px 24px 16px;
    gap: 18px 14px;
  }

  .guardian-section {
    flex: none;
    width: 100%;
    max-width: none;
    min-width: auto;
    flex-direction: row;
    height: 280px;
  }

  .face-panel {
    flex: 1;
    height: 100%;
  }

  .log-panel {
    flex: 1.5;
    height: 100%;
    min-height: auto;
  }

  .status-center {
    display: none;
  }
}

@media (max-width: 768px) {
  .servers-section {
    min-height: 400px;
  }

  .servers-grid {
    padding: 14px 14px 22px 14px;
    gap: 16px 12px;
  }

  .top-status-bar {
    flex-direction: column;
    gap: 12px;
    padding: 12px;
  }

  .status-left, .status-right {
    flex-wrap: wrap;
    justify-content: center;
  }

  .guardian-section {
    flex-direction: column;
    height: auto;
  }

  .face-panel {
    height: 220px;
  }

  .log-panel {
    height: 280px;
  }
}

@media (max-width: 620px) {
  .servers-section {
    min-height: 350px;
  }

  .servers-grid {
    padding: 12px 12px 20px 12px;
    gap: 14px 10px;
  }
}

// CRT Signal Interference Effect
.crt-interference {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 9998;
  opacity: 0;
  transition: opacity 0.05s ease;

  &.active {
    opacity: 1;
    animation: interferenceEffect 0.15s ease-out;
  }

  // Noise pattern
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: repeating-linear-gradient(
      0deg,
      rgba(0, 0, 0, 0.1) 0px,
      rgba(0, 0, 0, 0.1) 1px,
      transparent 1px,
      transparent 2px
    );
    animation: noiseMove 0.1s steps(3) infinite;
  }

  // Color shift overlay
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      rgba(255, 0, 0, 0.03) 0%,
      transparent 25%,
      rgba(0, 255, 0, 0.03) 50%,
      transparent 75%,
      rgba(0, 0, 255, 0.03) 100%
    );
  }
}

@keyframes interferenceEffect {
  0% {
    transform: translateX(0) skewX(0);
    filter: brightness(1);
  }
  20% {
    transform: translateX(-3px) skewX(-1deg);
    filter: brightness(1.2);
  }
  40% {
    transform: translateX(3px) skewX(1deg);
    filter: brightness(0.9);
  }
  60% {
    transform: translateX(-2px) skewX(-0.5deg);
    filter: brightness(1.1);
  }
  80% {
    transform: translateX(1px) skewX(0.5deg);
    filter: brightness(1);
  }
  100% {
    transform: translateX(0) skewX(0);
    filter: brightness(1);
  }
}

@keyframes noiseMove {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 0 10px;
  }
}
</style>
