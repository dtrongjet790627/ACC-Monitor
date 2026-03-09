<template>
  <div class="oracle-ops-container">
    <!-- Top Bar -->
    <header class="ops-top-bar">
      <div class="bar-left">
        <button class="back-btn" @click="$router.push('/')">
          <span class="bracket">[</span>
          <span class="arrow">&lt;</span>
          <span class="bracket">]</span>
        </button>
        <div class="page-title">
          <span class="title-icon">&#9671;</span>
          <span class="title-text">ORACLE DATABASE OPS</span>
        </div>
        <div class="status-group">
          <div class="status-item normal">
            <span class="stat-label">NORMAL</span>
            <span class="stat-value">{{ store.normalDatabases }}</span>
          </div>
          <div class="status-item warning" v-if="store.warningDatabases > 0">
            <span class="stat-label">WARNING</span>
            <span class="stat-value">{{ store.warningDatabases }}</span>
          </div>
          <div class="status-item critical" v-if="store.criticalDatabases > 0">
            <span class="stat-label">CRITICAL</span>
            <span class="stat-value">{{ store.criticalDatabases }}</span>
          </div>
        </div>
      </div>
      <div class="bar-right">
        <div class="nav-links">
          <router-link to="/oracle-ops-backups" class="nav-link">BACKUPS</router-link>
          <router-link to="/oracle-ops-alerts" class="nav-link">ALERTS</router-link>
        </div>
        <button class="refresh-btn" @click="refresh" :disabled="store.overviewLoading">
          <span class="bracket">[</span>
          <span :class="{ 'spin': store.overviewLoading }">&#8635;</span>
          <span class="bracket">]</span>
        </button>
      </div>
    </header>

    <!-- Database Cards Grid -->
    <div class="db-grid">
      <div
        v-for="server in store.overview"
        :key="server.server_id"
        class="db-card"
        :class="[`status-${server.status}`]"
        @click="goToDetail(server.server_id)"
      >
        <!-- Card header -->
        <div class="card-header">
          <div class="server-indicator" :class="server.status"></div>
          <div class="server-info">
            <div class="server-name">{{ getServerConfig(server.server_id).shortName }}</div>
            <div class="server-meta">
              <span class="server-ip">{{ getServerConfig(server.server_id).ip }}</span>
              <span class="edition-badge" :class="server.edition === 'XE' ? 'xe' : 'se'">
                {{ server.edition }}
              </span>
            </div>
          </div>
          <div class="status-badge" :class="server.status">
            {{ server.status.toUpperCase() }}
          </div>
        </div>

        <!-- Tablespace gauges -->
        <div class="gauge-section">
          <!-- Business data gauge (green) -->
          <div class="gauge-item">
            <div class="gauge-ring">
              <svg viewBox="0 0 100 100" class="gauge-svg">
                <circle cx="50" cy="50" r="42" class="gauge-bg" />
                <circle
                  cx="50" cy="50" r="42"
                  class="gauge-fill"
                  :class="getGaugeClass(server.max_tablespace_usage)"
                  :style="{ strokeDashoffset: getGaugeOffset(server.max_tablespace_usage) }"
                />
              </svg>
              <div class="gauge-value">
                <span class="gauge-number">{{ Math.round(server.max_tablespace_usage || 0) }}</span>
                <span class="gauge-unit">%</span>
              </div>
            </div>
            <div class="gauge-label">
              <div class="ts-name">{{ server.max_tablespace_name || 'N/A' }}</div>
              <div class="ts-sub" v-if="server.current_file_pct != null">CURRENT FILE</div>
            </div>
          </div>
          <!-- SYSTEM tablespace gauge (cyan) -->
          <div class="gauge-item" v-if="server.system_tablespace">
            <div class="gauge-ring">
              <svg viewBox="0 0 100 100" class="gauge-svg">
                <circle cx="50" cy="50" r="42" class="gauge-bg gauge-bg-cyan" />
                <circle
                  cx="50" cy="50" r="42"
                  class="gauge-fill"
                  :class="getSystemGaugeClass(server.system_tablespace.usage_pct)"
                  :style="{ strokeDashoffset: getGaugeOffset(server.system_tablespace.usage_pct) }"
                />
              </svg>
              <div class="gauge-value">
                <span class="gauge-number">{{ Math.round(server.system_tablespace.usage_pct || 0) }}</span>
                <span class="gauge-unit">%</span>
              </div>
            </div>
            <div class="gauge-label">
              <div class="ts-name ts-name-cyan">SYSTEM</div>
            </div>
          </div>
          <!-- Tablespace count -->
          <div class="gauge-count">
            <div class="ts-count">{{ server.tablespace_count }} tablespaces</div>
          </div>
        </div>

        <!-- Info rows -->
        <div class="info-rows">
          <div class="info-row">
            <span class="info-label">LAST BACKUP</span>
            <span class="info-value" :class="getBackupClass(server.latest_backup)">
              {{ formatBackupStatus(server) }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">ALERTS (24H)</span>
            <span class="info-value" :class="{ 'alert-active': server.recent_alerts_count > 0 }">
              {{ server.recent_alerts_count }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">LIMIT</span>
            <span class="info-value">
              {{ server.limit_gb ? server.limit_gb + ' GB' : 'UNLIMITED' }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">LAST REPORT</span>
            <span class="info-value time-value">
              {{ formatTime(server.last_report_time) }}
            </span>
          </div>
        </div>

        <!-- Card scanline effect -->
        <div class="card-scanline"></div>
      </div>
    </div>

    <!-- Recent Alerts Section -->
    <div class="recent-alerts-section" v-if="recentAlerts.length > 0">
      <div class="section-header">
        <span class="section-icon">&#9888;</span>
        <span class="section-title">RECENT ALERTS</span>
      </div>
      <div class="alert-list">
        <div
          v-for="alert in recentAlerts"
          :key="alert.server_id + '-' + alert.recent_alerts_count"
          class="alert-item"
        >
          <span class="alert-severity" :class="alert.status">
            {{ alert.status === 'critical' ? 'CRIT' : 'WARN' }}
          </span>
          <span class="alert-server">{{ getServerConfig(alert.server_id).shortName }}</span>
          <span class="alert-msg">
            {{ alert.max_tablespace_name }} tablespace at {{ Math.round(alert.max_tablespace_usage) }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-if="store.overviewLoading && store.overview.length === 0" class="loading-overlay">
      <div class="loading-text">SCANNING DATABASES<span class="loading-dots"></span></div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useOracleOpsStore, ORACLE_SERVER_CONFIG } from '@/stores/oracle_ops'

const router = useRouter()
const store = useOracleOpsStore()

let refreshInterval = null

// Get server config helper
function getServerConfig(serverId) {
  return ORACLE_SERVER_CONFIG[serverId] || { name: serverId, shortName: serverId, ip: '', edition: '?', limitGb: null }
}

// Gauge calculations (SVG circle circumference = 2 * PI * 42 = 263.89)
const CIRCUMFERENCE = 2 * Math.PI * 42

function getGaugeOffset(pct) {
  const p = Math.min(Math.max(pct || 0, 0), 100)
  return CIRCUMFERENCE - (p / 100) * CIRCUMFERENCE
}

function getGaugeClass(pct) {
  if (pct >= 95) return 'critical'
  if (pct >= 85) return 'warning'
  return 'normal'
}

function getSystemGaugeClass(pct) {
  if (pct >= 95) return 'critical'
  if (pct >= 85) return 'warning'
  return 'system'
}

function getBackupClass(status) {
  if (status === 'success') return 'backup-success'
  if (status === 'failed') return 'backup-failed'
  return 'backup-none'
}

function formatBackupStatus(server) {
  if (!server.latest_backup) return 'NO DATA'
  const status = server.latest_backup.toUpperCase()
  if (server.latest_backup_time) {
    const d = new Date(server.latest_backup_time)
    const dateStr = `${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`
    return `${dateStr} ${status}`
  }
  return status
}

function formatTime(isoStr) {
  if (!isoStr) return 'N/A'
  const d = new Date(isoStr)
  const now = new Date()
  const diffMs = now - d
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'JUST NOW'
  if (diffMin < 60) return `${diffMin}m AGO`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}h AGO`
  return `${Math.floor(diffH / 24)}d AGO`
}

// Recent alerts: servers that have warning/critical status
const recentAlerts = computed(() => {
  return store.overview.filter(s => s.status === 'warning' || s.status === 'critical')
})

function goToDetail(serverId) {
  router.push(`/oracle-ops/${serverId}`)
}

function refresh() {
  store.fetchOverview()
}

onMounted(() => {
  store.fetchOverview()
  refreshInterval = setInterval(() => store.fetchOverview(), 60000) // Refresh every 60s
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.oracle-ops-container {
  height: 100vh;
  padding: 16px 24px;
  overflow-y: auto;
  position: relative;

  &::-webkit-scrollbar {
    width: 4px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba($neon-green, 0.3);
    border-radius: 2px;
  }
}

// ============ Top Bar ============
.ops-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  margin-bottom: 20px;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba($neon-green, 0.3);
  box-shadow: 0 0 15px rgba($neon-green, 0.1);
}

.bar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.bar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  background: none;
  border: 1px solid rgba($neon-green, 0.3);
  color: $neon-green;
  padding: 4px 10px;
  cursor: pointer;
  font-family: $font-mono;
  font-size: 14px;
  transition: all 0.2s;

  &:hover {
    background: rgba($neon-green, 0.1);
    border-color: $neon-green;
  }

  .bracket { opacity: 0.5; }
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;

  .title-icon {
    color: $neon-cyan;
    font-size: 16px;
  }

  .title-text {
    font-family: $font-terminal;
    font-size: 16px;
    color: $neon-green;
    letter-spacing: 3px;
  }
}

.status-group {
  display: flex;
  gap: 12px;
  margin-left: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: $font-mono;
  font-size: 12px;

  .stat-label {
    color: $text-secondary;
    letter-spacing: 1px;
  }

  .stat-value {
    font-weight: bold;
    font-size: 14px;
  }

  &.normal .stat-value { color: $neon-green; }
  &.warning .stat-value { color: $neon-orange; }
  &.critical .stat-value { color: $neon-red; }
}

.nav-links {
  display: flex;
  gap: 8px;
}

.nav-link {
  font-family: $font-mono;
  font-size: 11px;
  color: rgba($neon-green, 0.6);
  text-decoration: none;
  padding: 4px 10px;
  border: 1px solid rgba($neon-green, 0.2);
  letter-spacing: 1px;
  transition: all 0.2s;

  &:hover {
    color: $neon-green;
    border-color: $neon-green;
    background: rgba($neon-green, 0.05);
  }
}

.refresh-btn {
  background: none;
  border: 1px solid rgba($neon-green, 0.3);
  color: $neon-green;
  padding: 4px 10px;
  cursor: pointer;
  font-family: $font-mono;
  font-size: 16px;
  transition: all 0.2s;

  &:hover { background: rgba($neon-green, 0.1); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }

  .bracket { opacity: 0.5; font-size: 14px; }
  .spin { display: inline-block; animation: spin 1s linear infinite; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ============ Database Cards Grid ============
.db-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.db-card {
  background: $bg-card;
  border: 1px solid rgba($neon-green, 0.2);
  padding: 16px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s;

  &:hover {
    border-color: rgba($neon-green, 0.5);
    box-shadow: 0 0 20px rgba($neon-green, 0.15);
    transform: translateY(-2px);
  }

  &.status-warning {
    border-color: rgba($neon-orange, 0.3);
    &:hover { border-color: $neon-orange; box-shadow: 0 0 20px rgba($neon-orange, 0.15); }
  }

  &.status-critical {
    border-color: rgba($neon-red, 0.3);
    &:hover { border-color: $neon-red; box-shadow: 0 0 20px rgba($neon-red, 0.15); }
  }

  &.status-unknown {
    border-color: rgba($text-secondary, 0.3);
    opacity: 0.7;
  }
}

// Card header
.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba($neon-green, 0.1);
}

.server-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: $neon-green;
  box-shadow: 0 0 8px $neon-green;
  animation: pulse 2s ease-in-out infinite;

  &.warning { background: $neon-orange; box-shadow: 0 0 8px $neon-orange; }
  &.critical { background: $neon-red; box-shadow: 0 0 8px $neon-red; animation: pulse-fast 1s ease-in-out infinite; }
  &.unknown { background: $text-secondary; box-shadow: none; animation: none; }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes pulse-fast {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.server-info {
  flex: 1;
}

.server-name {
  font-family: $font-terminal;
  font-size: 14px;
  color: $text-white;
  letter-spacing: 2px;
}

.server-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
}

.server-ip {
  font-family: $font-mono;
  font-size: 11px;
  color: $text-secondary;
}

.edition-badge {
  font-family: $font-mono;
  font-size: 9px;
  padding: 1px 5px;
  letter-spacing: 1px;

  &.xe {
    background: rgba($neon-orange, 0.15);
    color: $neon-orange;
    border: 1px solid rgba($neon-orange, 0.3);
  }

  &.se {
    background: rgba($neon-cyan, 0.15);
    color: $neon-cyan;
    border: 1px solid rgba($neon-cyan, 0.3);
  }
}

.status-badge {
  font-family: $font-mono;
  font-size: 10px;
  padding: 2px 8px;
  letter-spacing: 1px;
  border: 1px solid;

  &.normal {
    color: $neon-green;
    border-color: rgba($neon-green, 0.4);
    background: rgba($neon-green, 0.1);
  }
  &.warning {
    color: $neon-orange;
    border-color: rgba($neon-orange, 0.4);
    background: rgba($neon-orange, 0.1);
  }
  &.critical {
    color: $neon-red;
    border-color: rgba($neon-red, 0.4);
    background: rgba($neon-red, 0.1);
  }
  &.unknown {
    color: $text-secondary;
    border-color: rgba($text-secondary, 0.4);
    background: rgba($text-secondary, 0.1);
  }
}

// Gauge section
.gauge-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.gauge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 0 0 auto;
}

.gauge-ring {
  position: relative;
  width: 72px;
  height: 72px;
  flex-shrink: 0;
}

.gauge-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.gauge-bg {
  fill: none;
  stroke: rgba($neon-green, 0.08);
  stroke-width: 6;

  &.gauge-bg-cyan {
    stroke: rgba($neon-cyan, 0.08);
  }
}

.gauge-fill {
  fill: none;
  stroke-width: 6;
  stroke-linecap: round;
  stroke-dasharray: 263.89;
  transition: stroke-dashoffset 1s ease;

  &.normal { stroke: $neon-green; filter: drop-shadow(0 0 4px rgba($neon-green, 0.5)); }
  &.system { stroke: $neon-cyan; filter: drop-shadow(0 0 4px rgba($neon-cyan, 0.5)); }
  &.warning { stroke: $neon-orange; filter: drop-shadow(0 0 4px rgba($neon-orange, 0.5)); }
  &.critical { stroke: $neon-red; filter: drop-shadow(0 0 4px rgba($neon-red, 0.5)); }
}

.gauge-value {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;

  .gauge-number {
    font-family: $font-terminal;
    font-size: 18px;
    color: $text-white;
    text-shadow: 0 0 10px rgba($neon-green, 0.5);
  }

  .gauge-unit {
    font-family: $font-mono;
    font-size: 10px;
    color: $text-secondary;
    margin-left: 1px;
  }
}

.gauge-label {
  text-align: center;

  .ts-name {
    font-family: $font-mono;
    font-size: 10px;
    color: $neon-green;
    letter-spacing: 1px;
    word-break: break-all;
    line-height: 1.2;

    &.ts-name-cyan {
      color: $neon-cyan;
    }
  }

  .ts-sub {
    font-family: $font-mono;
    font-size: 9px;
    color: $neon-cyan;
    letter-spacing: 1px;
    margin-top: 1px;
    opacity: 0.8;
  }
}

.gauge-count {
  display: flex;
  align-items: center;
  margin-left: auto;

  .ts-count {
    font-family: $font-mono;
    font-size: 10px;
    color: $text-secondary;
    white-space: nowrap;
  }
}

// Info rows
.info-rows {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 0;

  .info-label {
    font-family: $font-mono;
    font-size: 10px;
    color: $text-secondary;
    letter-spacing: 1px;
  }

  .info-value {
    font-family: $font-mono;
    font-size: 11px;
    color: rgba($text-white, 0.8);

    &.backup-success { color: $neon-green; }
    &.backup-failed { color: $neon-red; }
    &.backup-none { color: $text-secondary; }
    &.alert-active { color: $neon-orange; font-weight: bold; }
    &.time-value { color: rgba($neon-green, 0.7); }
  }
}

// Card scanline
.card-scanline {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba($neon-green, 0.3), transparent);
  opacity: 0;
  transition: opacity 0.3s;

  .db-card:hover & {
    opacity: 1;
    animation: scanMove 2s linear infinite;
  }
}

@keyframes scanMove {
  0% { transform: translateY(0); }
  100% { transform: translateY(300px); }
}

// ============ Recent Alerts ============
.recent-alerts-section {
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba($neon-orange, 0.2);
  padding: 14px 18px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;

  .section-icon {
    color: $neon-orange;
    font-size: 14px;
  }

  .section-title {
    font-family: $font-terminal;
    font-size: 13px;
    color: $neon-orange;
    letter-spacing: 2px;
  }
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.4);
  border-left: 2px solid $neon-orange;
  font-family: $font-mono;
  font-size: 11px;
}

.alert-severity {
  font-size: 9px;
  padding: 1px 6px;
  letter-spacing: 1px;
  font-weight: bold;

  &.warning {
    color: $neon-orange;
    background: rgba($neon-orange, 0.1);
    border: 1px solid rgba($neon-orange, 0.3);
  }
  &.critical {
    color: $neon-red;
    background: rgba($neon-red, 0.1);
    border: 1px solid rgba($neon-red, 0.3);
  }
}

.alert-server {
  color: $neon-cyan;
  min-width: 80px;
}

.alert-msg {
  color: rgba($text-white, 0.7);
}

// ============ Loading ============
.loading-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
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

// ============ Responsive ============
@media (max-width: 1200px) {
  .db-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .db-grid {
    grid-template-columns: 1fr;
  }
}
</style>
