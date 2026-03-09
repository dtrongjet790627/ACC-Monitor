<template>
  <div class="oracle-ops-container">
    <!-- Top Status Bar - Matching Dashboard -->
    <header class="top-status-bar">
      <div class="status-left">
        <div class="system-title">
          <span class="title-bracket">[</span>
          <span class="title-icon">&#9671;</span>
          <span class="title-text">DATABASE OPS</span>
          <span class="title-icon">&#9671;</span>
          <span class="title-bracket">]</span>
        </div>
        <div class="status-group">
          <div class="status-item">
            <span class="stat-label">TOTAL</span>
            <span class="stat-value">{{ store.totalDatabases }}</span>
          </div>
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
      <div class="status-center">
        <div class="realtime-indicator">
          <span class="indicator-dot" :class="{ active: isLive }"></span>
          <span class="indicator-text">{{ isLive ? 'LIVE' : 'OFFLINE' }}</span>
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
          <span class="ping-label">AVG USAGE</span>
          <span class="ping-value">{{ avgUsage }}%</span>
        </div>
        <button class="server-monitor-btn" @click="$router.push('/')" title="Server Monitor">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
        </button>
        <button class="admin-entry-btn" @click="goToAdmin" title="Admin Console">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
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
            <div class="cabinet-label">RACK UNIT // ORACLE-OPS</div>
            <div class="handle-right"></div>
          </div>
          <div class="cabinet-rail-left">
            <div class="rail-led" :class="{ active: store.normalDatabases > 0 }"></div>
            <div class="rail-led warning" :class="{ active: store.warningDatabases > 0 }"></div>
            <div class="rail-led error" :class="{ active: store.criticalDatabases > 0 }"></div>
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
        <!-- Database CRT cards grid -->
        <div class="servers-grid">
          <div
            v-for="server in store.overview"
            :key="server.server_id"
            class="crt-monitor"
            :class="[`status-${server.status}`]"
            @click="goToDetail(server.server_id)"
          >
            <!-- Monitor Back Shell -->
            <div class="monitor-back-shell">
              <div class="shell-vent-grille">
                <div class="vent-slot" v-for="n in 8" :key="n"></div>
              </div>
            </div>

            <!-- Main CRT Body -->
            <div class="crt-body">
              <div class="monitor-outer-frame">
                <!-- Frame Corner Accents -->
                <div class="corner-accent top-left"></div>
                <div class="corner-accent top-right"></div>
                <div class="corner-accent bottom-left"></div>
                <div class="corner-accent bottom-right"></div>

                <!-- Frame Screws -->
                <div class="frame-screw top-left"></div>
                <div class="frame-screw top-right"></div>
                <div class="frame-screw bottom-left"></div>
                <div class="frame-screw bottom-right"></div>

                <!-- Brand Label -->
                <div class="brand-label">
                  <span class="brand-text">ORA</span>
                  <span class="model-text">DB-{{ server.server_id }}</span>
                </div>

                <!-- Inner Frame -->
                <div class="monitor-inner-frame">
                  <div class="inner-bezel">
                    <div class="screen-area">
                      <!-- CRT Effects -->
                      <div class="crt-vignette"></div>
                      <div class="scanlines"></div>
                      <div class="screen-glare"></div>
                      <div class="screen-glow"></div>
                      <div class="phosphor-pattern"></div>

                      <!-- Card Content -->
                      <div class="card-content">
                        <!-- Header -->
                        <div class="card-header">
                          <div class="server-info">
                            <div class="server-name">{{ getServerConfig(server.server_id).shortName }}</div>
                            <div class="server-meta">
                              <span class="server-ip">{{ getServerConfig(server.server_id).ip }}</span>
                              <span class="edition-badge" :class="server.edition === 'XE' ? 'xe' : 'se'">
                                {{ server.edition }}
                              </span>
                            </div>
                          </div>
                          <div class="server-status" :class="server.status">
                            <span class="status-led"></span>
                            <span class="status-text">{{ server.status.toUpperCase() }}</span>
                          </div>
                        </div>

                        <!-- Divider -->
                        <div class="section-divider"></div>

                        <!-- Tablespace gauges -->
                        <div class="gauge-section">
                          <div class="gauge-row">
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
                              </div>
                            </div>

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

                            <div class="gauge-count">
                              <div class="ts-count">{{ server.tablespace_count }}<br>TS</div>
                            </div>
                          </div>
                        </div>

                        <!-- Divider -->
                        <div class="section-divider"></div>

                        <!-- Info rows -->
                        <div class="info-rows">
                          <div class="info-row">
                            <span class="info-label">BACKUP</span>
                            <span class="info-value" :class="getBackupClass(server.latest_backup)">
                              {{ formatBackupStatus(server) }}
                            </span>
                          </div>
                          <div class="info-row">
                            <span class="info-label">ALERTS</span>
                            <span class="info-value" :class="{ 'alert-active': server.recent_alerts_count > 0 }">
                              {{ server.recent_alerts_count }}
                            </span>
                          </div>
                          <div class="info-row">
                            <span class="info-label">LIMIT</span>
                            <span class="info-value">
                              {{ server.limit_gb ? server.limit_gb + ' GB' : 'UNLIM' }}
                            </span>
                          </div>
                          <div class="info-row">
                            <span class="info-label">REPORT</span>
                            <span class="info-value time-value">
                              {{ formatTime(server.last_report_time) }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Control Panel -->
                <div class="control-panel">
                  <div class="power-button" :class="server.status">
                    <div class="button-ring"></div>
                    <div class="button-center"></div>
                  </div>
                  <div class="control-knobs">
                    <div class="knob brightness">
                      <div class="knob-cap"></div>
                      <div class="knob-indicator"></div>
                    </div>
                    <div class="knob contrast">
                      <div class="knob-cap"></div>
                      <div class="knob-indicator"></div>
                    </div>
                  </div>
                  <div class="led-panel">
                    <div class="led-indicator power" :class="server.status"></div>
                    <div class="led-indicator hdd" :class="{ active: server.recent_alerts_count > 0 }"></div>
                    <div class="led-indicator network" :class="{ active: server.status === 'normal' }"></div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Monitor Stand -->
            <div class="monitor-stand">
              <div class="stand-neck">
                <div class="neck-joint"></div>
                <div class="neck-shaft"></div>
              </div>
              <div class="stand-base">
                <div class="base-plate"></div>
                <div class="base-shadow"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Guardian Panel -->
      <div class="guardian-section">
        <!-- Pixel Face -->
        <div class="face-panel">
          <PixelFace :is-online="store.overview.length > 0" />
        </div>

        <!-- Database Alert Panel (Full) -->
        <div class="log-panel">
          <div class="db-alert-log">
            <!-- Corner Decorations -->
            <div class="corner-decoration top-left"></div>
            <div class="corner-decoration top-right"></div>
            <div class="corner-decoration bottom-left"></div>
            <div class="corner-decoration bottom-right"></div>

            <!-- Scanlines -->
            <div class="log-scanlines"></div>

            <!-- Header -->
            <div class="log-header">
              <div class="header-left">
                <span class="header-bracket">[</span>
                <span class="header-icon">></span>
                <span class="header-text">DB ALERTS</span>
                <span class="header-bracket">]</span>
              </div>
              <div class="header-right">
                <span class="live-indicator"></span>
                <span class="live-text">LIVE</span>
              </div>
            </div>

            <!-- Filter Bar -->
            <div class="alert-filter-bar">
              <div class="alert-filter-group">
                <label class="alert-filter-label">SVR</label>
                <select v-model="alertFilterServer" class="alert-filter-select" @change="loadAlertData">
                  <option value="">ALL</option>
                  <option v-for="(config, id) in ORACLE_SERVER_CONFIG" :key="id" :value="id">
                    {{ config.shortName }}
                  </option>
                </select>
              </div>
              <div class="alert-filter-group">
                <label class="alert-filter-label">LVL</label>
                <select v-model="alertFilterSeverity" class="alert-filter-select" @change="loadAlertData">
                  <option value="">ALL</option>
                  <option value="warning">WARNING</option>
                  <option value="critical">CRITICAL</option>
                  <option value="info">INFO</option>
                </select>
              </div>
              <div class="alert-filter-total">
                <span class="alert-total-count">{{ store.alerts.total }}</span>
              </div>
            </div>

            <!-- Summary Stats -->
            <div class="alert-stats-row">
              <div class="alert-stat-item">
                <span class="alert-stat-num total">{{ store.alerts.total }}</span>
                <span class="alert-stat-lbl">TOTAL</span>
              </div>
              <div class="alert-stat-item">
                <span class="alert-stat-num warning">{{ alertWarningCount }}</span>
                <span class="alert-stat-lbl">WARN</span>
              </div>
              <div class="alert-stat-item">
                <span class="alert-stat-num critical">{{ alertCriticalCount }}</span>
                <span class="alert-stat-lbl">CRIT</span>
              </div>
            </div>

            <!-- Alert Table -->
            <div class="alert-table-wrap" ref="alertLogContainer"
                 @mouseenter="isHovering = true"
                 @mouseleave="isHovering = false">
              <table class="alert-table">
                <thead>
                  <tr>
                    <th class="at-col-sev">SEV</th>
                    <th class="at-col-svr">SERVER</th>
                    <th class="at-col-msg">MESSAGE</th>
                    <th class="at-col-time">TIME</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="alert in store.alerts.records"
                    :key="alert.id"
                    :class="'at-row-' + alert.severity"
                  >
                    <td>
                      <span class="at-sev-badge" :class="alert.severity">
                        {{ (alert.severity || '').toUpperCase().slice(0, 4) }}
                      </span>
                    </td>
                    <td class="at-server-cell">{{ getServerConfig(alert.server_id).shortName }}</td>
                    <td class="at-msg-cell" :title="(alert.alert_type ? '[' + alert.alert_type.toUpperCase() + '] ' : '') + alert.message">
                      {{ alert.message }}
                    </td>
                    <td class="at-time-cell">{{ formatAlertTime(alert.triggered_at) }}</td>
                  </tr>
                  <tr v-if="store.alerts.records.length === 0">
                    <td colspan="4" class="at-empty-cell">
                      {{ store.alertsLoading ? 'SCANNING...' : 'NO ALERTS' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Pagination -->
            <div class="alert-pagination" v-if="store.alerts.total > alertPageSize">
              <button
                class="alert-page-btn"
                :disabled="store.alerts.page <= 1"
                @click="goAlertPage(store.alerts.page - 1)"
              >&lt;</button>
              <span class="alert-page-info">
                {{ store.alerts.page }}/{{ alertTotalPages }}
              </span>
              <button
                class="alert-page-btn"
                :disabled="store.alerts.page >= alertTotalPages"
                @click="goAlertPage(store.alerts.page + 1)"
              >&gt;</button>
            </div>

            <!-- Command line -->
            <div class="command-line">
              <span class="prompt-symbol">oracle@db-ops</span>
              <span class="prompt-separator">:</span>
              <span class="prompt-path">~</span>
              <span class="prompt-char">$</span>
              <span class="cursor"></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading overlay -->
    <div v-if="store.overviewLoading && store.overview.length === 0" class="loading-overlay">
      <div class="loading-text">SCANNING DATABASES<span class="loading-dots"></span></div>
    </div>

    <!-- Database Detail Modal -->
    <CyberModal
      v-model="showDetailModal"
      width="38vw"
      height="92vh"
      :show-footer="false"
    >
      <template #title>
        <div class="modal-title-bar">
          <span class="modal-db-name">{{ modalServerConfig.shortName }}</span>
          <span class="modal-db-ip">{{ modalServerConfig.ip }}</span>
          <div class="modal-time-range">
            <button
              v-for="opt in timeRangeOptions"
              :key="opt.days"
              class="modal-range-btn"
              :class="{ active: modalSelectedDays === opt.days }"
              @click="modalSelectedDays = opt.days; loadModalTrends()"
            >{{ opt.label }}</button>
          </div>
          <button class="modal-refresh-btn" @click="loadModalAll" :disabled="store.tablespacesLoading">
            <span class="bracket">[</span>
            <span :class="{ 'spin': store.tablespacesLoading }">&#8635;</span>
            <span class="bracket">]</span>
          </button>
        </div>
      </template>

      <div class="modal-charts-area">
        <!-- Usage bar chart -->
        <div class="modal-chart-card">
          <div class="modal-chart-title">
            <span class="ct-icon">&#9632;</span>
            TABLESPACE USAGE
          </div>
          <div ref="modalBarChartRef" class="modal-chart-container modal-chart-bar"></div>
        </div>

        <!-- Trend line chart -->
        <div class="modal-chart-card">
          <div class="modal-chart-title">
            <span class="ct-icon">&#9632;</span>
            USAGE TREND ({{ modalSelectedDays }}D)
          </div>
          <div ref="modalLineChartRef" class="modal-chart-container modal-chart-trend"></div>
        </div>

        <!-- Backup Records -->
        <div class="modal-chart-card">
          <div class="modal-chart-title">
            <span class="ct-icon">&#9632;</span>
            BACKUP RECORDS
          </div>
          <div class="modal-backup-table-wrap">
            <table class="modal-backup-table" v-if="modalBackupRecords.length > 0">
              <thead>
                <tr>
                  <th>TYPE</th>
                  <th>STATUS</th>
                  <th>SIZE</th>
                  <th>STARTED</th>
                  <th>FINISHED</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="record in modalBackupRecords" :key="record.id">
                  <td class="backup-type-cell">
                    <span class="backup-type-badge">{{ (record.backup_type || '').toUpperCase() }}</span>
                  </td>
                  <td>
                    <span class="backup-status-badge" :class="record.status">
                      {{ (record.status || '').toUpperCase() }}
                    </span>
                  </td>
                  <td class="backup-size-cell">{{ formatBackupSize(record.file_size_mb) }}</td>
                  <td class="backup-time-cell">{{ formatBackupDateTime(record.started_at) }}</td>
                  <td class="backup-time-cell">{{ formatBackupDateTime(record.finished_at) }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="modal-backup-empty">NO BACKUP RECORDS</div>
          </div>
        </div>
      </div>
    </CyberModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { useOracleOpsStore, ORACLE_SERVER_CONFIG } from '@/stores/oracle_ops'
import PixelFace from '@/components/PixelFace.vue'
import CyberModal from '@/components/CyberModal.vue'

const router = useRouter()
const store = useOracleOpsStore()

let refreshInterval = null
let alertScrollInterval = null

// Alert panel state
const alertLogContainer = ref(null)
const isHovering = ref(false)
const alertFilterServer = ref('')
const alertFilterSeverity = ref('')
const alertPageSize = 20

const alertTotalPages = computed(() => {
  return Math.ceil(store.alerts.total / alertPageSize) || 1
})

const alertWarningCount = computed(() => {
  return store.alerts.records.filter(a => a.severity === 'warning').length
})

const alertCriticalCount = computed(() => {
  return store.alerts.records.filter(a => a.severity === 'critical').length
})

// LIVE indicator - true when data has been loaded successfully
const isLive = computed(() => {
  return store.overview.length > 0 && !store.overviewLoading
})

// Last incident - from alert records
const lastIncident = computed(() => {
  const records = store.alerts.records
  if (records && records.length > 0) {
    const latest = records[0]
    const time = formatAlertTime(latest.alert_time || latest.created_at)
    const serverConfig = ORACLE_SERVER_CONFIG[latest.server_id]
    const server = serverConfig ? serverConfig.shortName : (latest.server_id || 'Unknown')
    return { time, server }
  }
  return { time: '--:--', server: 'N/A' }
})

// Uptime days - calculated from a baseline date
const uptimeDays = computed(() => {
  const baseline = new Date('2025-06-01')
  const now = new Date()
  return Math.floor((now - baseline) / (1000 * 60 * 60 * 24))
})

// Average tablespace usage across all databases
const avgUsage = computed(() => {
  const servers = store.overview
  if (!servers || servers.length === 0) return 0
  const usages = servers
    .filter(s => s.tablespace_usage_pct != null)
    .map(s => s.tablespace_usage_pct)
  if (usages.length === 0) return 0
  const total = usages.reduce((sum, u) => sum + u, 0)
  return Math.round(total / usages.length)
})

// Navigate to admin
function goToAdmin() {
  router.push('/admin')
}

function formatAlertTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const min = d.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

function loadAlertData() {
  store.fetchAlerts({
    serverId: alertFilterServer.value || undefined,
    severity: alertFilterSeverity.value || undefined,
    page: 1,
    pageSize: alertPageSize,
  })
}

function goAlertPage(page) {
  store.fetchAlerts({
    serverId: alertFilterServer.value || undefined,
    severity: alertFilterSeverity.value || undefined,
    page,
    pageSize: alertPageSize,
  })
}

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

// Build database alert logs from overview data and alerts API
const dbAlertLogs = computed(() => {
  const logs = []

  // From alerts API data
  if (store.alerts && store.alerts.records && store.alerts.records.length > 0) {
    store.alerts.records.forEach(record => {
      const serverConfig = getServerConfig(record.server_id)
      logs.push({
        level: record.severity === 'critical' ? 'critical' : record.severity === 'warning' ? 'warning' : 'info',
        server: serverConfig.shortName,
        type: record.alert_type || 'ALERT',
        message: record.message || `Alert on ${serverConfig.shortName}`,
        time: record.triggered_at || record.created_at || ''
      })
    })
  }

  // Also generate alerts from overview data for warning/critical servers
  if (logs.length === 0) {
    store.overview.forEach(server => {
      const serverConfig = getServerConfig(server.server_id)
      if (server.status === 'warning' || server.status === 'critical') {
        logs.push({
          level: server.status === 'critical' ? 'critical' : 'warning',
          server: serverConfig.shortName,
          type: 'TABLESPACE_WARNING',
          message: `[${serverConfig.name}] Tablespace ${server.max_tablespace_name} usage ${Math.round(server.max_tablespace_usage)}% >= 85%`,
          time: server.last_report_time || new Date().toISOString()
        })
      }
      if (server.system_tablespace && server.system_tablespace.usage_pct >= 80) {
        logs.push({
          level: server.system_tablespace.usage_pct >= 95 ? 'critical' : 'info',
          server: serverConfig.shortName,
          type: 'SYSAUX_INFO',
          message: `[${serverConfig.name}] SYSTEM tablespace usage ${Math.round(server.system_tablespace.usage_pct)}%`,
          time: server.last_report_time || new Date().toISOString()
        })
      }
      if (server.recent_alerts_count > 0 && server.status === 'normal') {
        logs.push({
          level: 'info',
          server: serverConfig.shortName,
          type: 'ALERT_SUMMARY',
          message: `[${serverConfig.name}] ${server.recent_alerts_count} alert(s) in last 24h`,
          time: server.last_report_time || new Date().toISOString()
        })
      }
    })
  }

  return logs
})

// Auto-scroll for alert log
function startAlertAutoScroll() {
  alertScrollInterval = setInterval(() => {
    if (!isHovering.value && alertLogContainer.value) {
      const el = alertLogContainer.value
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

// ========== Detail Modal State ==========
const showDetailModal = ref(false)
const modalServerId = ref(null)
const modalSelectedDays = ref(7)
const modalBarChartRef = ref(null)
const modalLineChartRef = ref(null)
let modalBarChart = null
let modalLineChart = null

const modalBackupRecords = ref([])

const timeRangeOptions = [
  { label: '24H', days: 1 },
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
]

const modalServerConfig = computed(() => {
  return ORACLE_SERVER_CONFIG[modalServerId.value] || { shortName: 'N/A', ip: '', name: '' }
})

const modalFilteredTablespaces = computed(() => {
  return store.tablespaces.filter(ts => ts.server_id === modalServerId.value)
})

// Business tablespace helpers (same logic as OracleOpsDetail)
function isBusinessTablespace(tsName) {
  if (!tsName) return false
  const upper = tsName.toUpperCase()
  if (upper.includes('ACC_DATA')) return true
  if (upper.startsWith('IPLANT_') && upper.endsWith('_DATA')) return true
  return false
}

function getDisplayPct(ts) {
  if (isBusinessTablespace(ts.tablespace_name) && ts.current_file_pct != null) {
    return ts.current_file_pct
  }
  return ts.usage_pct || 0
}

// Open modal on card click
function goToDetail(serverId) {
  modalServerId.value = serverId
  modalSelectedDays.value = 7
  showDetailModal.value = true
  loadModalAll()
}

// Load all modal data
async function loadModalAll() {
  if (!modalServerId.value) return
  await Promise.all([
    store.fetchTablespaces(modalServerId.value),
    loadModalTrends(),
    loadModalBackups(),
  ])
  await nextTick()
  renderModalBarChart()
}

// Load backup records for the modal
async function loadModalBackups() {
  if (!modalServerId.value) return
  try {
    await store.fetchBackups({ serverId: modalServerId.value, page: 1, pageSize: 5 })
    modalBackupRecords.value = (store.backups.records || []).slice(0, 5)
  } catch (e) {
    console.error('[OracleOps] Failed to load modal backups:', e)
    modalBackupRecords.value = []
  }
}

// Backup formatting helpers
function formatBackupSize(mb) {
  if (mb === null || mb === undefined) return '-'
  if (mb >= 1024) return (mb / 1024).toFixed(2) + ' GB'
  return mb.toFixed(2) + ' MB'
}

function formatBackupDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const min = d.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

async function loadModalTrends() {
  if (!modalServerId.value) return
  await store.fetchTrends(modalServerId.value, modalSelectedDays.value)
  await nextTick()
  renderModalLineChart()
}

// Render bar chart inside modal
function renderModalBarChart() {
  if (!modalBarChartRef.value) return
  if (!modalBarChart) {
    modalBarChart = echarts.init(modalBarChartRef.value)
  }

  const data = modalFilteredTablespaces.value
  const names = data.map(ts => ts.tablespace_name)
  const values = data.map(ts => getDisplayPct(ts))
  const colors = values.map(v => {
    if (v >= 95) return '#ff0055'
    if (v >= 85) return '#ff6b35'
    return '#00d4aa'
  })

  modalBarChart.setOption({
    grid: { left: 140, right: 50, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#6c757d', fontFamily: 'Consolas', formatter: '{value}%' },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.2)' } },
      splitLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.05)' } },
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: '#00d4aa', fontFamily: 'Consolas', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.2)' } },
    },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({
        value: v,
        itemStyle: { color: colors[i] }
      })),
      barWidth: 16,
      label: {
        show: true,
        position: 'right',
        color: '#ffffff',
        fontFamily: 'Consolas',
        fontSize: 12,
        formatter: '{c}%'
      }
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 10, 10, 0.95)',
      borderColor: 'rgba(0, 212, 170, 0.3)',
      textStyle: { color: '#00d4aa', fontFamily: 'Consolas', fontSize: 12 },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>Usage: ${p.value.toFixed(1)}%`
      }
    },
    animation: true,
    animationDuration: 800,
  })
}

// Render line chart inside modal
function renderModalLineChart() {
  if (!modalLineChartRef.value) return
  if (!modalLineChart) {
    modalLineChart = echarts.init(modalLineChartRef.value)
  }

  const trendData = store.trends.filter(t => t.server_id === modalServerId.value)

  if (trendData.length === 0) {
    modalLineChart.setOption({
      title: {
        text: 'No trend data available',
        left: 'center',
        top: 'center',
        textStyle: { color: '#6c757d', fontFamily: 'Consolas', fontSize: 13 }
      }
    }, true)
    return
  }

  const lineColors = ['#00d4aa', '#0099ff', '#ff6b35', '#9d4edd', '#ff0080', '#ffd700', '#00ff41', '#ff0055']

  const series = trendData.map((ts, idx) => ({
    name: ts.tablespace_name,
    type: 'line',
    data: ts.data_points.map(dp => [dp.time, dp.usage_pct]),
    smooth: true,
    lineStyle: { width: 2, color: lineColors[idx % lineColors.length] },
    itemStyle: { color: lineColors[idx % lineColors.length] },
    symbol: 'circle',
    symbolSize: 4,
    showSymbol: false,
  }))

  modalLineChart.setOption({
    grid: { left: 60, right: 30, top: 40, bottom: 50 },
    legend: {
      type: 'scroll',
      top: 5,
      textStyle: { color: '#6c757d', fontFamily: 'Consolas', fontSize: 10 },
      pageTextStyle: { color: '#6c757d' },
      pageIconColor: '#00d4aa',
    },
    xAxis: {
      type: 'time',
      axisLabel: { color: '#6c757d', fontFamily: 'Consolas', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.2)' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#6c757d', fontFamily: 'Consolas', formatter: '{value}%' },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.2)' } },
      splitLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.05)' } },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 10, 10, 0.95)',
      borderColor: 'rgba(0, 212, 170, 0.3)',
      textStyle: { color: '#00d4aa', fontFamily: 'Consolas', fontSize: 11 },
    },
    series,
    animation: true,
    animationDuration: 800,
  }, true)
}

// Watch modal visibility to init/dispose charts
watch(showDetailModal, async (visible) => {
  if (visible) {
    await nextTick()
    // Small delay to ensure DOM is fully rendered within the modal
    setTimeout(() => {
      renderModalBarChart()
      renderModalLineChart()
    }, 100)
  } else {
    // Dispose charts when modal closes
    if (modalBarChart) {
      modalBarChart.dispose()
      modalBarChart = null
    }
    if (modalLineChart) {
      modalLineChart.dispose()
      modalLineChart = null
    }
    // Clear backup records
    modalBackupRecords.value = []
  }
})

// Watch for data changes to re-render charts
watch(() => store.tablespaces, () => {
  if (showDetailModal.value) {
    nextTick(() => renderModalBarChart())
  }
}, { deep: true })

watch(() => store.trends, () => {
  if (showDetailModal.value) {
    nextTick(() => renderModalLineChart())
  }
}, { deep: true })

// Handle window resize for modal charts
let modalResizeHandler = null

function refresh() {
  store.fetchOverview()
  store.fetchAlerts({ pageSize: 50 })
}

onMounted(() => {
  store.fetchOverview()
  store.fetchAlerts({ pageSize: 50 })
  refreshInterval = setInterval(() => {
    store.fetchOverview()
    store.fetchAlerts({ pageSize: 50 })
  }, 60000)
  startAlertAutoScroll()

  modalResizeHandler = () => {
    if (showDetailModal.value) {
      modalBarChart?.resize()
      modalLineChart?.resize()
    }
  }
  window.addEventListener('resize', modalResizeHandler)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
  if (alertScrollInterval) clearInterval(alertScrollInterval)
  if (modalResizeHandler) window.removeEventListener('resize', modalResizeHandler)
  if (modalBarChart) { modalBarChart.dispose(); modalBarChart = null }
  if (modalLineChart) { modalLineChart.dispose(); modalLineChart = null }
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

// Monitor Colors
$monitor-frame-darkest: #141414;
$monitor-frame-dark: #1a1a1a;
$monitor-frame-mid: #252525;
$monitor-frame-light: #2d2d2d;

// ============================================
// Container
// ============================================
.oracle-ops-container {
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
// Top Status Bar - matching Dashboard
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

// Server Monitor switch button (matching Dashboard's oracle-ops-btn style)
.server-monitor-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid rgba($neon-green, 0.3);
  border-radius: 4px;
  background: rgba($neon-green, 0.06);
  color: rgba($neon-green, 0.6);
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 8px;

  &:hover {
    color: $neon-green;
    border-color: $neon-green;
    background: rgba($neon-green, 0.15);
    box-shadow: 0 0 15px rgba($neon-green, 0.3);
  }

  svg {
    transition: transform 0.3s ease;
  }
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

  &.normal {
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

// Admin entry button (gear icon) - matching Dashboard
.admin-entry-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid rgba($cyber-cyan, 0.3);
  border-radius: 4px;
  background: rgba($cyber-cyan, 0.06);
  color: rgba($cyber-cyan, 0.6);
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 8px;

  &:hover {
    color: $cyber-cyan;
    border-color: $cyber-cyan;
    background: rgba($cyber-cyan, 0.15);
    box-shadow: 0 0 15px rgba($cyber-cyan, 0.3);

    svg {
      animation: gear-spin 2s linear infinite;
    }
  }

  svg {
    transition: transform 0.3s ease;
  }
}

@keyframes gear-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

// ============================================
// Main Content - matching Dashboard layout
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
// Left: Server Rack Cabinet - matching Dashboard
// ============================================
.servers-section {
  flex: 7;
  min-width: 0;
  position: relative;
  overflow: visible;
  margin: 8px 0;

  background:
    repeating-linear-gradient(
      90deg,
      transparent 0px,
      transparent 1px,
      rgba(255, 255, 255, 0.008) 1px,
      rgba(255, 255, 255, 0.008) 2px
    ),
    repeating-linear-gradient(
      0deg,
      transparent 0px,
      transparent 3px,
      rgba(0, 212, 170, 0.012) 3px,
      rgba(0, 212, 170, 0.012) 4px
    ),
    radial-gradient(circle at 10% 20%, rgba(0, 212, 170, 0.025) 0%, transparent 20%),
    radial-gradient(circle at 90% 80%, rgba(0, 212, 170, 0.025) 0%, transparent 20%),
    radial-gradient(circle at 50% 50%, rgba(0, 212, 170, 0.015) 0%, transparent 40%),
    linear-gradient(180deg,
      rgba(15, 18, 22, 0.88) 0%,
      rgba(10, 12, 16, 0.85) 50%,
      rgba(8, 10, 14, 0.88) 100%
    );
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

// Top panel
.servers-section::before {
  content: '';
  position: absolute;
  top: -20px;
  left: 10px;
  right: 10px;
  height: 20px;
  pointer-events: none;
  z-index: 10;
  background:
    repeating-linear-gradient(90deg,
      transparent 0px, transparent 4px,
      rgba(10, 15, 15, 0.92) 4px, rgba(10, 15, 15, 0.92) 6px
    ),
    linear-gradient(90deg,
      transparent 0%, transparent 20%,
      rgba(0, 212, 170, 0.1) 50%,
      transparent 80%, transparent 100%
    ),
    linear-gradient(180deg,
      rgba(35, 38, 42, 0.95) 0%,
      rgba(28, 30, 34, 0.95) 40%,
      rgba(22, 24, 28, 0.95) 100%
    );
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

// Bottom panel
.servers-section::after {
  content: '';
  position: absolute;
  bottom: -24px;
  left: 10px;
  right: 10px;
  height: 24px;
  pointer-events: none;
  z-index: 10;
  background:
    radial-gradient(ellipse 20px 8px at 60px 16px, rgba(20, 22, 25, 0.95) 0%, transparent 100%),
    radial-gradient(ellipse 20px 8px at calc(100% - 60px) 16px, rgba(20, 22, 25, 0.95) 0%, transparent 100%),
    repeating-linear-gradient(90deg,
      transparent 0px, transparent 4px,
      rgba(10, 15, 15, 0.92) 4px, rgba(10, 15, 15, 0.92) 6px
    ),
    linear-gradient(90deg,
      transparent 0%, transparent 30%,
      rgba(0, 212, 170, 0.08) 50%,
      transparent 70%, transparent 100%
    ),
    linear-gradient(0deg,
      rgba(22, 24, 28, 0.95) 0%,
      rgba(28, 30, 34, 0.95) 60%,
      rgba(35, 38, 42, 0.95) 100%
    );
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

// Database CRT Cards Grid - 3x2 layout
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
}

// Cabinet frame decorations
.cabinet-frame {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 8;
}

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
  opacity: 0.7;
  background:
    repeating-linear-gradient(
      90deg,
      transparent 0px, transparent 1px,
      rgba(255, 255, 255, 0.015) 1px, rgba(255, 255, 255, 0.015) 2px
    ),
    linear-gradient(180deg,
      rgba(50, 55, 60, 0.85) 0%,
      rgba(38, 42, 48, 0.9) 50%,
      rgba(28, 32, 38, 0.9) 100%
    );
  border-radius: 4px;
  border: 1px solid rgba(0, 212, 170, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(100, 105, 110, 0.15),
    0 2px 8px rgba(0, 0, 0, 0.3),
    0 0 15px rgba(0, 212, 170, 0.05);
}

.handle-left, .handle-right {
  width: 32px;
  height: 8px;
  background: linear-gradient(180deg,
    rgba(70, 75, 80, 0.95) 0%,
    rgba(50, 55, 60, 0.95) 40%,
    rgba(35, 40, 45, 0.95) 100%
  );
  border-radius: 2px;
  border: 1px solid rgba(0, 212, 170, 0.15);
  box-shadow:
    inset 0 1px 0 rgba(100, 105, 110, 0.25),
    0 1px 3px rgba(0, 0, 0, 0.4),
    0 0 6px rgba(0, 212, 170, 0.08);
}

.cabinet-label {
  font-family: $font-mono;
  font-size: 9px;
  letter-spacing: 2px;
  color: rgba($cyber-cyan, 0.6);
  text-shadow: 0 0 8px rgba($cyber-cyan, 0.3);
}

// Left Rail
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
  opacity: 0.65;
  background:
    repeating-linear-gradient(180deg,
      transparent 0px, transparent 1px,
      rgba(255, 255, 255, 0.02) 1px, rgba(255, 255, 255, 0.02) 2px
    ),
    linear-gradient(90deg,
      rgba(40, 45, 50, 0.7) 0%,
      rgba(30, 35, 40, 0.85) 50%,
      rgba(40, 45, 50, 0.7) 100%
    );
  border-radius: 3px;
  border: 1px solid rgba(0, 212, 170, 0.12);
  box-shadow:
    inset 0 0 10px rgba(0, 0, 0, 0.3),
    0 0 8px rgba(0, 212, 170, 0.05);
}

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
    animation: led-blink-anim 0.5s ease-in-out infinite;
  }

  &.error.active {
    background: $cyber-red;
    box-shadow: 0 0 8px $cyber-red, 0 0 12px rgba($cyber-red, 0.5);
    animation: led-blink-anim 0.3s ease-in-out infinite;
  }
}

@keyframes led-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes led-blink-anim {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.rail-screw {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  opacity: 0.6;
  background: linear-gradient(135deg,
    rgba(70, 75, 80, 0.95) 0%,
    rgba(55, 60, 65, 0.95) 30%,
    rgba(40, 45, 50, 0.95) 70%,
    rgba(55, 60, 65, 0.95) 100%
  );
  border: 1px solid rgba(0, 212, 170, 0.1);
  margin-top: auto;
  box-shadow: 0 0 4px rgba(0, 212, 170, 0.05);

  &:last-child {
    margin-top: 8px;
    margin-bottom: 0;
  }

  &::after {
    content: '';
    display: block;
    width: 5px;
    height: 1px;
    background: rgba(15, 20, 25, 0.85);
    margin: 3px auto 0;
  }
}

// Right Rail
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
  opacity: 0.65;
  background:
    repeating-linear-gradient(180deg,
      transparent 0px, transparent 1px,
      rgba(255, 255, 255, 0.02) 1px, rgba(255, 255, 255, 0.02) 2px
    ),
    linear-gradient(270deg,
      rgba(40, 45, 50, 0.7) 0%,
      rgba(30, 35, 40, 0.85) 50%,
      rgba(40, 45, 50, 0.7) 100%
    );
  border-radius: 3px;
  border: 1px solid rgba(0, 212, 170, 0.12);
  box-shadow:
    inset 0 0 10px rgba(0, 0, 0, 0.3),
    0 0 8px rgba(0, 212, 170, 0.05);
}

.vent-slots {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;

  span {
    width: 10px;
    height: 3px;
    background: rgba(8, 12, 15, 0.85);
    border-radius: 1px;
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.5),
      0 0 3px rgba(0, 212, 170, 0.03);
  }
}

// ============================================
// CRT Monitor Card - Database Version
// ============================================
.crt-monitor {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: transform 0.3s ease;
  contain: layout style paint;

  &:hover {
    transform: translateY(-4px);

    .monitor-outer-frame {
      box-shadow:
        0 0 20px rgba($cyber-cyan, 0.25),
        0 12px 40px rgba(0, 0, 0, 0.7),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    .screen-glow {
      opacity: 0.18;
    }
  }

  // Status variants
  &.status-normal {
    .screen-glow { background: radial-gradient(ellipse at center, $cyber-cyan 0%, transparent 70%); }
    .led-indicator.power { background: $cyber-cyan; box-shadow: 0 0 6px $cyber-cyan; }
    .power-button .button-center { background: radial-gradient(circle, rgba($cyber-cyan, 0.6) 0%, rgba($cyber-cyan, 0.2) 100%); }
  }

  &.status-warning {
    .screen-glow { background: radial-gradient(ellipse at center, $cyber-yellow 0%, transparent 70%); }
    .led-indicator.power { background: $cyber-yellow; box-shadow: 0 0 6px $cyber-yellow; animation: led-blink-monitor 1.5s ease-in-out infinite; }
    .power-button .button-center { background: radial-gradient(circle, rgba($cyber-yellow, 0.6) 0%, rgba($cyber-yellow, 0.2) 100%); }
    .monitor-outer-frame { box-shadow: 0 0 15px rgba($cyber-yellow, 0.2), 0 8px 30px rgba(0, 0, 0, 0.6); }
  }

  &.status-critical {
    .screen-glow { background: radial-gradient(ellipse at center, $cyber-red 0%, transparent 70%); }
    .led-indicator.power { background: $cyber-red; box-shadow: 0 0 8px $cyber-red; animation: led-blink-monitor 0.8s ease-in-out infinite; }
    .power-button .button-center { background: radial-gradient(circle, rgba($cyber-red, 0.6) 0%, rgba($cyber-red, 0.2) 100%); }
    .monitor-outer-frame { box-shadow: 0 0 20px rgba($cyber-red, 0.3), 0 8px 30px rgba(0, 0, 0, 0.6); }
  }

  &.status-unknown {
    opacity: 0.5;
    .screen-glow { opacity: 0 !important; }
    .led-indicator.power { background: #333; box-shadow: none; }
    .power-button .button-center { background: #222; }
    .screen-area { background: #0a0a0a; }
  }
}

@keyframes led-blink-monitor {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

// Monitor Back Shell
.monitor-back-shell {
  width: 80%;
  height: 10px;
  margin: 0 auto;
  background: linear-gradient(180deg,
    $monitor-frame-mid 0%,
    $monitor-frame-dark 40%,
    $monitor-frame-darkest 100%
  );
  border-radius: 10px 10px 0 0;
  position: relative;
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.05),
    0 -2px 8px rgba(0, 0, 0, 0.5);

  &::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 15%;
    right: 15%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.12), transparent);
    border-radius: 2px;
  }

  .shell-vent-grille {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    display: flex;
    gap: 3px;

    .vent-slot {
      width: 6px;
      height: 2px;
      background: #0a0a0a;
      border-radius: 1px;
      box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.8);
    }
  }
}

// CRT Body
.crt-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

// Outer Frame
.monitor-outer-frame {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: linear-gradient(160deg,
    #2d2d2d 0%,
    #252525 15%,
    #1a1a1a 50%,
    #141414 85%,
    #0f0f0f 100%
  );
  border-radius: 6px;
  padding: 12px 12px 6px 12px;
  position: relative;
  box-shadow:
    0 0 10px rgba($cyber-cyan, 0.12),
    0 8px 30px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.08),
    inset 0 -1px 0 rgba(0, 0, 0, 0.4);
  transition: box-shadow 0.3s ease;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 6px;
    background: repeating-linear-gradient(
      0deg,
      transparent, transparent 2px,
      rgba(255, 255, 255, 0.01) 2px,
      rgba(255, 255, 255, 0.01) 4px
    );
    pointer-events: none;
    z-index: 0;
  }
}

// Corner Accents
.corner-accent {
  position: absolute;
  width: 10px;
  height: 10px;
  border: 2px solid rgba(255, 255, 255, 0.06);
  z-index: 5;

  &.top-left { top: 4px; left: 4px; border-right: none; border-bottom: none; border-radius: 3px 0 0 0; }
  &.top-right { top: 4px; right: 4px; border-left: none; border-bottom: none; border-radius: 0 3px 0 0; }
  &.bottom-left { bottom: 32px; left: 4px; border-right: none; border-top: none; border-radius: 0 0 0 3px; }
  &.bottom-right { bottom: 32px; right: 4px; border-left: none; border-top: none; border-radius: 0 0 3px 0; }
}

// Frame Screws
.frame-screw {
  position: absolute;
  width: 7px;
  height: 7px;
  background: radial-gradient(circle at 35% 35%,
    #3a3a3a 0%, #252525 40%, #1a1a1a 100%
  );
  border-radius: 50%;
  box-shadow:
    inset 0 1px 2px rgba(0, 0, 0, 0.9),
    0 1px 1px rgba(255, 255, 255, 0.05);
  z-index: 10;

  &::before, &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #151515;
  }

  &::before { width: 4px; height: 1px; }
  &::after { width: 1px; height: 4px; }

  &.top-left { top: 6px; left: 6px; }
  &.top-right { top: 6px; right: 6px; }
  &.bottom-left { bottom: 34px; left: 6px; }
  &.bottom-right { bottom: 34px; right: 6px; }
}

// Brand Label
.brand-label {
  position: absolute;
  top: 5px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 5px;
  z-index: 10;

  .brand-text {
    font-family: $font-mono;
    font-size: 7px;
    font-weight: bold;
    color: rgba($cyber-cyan, 0.6);
    letter-spacing: 2px;
    text-shadow: 0 0 4px rgba($cyber-cyan, 0.3);
  }

  .model-text {
    font-family: $font-mono;
    font-size: 6px;
    color: rgba(255, 255, 255, 0.25);
    letter-spacing: 1px;
  }
}

// Inner Frame
.monitor-inner-frame {
  flex: 1;
  background: linear-gradient(180deg, #1a1a1a 0%, #151515 50%, #101010 100%);
  border-radius: 4px;
  padding: 3px;
  box-shadow:
    inset 0 2px 6px rgba(0, 0, 0, 0.6),
    inset 0 0 0 1px rgba(0, 0, 0, 0.4);
  position: relative;
}

.inner-bezel {
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg, #0f0f0f 0%, #0a0a0a 100%);
  border-radius: 3px;
  padding: 3px;
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.5),
    inset 0 0 0 1px rgba(0, 0, 0, 0.3);
}

.screen-area {
  width: 100%;
  height: 100%;
  background: #050810;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  box-shadow:
    inset 0 0 30px rgba(0, 0, 0, 0.4),
    inset 0 0 60px rgba(0, 0, 0, 0.2);
}

// CRT Effects
.crt-vignette {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(
    ellipse 120% 120% at center,
    transparent 40%,
    rgba(0, 0, 0, 0.3) 80%,
    rgba(0, 0, 0, 0.6) 100%
  );
  pointer-events: none;
  z-index: 12;
  border-radius: 4px;
}

.screen-glow {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  opacity: 0.1;
  pointer-events: none;
  z-index: 1;
  transition: opacity 0.3s ease;
}

.screen-glare {
  position: absolute;
  top: 3%; left: 3%;
  width: 35%; height: 30%;
  background: linear-gradient(135deg,
    rgba(255, 255, 255, 0.08) 0%,
    rgba(255, 255, 255, 0.02) 30%,
    transparent 60%
  );
  border-radius: 50%;
  pointer-events: none;
  z-index: 14;
}

.scanlines {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent, transparent 2px,
    rgba(0, 0, 0, 0.06) 2px,
    rgba(0, 0, 0, 0.06) 4px
  );
  background-size: 100% 4px;
  pointer-events: none;
  z-index: 10;
  opacity: 0.4;
}

.phosphor-pattern {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    repeating-linear-gradient(
      90deg,
      rgba(255, 0, 0, 0.015) 0px,
      rgba(255, 0, 0, 0.015) 1px,
      rgba(0, 255, 0, 0.015) 1px,
      rgba(0, 255, 0, 0.015) 2px,
      rgba(0, 0, 255, 0.015) 2px,
      rgba(0, 0, 255, 0.015) 3px
    );
  pointer-events: none;
  z-index: 11;
  opacity: 0.5;
}

// Card Content
.card-content {
  position: relative;
  padding: 6px 8px;
  z-index: 5;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 3px;
  flex-shrink: 0;
}

.server-info {
  flex: 1;
  min-width: 0;
}

.server-name {
  font-family: $font-mono;
  font-size: 13px;
  font-weight: bold;
  color: $cyber-cyan;
  text-shadow:
    0 0 10px rgba($cyber-cyan, 0.6),
    0 0 20px rgba($cyber-cyan, 0.3);
  letter-spacing: 1px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.server-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 1px;
}

.server-ip {
  font-family: $font-mono;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
}

.edition-badge {
  font-family: $font-mono;
  font-size: 8px;
  padding: 1px 4px;
  letter-spacing: 1px;

  &.xe {
    background: rgba($cyber-yellow, 0.15);
    color: $cyber-yellow;
    border: 1px solid rgba($cyber-yellow, 0.3);
  }

  &.se {
    background: rgba($cyber-cyan, 0.15);
    color: $cyber-cyan;
    border: 1px solid rgba($cyber-cyan, 0.3);
  }
}

.server-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 9px;
  font-family: $font-mono;
  letter-spacing: 1px;
  flex-shrink: 0;

  .status-led {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: $cyber-cyan;
    box-shadow: 0 0 6px $cyber-cyan;
    flex-shrink: 0;
    animation: led-breathe 2s ease-in-out infinite;
  }

  .status-text {
    color: currentColor;
    font-weight: bold;
  }

  &.normal { color: $cyber-cyan; }
  &.warning {
    color: $cyber-yellow;
    .status-led { background: $cyber-yellow; box-shadow: 0 0 6px $cyber-yellow; }
  }
  &.critical {
    color: $cyber-red;
    .status-led { background: $cyber-red; box-shadow: 0 0 8px $cyber-red; animation: led-blink-monitor 0.8s ease-in-out infinite; }
  }
  &.unknown {
    color: #666;
    .status-led { background: #333; box-shadow: none; animation: none; }
  }
}

@keyframes led-breathe {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

// Section Divider
.section-divider {
  height: 1px;
  background: linear-gradient(90deg,
    rgba($cyber-cyan, 0.1) 0%,
    rgba($cyber-cyan, 0.35) 50%,
    rgba($cyber-cyan, 0.1) 100%);
  margin: 3px 0;
  flex-shrink: 0;
  box-shadow: 0 0 3px rgba($cyber-cyan, 0.15);
}

// Gauge Section
.gauge-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 4px 0;
  flex: 1;
  min-height: 0;
  justify-content: center;
}

.gauge-row {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  gap: 12px;
  width: 100%;
}

.gauge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  flex: 1;
  min-width: 0;
}

.gauge-ring {
  position: relative;
  width: 90px;
  height: 90px;
  flex-shrink: 0;
}

.gauge-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.gauge-bg {
  fill: none;
  stroke: rgba($cyber-cyan, 0.08);
  stroke-width: 5;

  &.gauge-bg-cyan {
    stroke: rgba(0, 153, 255, 0.08);
  }
}

.gauge-fill {
  fill: none;
  stroke-width: 5;
  stroke-linecap: round;
  stroke-dasharray: 263.89;
  transition: stroke-dashoffset 1s ease;

  &.normal { stroke: $cyber-cyan; filter: drop-shadow(0 0 6px rgba($cyber-cyan, 0.5)); }
  &.system { stroke: #0099ff; filter: drop-shadow(0 0 6px rgba(0, 153, 255, 0.5)); }
  &.warning { stroke: $cyber-yellow; filter: drop-shadow(0 0 6px rgba($cyber-yellow, 0.5)); }
  &.critical { stroke: $cyber-red; filter: drop-shadow(0 0 6px rgba($cyber-red, 0.5)); }
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
    text-shadow: 0 0 10px rgba($cyber-cyan, 0.5);
  }

  .gauge-unit {
    font-family: $font-mono;
    font-size: 11px;
    color: $text-secondary;
    margin-left: 1px;
  }
}

.gauge-label {
  text-align: center;

  .ts-name {
    font-family: $font-mono;
    font-size: 10px;
    color: $cyber-cyan;
    letter-spacing: 1px;
    word-break: break-all;
    line-height: 1.2;

    &.ts-name-cyan {
      color: #0099ff;
    }
  }
}

.gauge-count {
  display: flex;
  align-items: center;
  align-self: center;

  .ts-count {
    font-family: $font-mono;
    font-size: 11px;
    color: $text-secondary;
    white-space: nowrap;
    text-align: center;
    line-height: 1.3;
  }
}

// Info rows
.info-rows {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-height: 0;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1px 0;

  .info-label {
    font-family: $font-mono;
    font-size: 9px;
    color: rgba(255, 255, 255, 0.35);
    letter-spacing: 1px;
  }

  .info-value {
    font-family: $font-mono;
    font-size: 10px;
    color: rgba($text-white, 0.8);

    &.backup-success { color: $cyber-cyan; }
    &.backup-failed { color: $cyber-red; }
    &.backup-none { color: $text-secondary; }
    &.alert-active { color: $cyber-yellow; font-weight: bold; }
    &.time-value { color: rgba($cyber-cyan, 0.7); }
  }
}

// Control Panel
.control-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 24px;
  padding: 3px 6px;
  margin-top: 3px;
  background: linear-gradient(180deg,
    $monitor-frame-dark 0%,
    $monitor-frame-darkest 100%
  );
  border-radius: 0 0 4px 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  position: relative;
  z-index: 10;
}

.power-button {
  width: 14px;
  height: 14px;
  position: relative;
  cursor: pointer;

  .button-ring {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    border: 2px solid #2a2a2a;
    border-radius: 50%;
    background: linear-gradient(145deg, #1a1a1a, #0f0f0f);
    box-shadow:
      inset 0 1px 3px rgba(0, 0, 0, 0.8),
      0 1px 1px rgba(255, 255, 255, 0.05);
  }

  .button-center {
    position: absolute;
    top: 3px; left: 3px;
    width: 8px; height: 8px;
    border-radius: 50%;
    box-shadow: 0 0 4px rgba($cyber-cyan, 0.3);
  }
}

.control-knobs {
  display: flex;
  gap: 8px;

  .knob {
    width: 12px;
    height: 12px;
    position: relative;

    .knob-cap {
      width: 100%; height: 100%;
      background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
      border-radius: 50%;
      box-shadow:
        inset 0 1px 2px rgba(0, 0, 0, 0.6),
        0 1px 1px rgba(255, 255, 255, 0.05);
      border: 1px solid #333;
    }

    .knob-indicator {
      position: absolute;
      top: 2px;
      left: 50%;
      transform: translateX(-50%);
      width: 2px;
      height: 3px;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 1px;
    }

    &.brightness .knob-indicator {
      transform: translateX(-50%) rotate(-30deg);
      transform-origin: bottom center;
    }

    &.contrast .knob-indicator {
      transform: translateX(-50%) rotate(30deg);
      transform-origin: bottom center;
    }
  }
}

.led-panel {
  display: flex;
  align-items: center;
  gap: 5px;
}

.led-indicator {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #222;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.8);
  transition: all 0.3s ease;

  &.power {
    background: $cyber-cyan;
    box-shadow: 0 0 6px $cyber-cyan;
    animation: led-breathe 2s ease-in-out infinite;
  }

  &.hdd {
    &.active {
      background: #ff6600;
      box-shadow: 0 0 4px #ff6600;
      animation: led-flicker 0.5s ease-in-out infinite;
    }
  }

  &.network {
    &.active {
      background: #00ff00;
      box-shadow: 0 0 4px #00ff00;
      animation: led-breathe 1s ease-in-out infinite;
    }
  }
}

@keyframes led-flicker {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

// Monitor Stand
.monitor-stand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: -1px;
  position: relative;
}

.stand-neck {
  width: 24px;
  height: 14px;
  position: relative;
  z-index: 4;

  .neck-joint {
    width: 100%;
    height: 5px;
    background: linear-gradient(180deg,
      $monitor-frame-mid 0%,
      $monitor-frame-dark 100%
    );
    border-radius: 2px;
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.05),
      0 1px 2px rgba(0, 0, 0, 0.5);
  }

  .neck-shaft {
    width: 16px;
    height: 10px;
    margin: 0 auto;
    background: linear-gradient(90deg,
      #151515 0%, #252525 30%, #2a2a2a 50%, #252525 70%, #151515 100%
    );
    border-radius: 0 0 3px 3px;
    box-shadow:
      inset 2px 0 4px rgba(0, 0, 0, 0.4),
      inset -2px 0 4px rgba(0, 0, 0, 0.4);
  }
}

.stand-base {
  width: 56px;
  position: relative;

  .base-plate {
    width: 100%;
    height: 8px;
    background: linear-gradient(180deg,
      $monitor-frame-mid 0%,
      $monitor-frame-dark 40%,
      $monitor-frame-darkest 100%
    );
    border-radius: 50%;
    box-shadow:
      0 2px 6px rgba(0, 0, 0, 0.6),
      inset 0 1px 0 rgba(255, 255, 255, 0.06),
      inset 0 -1px 0 rgba(0, 0, 0, 0.5);
  }

  .base-shadow {
    position: absolute;
    bottom: -3px;
    left: 10%;
    right: 10%;
    height: 3px;
    background: radial-gradient(ellipse, rgba(0, 0, 0, 0.4) 0%, transparent 70%);
    filter: blur(2px);
  }
}

// ============================================
// Right: Guardian Section - matching Dashboard
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
// Database Alert Log - matching SystemLog style
// ============================================
.db-alert-log {
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

.log-scanlines {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent, transparent 2px,
    rgba(0, 0, 0, 0.04) 2px,
    rgba(0, 0, 0, 0.04) 4px
  );
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

  .header-bracket {
    color: rgba($cyber-cyan, 0.5);
  }

  .header-icon {
    color: $cyber-cyan;
    text-shadow: 0 0 10px $cyber-cyan;
    animation: header-blink 1s step-end infinite;
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

@keyframes header-blink {
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
  gap: 8px;
  padding: 5px 14px;
  font-size: 11px;
  line-height: 1.4;
  border-left: 2px solid transparent;
  transition: background 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
  flex-wrap: wrap;
  position: relative;

  &:hover {
    background: rgba($cyber-cyan, 0.05);
  }

  &.expanded {
    background: rgba($cyber-cyan, 0.08);
    white-space: normal;

    .log-message .message-text {
      white-space: normal;
      overflow: visible;
      text-overflow: unset;
    }
  }

  &.critical {
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
    min-width: 18px;
    text-align: right;
    font-size: 10px;
  }

  .log-level {
    flex-shrink: 0;
    font-weight: bold;
    min-width: 55px;
    font-size: 10px;

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

  .log-server {
    color: $cyber-cyan;
    flex-shrink: 0;
    min-width: 60px;
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

  .log-detail {
    width: 100%;
    padding: 6px 0 4px 28px;
    animation: detailFadeIn 0.2s ease-out;

    .detail-row {
      display: flex;
      gap: 8px;
      font-size: 10px;
      padding: 2px 0;
    }

    .detail-label {
      color: rgba($cyber-cyan, 0.5);
      min-width: 60px;
      flex-shrink: 0;
      font-weight: bold;
      letter-spacing: 0.5px;
    }

    .detail-value {
      color: rgba(255, 255, 255, 0.7);
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
    width: 8px;
    height: 14px;
    background: rgba($cyber-cyan, 0.5);
    animation: cursorBlink 1s step-end infinite;
    box-shadow: 0 0 6px rgba($cyber-cyan, 0.3);
  }
}

@keyframes cursorBlink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

// ============================================
// Alert Filter Bar
// ============================================
.alert-filter-bar {
  position: relative;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba($cyber-cyan, 0.1);
}

.alert-filter-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.alert-filter-label {
  font-family: $font-mono;
  font-size: 9px;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 1px;
}

.alert-filter-select {
  background: rgba(0, 0, 0, 0.7);
  border: 1px solid rgba($cyber-cyan, 0.25);
  color: $cyber-cyan;
  font-family: $font-mono;
  font-size: 10px;
  padding: 2px 4px;
  outline: none;
  cursor: pointer;
  max-width: 90px;

  option {
    background: #0a0a0a;
    color: $cyber-cyan;
  }

  &:focus {
    border-color: $cyber-cyan;
  }
}

.alert-filter-total {
  margin-left: auto;
  font-family: $font-mono;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.35);
}

.alert-total-count {
  color: $cyber-yellow;
  font-weight: bold;
  font-size: 12px;
  text-shadow: 0 0 6px rgba($cyber-yellow, 0.4);
}

// ============================================
// Alert Summary Stats
// ============================================
.alert-stats-row {
  position: relative;
  z-index: 5;
  display: flex;
  gap: 6px;
  padding: 5px 12px;
  background: rgba(0, 0, 0, 0.25);
  border-bottom: 1px solid rgba($cyber-cyan, 0.08);
}

.alert-stat-item {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 3px 0;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba($cyber-cyan, 0.1);
}

.alert-stat-num {
  font-family: $font-terminal;
  font-size: 14px;
  font-weight: bold;

  &.total {
    color: rgba(255, 255, 255, 0.85);
    text-shadow: 0 0 6px rgba(255, 255, 255, 0.15);
  }

  &.warning {
    color: $cyber-yellow;
    text-shadow: 0 0 6px rgba($cyber-yellow, 0.3);
  }

  &.critical {
    color: $cyber-red;
    text-shadow: 0 0 6px rgba($cyber-red, 0.3);
  }
}

.alert-stat-lbl {
  font-family: $font-mono;
  font-size: 8px;
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 1px;
}

// ============================================
// Alert Table
// ============================================
.alert-table-wrap {
  position: relative;
  z-index: 5;
  flex: 1;
  overflow-y: auto;
  min-height: 0;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.2); }
  &::-webkit-scrollbar-thumb {
    background: rgba($cyber-cyan, 0.3);
    border-radius: 2px;
    &:hover { background: rgba($cyber-cyan, 0.5); }
  }
}

.alert-table {
  width: 100%;
  border-collapse: collapse;
  font-family: $font-mono;
  font-size: 10px;

  thead {
    position: sticky;
    top: 0;
    z-index: 2;
  }

  th {
    color: rgba(255, 255, 255, 0.35);
    font-size: 9px;
    letter-spacing: 1px;
    text-align: left;
    padding: 5px 6px;
    border-bottom: 1px solid rgba($cyber-cyan, 0.2);
    background: rgba(0, 0, 0, 0.5);
  }

  td {
    padding: 4px 6px;
    border-bottom: 1px solid rgba($cyber-cyan, 0.04);
    color: rgba(255, 255, 255, 0.7);
    font-size: 10px;
    line-height: 1.3;
  }

  tr:hover td {
    background: rgba($cyber-cyan, 0.04);
  }
}

.at-col-sev { width: 40px; }
.at-col-svr { width: 60px; }
.at-col-msg { }
.at-col-time { width: 72px; }

.at-row-warning {
  border-left: 2px solid $cyber-yellow;
}

.at-row-critical {
  border-left: 2px solid $cyber-red;
}

.at-sev-badge {
  font-size: 8px;
  padding: 1px 4px;
  letter-spacing: 0.5px;
  font-weight: bold;
  white-space: nowrap;

  &.warning {
    color: $cyber-yellow;
    background: rgba($cyber-yellow, 0.1);
    border: 1px solid rgba($cyber-yellow, 0.3);
  }

  &.critical {
    color: $cyber-red;
    background: rgba($cyber-red, 0.1);
    border: 1px solid rgba($cyber-red, 0.3);
  }

  &.info {
    color: $cyber-blue;
    background: rgba($cyber-blue, 0.1);
    border: 1px solid rgba($cyber-blue, 0.3);
  }
}

.at-server-cell {
  color: $cyber-cyan;
  font-weight: bold;
  font-size: 9px;
  white-space: nowrap;
}

.at-msg-cell {
  color: rgba(255, 255, 255, 0.65);
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 10px;
}

.at-time-cell {
  white-space: nowrap;
  color: rgba($cyber-cyan, 0.5);
  font-size: 9px;
}

.at-empty-cell {
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  padding: 20px 10px !important;
  font-size: 11px;
  letter-spacing: 2px;
}

// ============================================
// Alert Pagination
// ============================================
.alert-pagination {
  position: relative;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 5px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba($cyber-cyan, 0.08);
}

.alert-page-btn {
  background: none;
  border: 1px solid rgba($cyber-cyan, 0.25);
  color: $cyber-cyan;
  font-family: $font-mono;
  font-size: 10px;
  padding: 2px 8px;
  cursor: pointer;
  letter-spacing: 1px;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: rgba($cyber-cyan, 0.1);
    border-color: $cyber-cyan;
  }

  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
}

.alert-page-info {
  font-family: $font-mono;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 1px;
}

// ============================================
// Command Line
// ============================================
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

// ============================================
// Loading
// ============================================
.loading-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 100;
}

.loading-text {
  font-family: $font-terminal;
  font-size: 16px;
  color: $cyber-cyan;
  letter-spacing: 3px;
  text-shadow: 0 0 15px rgba($cyber-cyan, 0.5);
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
// Responsive - matching Dashboard breakpoints
// ============================================
@media (max-width: 1600px) {
  .system-title {
    font-size: 18px;
    letter-spacing: 3px;
  }
}

@media (max-width: 1400px) {
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
  .servers-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .guardian-section {
    min-width: 240px;
  }
  .top-status-bar {
    padding: 12px 20px;
  }
  .system-title {
    font-size: 16px;
  }
}

@media (max-width: 1000px) {
  .status-center {
    display: none;
  }
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  .servers-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .guardian-section {
    max-width: none;
    flex-direction: row;
  }
  .face-panel {
    height: 200px;
    width: 200px;
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
}

// ============================================
// Database Detail Modal Styles
// ============================================

// Override CyberModal body max-height for larger chart content
// height prop on CyberModal handles sizing

.modal-title-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.modal-db-name {
  font-family: $font-terminal;
  font-size: 16px;
  color: $cyber-cyan;
  letter-spacing: 3px;
  text-shadow: 0 0 10px rgba($cyber-cyan, 0.5);
}

.modal-db-ip {
  font-family: $font-mono;
  font-size: 11px;
  color: $text-secondary;
  padding: 2px 10px;
  border: 1px solid rgba($text-secondary, 0.3);
}

.modal-time-range {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

.modal-range-btn {
  background: none;
  border: 1px solid rgba($cyber-cyan, 0.2);
  color: rgba($cyber-cyan, 0.5);
  font-family: $font-mono;
  font-size: 11px;
  padding: 3px 12px;
  cursor: pointer;
  letter-spacing: 1px;
  transition: all 0.2s;

  &:hover {
    border-color: rgba($cyber-cyan, 0.5);
    color: $cyber-cyan;
  }

  &.active {
    background: rgba($cyber-cyan, 0.1);
    border-color: $cyber-cyan;
    color: $cyber-cyan;
  }
}

.modal-refresh-btn {
  background: none;
  border: 1px solid rgba($cyber-cyan, 0.3);
  color: $cyber-cyan;
  padding: 4px 10px;
  cursor: pointer;
  font-family: $font-mono;
  font-size: 14px;
  transition: all 0.2s;

  &:hover { background: rgba($cyber-cyan, 0.1); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }

  .bracket { opacity: 0.5; }
  .spin { display: inline-block; animation: spin 1s linear infinite; }
}

.modal-charts-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.modal-chart-card {
  background: rgba(5, 5, 15, 0.6);
  border: 1px solid rgba($cyber-cyan, 0.15);
  padding: 8px 12px;
}

.modal-chart-title {
  font-family: $font-terminal;
  font-size: 12px;
  color: $cyber-cyan;
  letter-spacing: 2px;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba($cyber-cyan, 0.1);

  .ct-icon {
    color: $neon-cyan;
    margin-right: 6px;
    font-size: 10px;
  }
}

.modal-chart-container {
  width: 100%;
  height: 33vh;
}

.modal-chart-bar {
  height: 28vh;
}

.modal-chart-trend {
  height: 22vh;
}

// ============ Backup Records Table in Modal ============
.modal-backup-table-wrap {
  max-height: 20vh;
  overflow-y: auto;

  &::-webkit-scrollbar { width: 3px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba($cyber-cyan, 0.3); border-radius: 2px; }
}

.modal-backup-table {
  width: 100%;
  border-collapse: collapse;
  font-family: $font-mono;
  font-size: 11px;

  th {
    color: rgba(255, 255, 255, 0.4);
    font-size: 10px;
    letter-spacing: 1px;
    text-align: left;
    padding: 6px 10px;
    border-bottom: 1px solid rgba($cyber-cyan, 0.2);
    background: rgba(0, 0, 0, 0.3);
    position: sticky;
    top: 0;
    z-index: 1;
  }

  td {
    padding: 5px 10px;
    border-bottom: 1px solid rgba($cyber-cyan, 0.05);
    color: rgba(255, 255, 255, 0.75);
  }

  tr:hover td {
    background: rgba($cyber-cyan, 0.03);
  }
}

.backup-type-badge {
  font-size: 9px;
  padding: 1px 6px;
  background: rgba($cyber-cyan, 0.1);
  border: 1px solid rgba($cyber-cyan, 0.3);
  color: $cyber-cyan;
  letter-spacing: 1px;
}

.backup-status-badge {
  font-size: 9px;
  padding: 2px 8px;
  letter-spacing: 1px;
  font-weight: bold;

  &.success {
    color: $cyber-cyan;
    background: rgba($cyber-cyan, 0.1);
    border: 1px solid rgba($cyber-cyan, 0.3);
  }
  &.failed {
    color: $cyber-red;
    background: rgba($cyber-red, 0.1);
    border: 1px solid rgba($cyber-red, 0.3);
  }
  &.running {
    color: $cyber-yellow;
    background: rgba($cyber-yellow, 0.1);
    border: 1px solid rgba($cyber-yellow, 0.3);
  }
}

.backup-size-cell {
  text-align: right;
  white-space: nowrap;
}

.backup-time-cell {
  white-space: nowrap;
  color: rgba($cyber-cyan, 0.6);
  font-size: 10px;
}

.modal-backup-empty {
  text-align: center;
  color: rgba(255, 255, 255, 0.3);
  padding: 20px;
  font-family: $font-mono;
  font-size: 12px;
  letter-spacing: 2px;
}
</style>
