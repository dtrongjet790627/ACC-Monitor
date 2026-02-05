<template>
  <!-- CRT Monitor Container -->
  <div
    class="crt-monitor"
    :class="[`status-${server.status}`]"
    @click="handleClick"
  >
    <!-- Monitor Top Bulge (CRT Tube Back) -->
    <div class="monitor-top-bulge"></div>

    <!-- Monitor Frame -->
    <div class="monitor-frame">
      <!-- Frame Screws -->
      <div class="frame-screw top-left"></div>
      <div class="frame-screw top-right"></div>
      <div class="frame-screw bottom-left"></div>
      <div class="frame-screw bottom-right"></div>

      <!-- Inner Bezel -->
      <div class="inner-bezel">
        <!-- Screen Area -->
        <div class="screen-area">
          <!-- CRT Scanlines Effect -->
          <div class="scanlines"></div>

          <!-- Screen Glare Effect -->
          <div class="screen-glare"></div>

          <!-- Screen Glow (status based) -->
          <div class="screen-glow"></div>

          <!-- Card Content -->
          <div class="card-content">
            <!-- Header: Name + Status -->
            <div class="card-header">
              <div class="server-name">{{ server.name }}</div>
              <div class="server-status" :class="server.status">
                <span class="status-led"></span>
                <span class="status-text">{{ statusText }}</span>
              </div>
            </div>

            <!-- IP Address -->
            <div class="server-ip">
              <span class="ip-label">IP:</span>
              <span class="ip-value">{{ server.ip }}</span>
            </div>

            <!-- Divider Line -->
            <div class="section-divider"></div>

            <!-- Services Section -->
            <div class="services-section">
              <div class="section-header">
                <span class="section-label">SERVICES</span>
                <span class="section-count">[{{ server.processes?.length || 0 }}]</span>
              </div>
              <div class="services-grid">
                <div
                  v-for="(process, index) in displayProcesses"
                  :key="index"
                  class="service-tag"
                  :class="process.status"
                >
                  <span class="service-name">[{{ truncateName(process.name) }}</span>
                  <span class="service-status">{{ processStatusText(process.status) }}]</span>
                </div>
              </div>
            </div>

            <!-- Divider Line -->
            <div class="section-divider"></div>

            <!-- CPU Progress Bar (only CPU has progress bar) -->
            <div class="cpu-section">
              <div class="cpu-row">
                <span class="cpu-label">CPU</span>
                <div class="cpu-bar">
                  <div class="cpu-fill" :class="getCpuClass" :style="{ width: animatedCpu + '%' }"></div>
                </div>
                <span class="cpu-value" :class="[getCpuClass, { 'value-bounce': cpuBounce }]">{{ animatedCpu }}%</span>
              </div>
            </div>

            <!-- Divider Line -->
            <div class="section-divider"></div>

            <!-- Stats Row: MEM, DISK, PING (values only, no progress bars) -->
            <div class="stats-row">
              <div class="stat-item">
                <span class="stat-label">MEM:</span>
                <span class="stat-value" :class="[getMemClass, { 'value-bounce': memBounce }]">{{ animatedMem }}%</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">DISK:</span>
                <span class="stat-value" :class="[getDiskClass, { 'value-bounce': diskBounce }]">{{ animatedDisk }}%</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">PING:</span>
                <span class="stat-value" :class="[getPingClass, { 'value-bounce': pingBounce }]">{{ animatedPing }}ms</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Power LED on Frame -->
      <div class="power-led" :class="server.status"></div>
    </div>

    <!-- Monitor Stand -->
    <div class="monitor-stand">
      <div class="stand-neck"></div>
      <div class="stand-base"></div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'

const props = defineProps({
  server: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

// Animated values for smooth transitions
const animatedCpu = ref(0)
const animatedMem = ref(0)
const animatedDisk = ref(0)
const animatedPing = ref(0)

// Animation state for bounce effect
const cpuBounce = ref(false)
const memBounce = ref(false)
const diskBounce = ref(false)
const pingBounce = ref(false)

// Easing function: easeOutCubic
function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3)
}

// Animate value with easing and bounce effect
function animateValue(startVal, endVal, duration, updateFn, bounceRef) {
  const startTime = performance.now()

  // Trigger bounce effect if value changed significantly
  if (bounceRef && Math.abs(endVal - startVal) > 1) {
    bounceRef.value = true
    setTimeout(() => {
      bounceRef.value = false
    }, 300)
  }

  function update(currentTime) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)
    const easedProgress = easeOutCubic(progress)
    const currentValue = startVal + (endVal - startVal) * easedProgress

    updateFn(Math.round(currentValue))

    if (progress < 1) {
      requestAnimationFrame(update)
    }
  }

  requestAnimationFrame(update)
}

// Watch for value changes and animate
watch(() => props.server.cpuUsage, (newVal, oldVal) => {
  const start = oldVal || animatedCpu.value || 0
  const end = newVal || 0
  animateValue(start, end, 500, (v) => { animatedCpu.value = v }, cpuBounce)
}, { immediate: true })

watch(() => props.server.memoryUsage, (newVal, oldVal) => {
  const start = oldVal || animatedMem.value || 0
  const end = newVal || 0
  animateValue(start, end, 500, (v) => { animatedMem.value = v }, memBounce)
}, { immediate: true })

watch(() => props.server.tablespaceUsage, (newVal, oldVal) => {
  const start = oldVal || animatedDisk.value || 0
  const end = newVal || 0
  animateValue(start, end, 500, (v) => { animatedDisk.value = v }, diskBounce)
}, { immediate: true })

watch(() => props.server.ping, (newVal, oldVal) => {
  const start = oldVal || animatedPing.value || 0
  const end = newVal || 0
  animateValue(start, end, 500, (v) => { animatedPing.value = v }, pingBounce)
}, { immediate: true })

// Initialize animated values on mount
onMounted(() => {
  animatedCpu.value = props.server.cpuUsage || 0
  animatedMem.value = props.server.memoryUsage || 0
  animatedDisk.value = props.server.tablespaceUsage || 0
  animatedPing.value = props.server.ping || 0
})

const statusText = computed(() => {
  const statusMap = {
    normal: 'ONLINE',
    warning: 'WARNING',
    error: 'CRITICAL',
    offline: 'OFFLINE'
  }
  return statusMap[props.server.status] || 'UNKNOWN'
})

const displayProcesses = computed(() => {
  return props.server.processes || []
})

const getDiskClass = computed(() => {
  const disk = props.server.tablespaceUsage || 0
  if (disk >= 90) return 'critical'
  if (disk >= 70) return 'warning'
  return 'normal'
})

const getCpuClass = computed(() => {
  const cpu = props.server.cpuUsage || 0
  if (cpu >= 90) return 'critical'
  if (cpu >= 70) return 'warning'
  return 'normal'
})

const getMemClass = computed(() => {
  const mem = props.server.memoryUsage || 0
  if (mem >= 90) return 'critical'
  if (mem >= 70) return 'warning'
  return 'normal'
})

const getPingClass = computed(() => {
  const ping = props.server.ping || 0
  if (ping >= 100) return 'critical'
  if (ping >= 50) return 'warning'
  return 'normal'
})

function processStatusText(status) {
  const statusMap = {
    running: 'RUN',
    stopped: 'DOWN',
    slow: 'SLOW',
    warning: 'WARN'
  }
  return statusMap[status] || status?.toUpperCase() || 'N/A'
}

function truncateName(name) {
  if (!name) return 'N/A'
  return name.length > 10 ? name.substring(0, 8) + '..' : name
}

function handleClick() {
  emit('click', props.server)
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

// Cybercore Color System
$cyber-cyan: #00d4aa;
$cyber-cyan-glow: #00ffcc;
$cyber-magenta: #ff0080;
$cyber-yellow: #ffcc00;
$cyber-red: #ff3333;
$void-900: #0a0a0f;
$void-800: #12121a;
$void-700: #1a1a24;

// Monitor Colors
$monitor-frame-dark: #1a1a1a;
$monitor-frame-light: #2d2d2d;
$monitor-bezel: #232323;
$stand-color: #1f1f1f;

// CRT Monitor Container
.crt-monitor {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: transform 0.3s ease;

  &:hover {
    transform: translateY(-4px);

    .monitor-frame {
      box-shadow:
        0 0 15px rgba($cyber-cyan, 0.3),
        0 8px 30px rgba(0, 0, 0, 0.6);
    }

    .screen-glow {
      opacity: 0.15;
    }
  }

  // Status variants
  &.status-normal {
    .screen-glow { background: radial-gradient(ellipse at center, $cyber-cyan 0%, transparent 70%); }
    .power-led { background: $cyber-cyan; box-shadow: 0 0 6px $cyber-cyan; }
  }

  &.status-warning {
    .screen-glow { background: radial-gradient(ellipse at center, $cyber-yellow 0%, transparent 70%); }
    .power-led { background: $cyber-yellow; box-shadow: 0 0 6px $cyber-yellow; animation: led-blink 1.5s ease-in-out infinite; }
    .monitor-frame { box-shadow: 0 0 10px rgba($cyber-yellow, 0.2), 0 4px 20px rgba(0, 0, 0, 0.5); }
  }

  &.status-error {
    .screen-glow { background: radial-gradient(ellipse at center, $cyber-red 0%, transparent 70%); }
    .power-led { background: $cyber-red; box-shadow: 0 0 8px $cyber-red; animation: led-blink 0.8s ease-in-out infinite; }
    .monitor-frame { box-shadow: 0 0 15px rgba($cyber-red, 0.3), 0 4px 20px rgba(0, 0, 0, 0.5); }

    // Red edge pulse alert for error status
    .screen-area::before {
      content: '';
      position: absolute;
      inset: 0;
      border: 2px solid transparent;
      border-radius: 3px;
      animation: danger-pulse 0.5s ease-in-out infinite;
      pointer-events: none;
      z-index: 15;
    }
  }

  &.status-offline {
    opacity: 0.5;
    .screen-glow { opacity: 0 !important; }
    .power-led { background: #333; box-shadow: none; }
    .screen-area { background: #0a0a0a; }
  }
}

// Monitor Top Bulge (simulates CRT tube back) - Semi-transparent
.monitor-top-bulge {
  width: 70%;
  height: 8px;
  margin: 0 auto;
  background: linear-gradient(180deg, rgba(45, 45, 45, 0.6) 0%, rgba(26, 26, 26, 0.6) 100%);
  border-radius: 8px 8px 0 0;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 10%;
    right: 10%;
    height: 2px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    border-radius: 2px;
  }
}

// Monitor Frame - Semi-transparent to show matrix rain
.monitor-frame {
  flex: 1;
  background: linear-gradient(145deg, rgba(45, 45, 45, 0.55) 0%, rgba(26, 26, 26, 0.6) 50%, rgba(21, 21, 21, 0.55) 100%);
  border-radius: 6px;
  padding: 12px;
  position: relative;
  box-shadow:
    0 0 5px rgba($cyber-cyan, 0.1),
    0 4px 20px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transition: box-shadow 0.3s ease;

  // Frame edge highlight
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent 10%, rgba(255,255,255,0.15) 50%, transparent 90%);
  }
}

// Frame Screws
.frame-screw {
  position: absolute;
  width: 6px;
  height: 6px;
  background: radial-gradient(circle at 30% 30%, #444, #1a1a1a);
  border-radius: 50%;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.8);
  z-index: 10;

  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 4px;
    height: 1px;
    background: #222;
  }

  &.top-left { top: 6px; left: 6px; }
  &.top-right { top: 6px; right: 6px; }
  &.bottom-left { bottom: 6px; left: 6px; }
  &.bottom-right { bottom: 6px; right: 6px; }
}

// Inner Bezel - Semi-transparent
.inner-bezel {
  width: 100%;
  height: 100%;
  background: rgba(35, 35, 35, 0.5);
  border-radius: 4px;
  padding: 6px;
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.6),
    inset 0 0 0 1px rgba(0, 0, 0, 0.3);
}

// Screen Area - Semi-transparent to show matrix rain background
.screen-area {
  width: 100%;
  height: 100%;
  background: rgba(10, 10, 15, 0.75);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
  box-shadow:
    inset 0 0 20px rgba(0, 0, 0, 0.5),
    inset 0 0 40px rgba(0, 0, 0, 0.3);
}

// Screen Glow Effect
.screen-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.08;
  pointer-events: none;
  z-index: 1;
  transition: opacity 0.3s ease;
}

// Screen Glare Effect
.screen-glare {
  position: absolute;
  top: 5%;
  left: 5%;
  width: 30%;
  height: 25%;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.06) 0%,
    transparent 60%
  );
  border-radius: 50%;
  pointer-events: none;
  z-index: 14;
}

// CRT Scanlines - subtle effect with slow scroll animation
.scanlines {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.06) 2px,
    rgba(0, 0, 0, 0.06) 4px
  );
  background-size: 100% 4px;
  pointer-events: none;
  z-index: 10;
  opacity: 0.7;
  animation: scanline-scroll 8s linear infinite;
}

@keyframes scanline-scroll {
  0% { background-position: 0 0; }
  100% { background-position: 0 100px; }
}

// Power LED
.power-led {
  position: absolute;
  bottom: 8px;
  right: 12px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: $cyber-cyan;
  box-shadow: 0 0 6px $cyber-cyan;
  animation: led-breathe 2s ease-in-out infinite;
}

@keyframes led-breathe {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes led-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

// Danger pulse animation for error status
@keyframes danger-pulse {
  0%, 100% {
    border-color: rgba(255, 51, 51, 0.3);
    box-shadow: inset 0 0 10px rgba(255, 51, 51, 0.2);
  }
  50% {
    border-color: rgba(255, 51, 51, 0.8);
    box-shadow: inset 0 0 20px rgba(255, 51, 51, 0.4);
  }
}

// Monitor Stand - Semi-transparent
.monitor-stand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: -2px;
}

.stand-neck {
  width: 24px;
  height: 14px;
  background: linear-gradient(90deg, rgba(21, 21, 21, 0.6) 0%, rgba(31, 31, 31, 0.6) 30%, rgba(42, 42, 42, 0.6) 50%, rgba(31, 31, 31, 0.6) 70%, rgba(21, 21, 21, 0.6) 100%);
  border-radius: 0 0 3px 3px;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 60%;
    height: 2px;
    background: rgba(255, 255, 255, 0.05);
  }
}

.stand-base {
  width: 56px;
  height: 8px;
  background: linear-gradient(180deg, rgba(31, 31, 31, 0.6) 0%, rgba(21, 21, 21, 0.6) 100%);
  border-radius: 2px 2px 4px 4px;
  box-shadow:
    0 2px 4px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 10%;
    right: 10%;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  }
}

// Card Content - fills the screen area
.card-content {
  position: relative;
  padding: 10px 12px;
  z-index: 5;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

// Card Header
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  flex-shrink: 0;
}

.server-name {
  font-family: $font-mono;
  font-size: 16px;
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

.server-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-family: $font-mono;
  letter-spacing: 1px;
  flex-shrink: 0;

  .status-led {
    width: 6px;
    height: 6px;
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
  &.error {
    color: $cyber-red;
    .status-led { background: $cyber-red; box-shadow: 0 0 8px $cyber-red; animation: led-blink 0.8s ease-in-out infinite; }
  }
  &.offline {
    color: #666;
    .status-led { background: #333; box-shadow: none; animation: none; }
  }
}

// IP Address
.server-ip {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 6px;
  font-family: $font-mono;
  font-size: 12px;
  flex-shrink: 0;

  .ip-label {
    color: rgba($cyber-cyan, 0.5);
  }

  .ip-value {
    color: rgba(255, 255, 255, 0.8);
    text-shadow: 0 0 5px rgba(255, 255, 255, 0.15);
  }
}

// Section Divider
.section-divider {
  height: 1px;
  background: linear-gradient(90deg,
    rgba($cyber-cyan, 0.1) 0%,
    rgba($cyber-cyan, 0.4) 50%,
    rgba($cyber-cyan, 0.1) 100%);
  margin: 6px 0;
  flex-shrink: 0;
  box-shadow: 0 0 3px rgba($cyber-cyan, 0.2);
}

// Services Section
.services-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
  font-family: $font-mono;
  font-size: 11px;
  letter-spacing: 1px;
  flex-shrink: 0;

  .section-label {
    color: rgba($cyber-cyan, 0.6);
    text-shadow: 0 0 4px rgba($cyber-cyan, 0.2);
  }

  .section-count {
    color: $cyber-cyan;
    font-weight: bold;
  }
}

// Services Grid - 2 columns layout for better spacing
.services-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px 8px;
  overflow: hidden;
  flex: 1;
  align-content: flex-start;
}

.service-tag {
  display: flex;
  align-items: center;
  gap: 2px;
  font-family: $font-mono;
  font-size: 11px;
  line-height: 1.2;
  padding: 1px 0;

  .service-name {
    color: rgba(255, 255, 255, 0.85);
  }

  .service-status {
    font-weight: bold;
    transition: text-shadow 0.15s ease;
  }

  &.running {
    .service-status {
      color: $cyber-cyan;
      font-weight: 700;
      text-shadow:
        0 0 2px $cyber-cyan,
        0 0 4px rgba($cyber-cyan, 0.5);
    }
  }

  &.stopped {
    .service-status {
      color: $cyber-red;
      font-weight: 700;
      text-shadow:
        0 0 2px $cyber-red,
        0 0 4px rgba($cyber-red, 0.5);
    }
  }

  &.slow, &.warning {
    .service-status {
      color: $cyber-yellow;
      font-weight: 700;
      text-shadow:
        0 0 2px $cyber-yellow,
        0 0 4px rgba($cyber-yellow, 0.5);
    }
  }

  // UNKNOWN status - gray style
  &.unknown {
    .service-name {
      color: rgba(255, 255, 255, 0.5);
    }
    .service-status {
      color: #888;
      font-weight: 400;
      text-shadow: none;
    }
  }
}

// CPU Section (only CPU has progress bar)
.cpu-section {
  margin: 3px 0;
  flex-shrink: 0;
}

.cpu-row {
  display: grid;
  grid-template-columns: 28px 1fr 36px;
  align-items: center;
  gap: 6px;
  font-family: $font-mono;
}

.cpu-label {
  font-size: 11px;
  color: rgba($cyber-cyan, 0.6);
  letter-spacing: 1px;
  text-shadow: 0 0 4px rgba($cyber-cyan, 0.2);
}

.cpu-bar {
  height: 10px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba($cyber-cyan, 0.3);
  border-radius: 2px;
  overflow: hidden;
  box-shadow: inset 0 0 8px rgba(0, 0, 0, 0.5);
}

.cpu-fill {
  height: 100%;
  transition: width 0.5s ease;
  border-radius: 1px;

  &.normal {
    background: linear-gradient(90deg, rgba($cyber-cyan, 0.9), rgba($cyber-cyan, 0.7));
    box-shadow: 0 0 8px rgba($cyber-cyan, 0.5);
  }

  &.warning {
    background: linear-gradient(90deg, rgba($cyber-yellow, 0.9), rgba($cyber-yellow, 0.7));
    box-shadow: 0 0 8px rgba($cyber-yellow, 0.5);
  }

  &.critical {
    background: linear-gradient(90deg, rgba($cyber-red, 0.9), rgba($cyber-red, 0.7));
    box-shadow: 0 0 8px rgba($cyber-red, 0.5);
  }
}

.cpu-value {
  font-size: 12px;
  font-weight: bold;
  text-align: right;

  &.normal {
    color: $cyber-cyan;
    text-shadow: 0 0 6px rgba($cyber-cyan, 0.5);
  }

  &.warning {
    color: $cyber-yellow;
    text-shadow: 0 0 6px rgba($cyber-yellow, 0.5);
  }

  &.critical {
    color: $cyber-red;
    text-shadow: 0 0 6px rgba($cyber-red, 0.5);
  }
}

// Stats Row (MEM, DISK, PING - values only)
.stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: $font-mono;
  padding-top: 4px;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 3px;

  .stat-label {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.4);
    letter-spacing: 0.5px;
  }

  .stat-value {
    font-size: 12px;
    font-weight: bold;
    transition: transform 0.15s ease-out;

    &.normal {
      color: $cyber-cyan;
      text-shadow: 0 0 5px rgba($cyber-cyan, 0.4);
    }

    &.warning {
      color: $cyber-yellow;
      text-shadow: 0 0 5px rgba($cyber-yellow, 0.4);
    }

    &.critical {
      color: $cyber-red;
      text-shadow: 0 0 5px rgba($cyber-red, 0.4);
    }
  }
}

// Value bounce animation with highlight flash
.value-bounce {
  animation: valueBounceHighlight 0.3s ease-out;
}

@keyframes valueBounceHighlight {
  0% {
    transform: scale(1);
    filter: brightness(1);
  }
  15% {
    transform: scale(1.3);
    filter: brightness(2);
  }
  30% {
    transform: scale(1.15);
    filter: brightness(1.5);
  }
  50% {
    transform: scale(0.95);
    filter: brightness(1.2);
  }
  70% {
    transform: scale(1.1);
    filter: brightness(1.1);
  }
  100% {
    transform: scale(1);
    filter: brightness(1);
  }
}

// CPU value also needs bounce support
.cpu-value {
  transition: transform 0.15s ease-out, filter 0.15s ease-out;

  &.value-bounce {
    animation: valueBounceHighlight 0.3s ease-out;
  }
}
</style>
