<template>
  <div class="databases-page">
    <!-- Page Header -->
    <header class="page-header">
      <div class="header-left">
        <button class="back-btn" @click="$router.push('/')">
          <span class="bracket">[</span>
          <span class="arrow">&lt;</span>
          <span class="bracket">]</span>
        </button>
        <div class="page-title">
          <span class="title-icon">&#9671;</span>
          <span class="title-text">DATABASE MONITORING</span>
        </div>
        <div class="status-group">
          <div class="status-item normal">
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
      <div class="header-right">
        <button class="refresh-btn" @click="fetchDatabases" :disabled="loading">
          <span class="bracket">[</span>
          <span :class="{ 'spin': loading }">&#8635;</span>
          <span class="bracket">]</span>
        </button>
      </div>
    </header>

    <!-- Database Cards Grid -->
    <div class="databases-grid">
      <div
        v-for="dbItem in databases"
        :key="dbItem.server_id"
        class="database-card"
        :class="[`status-${dbItem.status}`]"
      >
        <!-- Card Header -->
        <div class="card-header">
          <div class="server-indicator" :class="dbItem.status"></div>
          <div class="server-info">
            <div class="server-name">{{ dbItem.server_name_cn || dbItem.server_id }}_DB</div>
            <div class="server-ip">{{ dbItem.server_ip }}</div>
          </div>
          <div class="status-badge" :class="dbItem.status">
            {{ getStatusText(dbItem.status) }}
          </div>
        </div>

        <!-- Tablespace Gauges Section -->
        <div class="gauges-section">
          <h4 class="section-label">TABLESPACE USAGE</h4>
          <div class="gauges-row">
            <!-- Business Data Tablespace Gauge -->
            <div class="gauge-item" v-if="dbItem.primary_business">
              <div class="gauge-ring">
                <svg viewBox="0 0 100 100" class="gauge-svg">
                  <circle cx="50" cy="50" r="42" class="gauge-bg" />
                  <circle
                    cx="50" cy="50" r="42"
                    class="gauge-fill"
                    :class="getGaugeClass(dbItem.primary_business.used_percent)"
                    :style="{ strokeDashoffset: getGaugeOffset(dbItem.primary_business.used_percent) }"
                  />
                </svg>
                <div class="gauge-value">
                  <span class="gauge-number">{{ Math.round(dbItem.primary_business.used_percent || 0) }}</span>
                  <span class="gauge-unit">%</span>
                </div>
              </div>
              <div class="gauge-label">
                <div class="ts-name">{{ dbItem.primary_business.name }}</div>
                <div class="ts-type business">BUSINESS DATA</div>
              </div>
            </div>

            <!-- No Business Tablespace Fallback -->
            <div class="gauge-item gauge-empty" v-else>
              <div class="gauge-ring">
                <svg viewBox="0 0 100 100" class="gauge-svg">
                  <circle cx="50" cy="50" r="42" class="gauge-bg" />
                </svg>
                <div class="gauge-value">
                  <span class="gauge-number empty">--</span>
                </div>
              </div>
              <div class="gauge-label">
                <div class="ts-name empty">N/A</div>
                <div class="ts-type business">BUSINESS DATA</div>
              </div>
            </div>

            <!-- SYSTEM Tablespace Gauge -->
            <div class="gauge-item" v-if="dbItem.system_tablespace">
              <div class="gauge-ring">
                <svg viewBox="0 0 100 100" class="gauge-svg">
                  <circle cx="50" cy="50" r="42" class="gauge-bg" />
                  <circle
                    cx="50" cy="50" r="42"
                    class="gauge-fill"
                    :class="getGaugeClass(dbItem.system_tablespace.used_percent)"
                    :style="{ strokeDashoffset: getGaugeOffset(dbItem.system_tablespace.used_percent) }"
                  />
                </svg>
                <div class="gauge-value">
                  <span class="gauge-number">{{ Math.round(dbItem.system_tablespace.used_percent || 0) }}</span>
                  <span class="gauge-unit">%</span>
                </div>
              </div>
              <div class="gauge-label">
                <div class="ts-name system">SYSTEM</div>
                <div class="ts-type system">SYSTEM SPACE</div>
              </div>
            </div>

            <!-- No SYSTEM Tablespace Fallback -->
            <div class="gauge-item gauge-empty" v-else>
              <div class="gauge-ring">
                <svg viewBox="0 0 100 100" class="gauge-svg">
                  <circle cx="50" cy="50" r="42" class="gauge-bg" />
                </svg>
                <div class="gauge-value">
                  <span class="gauge-number empty">--</span>
                </div>
              </div>
              <div class="gauge-label">
                <div class="ts-name empty">N/A</div>
                <div class="ts-type system">SYSTEM SPACE</div>
              </div>
            </div>
          </div>
          <div class="ts-count">{{ dbItem.filtered_tablespace_count || 0 }} tablespaces monitored</div>
        </div>

        <!-- Connection Metrics -->
        <div class="db-metrics">
          <div class="metric">
            <span class="metric-label">CONNECTIONS</span>
            <span class="metric-value">{{ dbItem.connections?.total_connections || 0 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">ACTIVE</span>
            <span class="metric-value">{{ dbItem.connections?.active_connections || 0 }}</span>
          </div>
        </div>

        <!-- Card Scanline Effect -->
        <div class="card-scanline"></div>
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

const API_BASE = '/api'
const databases = ref([])
const loading = ref(false)
let refreshInterval = null

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

function getStatusText(status) {
  if (status === 'critical') return 'CRITICAL'
  if (status === 'warning') return 'WARNING'
  return 'NORMAL'
}

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

onMounted(() => {
  fetchDatabases()
  refreshInterval = setInterval(fetchDatabases, 60000) // Refresh every 60s
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.databases-page {
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

// ============ Page Header ============
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  margin-bottom: 20px;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba($neon-green, 0.3);
  box-shadow: 0 0 15px rgba($neon-green, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
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
.databases-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.database-card {
  background: $bg-card;
  border: 1px solid rgba($neon-green, 0.2);
  padding: 16px;
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
}

// Card Header
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

.server-ip {
  font-family: $font-mono;
  font-size: 11px;
  color: $text-secondary;
  margin-top: 2px;
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
}

// ============ Gauges Section ============
.gauges-section {
  margin-bottom: 14px;
}

.section-label {
  font-family: $font-mono;
  font-size: 10px;
  color: $text-secondary;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 10px;
}

.gauges-row {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.gauge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.gauge-ring {
  position: relative;
  width: 80px;
  height: 80px;
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
}

.gauge-fill {
  fill: none;
  stroke-width: 6;
  stroke-linecap: round;
  stroke-dasharray: 263.89;
  transition: stroke-dashoffset 1s ease;

  &.normal { stroke: $neon-green; filter: drop-shadow(0 0 4px rgba($neon-green, 0.5)); }
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
    font-size: 20px;
    color: $text-white;
    text-shadow: 0 0 10px rgba($neon-green, 0.5);

    &.empty {
      color: $text-secondary;
      text-shadow: none;
    }
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
    line-height: 1.3;

    &.system {
      color: $neon-cyan;
    }

    &.empty {
      color: $text-secondary;
    }
  }

  .ts-type {
    font-family: $font-mono;
    font-size: 8px;
    letter-spacing: 1px;
    margin-top: 2px;
    padding: 1px 6px;
    display: inline-block;

    &.business {
      color: $neon-green;
      background: rgba($neon-green, 0.08);
      border: 1px solid rgba($neon-green, 0.2);
    }

    &.system {
      color: $neon-cyan;
      background: rgba($neon-cyan, 0.08);
      border: 1px solid rgba($neon-cyan, 0.2);
    }
  }
}

.ts-count {
  font-family: $font-mono;
  font-size: 10px;
  color: $text-secondary;
  text-align: center;
  margin-top: 8px;
  letter-spacing: 1px;
}

// ============ DB Metrics ============
.db-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;

  .metric {
    text-align: center;
    padding: 8px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba($neon-green, 0.1);

    .metric-label {
      display: block;
      font-family: $font-mono;
      font-size: 9px;
      color: $text-secondary;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 4px;
    }

    .metric-value {
      font-family: $font-terminal;
      font-size: 16px;
      color: $neon-cyan;
      font-weight: bold;
      text-shadow: 0 0 10px rgba($neon-cyan, 0.5);
    }
  }
}

// ============ Card Scanline Effect ============
.card-scanline {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba($neon-green, 0.3), transparent);
  opacity: 0;
  transition: opacity 0.3s;

  .database-card:hover & {
    opacity: 1;
    animation: scanMove 2s linear infinite;
  }
}

@keyframes scanMove {
  0% { transform: translateY(0); }
  100% { transform: translateY(300px); }
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
  .databases-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .databases-grid {
    grid-template-columns: 1fr;
  }
}
</style>
