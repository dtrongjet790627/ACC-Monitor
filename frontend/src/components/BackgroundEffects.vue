<template>
  <div class="background-effects">
    <!-- Deep black background -->
    <div class="abyss-bg"></div>

    <!-- Grid background -->
    <div class="grid-bg"></div>

    <!-- Single unified Matrix Rain canvas (merged 3 layers) -->
    <canvas ref="matrixCanvas" class="matrix-canvas matrix-unified-layer"></canvas>

    <!-- CRT scanlines -->
    <div class="crt-scanlines"></div>

    <!-- Noise overlay -->
    <div class="noise-overlay" ref="noiseOverlay"></div>

    <!-- Screen flicker -->
    <div class="screen-flicker" ref="screenFlicker"></div>

    <!-- Scan line -->
    <div class="scan-overlay">
      <div class="scan-line"></div>
    </div>

    <!-- Corner decorations -->
    <div class="corner-decor top-left">
      <span class="corner-text">[SYSTEM]</span>
    </div>
    <div class="corner-decor top-right">
      <span class="corner-text">[ACTIVE]</span>
    </div>
    <div class="corner-decor bottom-left">
      <span class="corner-text">>_ INIT</span>
    </div>
    <div class="corner-decor bottom-right">
      <span class="corner-text">$ ./ACC</span>
    </div>

    <!-- Gradient overlay -->
    <div class="gradient-overlay"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// Canvas refs
const matrixCanvas = ref(null)
const noiseOverlay = ref(null)
const screenFlicker = ref(null)

// Animation IDs
let animationId = null
let noiseInterval = null
let flickerInterval = null

// Visibility state
let isVisible = true

// Matrix characters
const matrixChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()01'
const charArray = matrixChars.split('')

// Matrix Rain Layer Config - used by unified renderer (NO shadowBlur)
class MatrixRainLayer {
  constructor(config) {
    this.columns = []
    this.fontSize = config.fontSize || 16
    this.speedMultiplier = config.speedMultiplier || 1.0
    this.speedMin = config.speedMin || 0.5
    this.speedMax = config.speedMax || 1.5
    this.brightnessMin = config.brightnessMin || 0.3
    this.brightnessMax = config.brightnessMax || 0.9
    this.headColor = config.headColor || '#ffffff'
    this.headColorBright = config.headColorBright || '#00ffcc'
    this.trailColor = config.trailColor || '#00d4aa'
    this.columnDensity = config.columnDensity || 0.6
    this.opacity = config.opacity || 1.0

    // Character pool for reuse
    this.charPool = []
    this.poolSize = 100
    this.initCharPool()
  }

  initCharPool() {
    for (let i = 0; i < this.poolSize; i++) {
      this.charPool.push(charArray[Math.floor(Math.random() * charArray.length)])
    }
  }

  getRandomChar() {
    return this.charPool[Math.floor(Math.random() * this.poolSize)]
  }

  initColumns(canvasWidth, canvasHeight) {
    const columnCount = Math.floor(canvasWidth / (this.fontSize * this.columnDensity))
    this.columns = []

    for (let i = 0; i < columnCount; i++) {
      this.columns.push({
        x: i * this.fontSize * this.columnDensity,
        y: Math.random() * canvasHeight,
        speed: (this.speedMin + Math.random() * (this.speedMax - this.speedMin)) * this.speedMultiplier,
        brightness: this.brightnessMin + Math.random() * (this.brightnessMax - this.brightnessMin),
        trail: [],
        trailLength: 5 + Math.floor(Math.random() * 15),
        charIndex: Math.floor(Math.random() * this.poolSize)
      })
    }
  }

  draw(ctx, canvasWidth, canvasHeight) {
    ctx.font = `${this.fontSize}px Consolas, monospace`
    ctx.textBaseline = 'top'
    ctx.globalAlpha = this.opacity

    for (let i = 0; i < this.columns.length; i++) {
      const col = this.columns[i]
      const char = this.getRandomChar()

      // Draw trail - NO shadowBlur, just color opacity for performance
      const trailLen = Math.min(col.trail.length, col.trailLength)
      for (let t = 0; t < trailLen; t++) {
        const trailY = col.y - (t + 1) * this.fontSize
        if (trailY > 0 && trailY < canvasHeight) {
          const trailOpacity = col.brightness * (1 - (t / col.trailLength)) * 0.6
          ctx.fillStyle = `rgba(0, 212, 170, ${trailOpacity})`
          ctx.fillText(col.trail[t] || char, col.x, trailY)
        }
      }

      // Draw head character - use brighter colors instead of shadowBlur
      const headBrightness = col.brightness
      if (headBrightness > 0.8) {
        ctx.fillStyle = this.headColor  // White for brightest heads
      } else if (headBrightness > 0.6) {
        ctx.fillStyle = this.headColorBright  // Bright cyan-green instead of shadowBlur
      } else {
        ctx.fillStyle = `rgba(0, 212, 170, ${headBrightness})`
      }

      ctx.fillText(char, col.x, col.y)

      // Update trail
      col.trail.unshift(char)
      if (col.trail.length > col.trailLength) {
        col.trail.pop()
      }

      // Move with speed multiplier applied
      col.y += col.speed * this.fontSize

      // Reset when off screen
      if (col.y > canvasHeight && Math.random() > 0.975) {
        col.y = -this.fontSize
        col.speed = (this.speedMin + Math.random() * (this.speedMax - this.speedMin)) * this.speedMultiplier
        col.brightness = this.brightnessMin + Math.random() * (this.brightnessMax - this.brightnessMin)
        col.trail = []
        col.trailLength = 5 + Math.floor(Math.random() * 15)
      }
    }

    ctx.globalAlpha = 1.0
  }
}

let bgLayer = null
let midLayer = null
let fgLayer = null
let ctx = null

function initMatrixRain() {
  const canvas = matrixCanvas.value
  if (!canvas) return

  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
  ctx = canvas.getContext('2d', { alpha: false })

  // Background layer config
  bgLayer = new MatrixRainLayer({
    fontSize: 12,
    speedMultiplier: 0.5,
    speedMin: 0.3,
    speedMax: 0.6,
    brightnessMin: 0.25,
    brightnessMax: 0.45,
    headColor: 'rgba(0, 212, 170, 0.5)',
    headColorBright: 'rgba(0, 255, 204, 0.5)',
    trailColor: '#00d4aa',
    columnDensity: 0.8,
    opacity: 0.45
  })
  bgLayer.initColumns(canvas.width, canvas.height)

  // Middle layer config
  midLayer = new MatrixRainLayer({
    fontSize: 14,
    speedMultiplier: 1.0,
    speedMin: 0.5,
    speedMax: 1.0,
    brightnessMin: 0.45,
    brightnessMax: 0.65,
    headColor: 'rgba(255, 255, 255, 0.8)',
    headColorBright: '#00ffcc',
    trailColor: '#00d4aa',
    columnDensity: 0.6,
    opacity: 0.65
  })
  midLayer.initColumns(canvas.width, canvas.height)

  // Foreground layer config
  fgLayer = new MatrixRainLayer({
    fontSize: 16,
    speedMultiplier: 1.5,
    speedMin: 0.8,
    speedMax: 1.5,
    brightnessMin: 0.7,
    brightnessMax: 0.95,
    headColor: '#ffffff',
    headColorBright: '#00ffcc',
    trailColor: '#00d4aa',
    columnDensity: 0.5,
    opacity: 0.9
  })
  fgLayer.initColumns(canvas.width, canvas.height)

  // Single unified animation loop at ~16fps (60ms interval)
  let lastTime = 0
  const frameInterval = 60  // ~16fps - matrix rain does not need high fps

  function animate(currentTime) {
    animationId = requestAnimationFrame(animate)
    if (!isVisible) return
    if (currentTime - lastTime < frameInterval) return
    lastTime = currentTime

    // Fade overlay for trail effect
    ctx.fillStyle = 'rgba(10, 10, 10, 0.04)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw all 3 layers in order: bg -> mid -> fg
    if (bgLayer) bgLayer.draw(ctx, canvas.width, canvas.height)
    if (midLayer) midLayer.draw(ctx, canvas.width, canvas.height)
    if (fgLayer) fgLayer.draw(ctx, canvas.width, canvas.height)
  }

  animate(0)
}

function startNoiseEffect() {
  const overlay = noiseOverlay.value
  if (!overlay) return

  noiseInterval = setInterval(() => {
    if (!isVisible) return
    const intensity = 0.02 + Math.random() * 0.03
    overlay.style.opacity = intensity.toString()
  }, 500)
}

function startFlickerEffect() {
  const flicker = screenFlicker.value
  if (!flicker) return

  flickerInterval = setInterval(() => {
    if (!isVisible) return
    if (Math.random() > 0.95) {
      flicker.classList.add('active')
      setTimeout(() => {
        flicker.classList.remove('active')
      }, 50 + Math.random() * 100)
    }
  }, 1000)
}

function handleResize() {
  const canvas = matrixCanvas.value
  if (!canvas) return
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
  if (bgLayer) bgLayer.initColumns(canvas.width, canvas.height)
  if (midLayer) midLayer.initColumns(canvas.width, canvas.height)
  if (fgLayer) fgLayer.initColumns(canvas.width, canvas.height)
}

function handleVisibilityChange() {
  isVisible = !document.hidden
}

onMounted(() => {
  initMatrixRain()
  startNoiseEffect()
  startFlickerEffect()

  window.addEventListener('resize', handleResize)
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (noiseInterval) clearInterval(noiseInterval)
  if (flickerInterval) clearInterval(flickerInterval)

  window.removeEventListener('resize', handleResize)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.background-effects {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.abyss-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: #0a0a0a;
  z-index: 0;
}

.grid-bg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  background-image:
    linear-gradient(rgba(0, 25, 0, 0.9) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 25, 0, 0.9) 1px, transparent 1px);
  background-size: 20px 20px;
  opacity: 0.5;
}

.matrix-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.matrix-unified-layer {
  z-index: 2;
  opacity: 1.0;
  // Use CSS filter for subtle glow instead of per-character shadowBlur (GPU composited once)
  filter: blur(0.5px) brightness(1.1);
}

// Global CRT scanlines - extremely subtle static texture only
.crt-scanlines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 100;
  pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.03) 0px,
    rgba(0, 0, 0, 0.03) 1px,
    transparent 1px,
    transparent 2px
  );
  // Static texture, no animation - scanline effects are JS-driven per card
  opacity: 0.05;
}

.noise-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 101;
  pointer-events: none;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}

.screen-flicker {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 102;
  pointer-events: none;
  background: rgba(0, 212, 170, 0.02);
  opacity: 0;

  &.active {
    opacity: 1;
    animation: flickerPulse 0.1s ease-out;
  }
}

@keyframes flickerPulse {
  0% { opacity: 0; }
  20% { opacity: 0.8; }
  40% { opacity: 0.3; }
  60% { opacity: 0.6; }
  80% { opacity: 0.2; }
  100% { opacity: 0; }
}

.scan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10;
  pointer-events: none;

  .scan-line {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg,
      transparent,
      rgba(0, 212, 170, 0.08),
      rgba(0, 212, 170, 0.12),
      rgba(0, 212, 170, 0.08),
      transparent
    );
    // Very slow ambient sweep, barely visible - not competing with card effects
    animation: scanLineGlobal 40s linear infinite reverse;
    opacity: 0.15;
  }
}

@keyframes scanLineGlobal {
  0% { transform: translateY(0); }
  100% { transform: translateY(100vh); }
}

.corner-decor {
  position: absolute;
  z-index: 15;
  font-family: $font-mono;
  font-size: 10px;
  letter-spacing: 2px;

  .corner-text {
    color: rgba(0, 212, 170, 0.4);
    text-shadow: 0 0 5px rgba(0, 212, 170, 0.3);
  }

  &::before, &::after {
    content: '';
    position: absolute;
    background: rgba(0, 212, 170, 0.5);
  }

  &.top-left {
    top: 20px;
    left: 20px;
    &::before { width: 60px; height: 2px; top: -10px; left: 0; }
    &::after { width: 2px; height: 60px; top: -10px; left: 0; }
  }

  &.top-right {
    top: 20px;
    right: 20px;
    &::before { width: 60px; height: 2px; top: -10px; right: 0; }
    &::after { width: 2px; height: 60px; top: -10px; right: 0; }
  }

  &.bottom-left {
    bottom: 20px;
    left: 20px;
    &::before { width: 60px; height: 2px; bottom: -10px; left: 0; }
    &::after { width: 2px; height: 60px; bottom: -10px; left: 0; }
  }

  &.bottom-right {
    bottom: 20px;
    right: 20px;
    &::before { width: 60px; height: 2px; bottom: -10px; right: 0; }
    &::after { width: 2px; height: 60px; bottom: -10px; right: 0; }
  }
}

.gradient-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 8;
  // Reduced center darkening to show more matrix rain through foreground
  background: radial-gradient(ellipse at center, transparent 0%, rgba(10, 10, 10, 0.20) 100%);
}
</style>
