import { ref, onMounted, onUnmounted } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import wsService from '@/utils/websocket'

export function useWebSocket() {
  const monitorStore = useMonitorStore()
  const isConnected = ref(false)
  const connectionError = ref(null)

  const unsubscribers = []

  function connect() {
    wsService.connect()
      .then(() => {
        isConnected.value = true
        monitorStore.wsConnected = true
        connectionError.value = null
        // Request initial system logs after connection
        setTimeout(() => {
          wsService.requestSystemLogs(50)
        }, 500)
      })
      .catch((error) => {
        isConnected.value = false
        monitorStore.wsConnected = false
        connectionError.value = error.message
      })
  }

  function disconnect() {
    wsService.disconnect()
    isConnected.value = false
    monitorStore.wsConnected = false
  }

  function setupListeners() {
    // 连接状态监听
    unsubscribers.push(
      wsService.on('connection', ({ status }) => {
        isConnected.value = status === 'connected'
        monitorStore.wsConnected = status === 'connected'
      })
    )

    // 服务器状态更新
    unsubscribers.push(
      wsService.on('serverStatus', (data) => {
        monitorStore.updateServerStatus(data.serverId, data.status)
      })
    )

    // 新告警
    unsubscribers.push(
      wsService.on('newAlert', (data) => {
        monitorStore.addAlert({
          level: data.level,
          message: data.message,
          source: data.source
        })
      })
    )

    // 服务器恢复事件
    unsubscribers.push(
      wsService.on('serverRecovered', (data) => {
        console.log('[WS] Server recovered:', data.serverId)
        monitorStore.handleServerRecovered(data.serverId, data.offlineDuration)
      })
    )

    // 服务器离线事件
    unsubscribers.push(
      wsService.on('serverOffline', (data) => {
        console.log('[WS] Server offline:', data.serverId)
        monitorStore.handleServerOffline(data.serverId)
      })
    )

    // 服务器状态更新（用于重连后的状态刷新）
    unsubscribers.push(
      wsService.on('serverStatusUpdate', (data) => {
        if (data.server) {
          monitorStore.updateFullServerStatus(data.server)
        }
      })
    )

    // 连接状态变化
    unsubscribers.push(
      wsService.on('connectionStateChange', (data) => {
        monitorStore.handleConnectionStateChange(data.serverId, data.newState, data.oldState)
      })
    )

    // 系统日志事件
    unsubscribers.push(
      wsService.on('systemLog', (data) => {
        if (data.log) {
          monitorStore.addSystemLog(data.log)
        }
      })
    )

    // 系统日志批量加载
    unsubscribers.push(
      wsService.on('systemLogsBatch', (data) => {
        if (data.logs) {
          monitorStore.setSystemLogs(data.logs)
        }
      })
    )
  }

  // 请求系统日志
  function requestSystemLogs(count = 50) {
    wsService.requestSystemLogs(count)
  }

  function cleanupListeners() {
    unsubscribers.forEach(unsub => unsub())
    unsubscribers.length = 0
  }

  onMounted(() => {
    setupListeners()
    connect()
  })

  onUnmounted(() => {
    cleanupListeners()
  })

  return {
    isConnected,
    connectionError,
    connect,
    disconnect,
    requestSystemLogs,
    wsService
  }
}
