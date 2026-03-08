<template>
  <div class="app-container">
    <!-- 背景特效层 - 代码雨 + 网格 -->
    <BackgroundEffects />

    <!-- 扫描线效果 -->
    <div class="scanlines"></div>

    <!-- JS驱动的全局偶发扫描线 -->
    <div
      class="global-scanline"
      :class="{ active: globalScanActive, 'scan-reverse': globalScanReverse }"
      :style="globalScanStyle"
    ></div>

    <!-- Glitch 故障层 -->
    <div class="glitch-overlay"></div>

    <!-- 鼠标跟随光标效果 - 绿色 -->
    <div class="cursor-glow" :style="cursorStyle"></div>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="terminal-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Toast通知容器 -->
    <ToastContainer />

    <!-- 版本标识 - 终端风格 -->
    <div class="version-tag">
      <span class="version-prefix">>_</span>
      <span class="version-text">V6</span>
      <span class="version-name">GUARDIAN</span>
      <span class="version-status">ONLINE</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BackgroundEffects from '@/components/BackgroundEffects.vue'
import ToastContainer from '@/components/ToastContainer.vue'

// ========================================
// JS-driven global sporadic scanline
// Appears every 15-30 seconds, sweeps full screen in 0.5-1s
// ========================================
const globalScanActive = ref(false)
const globalScanReverse = ref(false)
const globalScanDuration = ref(0.7)
let globalScanTimer = null
let globalScanEndTimer = null

const globalScanStyle = computed(() => ({
  '--scan-duration': globalScanDuration.value + 's'
}))

function scheduleGlobalScan() {
  // Random interval: 15-30 seconds between scans
  const delay = 15000 + Math.random() * 15000
  globalScanTimer = setTimeout(() => {
    // Randomly choose direction: top-to-bottom or bottom-to-top
    globalScanReverse.value = Math.random() > 0.5
    // Duration: 0.5-1 second
    globalScanDuration.value = 0.5 + Math.random() * 0.5
    globalScanActive.value = true

    // End the scan after duration
    const durationMs = globalScanDuration.value * 1000
    globalScanEndTimer = setTimeout(() => {
      globalScanActive.value = false
      scheduleGlobalScan() // Schedule next
    }, durationMs + 50) // Small buffer to ensure animation completes
  }, delay)
}

const mouseX = ref(0)
const mouseY = ref(0)
let rafId = null
let pendingX = 0
let pendingY = 0
let isUpdating = false

const cursorStyle = computed(() => ({
  left: mouseX.value + 'px',
  top: mouseY.value + 'px'
}))

// 使用requestAnimationFrame节流鼠标移动
function handleMouseMove(e) {
  pendingX = e.clientX
  pendingY = e.clientY

  if (!isUpdating) {
    isUpdating = true
    rafId = requestAnimationFrame(() => {
      mouseX.value = pendingX
      mouseY.value = pendingY
      isUpdating = false
    })
  }
}

// 添加事件监听
if (typeof window !== 'undefined') {
  window.addEventListener('mousemove', handleMouseMove, { passive: true })
}

// Start global sporadic scanline on mount
onMounted(() => {
  // Initial delay 5-15s so it doesn't fire immediately on load
  const initialDelay = 5000 + Math.random() * 10000
  globalScanTimer = setTimeout(() => scheduleGlobalScan(), initialDelay)
})

onUnmounted(() => {
  if (rafId) {
    cancelAnimationFrame(rafId)
  }
  if (globalScanTimer) clearTimeout(globalScanTimer)
  if (globalScanEndTimer) clearTimeout(globalScanEndTimer)
  if (typeof window !== 'undefined') {
    window.removeEventListener('mousemove', handleMouseMove)
  }
})
</script>

<style lang="scss">
@import '@/styles/variables.scss';

.app-container {
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: $bg-abyss;
}

.main-content {
  position: relative;
  z-index: 10;
  // Allow matrix rain to show through transparent areas
  pointer-events: auto;
}

// 鼠标跟随光晕 - 荧光绿
.cursor-glow {
  position: fixed;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle,
    rgba($neon-green, 0.08) 0%,
    rgba($neon-green, 0.03) 40%,
    transparent 70%
  );
  pointer-events: none;
  z-index: 5;
  transform: translate(-50%, -50%);
  will-change: left, top;
  transition: left 0.05s linear, top 0.05s linear;
}

// 扫描线效果 - 极淡的静态CRT纹理，无移动扫描线
.scanlines {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1000;
  // 极淡的静态水平纹理，仅作CRT氛围
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.015) 2px,
    rgba(0, 0, 0, 0.015) 4px
  );
  // 无移动扫描线 - 移除::before，扫描线效果由各卡片JS独立控制
}

// JS-driven global sporadic scanline
.global-scanline {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  pointer-events: none;
  z-index: 1002;
  opacity: 0;
  background: linear-gradient(180deg,
    transparent 0%,
    rgba(0, 255, 160, 0.08) 15%,
    rgba(0, 255, 160, 0.35) 40%,
    rgba(0, 255, 160, 0.6) 50%,
    rgba(0, 255, 160, 0.35) 60%,
    rgba(0, 255, 160, 0.08) 85%,
    transparent 100%
  );
  box-shadow:
    0 0 20px rgba(0, 255, 160, 0.3),
    0 0 60px rgba(0, 255, 160, 0.1);
  will-change: transform, opacity;

  &.active {
    opacity: 1;
    animation: globalScanDown var(--scan-duration, 0.7s) linear forwards;
  }

  &.active.scan-reverse {
    animation: globalScanUp var(--scan-duration, 0.7s) linear forwards;
  }
}

@keyframes globalScanDown {
  0% {
    transform: translateY(0);
    opacity: 0;
  }
  5% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(100vh);
    opacity: 0;
  }
}

@keyframes globalScanUp {
  0% {
    transform: translateY(100vh);
    opacity: 0;
  }
  5% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(0);
    opacity: 0;
  }
}

// Glitch故障效果层
.glitch-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1001;
  background: transparent;

  &::before, &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0;
    will-change: transform, opacity;
  }

  &::before {
    background: rgba($neon-red, 0.03);
    animation: glitchBefore 10s ease-in-out infinite;
  }

  &::after {
    background: rgba($neon-green, 0.03);
    animation: glitchAfter 10s ease-in-out infinite;
  }
}

@keyframes glitchBefore {
  0%, 90%, 100% { opacity: 0; transform: translateX(0); }
  92% { opacity: 1; transform: translateX(-4px); }
  94% { opacity: 0.5; transform: translateX(4px); }
  96% { opacity: 1; transform: translateX(-2px); }
  98% { opacity: 0; }
}

@keyframes glitchAfter {
  0%, 90%, 100% { opacity: 0; transform: translateX(0); }
  91% { opacity: 1; transform: translateX(4px); }
  93% { opacity: 0.5; transform: translateX(-4px); }
  95% { opacity: 1; transform: translateX(2px); }
  97% { opacity: 0; }
}

// 终端风格页面切换动画
.terminal-fade-enter-active {
  animation: terminalEnter 0.4s ease-out;
}

.terminal-fade-leave-active {
  animation: terminalLeave 0.3s ease-in;
}

@keyframes terminalEnter {
  0% {
    opacity: 0;
    transform: translateY(10px);
    filter: blur(5px) brightness(1.5);
  }
  50% {
    filter: blur(2px) brightness(1.2);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0) brightness(1);
  }
}

@keyframes terminalLeave {
  0% {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
  100% {
    opacity: 0;
    transform: translateY(-10px);
    filter: blur(3px);
  }
}

// 版本标识样式 - 终端风格
.version-tag {
  position: fixed;
  bottom: 20px;
  right: 30px;
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.9);
  border: 1px solid rgba($neon-green, 0.4);
  font-family: $font-mono;
  box-shadow: 0 0 15px rgba($neon-green, 0.15);

  .version-prefix {
    color: $neon-green;
    font-weight: bold;
  }

  .version-text {
    color: $neon-green;
  }

  .version-name {
    color: rgba($neon-green, 0.7);
    margin-left: 4px;
  }

  .version-status {
    font-size: 9px;
    padding: 2px 6px;
    background: rgba($neon-green, 0.15);
    border: 1px solid rgba($neon-green, 0.4);
    color: $neon-green;
    margin-left: 8px;
    animation: statusBlink 2s ease-in-out infinite;
  }

  @keyframes statusBlink {
    0%, 100% { opacity: 0.7; }
    50% { opacity: 1; }
  }
}
</style>
