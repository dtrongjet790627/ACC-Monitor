<template>
  <div class="stat-card" @click="handleClick">
    <!-- 全息投影叠加层 -->
    <div class="hologram-layer"></div>

    <!-- 脉冲波纹效果 - GPU加速版 -->
    <div class="pulse-ring pulse-ring-1"></div>
    <div class="pulse-ring pulse-ring-2"></div>
    <div class="pulse-ring pulse-ring-3"></div>

    <!-- 边角装饰 -->
    <div class="corner corner-tl"></div>
    <div class="corner corner-tr"></div>
    <div class="corner corner-bl"></div>
    <div class="corner corner-br"></div>

    <!-- 边框流光效果 -->
    <div class="border-flow"></div>

    <!-- 扫描线效果 -->
    <div class="scan-line"></div>

    <!-- 数值显示 -->
    <div class="stat-value" :class="colorClass">
      <span class="value-number glitch-text" :data-text="animatedValue" ref="valueRef">{{ animatedValue }}</span>
    </div>

    <!-- 标签 -->
    <div class="stat-label">{{ label }}</div>

    <!-- 能量波纹 -->
    <div class="energy-wave"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'

const props = defineProps({
  value: {
    type: Number,
    required: true
  },
  label: {
    type: String,
    required: true
  },
  color: {
    type: String,
    default: 'cyan',
    validator: (value) => ['cyan', 'green', 'orange', 'red', 'purple', 'blue'].includes(value)
  },
  animate: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['click'])

const animatedValue = ref(0)
const valueRef = ref(null)

const colorClass = computed(() => props.color)

function animateValue(start, end, duration) {
  if (!props.animate) {
    animatedValue.value = end
    return
  }

  const startTime = performance.now()
  const diff = end - start

  function update(currentTime) {
    const elapsed = currentTime - startTime
    const progress = Math.min(elapsed / duration, 1)

    // 更强的缓动函数
    const easeOut = 1 - Math.pow(1 - progress, 4)
    animatedValue.value = Math.round(start + diff * easeOut)

    if (progress < 1) {
      requestAnimationFrame(update)
    }
  }

  requestAnimationFrame(update)
}

onMounted(() => {
  animateValue(0, props.value, 1200)
})

watch(() => props.value, (newVal, oldVal) => {
  animateValue(oldVal, newVal, 600)
})

function handleClick() {
  emit('click')
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

// 统一边框风格 - 荧光绿主题（豆包反馈：边框风格不统一）
.stat-card {
  background: $bg-card;
  border: 2px solid rgba($neon-green, 0.4);
  padding: 28px 22px;
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease, border-color 0.3s ease;
  cursor: pointer;
  will-change: transform;
  box-shadow:
    0 0 20px rgba($neon-green, 0.15),
    0 0 40px rgba($neon-green, 0.08),
    inset 0 0 40px rgba(0, 0, 0, 0.3);

  // 全息投影叠加层 - 统一绿色主题
  .hologram-layer {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background:
      linear-gradient(135deg, rgba($neon-green, 0.03) 0%, transparent 50%, rgba($neon-green, 0.02) 100%),
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba($neon-green, 0.015) 2px,
        rgba($neon-green, 0.015) 4px
      );
    pointer-events: none;
    z-index: 1;
    animation: holoFlicker 4s ease-in-out infinite;
  }

  @keyframes holoFlicker {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
    52% { opacity: 1; }
    54% { opacity: 0.8; }
    56% { opacity: 1; }
  }

  // 边框流光效果 - 统一绿色主题
  .border-flow {
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(90deg, transparent, $neon-green, rgba($neon-green, 0.6), $neon-green, transparent);
    background-size: 400% 100%;
    z-index: -1;
    animation: borderFlowAnim 3s linear infinite;
    opacity: 0.4;
    will-change: background-position;

    &::before {
      content: '';
      position: absolute;
      top: 2px;
      left: 2px;
      right: 2px;
      bottom: 2px;
      background: $bg-card;
    }
  }

  @keyframes borderFlowAnim {
    0% { background-position: 100% 0; }
    100% { background-position: -100% 0; }
  }

  // 脉冲波纹效果 - 统一绿色主题
  .pulse-ring {
    position: absolute;
    top: 50%;
    left: 50%;
    width: 120%;
    height: 200%;
    border: 2px solid rgba($neon-green, 0.4);
    border-radius: 50%;
    transform: translate(-50%, -50%) scale(0.3);
    opacity: 0;
    pointer-events: none;
    will-change: transform, opacity;
  }

  .pulse-ring-1 {
    animation: pulseWave 2.5s ease-out infinite;
  }

  .pulse-ring-2 {
    animation: pulseWave 2.5s ease-out 0.8s infinite;
    border-color: rgba($neon-green, 0.3);
  }

  .pulse-ring-3 {
    animation: pulseWave 2.5s ease-out 1.6s infinite;
    border-color: rgba($neon-green, 0.2);
  }

  // 边角装饰 - 统一绿色主题
  .corner {
    position: absolute;
    width: 14px;
    height: 14px;
    z-index: 10;

    &::before, &::after {
      content: '';
      position: absolute;
      background: $neon-green;
      opacity: 0.8;
      transition: all 0.3s ease;
      filter: drop-shadow(0 0 3px $neon-green);
    }

    &-tl {
      top: 0;
      left: 0;
      &::before { width: 14px; height: 2px; top: 0; left: 0; }
      &::after { width: 2px; height: 14px; top: 0; left: 0; }
    }

    &-tr {
      top: 0;
      right: 0;
      &::before { width: 14px; height: 2px; top: 0; right: 0; }
      &::after { width: 2px; height: 14px; top: 0; right: 0; }
    }

    &-bl {
      bottom: 0;
      left: 0;
      &::before { width: 14px; height: 2px; bottom: 0; left: 0; }
      &::after { width: 2px; height: 14px; bottom: 0; left: 0; }
    }

    &-br {
      bottom: 0;
      right: 0;
      &::before { width: 14px; height: 2px; bottom: 0; right: 0; }
      &::after { width: 2px; height: 14px; bottom: 0; right: 0; }
    }
  }

  // 扫描线效果 - 统一绿色主题
  .scan-line {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, transparent, rgba($neon-green, 0.9), rgba($neon-green, 0.6), transparent);
    transform: translateY(-100%);
    opacity: 0;
    will-change: transform, opacity;
    animation: scanDown 3s ease-in-out infinite;
  }

  // 能量波纹 - 统一绿色主题
  .energy-wave {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 3px;
    background: linear-gradient(90deg, transparent, $neon-green, rgba($neon-green, 0.6), transparent);
    animation: waveMove 2s linear infinite;
    will-change: background-position;
    background-size: 200% 100%;
  }

  @keyframes waveMove {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  // 顶部流光边框 - 统一绿色主题
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, $neon-green, rgba($neon-green, 0.6), $neon-green, transparent);
    background-size: 200% 100%;
    animation: borderFlow 2.5s linear infinite;
    will-change: background-position;
  }

  // 底部发光线 - 统一绿色主题
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, $neon-green, transparent);
    animation: bottomGlow 3s ease-in-out infinite;
    will-change: opacity;
  }

  @keyframes bottomGlow {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.8; }
  }

  // Hover效果 - 统一绿色主题
  &:hover {
    border-color: $neon-green;
    transform: translateY(-8px) scale(1.02);
    box-shadow:
      0 0 30px rgba($neon-green, 0.3),
      0 0 60px rgba($neon-green, 0.15),
      inset 0 0 40px rgba(0, 0, 0, 0.3);

    .corner::before, .corner::after {
      background: #fff;
      opacity: 1;
      filter: drop-shadow(0 0 8px $neon-green);
    }

    .pulse-ring {
      border-color: rgba($neon-green, 0.6);
    }

    .hologram-layer {
      animation: holoFlickerFast 0.5s ease-in-out infinite;
    }
  }

  @keyframes holoFlickerFast {
    0%, 100% { opacity: 1; }
    25% { opacity: 0.7; }
    50% { opacity: 1; }
    75% { opacity: 0.8; }
  }
}

// 边框发光动画 - 统一绿色主题
@keyframes borderGlow {
  0%, 100% {
    box-shadow: inset 0 0 25px rgba($neon-green, 0.1);
  }
  50% {
    box-shadow: inset 0 0 35px rgba($neon-green, 0.2);
  }
}

// 脉冲波纹动画 - 仅使用transform和opacity
@keyframes pulseWave {
  0% {
    transform: translate(-50%, -50%) scale(0.3);
    opacity: 0.7;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0;
  }
}

// 扫描线动画
@keyframes scanDown {
  0%, 100% {
    transform: translateY(-100%);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  50% {
    transform: translateY(4000%);
    opacity: 1;
  }
  60%, 100% {
    opacity: 0;
  }
}

// 边框流光动画
@keyframes borderFlow {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

// 数值样式 - 带Glitch效果
.stat-value {
  font-size: 52px;
  font-weight: bold;
  margin-bottom: 12px;
  display: inline-block;
  position: relative;
  will-change: filter;
  z-index: 5;

  // Glitch效果
  .glitch-text {
    position: relative;
    display: inline-block;

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
      animation: glitchBefore 6s ease-in-out infinite;
      clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
    }

    &::after {
      color: $neon-cyan;
      animation: glitchAfter 6s ease-in-out infinite;
      clip-path: polygon(0 65%, 100% 65%, 100% 100%, 0 100%);
    }
  }

  @keyframes glitchBefore {
    0%, 90%, 100% { opacity: 0; transform: translateX(0); }
    92% { opacity: 0.8; transform: translateX(-3px); }
    94% { opacity: 0.5; transform: translateX(3px); }
    96% { opacity: 0.8; transform: translateX(-2px); }
    98% { opacity: 0; }
  }

  @keyframes glitchAfter {
    0%, 90%, 100% { opacity: 0; transform: translateX(0); }
    91% { opacity: 0.8; transform: translateX(3px); }
    93% { opacity: 0.5; transform: translateX(-3px); }
    95% { opacity: 0.8; transform: translateX(2px); }
    97% { opacity: 0; }
  }

  &.cyan {
    color: $neon-cyan;
    animation: glowPulse-cyan 2s ease-in-out infinite;
    text-shadow: 0 0 10px rgba($neon-cyan, 0.8), 0 0 20px rgba($neon-cyan, 0.5);
  }

  &.green {
    color: $neon-green;
    animation: glowPulse-green 2s ease-in-out infinite;
    text-shadow: 0 0 10px rgba($neon-green, 0.8), 0 0 20px rgba($neon-green, 0.5);
  }

  &.orange {
    color: $neon-orange;
    animation: glowPulse-orange 2s ease-in-out infinite;
    text-shadow: 0 0 10px rgba($neon-orange, 0.8), 0 0 20px rgba($neon-orange, 0.5);
  }

  &.red {
    color: $neon-red;
    animation: glowPulse-red 2s ease-in-out infinite;
    text-shadow: 0 0 10px rgba($neon-red, 0.8), 0 0 20px rgba($neon-red, 0.5);
  }

  &.purple {
    color: $neon-purple;
    animation: glowPulse-purple 2s ease-in-out infinite;
    text-shadow: 0 0 10px rgba($neon-purple, 0.8), 0 0 20px rgba($neon-purple, 0.5);
  }

  &.blue {
    color: $neon-blue;
    animation: glowPulse-blue 2s ease-in-out infinite;
    text-shadow: 0 0 10px rgba($neon-blue, 0.8), 0 0 20px rgba($neon-blue, 0.5);
  }
}

// 发光脉冲动画 - 使用filter代替text-shadow提升性能
@keyframes glowPulse-cyan {
  0%, 100% { filter: drop-shadow(0 0 10px rgba($neon-cyan, 0.6)) drop-shadow(0 0 20px rgba($neon-cyan, 0.3)); }
  50% { filter: drop-shadow(0 0 20px rgba($neon-cyan, 0.9)) drop-shadow(0 0 40px rgba($neon-cyan, 0.5)); }
}

@keyframes glowPulse-green {
  0%, 100% { filter: drop-shadow(0 0 10px rgba($neon-green, 0.6)) drop-shadow(0 0 20px rgba($neon-green, 0.3)); }
  50% { filter: drop-shadow(0 0 20px rgba($neon-green, 0.9)) drop-shadow(0 0 40px rgba($neon-green, 0.5)); }
}

@keyframes glowPulse-orange {
  0%, 100% { filter: drop-shadow(0 0 10px rgba($neon-orange, 0.6)) drop-shadow(0 0 20px rgba($neon-orange, 0.3)); }
  50% { filter: drop-shadow(0 0 20px rgba($neon-orange, 0.9)) drop-shadow(0 0 40px rgba($neon-orange, 0.5)); }
}

@keyframes glowPulse-red {
  0%, 100% { filter: drop-shadow(0 0 10px rgba($neon-red, 0.6)) drop-shadow(0 0 20px rgba($neon-red, 0.3)); }
  50% { filter: drop-shadow(0 0 20px rgba($neon-red, 0.9)) drop-shadow(0 0 40px rgba($neon-red, 0.5)); }
}

@keyframes glowPulse-purple {
  0%, 100% { filter: drop-shadow(0 0 10px rgba($neon-purple, 0.6)) drop-shadow(0 0 20px rgba($neon-purple, 0.3)); }
  50% { filter: drop-shadow(0 0 20px rgba($neon-purple, 0.9)) drop-shadow(0 0 40px rgba($neon-purple, 0.5)); }
}

@keyframes glowPulse-blue {
  0%, 100% { filter: drop-shadow(0 0 10px rgba($neon-blue, 0.6)) drop-shadow(0 0 20px rgba($neon-blue, 0.3)); }
  50% { filter: drop-shadow(0 0 20px rgba($neon-blue, 0.9)) drop-shadow(0 0 40px rgba($neon-blue, 0.5)); }
}

// 标签样式 - 统一绿色主题
.stat-label {
  font-size: 11px;
  color: $text-secondary;
  text-transform: uppercase;
  letter-spacing: 3px;
  position: relative;
  z-index: 5;
  font-family: $font-mono;

  &::before {
    content: '[ ';
    color: $neon-green;
    opacity: 0.6;
  }

  &::after {
    content: ' ]';
    color: $neon-green;
    opacity: 0.6;
  }
}
</style>
