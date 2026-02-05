<template>
  <div class="background-effects">
    <!-- Deep black background -->
    <div class="abyss-bg"></div>

    <!-- Grid background -->
    <div class="grid-bg"></div>

    <!-- Multi-layer Matrix Rain -->
    <canvas ref="matrixCanvasBg" class="matrix-canvas matrix-bg-layer"></canvas>
    <canvas ref="matrixCanvasMid" class="matrix-canvas matrix-mid-layer"></canvas>
    <canvas ref="matrixCanvasFg" class="matrix-canvas matrix-fg-layer"></canvas>

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
const matrixCanvasBg = ref(null)
const matrixCanvasMid = ref(null)
const matrixCanvasFg = ref(null)
const noiseOverlay = ref(null)
const screenFlicker = ref(null)

// Animation IDs
let bgAnimationId = null
let midAnimationId = null
let fgAnimationId = null
let noiseInterval = null
let flickerInterval = null

// Visibility state
let isVisible = true

// Matrix characters
const matrixChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()01'
const charArray = matrixChars.split('')

// Matrix Rain Layer Class - Optimized with requestAnimationFrame and reduced redraws
class MatrixRainLayer {
  constructor(canvas, config) {
    this.canvas = canvas
    this.ctx = canvas.getContext('2d', { alpha: false })
    this.config = config
    this.columns = []
    this.fontSize = config.fontSize || 16
    this.speedMultiplier = config.speedMultiplier || 1.0  // Speed multiplier for layer
    this.speedMin = config.speedMin || 0.5
    this.speedMax = config.speedMax || 1.5
    this.brightnessMin = config.brightnessMin || 0.3
    this.brightnessMax = config.brightnessMax || 0.9
    this.fadeAlpha = config.fadeAlpha || 0.05
    this.headColor = config.headColor || '#ffffff'
    this.trailColor = config.trailColor || '#00d4aa'
    this.columnDensity = config.columnDensity || 0.6  // Character column density

    // Character pool for reuse
    this.charPool = []
    this.poolSize = 100
    this.initCharPool()

    this.init()
  }

  initCharPool() {
    // Pre-generate characters for reuse
    for (let i = 0; i < this.poolSize; i++) {
      this.charPool.push(charArray[Math.floor(Math.random() * charArray.length)])
    }
  }

  getRandomChar() {
    return this.charPool[Math.floor(Math.random() * this.poolSize)]
  }

  init() {
    this.resize()
    this.initColumns()
  }

  resize() {
    this.canvas.width = window.innerWidth
    this.canvas.height = window.innerHeight
    this.initColumns()
  }

  initColumns() {
    const columnCount = Math.floor(this.canvas.width / (this.fontSize * this.columnDensity))
    this.columns = []

    for (let i = 0; i < columnCount; i++) {
      this.columns.push({
        x: i * this.fontSize * this.columnDensity,
        y: Math.random() * this.canvas.height,
        speed: (this.speedMin + Math.random() * (this.speedMax - this.speedMin)) * this.speedMultiplier,
        brightness: this.brightnessMin + Math.random() * (this.brightnessMax - this.brightnessMin),
        trail: [],
        trailLength: 5 + Math.floor(Math.random() * 15),
        charIndex: Math.floor(Math.random() * this.poolSize)
      })
    }
  }

  draw() {
    // Use semi-transparent black to create fade effect
    this.ctx.fillStyle = `rgba(10, 10, 10, ${this.fadeAlpha})`
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height)

    this.ctx.font = `${this.fontSize}px Consolas, monospace`
    this.ctx.textBaseline = 'top'

    for (let i = 0; i < this.columns.length; i++) {
      const col = this.columns[i]
      const char = this.getRandomChar()

      // Draw trail (optimized - only draw visible parts)
      const trailLen = Math.min(col.trail.length, col.trailLength)
      for (let t = 0; t < trailLen; t++) {
        const trailY = col.y - (t + 1) * this.fontSize
        if (trailY > 0 && trailY < this.canvas.height) {
          const trailOpacity = col.brightness * (1 - (t / col.trailLength)) * 0.6
          this.ctx.fillStyle = `rgba(0, 212, 170, ${trailOpacity})`
          this.ctx.shadowBlur = 0
          this.ctx.fillText(col.trail[t] || char, col.x, trailY)
        }
      }

      // Draw head character with glow effect
      const headBrightness = col.brightness
      if (headBrightness > 0.8) {
        this.ctx.fillStyle = this.headColor
        this.ctx.shadowBlur = 20
        this.ctx.shadowColor = this.trailColor
      } else if (headBrightness > 0.6) {
        this.ctx.fillStyle = this.trailColor
        this.ctx.shadowBlur = 15
        this.ctx.shadowColor = this.trailColor
      } else {
        this.ctx.fillStyle = `rgba(0, 212, 170, ${headBrightness})`
        this.ctx.shadowBlur = 8
        this.ctx.shadowColor = this.trailColor
      }

      this.ctx.fillText(char, col.x, col.y)
      this.ctx.shadowBlur = 0

      // Update trail
      col.trail.unshift(char)
      if (col.trail.length > col.trailLength) {
        col.trail.pop()
      }

      // Move with speed multiplier applied
      col.y += col.speed * this.fontSize

      // Reset when off screen
      if (col.y > this.canvas.height && Math.random() > 0.975) {
        col.y = -this.fontSize
        col.speed = (this.speedMin + Math.random() * (this.speedMax - this.speedMin)) * this.speedMultiplier
        col.brightness = this.brightnessMin + Math.random() * (this.brightnessMax - this.brightnessMin)
        col.trail = []
        col.trailLength = 5 + Math.floor(Math.random() * 15)
      }
    }
  }
}

let matrixBgLayer = null
let matrixMidLayer = null
let matrixFgLayer = null

function initMatrixRain() {
  // Background layer: slowest (0.5x speed), most transparent, largest font
  if (matrixCanvasBg.value) {
    matrixBgLayer = new MatrixRainLayer(matrixCanvasBg.value, {
      fontSize: 12,           // Smallest font (background)
      speedMultiplier: 0.5,   // 0.5x speed
      speedMin: 0.3,
      speedMax: 0.6,
      brightnessMin: 0.15,
      brightnessMax: 0.3,     // opacity 0.3
      fadeAlpha: 0.02,
      headColor: 'rgba(0, 212, 170, 0.4)',
      trailColor: '#00d4aa',
      columnDensity: 0.8
    })
  }

  // Middle layer: medium speed (1.0x), medium transparency
  if (matrixCanvasMid.value) {
    matrixMidLayer = new MatrixRainLayer(matrixCanvasMid.value, {
      fontSize: 14,           // Medium font
      speedMultiplier: 1.0,   // 1.0x speed
      speedMin: 0.5,
      speedMax: 1.0,
      brightnessMin: 0.35,
      brightnessMax: 0.5,     // opacity 0.5
      fadeAlpha: 0.04,
      headColor: 'rgba(255, 255, 255, 0.7)',
      trailColor: '#00d4aa',
      columnDensity: 0.6
    })
  }

  // Foreground layer: fastest (1.5x speed), most visible, largest font
  if (matrixCanvasFg.value) {
    matrixFgLayer = new MatrixRainLayer(matrixCanvasFg.value, {
      fontSize: 16,           // Largest font (foreground)
      speedMultiplier: 1.5,   // 1.5x speed
      speedMin: 0.8,
      speedMax: 1.5,
      brightnessMin: 0.6,
      brightnessMax: 0.8,     // opacity 0.8
      fadeAlpha: 0.06,
      headColor: '#ffffff',
      trailColor: '#00d4aa',
      columnDensity: 0.5
    })
  }

  // Animation timing - optimized for 60fps
  let bgLastTime = 0
  let midLastTime = 0
  let fgLastTime = 0

  // Background: ~12fps for slow movement
  function animateBg(currentTime) {
    bgAnimationId = requestAnimationFrame(animateBg)
    if (!isVisible) return
    if (currentTime - bgLastTime < 83) return  // ~12fps
    bgLastTime = currentTime
    if (matrixBgLayer) matrixBgLayer.draw()
  }

  // Middle: ~20fps for medium movement
  function animateMid(currentTime) {
    midAnimationId = requestAnimationFrame(animateMid)
    if (!isVisible) return
    if (currentTime - midLastTime < 50) return  // ~20fps
    midLastTime = currentTime
    if (matrixMidLayer) matrixMidLayer.draw()
  }

  // Foreground: ~30fps for fast movement
  function animateFg(currentTime) {
    fgAnimationId = requestAnimationFrame(animateFg)
    if (!isVisible) return
    if (currentTime - fgLastTime < 33) return  // ~30fps
    fgLastTime = currentTime
    if (matrixFgLayer) matrixFgLayer.draw()
  }

  animateBg(0)
  animateMid(0)
  animateFg(0)
}

function startNoiseEffect() {
  const overlay = noiseOverlay.value
  if (!overlay) return

  noiseInterval = setInterval(() => {
    if (!isVisible) return
    const intensity = 0.02 + Math.random() * 0.03
    overlay.style.opacity = intensity.toString()
  }, 100)
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
  }, 200)
}

function handleResize() {
  if (matrixBgLayer) matrixBgLayer.resize()
  if (matrixMidLayer) matrixMidLayer.resize()
  if (matrixFgLayer) matrixFgLayer.resize()
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
  if (bgAnimationId) cancelAnimationFrame(bgAnimationId)
  if (midAnimationId) cancelAnimationFrame(midAnimationId)
  if (fgAnimationId) cancelAnimationFrame(fgAnimationId)
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

.matrix-bg-layer {
  z-index: 2;
  opacity: 0.3;  // Background layer: 0.3 opacity
}

.matrix-mid-layer {
  z-index: 3;
  opacity: 0.5;  // Middle layer: 0.5 opacity
}

.matrix-fg-layer {
  z-index: 4;
  opacity: 0.8;  // Foreground layer: 0.8 opacity
  filter: brightness(1.15);
}

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
    rgba(0, 0, 0, 0.15) 0px,
    rgba(0, 0, 0, 0.15) 1px,
    transparent 1px,
    transparent 2px
  );
  animation: scanlineFlicker 0.1s steps(2) infinite;
}

@keyframes scanlineFlicker {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.25; }
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
    height: 3px;
    background: linear-gradient(90deg,
      transparent,
      rgba(0, 212, 170, 0.4),
      rgba(0, 212, 170, 0.7),
      rgba(0, 212, 170, 0.4),
      transparent
    );
    box-shadow: 0 0 15px rgba(0, 212, 170, 0.4);
    animation: scanLine 5s linear infinite;
  }
}

@keyframes scanLine {
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
  background: radial-gradient(ellipse at center, transparent 0%, rgba(10, 10, 10, 0.5) 100%);
}
</style>
