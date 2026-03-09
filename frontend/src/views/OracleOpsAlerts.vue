<template>
  <div class="ops-alerts-container">
    <!-- Top Bar -->
    <header class="ops-top-bar">
      <div class="bar-left">
        <button class="back-btn" @click="$router.push('/oracle-ops')">
          <span class="bracket">[</span>
          <span class="arrow">&lt;</span>
          <span class="bracket">]</span>
        </button>
        <div class="page-title">
          <span class="title-icon">&#9888;</span>
          <span class="title-text">ALERT HISTORY</span>
        </div>
      </div>
      <div class="bar-right">
        <button class="refresh-btn" @click="loadData" :disabled="store.alertsLoading">
          <span class="bracket">[</span>
          <span :class="{ 'spin': store.alertsLoading }">&#8635;</span>
          <span class="bracket">]</span>
        </button>
      </div>
    </header>

    <!-- Filters -->
    <div class="filter-bar">
      <div class="filter-group">
        <label class="filter-label">SERVER</label>
        <select v-model="filterServer" class="filter-select" @change="loadData">
          <option value="">ALL</option>
          <option v-for="(config, id) in ORACLE_SERVER_CONFIG" :key="id" :value="id">
            {{ config.shortName }}
          </option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">SEVERITY</label>
        <select v-model="filterSeverity" class="filter-select" @change="loadData">
          <option value="">ALL</option>
          <option value="warning">WARNING</option>
          <option value="critical">CRITICAL</option>
        </select>
      </div>
      <div class="filter-info">
        TOTAL: <span class="filter-count">{{ store.alerts.total }}</span> ALERTS
      </div>
    </div>

    <!-- Summary Stats -->
    <div class="stats-row">
      <div class="stat-box">
        <div class="stat-number total">{{ store.alerts.total }}</div>
        <div class="stat-label">TOTAL</div>
      </div>
      <div class="stat-box">
        <div class="stat-number warning">{{ warningCount }}</div>
        <div class="stat-label">WARNING</div>
      </div>
      <div class="stat-box">
        <div class="stat-number critical">{{ criticalCount }}</div>
        <div class="stat-label">CRITICAL</div>
      </div>
    </div>

    <!-- Alerts Table -->
    <div class="table-card">
      <table class="data-table">
        <thead>
          <tr>
            <th class="col-severity">SEVERITY</th>
            <th class="col-server">SERVER</th>
            <th class="col-type">TYPE</th>
            <th class="col-message">MESSAGE</th>
            <th class="col-time">TRIGGERED</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="alert in store.alerts.records"
            :key="alert.id"
            :class="'row-' + alert.severity"
          >
            <td>
              <span class="severity-badge" :class="alert.severity">
                {{ (alert.severity || '').toUpperCase() }}
              </span>
            </td>
            <td class="server-cell">{{ getServerName(alert.server_id) }}</td>
            <td class="type-cell">
              <span class="type-badge">{{ (alert.alert_type || '').toUpperCase() }}</span>
            </td>
            <td class="message-cell">{{ alert.message }}</td>
            <td class="time-cell">{{ formatDateTime(alert.triggered_at) }}</td>
          </tr>
          <tr v-if="store.alerts.records.length === 0">
            <td colspan="5" class="empty-cell">
              {{ store.alertsLoading ? 'SCANNING...' : 'NO ALERTS FOUND' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="store.alerts.total > store.alerts.page_size">
      <button
        class="page-btn"
        :disabled="store.alerts.page <= 1"
        @click="goPage(store.alerts.page - 1)"
      >&lt; PREV</button>
      <span class="page-info">
        PAGE {{ store.alerts.page }} / {{ totalPages }}
      </span>
      <button
        class="page-btn"
        :disabled="store.alerts.page >= totalPages"
        @click="goPage(store.alerts.page + 1)"
      >NEXT &gt;</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useOracleOpsStore, ORACLE_SERVER_CONFIG } from '@/stores/oracle_ops'

const store = useOracleOpsStore()

const filterServer = ref('')
const filterSeverity = ref('')

const totalPages = computed(() => {
  return Math.ceil(store.alerts.total / store.alerts.page_size) || 1
})

const warningCount = computed(() => {
  return store.alerts.records.filter(a => a.severity === 'warning').length
})

const criticalCount = computed(() => {
  return store.alerts.records.filter(a => a.severity === 'critical').length
})

function getServerName(serverId) {
  return ORACLE_SERVER_CONFIG[serverId]?.shortName || serverId
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const min = d.getMinutes().toString().padStart(2, '0')
  const sec = d.getSeconds().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${min}:${sec}`
}

function loadData() {
  store.fetchAlerts({
    serverId: filterServer.value || undefined,
    severity: filterSeverity.value || undefined,
    page: 1,
  })
}

function goPage(page) {
  store.fetchAlerts({
    serverId: filterServer.value || undefined,
    severity: filterSeverity.value || undefined,
    page,
  })
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.ops-alerts-container {
  height: 100vh;
  padding: 16px 24px;
  overflow-y: auto;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba($neon-green, 0.3); border-radius: 2px; }
}

// ============ Top Bar ============
.ops-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  margin-bottom: 16px;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba($neon-green, 0.3);
}

.bar-left, .bar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn, .refresh-btn {
  background: none;
  border: 1px solid rgba($neon-green, 0.3);
  color: $neon-green;
  padding: 4px 10px;
  cursor: pointer;
  font-family: $font-mono;
  font-size: 14px;
  transition: all 0.2s;

  &:hover { background: rgba($neon-green, 0.1); border-color: $neon-green; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
  .bracket { opacity: 0.5; }
  .spin { display: inline-block; animation: spin 1s linear infinite; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  .title-icon { color: $neon-orange; font-size: 16px; }
  .title-text {
    font-family: $font-terminal;
    font-size: 15px;
    color: $neon-green;
    letter-spacing: 2px;
  }
}

// ============ Filters ============
.filter-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 16px;
  margin-bottom: 16px;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba($neon-green, 0.1);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-family: $font-mono;
  font-size: 10px;
  color: $text-secondary;
  letter-spacing: 1px;
}

.filter-select {
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba($neon-green, 0.3);
  color: $neon-green;
  font-family: $font-mono;
  font-size: 11px;
  padding: 4px 8px;
  outline: none;
  cursor: pointer;

  option { background: #0a0a0a; color: $neon-green; }
  &:focus { border-color: $neon-green; }
}

.filter-info {
  margin-left: auto;
  font-family: $font-mono;
  font-size: 11px;
  color: $text-secondary;
  letter-spacing: 1px;
  .filter-count { color: $neon-orange; font-weight: bold; }
}

// ============ Stats Row ============
.stats-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.stat-box {
  flex: 1;
  background: $bg-card;
  border: 1px solid rgba($neon-green, 0.15);
  padding: 12px 16px;
  text-align: center;
}

.stat-number {
  font-family: $font-terminal;
  font-size: 24px;
  margin-bottom: 4px;

  &.total { color: $neon-green; text-shadow: 0 0 10px rgba($neon-green, 0.3); }
  &.warning { color: $neon-orange; text-shadow: 0 0 10px rgba($neon-orange, 0.3); }
  &.critical { color: $neon-red; text-shadow: 0 0 10px rgba($neon-red, 0.3); }
}

.stat-label {
  font-family: $font-mono;
  font-size: 10px;
  color: $text-secondary;
  letter-spacing: 2px;
}

// ============ Table ============
.table-card {
  background: $bg-card;
  border: 1px solid rgba($neon-green, 0.15);
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-family: $font-mono;
  font-size: 11px;

  th {
    color: $text-secondary;
    font-size: 10px;
    letter-spacing: 1px;
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid rgba($neon-green, 0.2);
    background: rgba(0, 0, 0, 0.3);
    position: sticky;
    top: 0;
  }

  td {
    padding: 8px 12px;
    border-bottom: 1px solid rgba($neon-green, 0.05);
    color: rgba($text-white, 0.8);
  }

  tr:hover td { background: rgba($neon-green, 0.03); }

  .row-warning { border-left: 2px solid $neon-orange; }
  .row-critical { border-left: 2px solid $neon-red; }
}

.col-severity { width: 90px; }
.col-server { width: 100px; }
.col-type { width: 120px; }
.col-message { min-width: 200px; }
.col-time { width: 130px; }

.severity-badge {
  font-size: 9px;
  padding: 2px 8px;
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

.server-cell {
  color: $neon-cyan;
  font-weight: bold;
}

.type-badge {
  font-size: 9px;
  padding: 1px 6px;
  background: rgba($text-secondary, 0.1);
  border: 1px solid rgba($text-secondary, 0.3);
  color: $text-secondary;
  letter-spacing: 1px;
}

.message-cell {
  color: rgba($text-white, 0.7);
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.time-cell {
  white-space: nowrap;
  color: rgba($neon-green, 0.6);
  font-size: 10px;
}

.empty-cell {
  text-align: center;
  color: $text-secondary;
  padding: 30px;
  font-size: 12px;
  letter-spacing: 2px;
}

// ============ Pagination ============
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px 0;
}

.page-btn {
  background: none;
  border: 1px solid rgba($neon-green, 0.3);
  color: $neon-green;
  font-family: $font-mono;
  font-size: 11px;
  padding: 4px 12px;
  cursor: pointer;
  letter-spacing: 1px;
  transition: all 0.2s;

  &:hover:not(:disabled) { background: rgba($neon-green, 0.1); border-color: $neon-green; }
  &:disabled { opacity: 0.3; cursor: not-allowed; }
}

.page-info {
  font-family: $font-mono;
  font-size: 11px;
  color: $text-secondary;
  letter-spacing: 1px;
}
</style>
