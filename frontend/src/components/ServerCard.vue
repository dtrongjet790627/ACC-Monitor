<template>
  <div
    class="server-card"
    :class="[`status-${server.status}`]"
    @click="handleClick"
    ref="cardRef"
  >
    <!-- 霓虹边框发光效果 -->
    <div class="neon-border"></div>

    <!-- 电路板纹理背景 -->
    <div class="circuit-bg"></div>

    <!-- 扫描线效果 -->
    <div class="card-scanline"></div>

    <!-- 边角装饰 - 终端风格 -->
    <div class="corner corner-tl"></div>
    <div class="corner corner-tr"></div>
    <div class="corner corner-bl"></div>
    <div class="corner corner-br"></div>

    <!-- 状态指示条 -->
    <div class="status-bar">
      <div class="status-glow"></div>
    </div>

    <!-- 服务器头部信息 -->
    <div class="server-header">
      <div class="server-info">
        <!-- 终端装饰前缀 -->
        <div class="terminal-line">
          <span class="prefix">$</span>
          <span class="command">./server</span>
        </div>
        <h3 class="glitch-title" :data-text="server.name + ' // ' + server.fullName">
          {{ server.name }} // {{ server.fullName }}
        </h3>
        <div class="ip">
          <span class="ip-label">>> IP:</span>
          <span class="ip-value">{{ server.ip }}</span>
        </div>
      </div>
      <div class="server-status" :class="server.status">
        <div class="status-core"></div>
        <div class="status-ring"></div>
        <span>{{ statusText }}</span>
      </div>
    </div>

    <!-- 进程服务列表 -->
    <div class="services-section">
      <h4>
        <span class="section-prefix">[SERVICES]</span>
        <span class="section-line"></span>
      </h4>
      <div class="services-list">
        <div
          v-for="(process, index) in server.processes"
          :key="index"
          class="service-item"
        >
          <!-- Alert indicator icon -->
          <div
            v-if="process.has_alert"
            class="alert-indicator"
            @mouseenter="showTooltip($event, process)"
            @mouseleave="hideTooltip"
          >
            <span class="alert-icon"></span>
            <div class="alert-pulse"></div>
          </div>
          <span class="service-prefix">>></span>
          <div class="service-icon" :class="process.status"></div>
          <span class="service-name">{{ process.name }}</span>
          <span class="service-status" :class="process.status">
            {{ processStatusText(process.status) }}
          </span>
        </div>
      </div>
    </div>

    <!-- CPU使用率进度条 -->
    <div class="cpu-section">
      <h4>
        <span class="section-prefix">[CPU]</span>
        <span class="section-line"></span>
      </h4>
      <div class="cpu-bar">
        <div
          class="cpu-fill"
          :class="getCpuBarClass"
          :style="{ width: (server.cpuUsage || 0) + '%' }"
        >
          <div class="fill-shine"></div>
          <div class="fill-flow"></div>
        </div>
        <span class="cpu-text" :class="{ 'value-updating': cpuAnimating }">{{ server.cpuUsage || 0 }}%</span>
        <div class="bar-markers">
          <span class="marker" style="left: 50%"></span>
          <span class="marker" style="left: 70%"></span>
          <span class="marker" style="left: 90%"></span>
        </div>
      </div>
    </div>

    <!-- Docker服务器显示容器状态提示 -->
    <div v-if="server.serverType === 'docker'" class="docker-section">
      <h4>
        <span class="section-prefix">[DOCKER]</span>
        <span class="section-line"></span>
      </h4>
      <div class="docker-info">
        <span class="docker-badge">
          <span class="badge-icon"></span>
          $ docker ps
        </span>
        <span class="container-count">
          <span class="count-value">{{ server.processes.length }}</span>
          containers
        </span>
      </div>
    </div>

    <!-- 底部数据面板 - 增强动效 -->
    <div class="data-panel">
      <div class="data-item">
        <span class="data-label">$ DISK</span>
        <span class="data-value" :class="[getDiskClass, { 'value-updating': diskAnimating }]">{{ server.tablespaceUsage || 0 }}%</span>
        <div class="data-bar">
          <div class="data-bar-fill" :class="getDiskClass" :style="{ width: (server.tablespaceUsage || 0) + '%' }">
            <div class="bar-flow"></div>
          </div>
        </div>
      </div>
      <div class="data-item">
        <span class="data-label">$ MEM</span>
        <span class="data-value" :class="[getMemClass, { 'value-updating': memAnimating }]">{{ server.memoryUsage || 0 }}%</span>
        <div class="data-bar">
          <div class="data-bar-fill" :class="getMemClass" :style="{ width: (server.memoryUsage || 0) + '%' }">
            <div class="bar-flow"></div>
          </div>
        </div>
      </div>
      <div class="data-item">
        <span class="data-label">$ PING</span>
        <span class="data-value" :class="[getPingClass, { 'value-updating': pingAnimating }]">{{ server.ping || 0 }}ms</span>
        <div class="ping-indicator" :class="getPingClass">
          <span class="ping-dot"></span>
          <span class="ping-dot"></span>
          <span class="ping-dot"></span>
        </div>
      </div>
    </div>

    <!-- Alert Tooltip (teleported to body) -->
    <Teleport to="body">
      <div
        v-if="tooltipVisible"
        class="alert-tooltip"
        :style="tooltipStyle"
      >
        <div class="tooltip-header">
          <span class="tooltip-title">[ALERT] {{ tooltipData?.name }}</span>
          <span class="tooltip-close" @click="hideTooltip">X</span>
        </div>
        <div class="tooltip-content">
          <!-- Restart Info -->
          <div v-if="tooltipData?.alert_info?.restart_info" class="tooltip-section">
            <div class="section-label">> RESTART STATUS</div>
            <div class="restart-status" :class="tooltipData.alert_info.restart_info.success ? 'success' : 'failed'">
              <span class="status-icon"></span>
              <span>{{ tooltipData.alert_info.restart_info.success ? '$ OK' : '$ FAILED' }}</span>
            </div>
            <div class="restart-time">
              {{ formatTime(tooltipData.alert_info.restart_info.last_restart) }}
            </div>
            <div v-if="tooltipData.alert_info.restart_info.message" class="restart-message">
              {{ tooltipData.alert_info.restart_info.message }}
            </div>
          </div>

          <!-- Error Logs -->
          <div v-if="tooltipData?.alert_info?.errors?.length" class="tooltip-section">
            <div class="section-label">> ERRORS ({{ tooltipData.alert_info.errors.length }})</div>
            <div class="error-list">
              <div
                v-for="(error, idx) in tooltipData.alert_info.errors.slice(0, 3)"
                :key="idx"
                class="error-item"
                :class="error.level"
              >
                <span class="error-level">{{ error.level.toUpperCase() }}</span>
                <span class="error-time">{{ error.timestamp }}</span>
                <div class="error-message">{{ truncateMessage(error.message) }}</div>
              </div>
            </div>
          </div>

          <!-- No alerts -->
          <div v-if="!tooltipData?.alert_info?.restart_info && !tooltipData?.alert_info?.errors?.length" class="no-alerts">
            // No alert details available
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref, reactive, watch, onMounted } from 'vue'

const props = defineProps({
  server: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

const cardRef = ref(null)

// Data animation states
const cpuAnimating = ref(false)
const diskAnimating = ref(false)
const memAnimating = ref(false)
const pingAnimating = ref(false)

// Previous values for change detection
let prevCpu = null
let prevDisk = null
let prevMem = null
let prevPing = null

// Watch for data changes to trigger animations
watch(() => props.server.cpuUsage, (newVal) => {
  if (prevCpu !== null && prevCpu !== newVal) {
    cpuAnimating.value = true
    setTimeout(() => { cpuAnimating.value = false }, 400)
  }
  prevCpu = newVal
})

watch(() => props.server.tablespaceUsage, (newVal) => {
  if (prevDisk !== null && prevDisk !== newVal) {
    diskAnimating.value = true
    setTimeout(() => { diskAnimating.value = false }, 400)
  }
  prevDisk = newVal
})

watch(() => props.server.memoryUsage, (newVal) => {
  if (prevMem !== null && prevMem !== newVal) {
    memAnimating.value = true
    setTimeout(() => { memAnimating.value = false }, 400)
  }
  prevMem = newVal
})

watch(() => props.server.ping, (newVal) => {
  if (prevPing !== null && prevPing !== newVal) {
    pingAnimating.value = true
    setTimeout(() => { pingAnimating.value = false }, 400)
  }
  prevPing = newVal
})

onMounted(() => {
  prevCpu = props.server.cpuUsage
  prevDisk = props.server.tablespaceUsage
  prevMem = props.server.memoryUsage
  prevPing = props.server.ping
})

// Tooltip state
const tooltipVisible = ref(false)
const tooltipData = ref(null)
const tooltipStyle = reactive({
  top: '0px',
  left: '0px'
})

const statusText = computed(() => {
  const statusMap = {
    normal: '$ ONLINE',
    warning: '$ WARNING',
    error: '$ CRITICAL',
    offline: '$ OFFLINE'
  }
  return statusMap[props.server.status] || '$ UNKNOWN'
})

const getCpuBarClass = computed(() => {
  const cpu = props.server.cpuUsage || 0
  if (cpu >= 90) return 'critical'
  if (cpu >= 70) return 'high'
  if (cpu >= 50) return 'medium'
  return 'low'
})

const getDiskClass = computed(() => {
  const disk = props.server.tablespaceUsage || 0
  if (disk >= 90) return 'critical'
  if (disk >= 70) return 'high'
  return 'normal'
})

const getMemClass = computed(() => {
  const mem = props.server.memoryUsage || 0
  if (mem >= 90) return 'critical'
  if (mem >= 70) return 'high'
  return 'normal'
})

const getPingClass = computed(() => {
  const ping = props.server.ping || 0
  if (ping >= 100) return 'critical'
  if (ping >= 50) return 'high'
  return 'normal'
})

function processStatusText(status) {
  const statusMap = {
    running: 'RUN',
    stopped: 'DOWN',
    slow: 'SLOW',
    warning: 'WARN'
  }
  return statusMap[status] || status.toUpperCase()
}

function handleClick() {
  emit('click', props.server)
}

// Tooltip functions
function showTooltip(event, process) {
  const rect = event.target.getBoundingClientRect()
  tooltipStyle.top = `${rect.bottom + 8}px`
  tooltipStyle.left = `${rect.left - 100}px`

  if (tooltipStyle.left < 10) {
    tooltipStyle.left = '10px'
  }

  tooltipData.value = process
  tooltipVisible.value = true
}

function hideTooltip() {
  tooltipVisible.value = false
  tooltipData.value = null
}

function formatTime(isoString) {
  if (!isoString) return 'Unknown'
  try {
    const date = new Date(isoString)
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return isoString
  }
}

function truncateMessage(message) {
  if (!message) return ''
  return message.length > 100 ? message.substring(0, 100) + '...' : message
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.server-card {
  // 深黑背景
  background: $bg-card;
  // 荧光绿霓虹边框（设计文档要求）
  border: 2px solid rgba($neon-green, 0.4);
  padding: 20px;
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease;
  // 霓虹发光效果
  box-shadow: 0 0 20px rgba($neon-green, 0.15), inset 0 0 40px rgba(0, 0, 0, 0.5);
  cursor: pointer;
  will-change: transform;

  // 统一卡片高度
  min-height: $card-total-min-height;
  display: flex;
  flex-direction: column;

  // 霓虹边框外层
  .neon-border {
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    border: 2px solid transparent;
    pointer-events: none;
    z-index: 0;
  }

  // 电路板纹理背景
  .circuit-bg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0.03;
    background-image:
      linear-gradient(90deg, transparent 48%, rgba($neon-green, 0.5) 48%, rgba($neon-green, 0.5) 52%, transparent 52%),
      linear-gradient(0deg, transparent 48%, rgba($neon-green, 0.4) 48%, rgba($neon-green, 0.4) 52%, transparent 52%);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 1;
  }

  // 扫描线效果
  .card-scanline {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, transparent, rgba($neon-green, 0.8), transparent);
    transform: translateX(-100%);
    animation: cardScan 4s linear infinite;
    pointer-events: none;
    z-index: 2;
  }

  @keyframes cardScan {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  // 边角装饰
  .corner {
    position: absolute;
    width: 16px;
    height: 16px;
    z-index: 20;

    &::before, &::after {
      content: '';
      position: absolute;
      background: $neon-green;
      transition: all 0.3s ease;
    }

    &-tl {
      top: 0;
      left: 0;
      &::before { width: 16px; height: 2px; top: 0; left: 0; }
      &::after { width: 2px; height: 16px; top: 0; left: 0; }
    }

    &-tr {
      top: 0;
      right: 0;
      &::before { width: 16px; height: 2px; top: 0; right: 0; }
      &::after { width: 2px; height: 16px; top: 0; right: 0; }
    }

    &-bl {
      bottom: 0;
      left: 0;
      &::before { width: 16px; height: 2px; bottom: 0; left: 0; }
      &::after { width: 2px; height: 16px; bottom: 0; left: 0; }
    }

    &-br {
      bottom: 0;
      right: 0;
      &::before { width: 16px; height: 2px; bottom: 0; right: 0; }
      &::after { width: 2px; height: 16px; bottom: 0; right: 0; }
    }
  }

  // 状态指示条
  .status-bar {
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    overflow: hidden;

    .status-glow {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      animation: statusPulse 2s ease-in-out infinite;
    }
  }

  @keyframes statusPulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 1; }
  }

  // 状态样式
  &.status-normal {
    .status-bar .status-glow {
      background: $neon-green;
      box-shadow: 0 0 10px $neon-green;
    }
    .corner::before, .corner::after {
      background: $neon-green;
      box-shadow: 0 0 5px $neon-green;
    }
  }

  &.status-warning {
    border-color: rgba($neon-orange, 0.4);
    .status-bar .status-glow {
      background: $neon-orange;
      box-shadow: 0 0 10px $neon-orange;
    }
    .corner::before, .corner::after {
      background: $neon-orange;
      box-shadow: 0 0 5px $neon-orange;
    }
    animation: warningPulse 2s ease-in-out infinite;
  }

  &.status-error {
    border-color: rgba($neon-red, 0.5);
    .status-bar .status-glow {
      background: $neon-red;
      box-shadow: 0 0 10px $neon-red;
    }
    .corner::before, .corner::after {
      background: $neon-red;
      box-shadow: 0 0 5px $neon-red;
    }
    animation: errorPulse 1.5s ease-in-out infinite;
  }

  &.status-offline {
    border-color: rgba($text-secondary, 0.3);
    opacity: 0.6;
    .status-bar .status-glow {
      background: $text-secondary;
      animation: none;
      opacity: 0.3;
    }
    .corner::before, .corner::after {
      background: $text-secondary;
      opacity: 0.4;
    }
    .card-scanline {
      display: none;
    }
  }

  // Hover效果 - Glitch抖动
  &:hover {
    border-color: rgba($neon-green, 0.7);
    box-shadow: 0 0 30px rgba($neon-green, 0.3), inset 0 0 40px rgba(0, 0, 0, 0.5);
    transform: translateY(-5px);
    animation: hoverGlitch 0.3s ease-in-out;

    .corner::before, .corner::after {
      box-shadow: 0 0 10px $neon-green;
    }

    .card-scanline {
      animation-duration: 2s;
    }
  }

  @keyframes hoverGlitch {
    0%, 100% { transform: translateY(-5px) translateX(0); }
    25% { transform: translateY(-5px) translateX(-1px); }
    50% { transform: translateY(-5px) translateX(1px); }
    75% { transform: translateY(-5px) translateX(-1px); }
  }
}

@keyframes warningPulse {
  0%, 100% { box-shadow: 0 0 20px rgba($neon-orange, 0.15); }
  50% { box-shadow: 0 0 35px rgba($neon-orange, 0.3); }
}

@keyframes errorPulse {
  0%, 100% { box-shadow: 0 0 20px rgba($neon-red, 0.2); }
  50% { box-shadow: 0 0 40px rgba($neon-red, 0.4); }
}

// 服务器头部
.server-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  min-height: $card-header-height;
  height: auto; // 改为自动高度避免内容被截断
  margin-bottom: 16px;
  padding-bottom: 16px; // 增加底部间距
  border-bottom: 1px solid rgba($neon-green, 0.2);
  position: relative;
  z-index: 5;
  flex-shrink: 0;

  &::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 60px;
    height: 2px;
    background: $neon-green;
  }
}

.server-info {
  flex: 1;
  min-width: 0; // 防止flex子项溢出

  .terminal-line {
    font-size: 10px;
    margin-bottom: 6px;
    font-family: $font-mono;

    .prefix {
      color: $neon-green;
      margin-right: 4px;
    }

    .command {
      color: $text-secondary;
    }
  }

  h3, .glitch-title {
    font-size: 14px;
    font-weight: 400;
    color: $neon-green;
    margin-bottom: 10px; // 增加标题与IP的间距
    text-transform: uppercase;
    letter-spacing: 2px;
    text-shadow: 0 0 10px rgba($neon-green, 0.5);
    font-family: $font-terminal;
    position: relative;
    word-break: break-word; // 防止长名称溢出

    &::before, &::after {
      content: attr(data-text);
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      opacity: 0;
    }

    &::before {
      color: $neon-red;
      animation: titleGlitch1 8s ease-in-out infinite;
      clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
    }

    &::after {
      color: $neon-cyan;
      animation: titleGlitch2 8s ease-in-out infinite;
      clip-path: polygon(0 65%, 100% 65%, 100% 100%, 0 100%);
    }
  }

  @keyframes titleGlitch1 {
    0%, 94%, 100% { opacity: 0; transform: translateX(0); }
    95% { opacity: 0.6; transform: translateX(-2px); }
    97% { opacity: 0.4; transform: translateX(2px); }
  }

  @keyframes titleGlitch2 {
    0%, 94%, 100% { opacity: 0; transform: translateX(0); }
    96% { opacity: 0.6; transform: translateX(2px); }
    98% { opacity: 0.4; transform: translateX(-2px); }
  }

  .ip {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: $font-mono;
    margin-top: 8px; // 增加与上方元素的间距
    padding-bottom: 4px; // 增加与分隔线的间距

    .ip-label {
      font-size: 10px;
      color: $neon-green;
      opacity: 0.7;
      flex-shrink: 0;
    }

    .ip-value {
      font-size: 16px; // 稍微减小字号以适应布局
      color: #ffffff;
      text-shadow: 0 0 8px rgba($neon-green, 0.3);
      letter-spacing: 1px;
    }
  }
}

.server-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 2px;
  font-weight: bold;
  font-family: $font-mono;
  position: relative;

  .status-core {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    position: relative;
    z-index: 2;
  }

  .status-ring {
    position: absolute;
    left: 6px;
    width: 8px;
    height: 8px;
    border: 1px solid currentColor;
    border-radius: 50%;
    animation: statusRingPulse 1.5s ease-out infinite;
  }

  @keyframes statusRingPulse {
    0% { transform: scale(1); opacity: 0.8; }
    100% { transform: scale(2.5); opacity: 0; }
  }

  &.normal {
    background: rgba($neon-green, 0.15);
    border: 1px solid rgba($neon-green, 0.5);
    color: $neon-green;
    .status-core { box-shadow: 0 0 10px $neon-green; }
  }

  &.warning {
    background: rgba($neon-orange, 0.15);
    border: 1px solid rgba($neon-orange, 0.5);
    color: $neon-orange;
    .status-core { box-shadow: 0 0 10px $neon-orange; }
  }

  &.error {
    background: rgba($neon-red, 0.2);
    border: 1px solid rgba($neon-red, 0.6);
    color: $neon-red;
    .status-core { box-shadow: 0 0 10px $neon-red; }
  }

  &.offline {
    background: rgba($text-secondary, 0.1);
    border: 1px solid rgba($text-secondary, 0.3);
    color: $text-secondary;
    .status-core { animation: none; opacity: 0.5; }
    .status-ring { animation: none; opacity: 0; }
  }
}

// 服务区域
.services-section {
  min-height: $card-services-height;
  height: $card-services-height;
  margin-bottom: 16px;
  position: relative;
  z-index: 5;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;

  h4 {
    font-size: 10px;
    color: $text-secondary;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    font-family: $font-mono;

    .section-prefix {
      color: $neon-green;
    }

    .section-line {
      flex: 1;
      height: 1px;
      background: linear-gradient(90deg, rgba($neon-green, 0.3), transparent);
    }
  }
}

.services-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 6px;
  flex: 1;
  min-height: 0;
}

.service-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: $bg-card-inner;
  border: 1px solid rgba($neon-green, 0.15);
  font-size: 11px;
  transition: border-color 0.2s ease, background 0.2s ease;
  position: relative;
  font-family: $font-mono;

  &:hover {
    border-color: rgba($neon-green, 0.4);
    background: rgba($neon-green, 0.05);
  }

  .service-prefix {
    color: $neon-green;
    font-size: 10px;
    opacity: 0.6;
  }

  .alert-indicator {
    position: absolute;
    top: 4px;
    right: 4px;
    width: 12px;
    height: 12px;
    cursor: pointer;
    z-index: 10;

    .alert-icon {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 6px;
      height: 6px;
      background: $neon-orange;
      border-radius: 50%;
      box-shadow: 0 0 6px $neon-orange;
    }

    .alert-pulse {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 6px;
      height: 6px;
      background: $neon-orange;
      border-radius: 50%;
      animation: alertPulse 1.5s ease-out infinite;
    }

    @keyframes alertPulse {
      0% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
      100% { transform: translate(-50%, -50%) scale(2.5); opacity: 0; }
    }
  }
}

// 状态指示灯 - 呼吸效果
.service-icon {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
  position: relative;

  &.running {
    background: $neon-green;
    box-shadow: 0 0 6px $neon-green;
    animation: statusBreathe 2s ease-in-out infinite;

    &::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      border-radius: 2px;
      background: $neon-green;
      animation: statusRingExpand 2s ease-out infinite;
    }
  }

  &.stopped {
    background: $neon-red;
    box-shadow: 0 0 6px $neon-red;
    animation: statusBlinkSlow 1.5s ease-in-out infinite;
  }

  &.slow, &.warning {
    background: $neon-orange;
    box-shadow: 0 0 6px $neon-orange;
    animation: statusBreathe 1.5s ease-in-out infinite;
  }
}

@keyframes statusBreathe {
  0%, 100% {
    box-shadow: 0 0 5px currentColor;
    opacity: 0.8;
  }
  50% {
    box-shadow: 0 0 15px currentColor, 0 0 25px currentColor;
    opacity: 1;
  }
}

@keyframes statusBlinkSlow {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 8px currentColor;
  }
  50% {
    opacity: 0.4;
    box-shadow: 0 0 3px currentColor;
  }
}

@keyframes statusRingExpand {
  0% {
    transform: scale(1);
    opacity: 0.6;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

.service-name {
  flex: 1;
  color: $text-secondary;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

// 服务状态标签 - 提高可读性（豆包反馈：颜色太暗）
.service-status {
  font-size: 9px;
  text-transform: uppercase;
  font-weight: bold;
  letter-spacing: 1px;
  padding: 3px 8px;
  flex-shrink: 0;
  border-radius: 2px;

  &.running {
    color: #00ff41; // 纯荧光绿，更亮
    background: rgba($neon-green, 0.25); // 提高背景不透明度
    text-shadow: 0 0 8px rgba($neon-green, 0.8);
    border: 1px solid rgba($neon-green, 0.4);
  }
  &.stopped {
    color: #ff4466; // 更亮的红色
    background: rgba($neon-red, 0.25);
    text-shadow: 0 0 8px rgba($neon-red, 0.8);
    border: 1px solid rgba($neon-red, 0.4);
  }
  &.slow, &.warning {
    color: #ffaa00; // 更亮的橙色
    background: rgba($neon-orange, 0.25);
    text-shadow: 0 0 8px rgba($neon-orange, 0.8);
    border: 1px solid rgba($neon-orange, 0.4);
  }
}

// CPU区域
.cpu-section {
  min-height: $card-cpu-height;
  height: $card-cpu-height;
  position: relative;
  z-index: 5;
  flex-shrink: 0;

  h4 {
    font-size: 10px;
    color: $text-secondary;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: $font-mono;

    .section-prefix {
      color: $neon-green;
    }

    .section-line {
      flex: 1;
      height: 1px;
      background: linear-gradient(90deg, rgba($neon-green, 0.3), transparent);
    }
  }
}

.cpu-bar {
  position: relative;
  height: 26px;
  background: $bg-card-inner;
  overflow: hidden;
  border: 1px solid rgba($neon-green, 0.2);

  .bar-markers {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;

    .marker {
      position: absolute;
      top: 0;
      width: 1px;
      height: 100%;
      background: rgba(255, 255, 255, 0.08);
    }
  }
}

.cpu-fill {
  height: 100%;
  transition: width 0.5s ease;
  position: relative;
  overflow: hidden;

  .fill-shine {
    position: absolute;
    top: 0;
    left: -100%;
    width: 50%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    animation: fillShine 2s linear infinite;
  }

  @keyframes fillShine {
    0% { transform: translateX(0); }
    100% { transform: translateX(400%); }
  }

  // 流动效果
  .fill-flow {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.15) 25%,
      rgba(255, 255, 255, 0.3) 50%,
      rgba(255, 255, 255, 0.15) 75%,
      transparent 100%
    );
    animation: flowEffect 2s linear infinite;
  }

  @keyframes flowEffect {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  &.low {
    background: linear-gradient(90deg, $neon-green, lighten($neon-green, 10%));
    box-shadow: 0 0 10px rgba($neon-green, 0.4);
  }

  &.medium {
    background: linear-gradient(90deg, $neon-green, $neon-cyan);
    box-shadow: 0 0 10px rgba($neon-green, 0.3);
  }

  &.high {
    background: linear-gradient(90deg, $neon-orange, lighten($neon-orange, 10%));
    box-shadow: 0 0 10px rgba($neon-orange, 0.4);
  }

  &.critical {
    background: linear-gradient(90deg, $neon-red, lighten($neon-red, 10%));
    box-shadow: 0 0 15px rgba($neon-red, 0.5);
    .fill-shine { animation-duration: 1s; }
  }
}

.cpu-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 13px;
  font-weight: bold;
  color: #fff;
  text-shadow: 0 0 10px rgba(0, 0, 0, 0.9);
  z-index: 10;
  letter-spacing: 2px;
  font-family: $font-mono;
  transition: transform 0.1s ease;

  &.value-updating {
    animation: valueJump 0.4s ease-out;
  }
}

// 数值跳动动画
@keyframes valueJump {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1);
  }
  25% {
    transform: translate(-50%, -50%) scale(1.2);
    text-shadow: 0 0 20px $neon-green;
  }
  50% {
    transform: translate(-50%, -50%) scale(0.95);
  }
  75% {
    transform: translate(-50%, -50%) scale(1.1);
  }
}

// Docker区域
.docker-section {
  position: relative;
  z-index: 5;
  margin-top: 12px;

  h4 {
    font-size: 10px;
    color: $text-secondary;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: $font-mono;

    .section-prefix {
      color: $neon-cyan;
    }

    .section-line {
      flex: 1;
      height: 1px;
      background: linear-gradient(90deg, rgba($neon-cyan, 0.3), transparent);
    }
  }
}

.docker-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: $bg-card-inner;
  border: 1px solid rgba($neon-cyan, 0.2);
}

.docker-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: $neon-cyan;
  font-family: $font-mono;

  .badge-icon {
    width: 8px;
    height: 8px;
    background: $neon-cyan;
    box-shadow: 0 0 6px $neon-cyan;
  }
}

.container-count {
  font-size: 11px;
  color: $text-secondary;
  font-family: $font-mono;

  .count-value {
    color: $neon-green;
    font-size: 16px;
    font-weight: bold;
    margin-right: 6px;
    text-shadow: 0 0 8px rgba($neon-green, 0.5);
  }
}

// 底部数据面板
.data-panel {
  display: flex;
  justify-content: space-around;
  min-height: $card-footer-height;
  height: $card-footer-height;
  padding-top: 12px;
  margin-top: auto;
  border-top: 1px solid rgba($neon-green, 0.15);
  position: relative;
  z-index: 5;
  flex-shrink: 0;

  &::before {
    content: '';
    position: absolute;
    top: -1px;
    left: 0;
    width: 40px;
    height: 2px;
    background: $neon-green;
  }
}

.data-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  flex: 1;

  .data-label {
    font-size: 8px;
    color: $neon-green;
    text-transform: uppercase;
    letter-spacing: 1px;
    opacity: 0.7;
    font-family: $font-mono;
  }

  .data-value {
    font-size: 12px;
    font-weight: bold;
    font-family: $font-mono;
    transition: transform 0.1s ease;

    &.normal {
      color: $neon-green;
      text-shadow: 0 0 6px rgba($neon-green, 0.4);
    }

    &.high {
      color: $neon-orange;
      text-shadow: 0 0 6px rgba($neon-orange, 0.4);
    }

    &.critical {
      color: $neon-red;
      text-shadow: 0 0 6px rgba($neon-red, 0.4);
      animation: criticalBlink 1.2s ease-in-out infinite;
    }

    // 数值更新动画
    &.value-updating {
      animation: dataValuePulse 0.4s ease-out;
    }

    @keyframes criticalBlink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    @keyframes dataValuePulse {
      0%, 100% {
        transform: scale(1);
      }
      30% {
        transform: scale(1.25);
        text-shadow: 0 0 15px currentColor;
      }
      60% {
        transform: scale(0.95);
      }
    }
  }

  .data-bar {
    width: 100%;
    height: 2px;
    background: $bg-card-inner;
    overflow: hidden;
    margin-top: 2px;
    position: relative;

    .data-bar-fill {
      height: 100%;
      transition: width 0.5s ease;
      position: relative;
      overflow: hidden;

      &.normal { background: $neon-green; box-shadow: 0 0 3px $neon-green; }
      &.high { background: $neon-orange; box-shadow: 0 0 3px $neon-orange; }
      &.critical { background: $neon-red; box-shadow: 0 0 3px $neon-red; }

      // 进度条流动效果
      .bar-flow {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(
          90deg,
          transparent,
          rgba(255, 255, 255, 0.4),
          transparent
        );
        animation: barFlowAnim 1.5s linear infinite;
      }
    }
  }

  @keyframes barFlowAnim {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  .ping-indicator {
    display: flex;
    gap: 2px;
    margin-top: 2px;

    .ping-dot {
      width: 3px;
      height: 3px;
      border-radius: 50%;
      animation: pingDot 2s ease-in-out infinite;

      &:nth-child(2) { animation-delay: 0.3s; }
      &:nth-child(3) { animation-delay: 0.6s; }
    }

    &.normal .ping-dot { background: $neon-green; }
    &.high .ping-dot { background: $neon-orange; }
    &.critical .ping-dot { background: $neon-red; }

    @keyframes pingDot {
      0%, 100% { opacity: 0.2; transform: scale(1); }
      50% { opacity: 0.8; transform: scale(1.2); }
    }
  }
}
</style>

<!-- Global styles for tooltip -->
<style lang="scss">
@import '@/styles/variables.scss';

.alert-tooltip {
  position: fixed;
  z-index: 9999;
  min-width: 280px;
  max-width: 400px;
  background: rgba(10, 10, 10, 0.98);
  border: 2px solid rgba($neon-orange, 0.5);
  box-shadow: 0 0 20px rgba($neon-orange, 0.3), inset 0 0 30px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  animation: tooltipFadeIn 0.2s ease-out;
  font-family: $font-mono;

  @keyframes tooltipFadeIn {
    from { opacity: 0; transform: translateY(-5px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .tooltip-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    background: rgba($neon-orange, 0.15);
    border-bottom: 1px solid rgba($neon-orange, 0.3);

    .tooltip-title {
      font-size: 11px;
      font-weight: bold;
      color: $neon-orange;
      text-transform: uppercase;
      letter-spacing: 2px;
      text-shadow: 0 0 8px rgba($neon-orange, 0.5);
    }

    .tooltip-close {
      font-size: 10px;
      color: $text-secondary;
      cursor: pointer;
      padding: 2px 6px;
      border: 1px solid rgba($text-secondary, 0.3);
      transition: all 0.2s ease;

      &:hover {
        color: $neon-red;
        border-color: $neon-red;
      }
    }
  }

  .tooltip-content {
    padding: 12px 14px;
    max-height: 300px;
    overflow-y: auto;

    &::-webkit-scrollbar {
      width: 4px;
    }

    &::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.3);
    }

    &::-webkit-scrollbar-thumb {
      background: rgba($neon-green, 0.3);
    }
  }

  .tooltip-section {
    margin-bottom: 12px;

    &:last-child {
      margin-bottom: 0;
    }

    .section-label {
      font-size: 9px;
      color: $neon-green;
      text-transform: uppercase;
      letter-spacing: 2px;
      margin-bottom: 8px;
      padding-bottom: 4px;
      border-bottom: 1px solid rgba($neon-green, 0.2);
    }
  }

  .restart-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;

    .status-icon {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    &.success {
      background: rgba($neon-green, 0.15);
      border: 1px solid rgba($neon-green, 0.4);
      color: $neon-green;
      .status-icon { background: $neon-green; box-shadow: 0 0 4px $neon-green; }
    }

    &.failed {
      background: rgba($neon-red, 0.15);
      border: 1px solid rgba($neon-red, 0.4);
      color: $neon-red;
      .status-icon { background: $neon-red; box-shadow: 0 0 4px $neon-red; }
    }
  }

  .restart-time {
    font-size: 10px;
    color: $text-secondary;
    margin-top: 6px;
  }

  .restart-message {
    font-size: 10px;
    color: $neon-green;
    margin-top: 4px;
    padding: 6px 8px;
    background: rgba($neon-green, 0.1);
    border-left: 2px solid $neon-green;
  }

  .error-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .error-item {
    padding: 8px 10px;
    background: rgba(0, 0, 0, 0.4);
    border-left: 2px solid $neon-orange;

    &.critical { border-left-color: $neon-red; background: rgba($neon-red, 0.1); }
    &.error { border-left-color: $neon-orange; background: rgba($neon-orange, 0.08); }
    &.warning { border-left-color: $neon-yellow; background: rgba($neon-yellow, 0.08); }

    .error-level {
      display: inline-block;
      font-size: 8px;
      padding: 2px 6px;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-right: 8px;

      .critical & { background: rgba($neon-red, 0.3); color: $neon-red; }
      .error & { background: rgba($neon-orange, 0.3); color: $neon-orange; }
      .warning & { background: rgba($neon-yellow, 0.3); color: $neon-yellow; }
    }

    .error-time {
      font-size: 9px;
      color: $text-secondary;
    }

    .error-message {
      font-size: 10px;
      color: #ffffff;
      margin-top: 6px;
      line-height: 1.4;
      word-break: break-word;
    }
  }

  .no-alerts {
    text-align: center;
    padding: 20px;
    color: $text-secondary;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
}
</style>
