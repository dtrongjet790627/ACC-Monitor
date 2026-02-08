import { io } from 'socket.io-client'

class WebSocketService {
  constructor() {
    this.socket = null
    this.callbacks = new Map()
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000
  }

  connect(url = '/') {
    if (this.socket?.connected) {
      return Promise.resolve(this.socket)
    }

    return new Promise((resolve, reject) => {
      try {
        this.socket = io(url, {
          transports: ['websocket'],
          reconnection: true,
          reconnectionAttempts: this.maxReconnectAttempts,
          reconnectionDelay: this.reconnectDelay
        })

        this.socket.on('connect', () => {
          console.log('[WS] Connected to server')
          this.reconnectAttempts = 0
          this.emit('connection', { status: 'connected' })
          resolve(this.socket)
        })

        this.socket.on('disconnect', (reason) => {
          console.log('[WS] Disconnected:', reason)
          this.emit('connection', { status: 'disconnected', reason })
        })

        this.socket.on('connect_error', (error) => {
          console.error('[WS] Connection error:', error)
          this.emit('connection', { status: 'error', error })
          reject(error)
        })

        // 监控数据事件
        this.socket.on('server:status', (data) => {
          this.emit('serverStatus', data)
        })

        this.socket.on('alert:new', (data) => {
          this.emit('newAlert', data)
        })

        this.socket.on('process:status', (data) => {
          this.emit('processStatus', data)
        })

        this.socket.on('database:status', (data) => {
          this.emit('databaseStatus', data)
        })

        this.socket.on('log:new', (data) => {
          this.emit('newLog', data)
        })

        // Server recovery events
        this.socket.on('server_recovered', (data) => {
          console.log('[WS] Server recovered:', data.server_id)
          this.emit('serverRecovered', data)
        })

        this.socket.on('server_offline', (data) => {
          console.log('[WS] Server offline:', data.server_id)
          this.emit('serverOffline', data)
        })

        this.socket.on('connection_state_change', (data) => {
          console.log('[WS] Connection state change:', data.server_id, data.new_state)
          this.emit('connectionStateChange', data)
        })

        // All servers status update (full refresh)
        this.socket.on('all_servers_status', (data) => {
          this.emit('allServersStatus', data)
        })

        // Server status update (for reconnection broadcasts)
        this.socket.on('server_status_update', (data) => {
          this.emit('serverStatusUpdate', data)
        })

      } catch (error) {
        console.error('[WS] Failed to create socket:', error)
        reject(error)
      }
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  // 订阅事件
  on(event, callback) {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, [])
    }
    this.callbacks.get(event).push(callback)

    // 返回取消订阅函数
    return () => this.off(event, callback)
  }

  // 取消订阅
  off(event, callback) {
    const callbacks = this.callbacks.get(event)
    if (callbacks) {
      const index = callbacks.indexOf(callback)
      if (index > -1) {
        callbacks.splice(index, 1)
      }
    }
  }

  // 触发事件
  emit(event, data) {
    const callbacks = this.callbacks.get(event)
    if (callbacks) {
      callbacks.forEach(callback => callback(data))
    }
  }

  // 发送消息到服务器
  send(event, data) {
    if (this.socket?.connected) {
      this.socket.emit(event, data)
    } else {
      console.warn('[WS] Socket not connected, message not sent')
    }
  }

  // 请求服务器状态
  requestServerStatus(serverId) {
    this.send('server:get', { serverId })
  }

  // 请求重启进程
  requestProcessRestart(serverId, processName) {
    this.send('process:restart', { serverId, processName })
  }

  // 确认告警
  acknowledgeAlert(alertId) {
    this.send('alert:ack', { alertId })
  }

  // 获取连接状态
  get isConnected() {
    return this.socket?.connected || false
  }
}

// 单例导出
export const wsService = new WebSocketService()
export default wsService
