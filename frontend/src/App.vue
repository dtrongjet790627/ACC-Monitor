<template>
  <div class="app-container">
    <!-- 背景特效层 - 代码雨 + 网格 -->
    <BackgroundEffects />

    <!-- 扫描线效果 -->
    <div class="scanlines"></div>

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
import { ref, computed, onUnmounted } from 'vue'
import BackgroundEffects from '@/components/BackgroundEffects.vue'
import ToastContainer from '@/components/ToastContainer.vue'

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

onUnmounted(() => {
  if (rafId) {
    cancelAnimationFrame(rafId)
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('mousemove', handleMouseMove)
  }
})
</script>

<style lang="scss">
@import '@/styles/variables.scss';

.app-container {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: $bg-abyss;
}

.main-content {
  position: relative;
  z-index: 10;
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
  mix-blend-mode: screen;
  will-change: left, top;
  transition: left 0.05s linear, top 0.05s linear;
}

// 扫描线效果
.scanlines {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1000;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0, 0, 0, 0.03) 2px,
    rgba(0, 0, 0, 0.03) 4px
  );

  // 扫描线移动
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg,
      transparent,
      rgba($neon-green, 0.4),
      rgba($neon-green, 0.6),
      rgba($neon-green, 0.4),
      transparent
    );
    animation: scanMove 5s linear infinite;
    will-change: transform;
  }
}

@keyframes scanMove {
  0% { transform: translateY(0); }
  100% { transform: translateY(100vh); }
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
