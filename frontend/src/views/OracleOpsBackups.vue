<template>
  <div class="ops-backups-container">
    <!-- Top Bar -->
    <header class="ops-top-bar">
      <div class="bar-left">
        <button class="back-btn" @click="$router.push('/oracle-ops')">
          <span class="bracket">[</span>
          <span class="arrow">&lt;</span>
          <span class="bracket">]</span>
        </button>
        <div class="page-title">
          <span class="title-icon">&#9671;</span>
          <span class="title-text">BACKUP &amp; CLEANUP RECORDS</span>
        </div>
      </div>
      <div class="bar-right">
        <div class="tab-switcher">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'backups' }"
            @click="activeTab = 'backups'; loadData()"
          >BACKUPS</button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'cleanups' }"
            @click="activeTab = 'cleanups'; loadData()"
          >CLEANUPS</button>
        </div>
        <button class="refresh-btn" @click="loadData" :disabled="isLoading">
          <span class="bracket">[</span>
          <span :class="{ 'spin': isLoading }">&#8635;</span>
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
        <label class="filter-label">STATUS</label>
        <select v-model="filterStatus" class="filter-select" @change="loadData">
          <option value="">ALL</option>
          <option value="success">SUCCESS</option>
          <option value="failed">FAILED</option>
          <option value="running">RUNNING</option>
        </select>
      </div>
      <div class="filter-info">
        TOTAL: <span class="filter-count">{{ currentData.total }}</span> RECORDS
      </div>
    </div>

    <!-- Backup Records Table -->
    <div class="table-card" v-if="activeTab === 'backups'">
      <table class="data-table">
        <thead>
          <tr>
            <th>SERVER</th>
            <th>TYPE</th>
            <th>STATUS</th>
            <th>ROWS</th>
            <th>SIZE</th>
            <th>STARTED</th>
            <th>FINISHED</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in store.backups.records" :key="record.id">
            <td class="server-cell">{{ getServerName(record.server_id) }}</td>
            <td class="type-cell">
              <span class="type-badge">{{ (record.backup_type || '').toUpperCase() }}</span>
            </td>
            <td>
              <span class="status-badge" :class="record.status">
                {{ (record.status || '').toUpperCase() }}
              </span>
            </td>
            <td class="number-cell">{{ formatNumber(record.rows_exported) }}</td>
            <td class="number-cell">{{ formatSize(record.file_size_mb) }}</td>
            <td class="time-cell">{{ formatDateTime(record.started_at) }}</td>
            <td class="time-cell">{{ formatDateTime(record.finished_at) }}</td>
          </tr>
          <tr v-if="store.backups.records.length === 0">
            <td colspan="7" class="empty-cell">NO BACKUP RECORDS</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Cleanup Records Table -->
    <div class="table-card" v-if="activeTab === 'cleanups'">
      <table class="data-table">
        <thead>
          <tr>
            <th>SERVER</th>
            <th>TYPE</th>
            <th>STATUS</th>
            <th>ROWS DELETED</th>
            <th>SPACE FREED</th>
            <th>STARTED</th>
            <th>FINISHED</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="record in store.cleanups.records" :key="record.id">
            <td class="server-cell">{{ getServerName(record.server_id) }}</td>
            <td class="type-cell">
              <span class="type-badge">{{ (record.cleanup_type || '').toUpperCase() }}</span>
            </td>
            <td>
              <span class="status-badge" :class="record.status">
                {{ (record.status || '').toUpperCase() }}
              </span>
            </td>
            <td class="number-cell">{{ formatNumber(record.rows_deleted) }}</td>
            <td class="number-cell">{{ formatSize(record.space_freed_mb) }}</td>
            <td class="time-cell">{{ formatDateTime(record.started_at) }}</td>
            <td class="time-cell">{{ formatDateTime(record.finished_at) }}</td>
          </tr>
          <tr v-if="store.cleanups.records.length === 0">
            <td colspan="7" class="empty-cell">NO CLEANUP RECORDS</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination" v-if="currentData.total > currentData.page_size">
      <button
        class="page-btn"
        :disabled="currentData.page <= 1"
        @click="goPage(currentData.page - 1)"
      >&lt; PREV</button>
      <span class="page-info">
        PAGE {{ currentData.page }} / {{ totalPages }}
      </span>
      <button
        class="page-btn"
        :disabled="currentData.page >= totalPages"
        @click="goPage(currentData.page + 1)"
      >NEXT &gt;</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useOracleOpsStore, ORACLE_SERVER_CONFIG } from '@/stores/oracle_ops'

const store = useOracleOpsStore()

const activeTab = ref('backups')
const filterServer = ref('')
const filterStatus = ref('')
const currentPage = ref(1)

const isLoading = computed(() => store.backupsLoading || store.cleanupsLoading)

const currentData = computed(() => {
  return activeTab.value === 'backups' ? store.backups : store.cleanups
})

const totalPages = computed(() => {
  const d = currentData.value
  return Math.ceil(d.total / d.page_size) || 1
})

function getServerName(serverId) {
  return ORACLE_SERVER_CONFIG[serverId]?.shortName || serverId
}

function formatNumber(val) {
  if (val === null || val === undefined) return '-'
  return val.toLocaleString()
}

function formatSize(mb) {
  if (mb === null || mb === undefined) return '-'
  if (mb >= 1024) return (mb / 1024).toFixed(2) + ' GB'
  return mb.toFixed(2) + ' MB'
}

function formatDateTime(isoStr) {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hour = d.getHours().toString().padStart(2, '0')
  const min = d.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

function loadData() {
  currentPage.value = 1
  const params = {
    serverId: filterServer.value || undefined,
    status: filterStatus.value || undefined,
    page: currentPage.value,
  }

  if (activeTab.value === 'backups') {
    store.fetchBackups(params)
  } else {
    store.fetchCleanups(params)
  }
}

function goPage(page) {
  currentPage.value = page
  const params = {
    serverId: filterServer.value || undefined,
    status: filterStatus.value || undefined,
    page,
  }

  if (activeTab.value === 'backups') {
    store.fetchBackups(params)
  } else {
    store.fetchCleanups(params)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.ops-backups-container {
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
  .title-icon { color: $neon-cyan; font-size: 16px; }
  .title-text {
    font-family: $font-terminal;
    font-size: 15px;
    color: $neon-green;
    letter-spacing: 2px;
  }
}

.tab-switcher {
  display: flex;
  gap: 4px;
}

.tab-btn {
  background: none;
  border: 1px solid rgba($neon-green, 0.2);
  color: rgba($neon-green, 0.5);
  font-family: $font-mono;
  font-size: 11px;
  padding: 4px 14px;
  cursor: pointer;
  letter-spacing: 1px;
  transition: all 0.2s;

  &:hover { border-color: rgba($neon-green, 0.5); color: $neon-green; }
  &.active {
    background: rgba($neon-green, 0.1);
    border-color: $neon-green;
    color: $neon-green;
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

  option {
    background: #0a0a0a;
    color: $neon-green;
  }

  &:focus { border-color: $neon-green; }
}

.filter-info {
  margin-left: auto;
  font-family: $font-mono;
  font-size: 11px;
  color: $text-secondary;
  letter-spacing: 1px;

  .filter-count {
    color: $neon-green;
    font-weight: bold;
  }
}

// ============ Table ============
.table-card {
  background: $bg-card;
  border: 1px solid rgba($neon-green, 0.15);
  padding: 0;
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

  tr:hover td {
    background: rgba($neon-green, 0.03);
  }
}

.server-cell {
  color: $neon-cyan;
  font-weight: bold;
}

.type-badge {
  font-size: 9px;
  padding: 1px 6px;
  background: rgba($neon-cyan, 0.1);
  border: 1px solid rgba($neon-cyan, 0.3);
  color: $neon-cyan;
  letter-spacing: 1px;
}

.status-badge {
  font-size: 9px;
  padding: 2px 8px;
  letter-spacing: 1px;
  font-weight: bold;

  &.success {
    color: $neon-green;
    background: rgba($neon-green, 0.1);
    border: 1px solid rgba($neon-green, 0.3);
  }
  &.failed {
    color: $neon-red;
    background: rgba($neon-red, 0.1);
    border: 1px solid rgba($neon-red, 0.3);
  }
  &.running {
    color: $neon-cyan;
    background: rgba($neon-cyan, 0.1);
    border: 1px solid rgba($neon-cyan, 0.3);
  }
}

.number-cell {
  text-align: right;
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

  &:hover:not(:disabled) {
    background: rgba($neon-green, 0.1);
    border-color: $neon-green;
  }

  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
}

.page-info {
  font-family: $font-mono;
  font-size: 11px;
  color: $text-secondary;
  letter-spacing: 1px;
}
</style>
