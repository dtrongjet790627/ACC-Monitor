import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:5002/api'

// 服务器配置（与后端settings.py保持一致）
// 排序顺序: 153、164、168、193、194、160、163、165
const SERVER_CONFIG = {
  '153': { name: 'DP_EPS', fullName: 'DP EPS Production', ip: '172.17.10.153', serverType: 'production', sortOrder: 1 },
  '164': { name: 'DP EPP', fullName: 'DP EPP Production', ip: '172.17.10.164', serverType: 'production', sortOrder: 2 },
  '168': { name: 'SMT Line2', fullName: 'SMT Line2 Production', ip: '172.17.10.168', serverType: 'production', sortOrder: 3 },
  '193': { name: 'C_EPS', fullName: 'C EPS Production', ip: '172.17.10.193', serverType: 'production', sortOrder: 4 },
  '194': { name: 'L_EPP', fullName: 'L EPP Production', ip: '172.17.10.194', serverType: 'production', sortOrder: 5 },
  '160': { name: 'iPlant', fullName: 'iPlant Server', ip: '172.17.10.160', serverType: 'production', sortOrder: 6 },
  '163': { name: 'EAI', fullName: 'EAI Server', ip: '172.17.10.163', serverType: 'docker', sortOrder: 7 },
  '165': { name: 'SHARED', fullName: 'Common Services', ip: '172.17.10.165', serverType: 'shared', sortOrder: 8 }
}

// 根据配置生成初始服务器列表（显示失联状态）
function createInitialServers() {
  return Object.entries(SERVER_CONFIG)
    .map(([id, config]) => ({
      id,
      name: config.name,
      fullName: config.fullName,
      ip: config.ip,
      status: 'offline',  // 初始状态为失联
      serverType: config.serverType,
      processes: [],
      tablespaceUsage: 0,
      cpuUsage: 0,
      memoryUsage: 0,
      sortOrder: config.sortOrder
    }))
    .sort((a, b) => a.sortOrder - b.sortOrder)
}

export const useMonitorStore = defineStore('monitor', () => {
  // 加载状态
  const loading = ref(false)
  const lastUpdate = ref(null)

  // 服务器列表 - 初始化为配置的服务器列表，状态为失联
  const servers = ref(createInitialServers())

  // 告警列表 - 初始为空，从API获取
  const alerts = ref([])

  // WebSocket连接状态
  const wsConnected = ref(false)

  // 计算属性
  const totalServers = computed(() => servers.value.length)
  const onlineServers = computed(() => servers.value.filter(s => s.status === 'normal').length)
  const warningServers = computed(() => servers.value.filter(s => s.status === 'warning').length)
  const criticalServers = computed(() => servers.value.filter(s => s.status === 'error').length)
  const offlineServers = computed(() => servers.value.filter(s => s.status === 'offline').length)
  const alertCount = computed(() => alerts.value.length)

  // 更新服务器状态
  function updateServerStatus(serverId, newStatus) {
    const server = servers.value.find(s => s.id === serverId)
    if (server) {
      server.status = newStatus
    }
  }

  // 更新服务器完整状态（用于重连后的状态刷新）
  function updateFullServerStatus(serverData) {
    const index = servers.value.findIndex(s => s.id === serverData.id)
    if (index !== -1) {
      const config = SERVER_CONFIG[serverData.id] || {}
      servers.value[index] = {
        id: serverData.id,
        name: serverData.name_cn || serverData.name,
        fullName: serverData.name,
        ip: serverData.ip,
        status: serverData.status,
        serverType: serverData.os_type === 'linux' ? 'docker' : 'production',
        processes: (serverData.processes || []).map(p => ({
          name: p.name,
          status: p.status,
          pid: p.pid,
          memory: p.memory,
          type: p.type || 'process',
          dataSource: p.data_source
        })),
        tablespaceUsage: serverData.disk_usage || 0,
        cpuUsage: serverData.cpu_usage || 0,
        memoryUsage: serverData.memory_usage || 0,
        dataSource: serverData.data_source,
        connectionInfo: serverData.connection_info,
        sortOrder: config.sortOrder || 99
      }
      console.log(`[Store] Updated full status for server ${serverData.id}:`, serverData.status)
    }
  }

  // 处理服务器恢复事件
  function handleServerRecovered(serverId, offlineDuration) {
    console.log(`[Store] Server ${serverId} recovered after ${offlineDuration}s`)
    // 添加恢复告警
    addAlert({
      level: 'info',
      message: `Server ${serverId} connection recovered (was offline for ${Math.round(offlineDuration)}s)`,
      source: 'connection'
    })
    // 触发立即刷新该服务器状态
    fetchServers()
  }

  // 处理服务器离线事件
  function handleServerOffline(serverId) {
    console.log(`[Store] Server ${serverId} went offline`)
    const server = servers.value.find(s => s.id === serverId)
    if (server) {
      server.status = 'offline'
    }
    // 添加离线告警
    addAlert({
      level: 'warning',
      message: `Server ${serverId} connection lost`,
      source: 'connection'
    })
  }

  // 处理连接状态变化
  function handleConnectionStateChange(serverId, newState, oldState) {
    console.log(`[Store] Server ${serverId} state changed: ${oldState} -> ${newState}`)
    const server = servers.value.find(s => s.id === serverId)
    if (server && newState) {
      // Map connection state to server status if needed
      if (newState === 'recovered') {
        // Will be updated by full status refresh
        fetchServers()
      }
    }
  }

  // 添加告警
  function addAlert(alert) {
    alerts.value.unshift({
      id: Date.now(),
      time: new Date().toTimeString().split(' ')[0],
      ...alert
    })
    if (alerts.value.length > 50) {
      alerts.value.pop()
    }
  }

  // 获取服务器详情
  function getServerById(id) {
    return servers.value.find(s => s.id === id)
  }

  // 从API获取服务器数据
  async function fetchServers() {
    loading.value = true
    try {
      const response = await axios.get(`${API_BASE}/servers`, { timeout: 60000 })
      if (response.data && response.data.data) {
        // 转换API数据格式，保持配置的排序顺序
        const apiServers = response.data.data.map(server => {
          const config = SERVER_CONFIG[server.id] || {}
          return {
            id: server.id,
            name: server.name_cn || server.name,
            fullName: server.name,
            ip: server.ip,
            status: server.status,  // 保持后端返回的状态（normal/warning/error/offline）
            serverType: server.os_type === 'linux' ? 'docker' : 'production',
            processes: (server.processes || []).map(p => ({
              name: p.name,
              status: p.status,
              pid: p.pid,
              memory: p.memory,
              type: p.type || 'process',
              dataSource: p.data_source
            })),
            tablespaceUsage: server.disk_usage || 0,
            cpuUsage: server.cpu_usage || 0,
            memoryUsage: server.memory_usage || 0,
            dataSource: server.data_source,
            sortOrder: config.sortOrder || 99
          }
        })
        // 按sortOrder排序
        servers.value = apiServers.sort((a, b) => a.sortOrder - b.sortOrder)
        lastUpdate.value = new Date().toISOString()
      }
    } catch (error) {
      console.error('Failed to fetch servers:', error)
      // 请求失败时保持当前服务器列表，状态为offline
    } finally {
      loading.value = false
    }
  }

  // 定时刷新ID
  let refreshIntervalId = null

  // 启动定时刷新
  function startAutoRefresh(interval = 30000) {
    // 防止重复启动
    if (refreshIntervalId) {
      clearInterval(refreshIntervalId)
    }
    fetchServers()  // 立即获取一次
    refreshIntervalId = setInterval(fetchServers, interval)  // 每30秒刷新
  }

  // 停止定时刷新
  function stopAutoRefresh() {
    if (refreshIntervalId) {
      clearInterval(refreshIntervalId)
      refreshIntervalId = null
    }
  }

  return {
    servers,
    alerts,
    wsConnected,
    loading,
    lastUpdate,
    totalServers,
    onlineServers,
    warningServers,
    criticalServers,
    offlineServers,
    alertCount,
    updateServerStatus,
    updateFullServerStatus,
    handleServerRecovered,
    handleServerOffline,
    handleConnectionStateChange,
    addAlert,
    getServerById,
    fetchServers,
    startAutoRefresh,
    stopAutoRefresh
  }
})
