<template>
  <!-- CRT Monitor Container - Deep Optimized Version -->
  <div
    class="crt-monitor"
    :class="[`status-${server.status}`]"
    @click="handleClick"
  >
    <!-- Monitor Back Shell (CRT Tube Housing) - Visible top arc -->
    <div class="monitor-back-shell">
      <div class="shell-vent-grille">
        <div class="vent-slot" v-for="n in 8" :key="n"></div>
      </div>
    </div>

    <!-- Main CRT Body -->
    <div class="crt-body">
      <!-- Outer Frame (Thick Bezel like real CRT) -->
      <div class="monitor-outer-frame">
        <!-- Frame Corner Accents -->
        <div class="corner-accent top-left"></div>
        <div class="corner-accent top-right"></div>
        <div class="corner-accent bottom-left"></div>
        <div class="corner-accent bottom-right"></div>

        <!-- Frame Screws (Phillips head) -->
        <div class="frame-screw top-left"></div>
        <div class="frame-screw top-right"></div>
        <div class="frame-screw bottom-left"></div>
        <div class="frame-screw bottom-right"></div>

        <!-- Brand Label Area -->
        <div class="brand-label">
          <span class="brand-text">ACC</span>
          <span class="model-text">MON-2600</span>
        </div>

        <!-- Inner Frame (Screen Housing) -->
        <div class="monitor-inner-frame">
          <!-- Inner Bezel with rounded corners for CRT effect -->
          <div class="inner-bezel">
            <!-- Screen Area with CRT curvature simulation -->
            <div class="screen-area">
              <!-- CRT Edge Vignette -->
              <div class="crt-vignette"></div>

              <!-- CRT Scanlines Effect -->
              <div class="scanlines"></div>

              <!-- Screen Glare Effect -->
              <div class="screen-glare"></div>

              <!-- Screen Glow (status based) -->
              <div class="screen-glow"></div>

              <!-- Phosphor Dot Pattern (subtle) -->
              <div class="phosphor-pattern"></div>

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

                <!-- CPU Progress Bar -->
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

                <!-- Stats Row: MEM, DISK, PING -->
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
        </div>

        <!-- Control Panel (Bottom of frame) -->
        <div class="control-panel">
          <!-- Power Button -->
          <div class="power-button" :class="server.status">
            <div class="button-ring"></div>
            <div class="button-center"></div>
          </div>

          <!-- Control Knobs -->
          <div class="control-knobs">
            <div class="knob brightness">
              <div class="knob-cap"></div>
              <div class="knob-indicator"></div>
            </div>
            <div class="knob contrast">
              <div class="knob-cap"></div>
              <div class="knob-indicator"></div>
            </div>
          </div>

          <!-- LED Indicators -->
          <div class="led-panel">
            <div class="led-indicator power" :class="server.status"></div>
            <div class="led-indicator hdd" :class="{ active: animatedCpu > 20 }"></div>
            <div class="led-indicator network" :class="{ active: animatedPing < 100 }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Monitor Stand (Improved design) -->
    <div class="monitor-stand">
      <!-- Cable Connection Port -->
      <div class="cable-port">
        <div class="port-socket"></div>
        <div class="cable-connector">
          <div class="cable-wire"></div>
        </div>
      </div>

      <!-- Stand Neck with tilt mechanism -->
      <div class="stand-neck">
        <div class="neck-joint"></div>
        <div class="neck-shaft"></div>
      </div>

      <!-- Stand Base (Oval shape) -->
      <div class="stand-base">
        <div class="base-plate"></div>
        <div class="base-shadow"></div>
      </div>
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

// Monitor Colors - Deep CRT aesthetics
$monitor-frame-darkest: #141414;
$monitor-frame-dark: #1a1a1a;
$monitor-frame-mid: #252525;
$monitor-frame-light: #2d2d2d;
$monitor-bezel: #1e1e1e;
$stand-color: #1a1a1a;

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

    .monitor-outer-frame {
      box-shadow:
        0 0 20px rgba($cyber-cyan, 0.25),
        0 12px 40px rgba(0, 0, 0, 0.7),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
    }

    .screen-glow {
      opacity: 0.18;
    }

    .control-panel {
      .led-indicator.power {
        box-shadow: 0 0 10px currentColor;
      }
    }
  }

  // Status variants
  &.status-normal {
    .screen-glow { background: radial-gradient(ellipse at center, $cyber-cyan 0%, transparent 70%); }
    .led-indicator.power { background: $cyber-cyan; box-shadow: 0 0 6px $cyber-cyan; }
    .power-button .button-center { background: radial-gradient(circle, rgba($cyber-cyan, 0.6) 0%, rgba($cyber-cyan, 0.2) 100%); }
  }

  &.status-warning {
    .screen-glow { background: radial-gradient(ellipse at center, $cyber-yellow 0%, transparent 70%); }
    .led-indicator.power { background: $cyber-yellow; box-shadow: 0 0 6px $cyber-yellow; animation: led-blink 1.5s ease-in-out infinite; }
    .power-button .button-center { background: radial-gradient(circle, rgba($cyber-yellow, 0.6) 0%, rgba($cyber-yellow, 0.2) 100%); }
    .monitor-outer-frame { box-shadow: 0 0 15px rgba($cyber-yellow, 0.2), 0 8px 30px rgba(0, 0, 0, 0.6); }
  }

  &.status-error {
    .screen-glow { background: radial-gradient(ellipse at center, $cyber-red 0%, transparent 70%); }
    .led-indicator.power { background: $cyber-red; box-shadow: 0 0 8px $cyber-red; animation: led-blink 0.8s ease-in-out infinite; }
    .power-button .button-center { background: radial-gradient(circle, rgba($cyber-red, 0.6) 0%, rgba($cyber-red, 0.2) 100%); }
    .monitor-outer-frame { box-shadow: 0 0 20px rgba($cyber-red, 0.3), 0 8px 30px rgba(0, 0, 0, 0.6); }

    .screen-area::after {
      content: '';
      position: absolute;
      inset: 0;
      border: 2px solid transparent;
      border-radius: 4px;
      animation: danger-pulse 0.5s ease-in-out infinite;
      pointer-events: none;
      z-index: 15;
    }
  }

  &.status-offline {
    opacity: 0.5;
    .screen-glow { opacity: 0 !important; }
    .led-indicator.power { background: #333; box-shadow: none; }
    .power-button .button-center { background: #222; }
    .screen-area { background: #0a0a0a; }
  }
}

// ============================================
// Monitor Back Shell - CRT Tube Housing
// ============================================
.monitor-back-shell {
  width: 80%;
  height: 12px;
  margin: 0 auto;
  background: linear-gradient(180deg,
    $monitor-frame-mid 0%,
    $monitor-frame-dark 40%,
    $monitor-frame-darkest 100%
  );
  border-radius: 12px 12px 0 0;
  position: relative;
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.05),
    0 -2px 8px rgba(0, 0, 0, 0.5);

  // Shell top highlight
  &::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 15%;
    right: 15%;
    height: 2px;
    background: linear-gradient(90deg,
      transparent,
      rgba(255, 255, 255, 0.12),
      transparent
    );
    border-radius: 2px;
  }

  // Ventilation grille
  .shell-vent-grille {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    display: flex;
    gap: 4px;

    .vent-slot {
      width: 8px;
      height: 3px;
      background: #0a0a0a;
      border-radius: 1px;
      box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.8);
    }
  }
}

// ============================================
// CRT Body - Main frame housing
// ============================================
.crt-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

// ============================================
// Outer Frame - Thick CRT Bezel (15-20px)
// ============================================
.monitor-outer-frame {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: linear-gradient(160deg,
    $monitor-frame-light 0%,
    $monitor-frame-mid 15%,
    $monitor-frame-dark 50%,
    $monitor-frame-darkest 85%,
    #0f0f0f 100%
  );
  border-radius: 6px;
  padding: 14px 14px 8px 14px;
  position: relative;
  box-shadow:
    0 0 8px rgba($cyber-cyan, 0.08),
    0 8px 30px rgba(0, 0, 0, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    inset 0 -1px 0 rgba(0, 0, 0, 0.5);
  transition: box-shadow 0.3s ease;

  // Frame texture pattern (subtle)
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 6px;
    background:
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(255, 255, 255, 0.01) 2px,
        rgba(255, 255, 255, 0.01) 4px
      );
    pointer-events: none;
    z-index: 0;
  }
}

// Corner Accents (industrial detail)
.corner-accent {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.06);
  z-index: 5;

  &.top-left {
    top: 4px;
    left: 4px;
    border-right: none;
    border-bottom: none;
    border-radius: 3px 0 0 0;
  }

  &.top-right {
    top: 4px;
    right: 4px;
    border-left: none;
    border-bottom: none;
    border-radius: 0 3px 0 0;
  }

  &.bottom-left {
    bottom: 36px;
    left: 4px;
    border-right: none;
    border-top: none;
    border-radius: 0 0 0 3px;
  }

  &.bottom-right {
    bottom: 36px;
    right: 4px;
    border-left: none;
    border-top: none;
    border-radius: 0 0 3px 0;
  }
}

// Frame Screws (Phillips head)
.frame-screw {
  position: absolute;
  width: 8px;
  height: 8px;
  background: radial-gradient(circle at 35% 35%,
    #3a3a3a 0%,
    #252525 40%,
    #1a1a1a 100%
  );
  border-radius: 50%;
  box-shadow:
    inset 0 1px 2px rgba(0, 0, 0, 0.9),
    0 1px 1px rgba(255, 255, 255, 0.05);
  z-index: 10;

  // Phillips cross pattern
  &::before,
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #151515;
  }

  &::before {
    width: 5px;
    height: 1px;
  }

  &::after {
    width: 1px;
    height: 5px;
  }

  &.top-left { top: 8px; left: 8px; }
  &.top-right { top: 8px; right: 8px; }
  &.bottom-left { bottom: 40px; left: 8px; }
  &.bottom-right { bottom: 40px; right: 8px; }
}

// Brand Label
.brand-label {
  position: absolute;
  top: 6px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 6px;
  z-index: 10;

  .brand-text {
    font-family: $font-mono;
    font-size: 8px;
    font-weight: bold;
    color: rgba($cyber-cyan, 0.6);
    letter-spacing: 2px;
    text-shadow: 0 0 4px rgba($cyber-cyan, 0.3);
  }

  .model-text {
    font-family: $font-mono;
    font-size: 7px;
    color: rgba(255, 255, 255, 0.25);
    letter-spacing: 1px;
  }
}

// ============================================
// Inner Frame - Screen Housing
// ============================================
.monitor-inner-frame {
  flex: 1;
  background: linear-gradient(180deg,
    #1a1a1a 0%,
    #151515 50%,
    #101010 100%
  );
  border-radius: 4px;
  padding: 4px;
  box-shadow:
    inset 0 2px 6px rgba(0, 0, 0, 0.8),
    inset 0 0 0 1px rgba(0, 0, 0, 0.5);
  position: relative;
}

// Inner Bezel
.inner-bezel {
  width: 100%;
  height: 100%;
  background: linear-gradient(180deg,
    #0f0f0f 0%,
    #0a0a0a 100%
  );
  border-radius: 3px;
  padding: 4px;
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.6),
    inset 0 0 0 1px rgba(0, 0, 0, 0.4);
}

// Screen Area with CRT curvature simulation
.screen-area {
  width: 100%;
  height: 100%;
  background: rgba(8, 10, 12, 0.9);
  border-radius: 4px;
  position: relative;
  overflow: hidden;
  box-shadow:
    inset 0 0 30px rgba(0, 0, 0, 0.6),
    inset 0 0 60px rgba(0, 0, 0, 0.4);
}

// CRT Edge Vignette (curved screen effect)
.crt-vignette {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(
    ellipse 120% 120% at center,
    transparent 40%,
    rgba(0, 0, 0, 0.3) 80%,
    rgba(0, 0, 0, 0.6) 100%
  );
  pointer-events: none;
  z-index: 12;
  border-radius: 4px;
}

// Screen Glow Effect
.screen-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.1;
  pointer-events: none;
  z-index: 1;
  transition: opacity 0.3s ease;
}

// Screen Glare Effect
.screen-glare {
  position: absolute;
  top: 3%;
  left: 3%;
  width: 35%;
  height: 30%;
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.08) 0%,
    rgba(255, 255, 255, 0.02) 30%,
    transparent 60%
  );
  border-radius: 50%;
  pointer-events: none;
  z-index: 14;
}

// CRT Scanlines
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
    rgba(0, 0, 0, 0.08) 2px,
    rgba(0, 0, 0, 0.08) 4px
  );
  background-size: 100% 4px;
  pointer-events: none;
  z-index: 10;
  opacity: 0.8;
  animation: scanline-scroll 8s linear infinite;
}

// Phosphor Dot Pattern (RGB subpixel simulation)
.phosphor-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    repeating-linear-gradient(
      90deg,
      rgba(255, 0, 0, 0.015) 0px,
      rgba(255, 0, 0, 0.015) 1px,
      rgba(0, 255, 0, 0.015) 1px,
      rgba(0, 255, 0, 0.015) 2px,
      rgba(0, 0, 255, 0.015) 2px,
      rgba(0, 0, 255, 0.015) 3px
    );
  pointer-events: none;
  z-index: 11;
  opacity: 0.5;
}

@keyframes scanline-scroll {
  0% { background-position: 0 0; }
  100% { background-position: 0 100px; }
}

// ============================================
// Control Panel - Bottom of Frame
// ============================================
.control-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 28px;
  padding: 4px 8px;
  margin-top: 4px;
  background: linear-gradient(180deg,
    $monitor-frame-dark 0%,
    $monitor-frame-darkest 100%
  );
  border-radius: 0 0 4px 4px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  position: relative;
  z-index: 10;
}

// Power Button
.power-button {
  width: 16px;
  height: 16px;
  position: relative;
  cursor: pointer;

  .button-ring {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: 2px solid #2a2a2a;
    border-radius: 50%;
    background: linear-gradient(145deg, #1a1a1a, #0f0f0f);
    box-shadow:
      inset 0 1px 3px rgba(0, 0, 0, 0.8),
      0 1px 1px rgba(255, 255, 255, 0.05);
  }

  .button-center {
    position: absolute;
    top: 4px;
    left: 4px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba($cyber-cyan, 0.4) 0%, rgba($cyber-cyan, 0.1) 100%);
    box-shadow: 0 0 4px rgba($cyber-cyan, 0.3);
  }
}

// Control Knobs
.control-knobs {
  display: flex;
  gap: 10px;

  .knob {
    width: 14px;
    height: 14px;
    position: relative;

    .knob-cap {
      width: 100%;
      height: 100%;
      background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
      border-radius: 50%;
      box-shadow:
        inset 0 1px 2px rgba(0, 0, 0, 0.6),
        0 1px 1px rgba(255, 255, 255, 0.05);
      border: 1px solid #333;
    }

    .knob-indicator {
      position: absolute;
      top: 2px;
      left: 50%;
      transform: translateX(-50%);
      width: 2px;
      height: 4px;
      background: rgba(255, 255, 255, 0.3);
      border-radius: 1px;
    }

    &.brightness .knob-indicator {
      transform: translateX(-50%) rotate(-30deg);
      transform-origin: bottom center;
    }

    &.contrast .knob-indicator {
      transform: translateX(-50%) rotate(30deg);
      transform-origin: bottom center;
    }
  }
}

// LED Indicators Panel
.led-panel {
  display: flex;
  align-items: center;
  gap: 6px;
}

.led-indicator {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #222;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.8);
  transition: all 0.3s ease;

  &.power {
    background: $cyber-cyan;
    box-shadow: 0 0 6px $cyber-cyan;
    animation: led-breathe 2s ease-in-out infinite;
  }

  &.hdd {
    &.active {
      background: #ff6600;
      box-shadow: 0 0 4px #ff6600;
      animation: led-flicker 0.1s ease-in-out infinite;
    }
  }

  &.network {
    &.active {
      background: #00ff00;
      box-shadow: 0 0 4px #00ff00;
      animation: led-breathe 1s ease-in-out infinite;
    }
  }
}

@keyframes led-breathe {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes led-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes led-flicker {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

// Danger pulse animation
@keyframes danger-pulse {
  0%, 100% {
    border-color: rgba(255, 51, 51, 0.3);
    box-shadow: inset 0 0 15px rgba(255, 51, 51, 0.2);
  }
  50% {
    border-color: rgba(255, 51, 51, 0.8);
    box-shadow: inset 0 0 25px rgba(255, 51, 51, 0.4);
  }
}

// ============================================
// Monitor Stand - Enhanced Design
// ============================================
.monitor-stand {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: -1px;
  position: relative;
}

// Cable Port
.cable-port {
  position: absolute;
  top: 2px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;

  .port-socket {
    width: 12px;
    height: 6px;
    background: #0a0a0a;
    border-radius: 1px;
    border: 1px solid #252525;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.8);
  }

  .cable-connector {
    position: absolute;
    top: 4px;
    left: 50%;
    transform: translateX(-50%);

    .cable-wire {
      width: 4px;
      height: 18px;
      background: linear-gradient(180deg,
        #1a1a1a 0%,
        #0f0f0f 50%,
        #1a1a1a 100%
      );
      border-radius: 2px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
  }
}

// Stand Neck
.stand-neck {
  width: 28px;
  height: 18px;
  position: relative;
  z-index: 4;

  .neck-joint {
    width: 100%;
    height: 6px;
    background: linear-gradient(180deg,
      $monitor-frame-mid 0%,
      $monitor-frame-dark 100%
    );
    border-radius: 2px;
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.05),
      0 1px 2px rgba(0, 0, 0, 0.5);
  }

  .neck-shaft {
    width: 20px;
    height: 14px;
    margin: 0 auto;
    background: linear-gradient(90deg,
      #151515 0%,
      #252525 30%,
      #2a2a2a 50%,
      #252525 70%,
      #151515 100%
    );
    border-radius: 0 0 3px 3px;
    box-shadow:
      inset 2px 0 4px rgba(0, 0, 0, 0.4),
      inset -2px 0 4px rgba(0, 0, 0, 0.4);
  }
}

// Stand Base (Oval)
.stand-base {
  width: 70px;
  position: relative;

  .base-plate {
    width: 100%;
    height: 10px;
    background: linear-gradient(180deg,
      $monitor-frame-mid 0%,
      $monitor-frame-dark 40%,
      $monitor-frame-darkest 100%
    );
    border-radius: 50%;
    box-shadow:
      0 2px 6px rgba(0, 0, 0, 0.6),
      inset 0 1px 0 rgba(255, 255, 255, 0.06),
      inset 0 -1px 0 rgba(0, 0, 0, 0.5);
  }

  .base-shadow {
    position: absolute;
    bottom: -4px;
    left: 10%;
    right: 10%;
    height: 4px;
    background: radial-gradient(ellipse, rgba(0, 0, 0, 0.4) 0%, transparent 70%);
    filter: blur(2px);
  }
}

// ============================================
// Card Content - Screen Display Area
// ============================================
.card-content {
  position: relative;
  padding: 8px 10px;
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
  margin-bottom: 5px;
  flex-shrink: 0;
}

.server-name {
  font-family: $font-mono;
  font-size: 14px;
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
  gap: 4px;
  font-size: 10px;
  font-family: $font-mono;
  letter-spacing: 1px;
  flex-shrink: 0;

  .status-led {
    width: 5px;
    height: 5px;
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
  gap: 4px;
  margin-bottom: 5px;
  font-family: $font-mono;
  font-size: 11px;
  flex-shrink: 0;

  .ip-label {
    color: rgba($cyber-cyan, 0.5);
  }

  .ip-value {
    color: rgba(255, 255, 255, 0.75);
    text-shadow: 0 0 4px rgba(255, 255, 255, 0.1);
  }
}

// Section Divider
.section-divider {
  height: 1px;
  background: linear-gradient(90deg,
    rgba($cyber-cyan, 0.1) 0%,
    rgba($cyber-cyan, 0.35) 50%,
    rgba($cyber-cyan, 0.1) 100%);
  margin: 5px 0;
  flex-shrink: 0;
  box-shadow: 0 0 3px rgba($cyber-cyan, 0.15);
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
  margin-bottom: 4px;
  font-family: $font-mono;
  font-size: 10px;
  letter-spacing: 1px;
  flex-shrink: 0;

  .section-label {
    color: rgba($cyber-cyan, 0.55);
    text-shadow: 0 0 4px rgba($cyber-cyan, 0.2);
  }

  .section-count {
    color: $cyber-cyan;
    font-weight: bold;
  }
}

// Services Grid
.services-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 3px 6px;
  overflow: hidden;
  flex: 1;
  align-content: flex-start;
}

.service-tag {
  display: flex;
  align-items: center;
  gap: 2px;
  font-family: $font-mono;
  font-size: 10px;
  line-height: 1.2;
  padding: 1px 0;

  .service-name {
    color: rgba(255, 255, 255, 0.8);
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

// CPU Section
.cpu-section {
  margin: 2px 0;
  flex-shrink: 0;
}

.cpu-row {
  display: grid;
  grid-template-columns: 26px 1fr 34px;
  align-items: center;
  gap: 5px;
  font-family: $font-mono;
}

.cpu-label {
  font-size: 10px;
  color: rgba($cyber-cyan, 0.55);
  letter-spacing: 1px;
  text-shadow: 0 0 4px rgba($cyber-cyan, 0.2);
}

.cpu-bar {
  height: 8px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba($cyber-cyan, 0.25);
  border-radius: 2px;
  overflow: hidden;
  box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.5);
}

.cpu-fill {
  height: 100%;
  transition: width 0.5s ease;
  border-radius: 1px;

  &.normal {
    background: linear-gradient(90deg, rgba($cyber-cyan, 0.9), rgba($cyber-cyan, 0.7));
    box-shadow: 0 0 6px rgba($cyber-cyan, 0.4);
  }

  &.warning {
    background: linear-gradient(90deg, rgba($cyber-yellow, 0.9), rgba($cyber-yellow, 0.7));
    box-shadow: 0 0 6px rgba($cyber-yellow, 0.4);
  }

  &.critical {
    background: linear-gradient(90deg, rgba($cyber-red, 0.9), rgba($cyber-red, 0.7));
    box-shadow: 0 0 6px rgba($cyber-red, 0.4);
  }
}

.cpu-value {
  font-size: 11px;
  font-weight: bold;
  text-align: right;
  transition: transform 0.15s ease-out, filter 0.15s ease-out;

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

  &.value-bounce {
    animation: valueBounceHighlight 0.3s ease-out;
  }
}

// Stats Row
.stats-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: $font-mono;
  padding-top: 3px;
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 2px;

  .stat-label {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.35);
    letter-spacing: 0.5px;
  }

  .stat-value {
    font-size: 11px;
    font-weight: bold;
    transition: transform 0.15s ease-out;

    &.normal {
      color: $cyber-cyan;
      text-shadow: 0 0 4px rgba($cyber-cyan, 0.35);
    }

    &.warning {
      color: $cyber-yellow;
      text-shadow: 0 0 4px rgba($cyber-yellow, 0.35);
    }

    &.critical {
      color: $cyber-red;
      text-shadow: 0 0 4px rgba($cyber-red, 0.35);
    }
  }
}

// Value bounce animation
.value-bounce {
  animation: valueBounceHighlight 0.3s ease-out;
}

@keyframes valueBounceHighlight {
  0% {
    transform: scale(1);
    filter: brightness(1);
  }
  15% {
    transform: scale(1.25);
    filter: brightness(1.8);
  }
  30% {
    transform: scale(1.1);
    filter: brightness(1.4);
  }
  50% {
    transform: scale(0.95);
    filter: brightness(1.2);
  }
  70% {
    transform: scale(1.05);
    filter: brightness(1.1);
  }
  100% {
    transform: scale(1);
    filter: brightness(1);
  }
}
</style>
