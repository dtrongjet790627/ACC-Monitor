<template>
  <div class="logs-page">
    <div class="page-header">
      <h1>// LOG VIEWER</h1>
      <router-link to="/" class="cyber-btn cyber-btn--ghost">
        BACK TO DASHBOARD
      </router-link>
    </div>

    <!-- 搜索过滤栏 -->
    <div class="search-bar">
      <div class="search-row">
        <input
          v-model="searchKeyword"
          type="text"
          class="cyber-input"
          placeholder="Search keywords..."
        />
        <select v-model="selectedServer" class="cyber-input">
          <option value="">All Servers</option>
          <option v-for="server in monitorStore.servers" :key="server.id" :value="server.id">
            {{ server.name }} - {{ server.ip }}
          </option>
        </select>
        <select v-model="selectedLevel" class="cyber-input">
          <option value="">All Levels</option>
          <option value="error">ERROR</option>
          <option value="warning">WARNING</option>
          <option value="info">INFO</option>
        </select>
        <button class="cyber-btn" @click="searchLogs">
          SEARCH
        </button>
      </div>
    </div>

    <!-- 日志列表 -->
    <div class="logs-container">
      <div class="logs-header">
        <span class="log-count">Showing {{ filteredLogs.length }} entries</span>
        <button class="cyber-btn cyber-btn--ghost" @click="exportLogs">
          EXPORT
        </button>
      </div>

      <div class="logs-content">
        <div
          v-for="(log, index) in filteredLogs"
          :key="index"
          class="log-entry"
          :class="log.level"
        >
          <span class="log-time">{{ log.timestamp }}</span>
          <span class="log-level" :class="log.level">
            [{{ log.level.toUpperCase() }}]
          </span>
          <span class="log-server">[{{ log.server }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>

        <div v-if="filteredLogs.length === 0" class="no-logs">
          <div class="empty-icon">[...]</div>
          <p>No logs found matching your criteria</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMonitorStore } from '@/stores/monitor'

const monitorStore = useMonitorStore()

const searchKeyword = ref('')
const selectedServer = ref('')
const selectedLevel = ref('')

// 模拟日志数据
const mockLogs = ref([
  { timestamp: '2026-01-29 13:42:15', level: 'error', server: 'SHARED', message: 'MES Client service stopped unexpectedly - Connection timeout after 30000ms' },
  { timestamp: '2026-01-29 13:41:58', level: 'error', server: 'SHARED', message: 'Data Sync service connection timeout - Remote host not responding' },
  { timestamp: '2026-01-29 13:40:22', level: 'warning', server: 'DP_EPS', message: 'MES Client response time exceeded threshold: 2156ms > 2000ms' },
  { timestamp: '2026-01-29 13:38:45', level: 'error', server: 'SHARED', message: 'Tablespace ACC_DATA usage critical: 92% used (9421MB/10240MB)' },
  { timestamp: '2026-01-29 13:35:11', level: 'warning', server: 'DP_EPS', message: 'Tablespace usage high: 78% used - Consider expanding or archiving' },
  { timestamp: '2026-01-29 13:32:08', level: 'info', server: 'DKEX', message: 'Scheduled backup completed successfully - 15.2GB archived' },
  { timestamp: '2026-01-29 13:28:44', level: 'info', server: 'DKYX', message: 'Oracle listener restarted - All connections restored' },
  { timestamp: '2026-01-29 13:25:19', level: 'warning', server: 'SHARED', message: 'Memory usage above 80%: 89% current utilization' },
  { timestamp: '2026-01-29 13:22:33', level: 'info', server: 'EAI', message: 'API Gateway health check passed - All endpoints responding' },
  { timestamp: '2026-01-29 13:18:57', level: 'info', server: 'C_EPS', message: 'Data sync completed: 15,847 records synchronized in 45s' },
  { timestamp: '2026-01-29 13:15:42', level: 'info', server: 'L_EPP', message: 'Scheduled maintenance window started - Non-critical alerts suppressed' },
  { timestamp: '2026-01-29 13:12:28', level: 'warning', server: 'SHARED', message: 'CPU usage spike detected: 95% - Process ACC.Server consuming 82%' },
  { timestamp: '2026-01-29 13:10:15', level: 'info', server: 'DKYX', message: 'ACC.Server process started successfully - PID 4521' },
  { timestamp: '2026-01-29 13:08:30', level: 'error', server: 'DKYX', message: 'ACC.Server process crashed - Exit code: -1073741819 (ACCESS_VIOLATION)' },
  { timestamp: '2026-01-29 13:05:22', level: 'info', server: 'EAI', message: 'Redis cache flushed - 2.4GB memory freed' }
])

const filteredLogs = computed(() => {
  return mockLogs.value.filter(log => {
    const matchKeyword = !searchKeyword.value ||
      log.message.toLowerCase().includes(searchKeyword.value.toLowerCase())
    const matchServer = !selectedServer.value ||
      log.server === monitorStore.getServerById(selectedServer.value)?.name
    const matchLevel = !selectedLevel.value || log.level === selectedLevel.value
    return matchKeyword && matchServer && matchLevel
  })
})

function searchLogs() {
  console.log('Searching logs...')
}

function exportLogs() {
  console.log('Exporting logs...')
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.logs-page {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: $bg-card;
  border: 1px solid rgba($neon-cyan, 0.2);

  h1 {
    font-size: 24px;
    color: $neon-cyan;
    text-transform: uppercase;
    letter-spacing: 4px;
    text-shadow: 0 0 20px rgba($neon-cyan, 0.5);
  }
}

.search-bar {
  background: $bg-card;
  border: 1px solid rgba($neon-cyan, 0.2);
  padding: 20px;
  margin-bottom: 20px;

  .search-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr auto;
    gap: 15px;
    align-items: center;
  }
}

select.cyber-input {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2300fff2' d='M6 8L2 4h8z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 35px;
}

.logs-container {
  background: $bg-card;
  border: 1px solid rgba($neon-cyan, 0.2);
  overflow: hidden;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: rgba($neon-cyan, 0.05);
  border-bottom: 1px solid rgba($neon-cyan, 0.2);

  .log-count {
    font-size: 13px;
    color: $text-secondary;
  }
}

.logs-content {
  max-height: 600px;
  overflow-y: auto;
  font-family: $font-mono;
  font-size: 13px;
  line-height: 1.6;
}

.log-entry {
  padding: 10px 20px;
  border-bottom: 1px solid rgba($neon-cyan, 0.05);
  display: flex;
  gap: 15px;
  transition: background 0.2s ease;

  &:hover {
    background: rgba($neon-cyan, 0.03);
  }

  &.error {
    border-left: 3px solid $neon-red;
  }

  &.warning {
    border-left: 3px solid $neon-orange;
  }

  &.info {
    border-left: 3px solid $neon-blue;
  }
}

.log-time {
  color: $text-secondary;
  white-space: nowrap;
  min-width: 150px;
}

.log-level {
  font-weight: bold;
  white-space: nowrap;
  min-width: 80px;

  &.error { color: $neon-red; }
  &.warning { color: $neon-orange; }
  &.info { color: $neon-blue; }
}

.log-server {
  color: $neon-purple;
  white-space: nowrap;
  min-width: 80px;
}

.log-message {
  color: $text-primary;
  flex: 1;
}

.no-logs {
  text-align: center;
  padding: 60px 20px;

  .empty-icon {
    font-size: 48px;
    color: $text-secondary;
    margin-bottom: 15px;
  }

  p {
    color: $text-secondary;
  }
}

@media (max-width: 768px) {
  .search-row {
    grid-template-columns: 1fr !important;
  }

  .log-entry {
    flex-wrap: wrap;
  }
}
</style>
