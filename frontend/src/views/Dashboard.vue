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
      <!-- Left: Server Cards Grid - Server Rack Cabinet -->
      <div class="servers-section">
        <!-- Cabinet frame decorations -->
        <div class="cabinet-frame">
          <!-- Top frame with handles -->
          <div class="cabinet-top">
            <div class="handle-left"></div>
            <div class="cabinet-label">RACK UNIT // SYS-MONITOR</div>
            <div class="handle-right"></div>
          </div>
          <!-- Left rail with status LEDs -->
          <div class="cabinet-rail-left">
            <div class="rail-led" :class="{ active: wsConnected }"></div>
            <div class="rail-led warning" :class="{ active: monitorStore.warningServers > 0 }"></div>
            <div class="rail-led error" :class="{ active: monitorStore.criticalServers > 0 }"></div>
            <div class="rail-screw"></div>
            <div class="rail-screw"></div>
          </div>
          <!-- Right rail with ventilation -->
          <div class="cabinet-rail-right">
            <div class="vent-slots">
              <span></span><span></span><span></span><span></span><span></span>
            </div>
            <div class="rail-screw"></div>
            <div class="rail-screw"></div>
          </div>
        </div>
        <!-- Server cards grid -->
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

// Top Status Bar - ENLARGED with transparency for matrix rain visibility
.top-status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
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

// Left: Servers Section (70%) - Real Server Rack Cabinet
.servers-section {
  flex: 7;
  min-width: 0;
  position: relative;
  overflow: visible;
  margin: 8px 0;

  // Server Rack Cabinet Frame - Main container with 3D depth
  background: linear-gradient(180deg,
    #1a1a1e 0%,
    #141418 50%,
    #0e0e12 100%
  );
  border-radius: 8px;

  // Cabinet outer frame (thick metal border)
  border: none;
  box-shadow:
    // Outer cabinet frame
    0 0 0 3px #2a2a2e,
    0 0 0 6px #1e1e22,
    0 0 0 8px #161618,
    // 3D depth shadow
    0 8px 32px rgba(0, 0, 0, 0.6),
    0 16px 48px rgba(0, 0, 0, 0.4),
    // Inner depth
    inset 0 0 60px rgba(0, 0, 0, 0.5),
    // Subtle cyan glow from monitors inside
    inset 0 0 40px rgba(0, 212, 170, 0.02);
}

// Rack Cabinet Top Panel (with ventilation grilles)
.servers-section::before {
  content: '';
  position: absolute;
  top: -20px;
  left: 10px;
  right: 10px;
  height: 20px;
  pointer-events: none;
  z-index: 10;
  // Top panel with ventilation holes
  background:
    // Ventilation grille pattern
    repeating-linear-gradient(90deg,
      transparent 0px,
      transparent 4px,
      rgba(15, 15, 18, 0.95) 4px,
      rgba(15, 15, 18, 0.95) 6px
    ),
    // Top panel base
    linear-gradient(180deg,
      #2a2a2e 0%,
      #222226 40%,
      #1a1a1e 100%
    );
  border-radius: 6px 6px 0 0;
  box-shadow:
    // Top panel depth
    0 -2px 8px rgba(0, 0, 0, 0.4),
    inset 0 2px 4px rgba(60, 60, 65, 0.15),
    inset 0 -2px 4px rgba(0, 0, 0, 0.3);
  // Metal edge highlight
  border-top: 1px solid rgba(70, 70, 75, 0.4);
  border-left: 1px solid rgba(60, 60, 65, 0.3);
  border-right: 1px solid rgba(60, 60, 65, 0.3);
}

// Rack Cabinet Bottom Panel (with feet/casters)
.servers-section::after {
  content: '';
  position: absolute;
  bottom: -24px;
  left: 10px;
  right: 10px;
  height: 24px;
  pointer-events: none;
  z-index: 10;
  // Bottom panel with caster/feet indicators
  background:
    // Caster wheel indicators
    radial-gradient(ellipse 20px 8px at 60px 16px, #1a1a1e 0%, transparent 100%),
    radial-gradient(ellipse 20px 8px at calc(100% - 60px) 16px, #1a1a1e 0%, transparent 100%),
    // Ventilation grille
    repeating-linear-gradient(90deg,
      transparent 0px,
      transparent 4px,
      rgba(15, 15, 18, 0.95) 4px,
      rgba(15, 15, 18, 0.95) 6px
    ),
    // Bottom panel base
    linear-gradient(0deg,
      #1a1a1e 0%,
      #222226 60%,
      #2a2a2e 100%
    );
  border-radius: 0 0 6px 6px;
  box-shadow:
    // Bottom panel depth
    0 4px 12px rgba(0, 0, 0, 0.5),
    inset 0 -2px 4px rgba(60, 60, 65, 0.1),
    inset 0 2px 4px rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(40, 40, 45, 0.5);
  border-left: 1px solid rgba(50, 50, 55, 0.3);
  border-right: 1px solid rgba(50, 50, 55, 0.3);
}

// Server Cards Grid - 4x2 layout inside rack cabinet
.servers-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 28px 24px;
  padding: 32px 48px 40px 48px; // Extra padding for rack rails
  height: 100%;
  align-content: center;
  position: relative;
  z-index: 5;

  // Inner rack structure with U-rails
  &::before {
    content: '';
    position: absolute;
    top: 8px;
    left: 18px;
    right: 18px;
    bottom: 8px;
    pointer-events: none;
    z-index: 0;
    border-radius: 4px;

    // Left and Right vertical rack rails (U-slot pattern)
    background:
      // Left U-rail
      linear-gradient(90deg,
        #1e1e22 0px,
        #2a2a2e 2px,
        #323236 4px,
        #2a2a2e 6px,
        #222226 8px,
        transparent 14px
      ),
      // Left rail mounting holes (repeating pattern)
      repeating-linear-gradient(0deg,
        transparent 0px,
        transparent 20px,
        rgba(10, 10, 12, 0.8) 20px,
        rgba(10, 10, 12, 0.8) 24px,
        transparent 24px,
        transparent 44px
      ),
      // Right U-rail
      linear-gradient(270deg,
        #1e1e22 0px,
        #2a2a2e 2px,
        #323236 4px,
        #2a2a2e 6px,
        #222226 8px,
        transparent 14px
      ),
      // Right rail mounting holes
      repeating-linear-gradient(0deg,
        transparent 0px,
        transparent 20px,
        rgba(10, 10, 12, 0.8) 20px,
        rgba(10, 10, 12, 0.8) 24px,
        transparent 24px,
        transparent 44px
      ),
      // Horizontal rack unit dividers
      repeating-linear-gradient(0deg,
        transparent 0%,
        transparent calc(50% - 2px),
        rgba(30, 30, 35, 0.5) calc(50% - 2px),
        rgba(35, 35, 40, 0.6) 50%,
        rgba(30, 30, 35, 0.5) calc(50% + 2px),
        transparent calc(50% + 2px),
        transparent 100%
      ),
      // Inner cabinet depth gradient
      linear-gradient(180deg,
        rgba(0, 0, 0, 0.3) 0%,
        rgba(0, 0, 0, 0.1) 20%,
        transparent 50%,
        rgba(0, 0, 0, 0.1) 80%,
        rgba(0, 0, 0, 0.3) 100%
      );
    background-size:
      14px 100%,
      10px 44px,
      14px 100%,
      10px 44px,
      100% 100%,
      100% 100%;
    background-position:
      left top,
      2px top,
      right top,
      calc(100% - 2px) top,
      center center,
      center center;
    background-repeat:
      no-repeat,
      repeat-y,
      no-repeat,
      repeat-y,
      no-repeat,
      no-repeat;

    // Inner shadow for depth
    box-shadow:
      inset 0 0 40px rgba(0, 0, 0, 0.4),
      inset 0 0 80px rgba(0, 0, 0, 0.2);
  }

  // Subtle mesh/grille overlay for airflow visual
  &::after {
    content: '';
    position: absolute;
    top: 8px;
    left: 32px;
    right: 32px;
    bottom: 8px;
    pointer-events: none;
    z-index: 1;
    // Hexagonal mesh pattern (ventilation)
    background:
      radial-gradient(circle at center, transparent 1px, rgba(0, 0, 0, 0.05) 1px, rgba(0, 0, 0, 0.05) 2px, transparent 2px);
    background-size: 8px 8px;
    opacity: 0.5;
  }
}

// Cabinet Frame Decorations
.cabinet-frame {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 8;
}

// Cabinet Top Bar with handles and label
.cabinet-top {
  position: absolute;
  top: 8px;
  left: 50px;
  right: 50px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: linear-gradient(180deg,
    rgba(45, 45, 50, 0.8) 0%,
    rgba(35, 35, 40, 0.9) 50%,
    rgba(25, 25, 30, 0.9) 100%
  );
  border-radius: 4px;
  border: 1px solid rgba(60, 60, 65, 0.5);
  box-shadow:
    inset 0 1px 0 rgba(80, 80, 85, 0.2),
    0 2px 8px rgba(0, 0, 0, 0.3);
}

// Door handles
.handle-left, .handle-right {
  width: 32px;
  height: 8px;
  background: linear-gradient(180deg,
    #4a4a4e 0%,
    #3a3a3e 40%,
    #2a2a2e 100%
  );
  border-radius: 2px;
  border: 1px solid rgba(70, 70, 75, 0.5);
  box-shadow:
    inset 0 1px 0 rgba(90, 90, 95, 0.3),
    0 1px 3px rgba(0, 0, 0, 0.4);
}

// Cabinet label
.cabinet-label {
  font-family: $font-mono;
  font-size: 9px;
  letter-spacing: 2px;
  color: rgba($cyber-cyan, 0.6);
  text-shadow: 0 0 8px rgba($cyber-cyan, 0.3);
}

// Left Rail with LEDs
.cabinet-rail-left {
  position: absolute;
  left: 16px;
  top: 60px;
  bottom: 60px;
  width: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  background: linear-gradient(90deg,
    rgba(35, 35, 40, 0.6) 0%,
    rgba(28, 28, 32, 0.8) 50%,
    rgba(35, 35, 40, 0.6) 100%
  );
  border-radius: 3px;
  border: 1px solid rgba(50, 50, 55, 0.4);
}

// Status LEDs
.rail-led {
  width: 6px;
  height: 6px;
  border-radius: 50%;
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
    animation: led-blink 0.5s ease-in-out infinite;
  }

  &.error.active {
    background: $cyber-red;
    box-shadow: 0 0 8px $cyber-red, 0 0 12px rgba($cyber-red, 0.5);
    animation: led-blink 0.3s ease-in-out infinite;
  }
}

@keyframes led-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes led-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

// Rail screws
.rail-screw {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg,
    #4a4a4e 0%,
    #3a3a3e 30%,
    #2a2a2e 70%,
    #3a3a3e 100%
  );
  border: 1px solid rgba(60, 60, 65, 0.4);
  margin-top: auto;

  &:last-child {
    margin-top: 8px;
    margin-bottom: 0;
  }

  // Screw slot
  &::after {
    content: '';
    display: block;
    width: 5px;
    height: 1px;
    background: rgba(20, 20, 25, 0.8);
    margin: 3px auto 0;
  }
}

// Right Rail with ventilation
.cabinet-rail-right {
  position: absolute;
  right: 16px;
  top: 60px;
  bottom: 60px;
  width: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  background: linear-gradient(270deg,
    rgba(35, 35, 40, 0.6) 0%,
    rgba(28, 28, 32, 0.8) 50%,
    rgba(35, 35, 40, 0.6) 100%
  );
  border-radius: 3px;
  border: 1px solid rgba(50, 50, 55, 0.4);
}

// Ventilation slots
.vent-slots {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;

  span {
    width: 10px;
    height: 3px;
    background: rgba(10, 10, 12, 0.8);
    border-radius: 1px;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
  }
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
    padding: 40px 44px 48px 44px;
  }

  .system-title {
    font-size: 18px;
    letter-spacing: 3px;
  }

  .cabinet-top {
    left: 40px;
    right: 40px;
  }

  .cabinet-rail-left,
  .cabinet-rail-right {
    top: 50px;
    bottom: 50px;
  }
}

@media (max-width: 1400px) {
  .servers-grid {
    padding: 38px 40px 46px 40px;
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

  .cabinet-top {
    left: 36px;
    right: 36px;
    height: 24px;
  }

  .cabinet-label {
    font-size: 8px;
  }

  .cabinet-rail-left,
  .cabinet-rail-right {
    width: 16px;
    left: 12px;
  }

  .cabinet-rail-right {
    left: auto;
    right: 12px;
  }
}

@media (max-width: 1200px) {
  .main-content {
    padding: 16px;
    gap: 20px;
  }

  .servers-grid {
    padding: 36px 36px 44px 36px;
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

  // Hide cabinet decorations on smaller screens
  .cabinet-frame {
    display: none;
  }

  .servers-section::before,
  .servers-section::after {
    display: none;
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
    margin: 0;
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
