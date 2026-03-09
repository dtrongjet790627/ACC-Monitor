import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:5004/api/oracle-ops'

// Oracle database server configuration
const ORACLE_SERVER_CONFIG = {
  '165': { name: 'Factory (165)', shortName: 'SHARED', ip: '172.17.10.165', edition: 'SE', limitGb: null },
  '164': { name: 'ECU Line1 (164)', shortName: 'DP EPP', ip: '172.17.10.164', edition: 'XE', limitGb: 11 },
  '153': { name: 'DP Assembly (153)', shortName: 'DP EPS', ip: '172.17.10.153', edition: 'XE', limitGb: 11 },
  '168': { name: 'ECU Line2 (168)', shortName: 'SMT Line2', ip: '172.17.10.168', edition: 'XE', limitGb: 11 },
  '193': { name: 'C-EPS (193)', shortName: 'C_EPS', ip: '172.17.10.193', edition: 'XE', limitGb: 11 },
  '194': { name: 'L-EPP (194)', shortName: 'L_EPP', ip: '172.17.10.194', edition: 'XE', limitGb: 11 },
}

export { ORACLE_SERVER_CONFIG }

export const useOracleOpsStore = defineStore('oracleOps', () => {
  // Loading states
  const overviewLoading = ref(false)
  const tablespacesLoading = ref(false)
  const trendsLoading = ref(false)
  const backupsLoading = ref(false)
  const cleanupsLoading = ref(false)
  const alertsLoading = ref(false)

  // Data
  const overview = ref([])
  const tablespaces = ref([])
  const trends = ref([])
  const backups = ref({ total: 0, page: 1, page_size: 20, records: [] })
  const cleanups = ref({ total: 0, page: 1, page_size: 20, records: [] })
  const alerts = ref({ total: 0, page: 1, page_size: 20, records: [] })

  // Computed
  const totalDatabases = computed(() => Object.keys(ORACLE_SERVER_CONFIG).length)
  const normalDatabases = computed(() => overview.value.filter(s => s.status === 'normal').length)
  const warningDatabases = computed(() => overview.value.filter(s => s.status === 'warning').length)
  const criticalDatabases = computed(() => overview.value.filter(s => s.status === 'critical').length)
  const unknownDatabases = computed(() => overview.value.filter(s => s.status === 'unknown').length)

  // ========================================
  // API calls
  // ========================================

  async function fetchOverview() {
    overviewLoading.value = true
    try {
      const response = await axios.get(`${API_BASE}/overview`, { timeout: 30000 })
      if (response.data && response.data.data) {
        overview.value = response.data.data
      }
    } catch (error) {
      console.error('[OracleOps] Failed to fetch overview:', error)
    } finally {
      overviewLoading.value = false
    }
  }

  async function fetchTablespaces(serverId = null) {
    tablespacesLoading.value = true
    try {
      const params = {}
      if (serverId) params.server_id = serverId
      const response = await axios.get(`${API_BASE}/tablespaces`, { params, timeout: 30000 })
      if (response.data && response.data.data) {
        tablespaces.value = response.data.data
      }
    } catch (error) {
      console.error('[OracleOps] Failed to fetch tablespaces:', error)
    } finally {
      tablespacesLoading.value = false
    }
  }

  async function fetchTrends(serverId = null, days = 7) {
    trendsLoading.value = true
    try {
      const params = { days }
      if (serverId) params.server_id = serverId
      const response = await axios.get(`${API_BASE}/tablespaces/trends`, { params, timeout: 30000 })
      if (response.data && response.data.data) {
        trends.value = response.data.data
      }
    } catch (error) {
      console.error('[OracleOps] Failed to fetch trends:', error)
    } finally {
      trendsLoading.value = false
    }
  }

  async function fetchBackups({ serverId, status, page = 1, pageSize = 20 } = {}) {
    backupsLoading.value = true
    try {
      const params = { page, page_size: pageSize }
      if (serverId) params.server_id = serverId
      if (status) params.status = status
      const response = await axios.get(`${API_BASE}/backups`, { params, timeout: 30000 })
      if (response.data && response.data.data) {
        backups.value = response.data.data
      }
    } catch (error) {
      console.error('[OracleOps] Failed to fetch backups:', error)
    } finally {
      backupsLoading.value = false
    }
  }

  async function fetchCleanups({ serverId, status, page = 1, pageSize = 20 } = {}) {
    cleanupsLoading.value = true
    try {
      const params = { page, page_size: pageSize }
      if (serverId) params.server_id = serverId
      if (status) params.status = status
      const response = await axios.get(`${API_BASE}/cleanups`, { params, timeout: 30000 })
      if (response.data && response.data.data) {
        cleanups.value = response.data.data
      }
    } catch (error) {
      console.error('[OracleOps] Failed to fetch cleanups:', error)
    } finally {
      cleanupsLoading.value = false
    }
  }

  async function fetchAlerts({ serverId, severity, page = 1, pageSize = 20 } = {}) {
    alertsLoading.value = true
    try {
      const params = { page, page_size: pageSize }
      if (serverId) params.server_id = serverId
      if (severity) params.severity = severity
      const response = await axios.get(`${API_BASE}/alerts`, { params, timeout: 30000 })
      if (response.data && response.data.data) {
        alerts.value = response.data.data
      }
    } catch (error) {
      console.error('[OracleOps] Failed to fetch alerts:', error)
    } finally {
      alertsLoading.value = false
    }
  }

  async function fetchConfig(serverId) {
    try {
      const response = await axios.get(`${API_BASE}/config/${serverId}`, { timeout: 15000 })
      if (response.data && response.data.data) {
        return response.data.data
      }
      return null
    } catch (error) {
      console.error('[OracleOps] Failed to fetch config:', error)
      return null
    }
  }

  async function pushConfig(serverId, configData) {
    try {
      const response = await axios.post(`${API_BASE}/config/${serverId}`, configData, { timeout: 15000 })
      return response.data
    } catch (error) {
      console.error('[OracleOps] Failed to push config:', error)
      return { code: 500, message: error.message }
    }
  }

  return {
    // Loading
    overviewLoading,
    tablespacesLoading,
    trendsLoading,
    backupsLoading,
    cleanupsLoading,
    alertsLoading,
    // Data
    overview,
    tablespaces,
    trends,
    backups,
    cleanups,
    alerts,
    // Computed
    totalDatabases,
    normalDatabases,
    warningDatabases,
    criticalDatabases,
    unknownDatabases,
    // Actions
    fetchOverview,
    fetchTablespaces,
    fetchTrends,
    fetchBackups,
    fetchCleanups,
    fetchAlerts,
    fetchConfig,
    pushConfig,
  }
})
