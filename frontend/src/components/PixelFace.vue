<template>
  <div class="guardian-container">
    <!-- Corner decorations -->
    <div class="corner-decor top-left"></div>
    <div class="corner-decor top-right"></div>
    <div class="corner-decor bottom-left"></div>
    <div class="corner-decor bottom-right"></div>

    <!-- Glow effect behind image -->
    <div class="guardian-glow"></div>

    <!-- Guardian wrapper for CRT effects -->
    <div class="guardian-wrapper" :class="{ 'glitch-active': glitchActive }">
      <!-- Guardian image with CRT effects -->
      <img
        src="@/assets/hacker-guardian.png"
        alt="System Guardian"
        class="guardian-image"
      />

      <!-- Noise overlay on image -->
      <div class="image-noise"></div>

      <!-- Scanline moving through image -->
      <div class="image-scanline"></div>

      <!-- Eye overlays for blink effect -->
      <div class="eye-overlay left-eye"></div>
      <div class="eye-overlay right-eye"></div>

      <!-- Mouth overlay for talking effect -->
      <div class="mouth-overlay"></div>
    </div>

    <!-- Status label -->
    <div class="guardian-label" :class="{ active: isOnline }">
      <span class="status-dot"></span>
      <span class="status-text">SYSTEM GUARDIAN {{ isOnline ? 'ONLINE' : 'OFFLINE' }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
  isOnline: {
    type: Boolean,
    default: true
  }
})

// --- Glitch Fade: random appear/disappear effect ---
const glitchActive = ref(false)
let glitchTimer = null

function scheduleGlitch() {
  // Random interval between 3-8 seconds
  const delay = 3000 + Math.random() * 5000
  glitchTimer = setTimeout(() => {
    glitchActive.value = true
    // Duration between 150-400ms
    const duration = 150 + Math.random() * 250
    setTimeout(() => {
      glitchActive.value = false
      scheduleGlitch()
    }, duration)
  }, delay)
}

onMounted(() => {
  scheduleGlitch()
})

onUnmounted(() => {
  if (glitchTimer) clearTimeout(glitchTimer)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.guardian-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(180deg, rgba(0, 10, 20, 0.30) 0%, rgba(0, 5, 15, 0.35) 100%);
  border: 1px solid rgba(0, 212, 170, 0.3);
  overflow: hidden;
}

// Corner decorations - matching server card style
.corner-decor {
  position: absolute;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(0, 212, 170, 0.6);
  z-index: 10;
  pointer-events: none;

  &.top-left {
    top: 0;
    left: 0;
    border-right: none;
    border-bottom: none;
  }
  &.top-right {
    top: 0;
    right: 0;
    border-left: none;
    border-bottom: none;
  }
  &.bottom-left {
    bottom: 0;
    left: 0;
    border-right: none;
    border-top: none;
  }
  &.bottom-right {
    bottom: 0;
    right: 0;
    border-left: none;
    border-top: none;
  }
}

// Glow effect with breathing animation
.guardian-glow {
  position: absolute;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at center 40%, rgba(0, 212, 170, 0.25) 0%, rgba(0, 255, 200, 0.1) 30%, transparent 70%);
  pointer-events: none;
  animation: glowBreath 3s ease-in-out infinite;
}

@keyframes glowBreath {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}

// Guardian wrapper - contains the image and overlays
.guardian-wrapper {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
}

// Guardian image with CRT signal effects - NO position movement
.guardian-image {
  position: relative;
  width: 100%;
  height: auto;
  max-height: 220px;
  object-fit: contain;
  // CRT signal animation - only opacity and filter changes, no translate
  animation: crtSignal 5s ease-in-out infinite;
  will-change: transform, opacity, filter;
  // Base CRT filter - single drop-shadow for performance
  filter:
    contrast(1.2)
    brightness(1.15)
    drop-shadow(0 0 25px rgba(0, 212, 170, 0.5));
}

// CRT Signal animation - optimized: max 1 drop-shadow per keyframe for performance
@keyframes crtSignal {
  0%, 100% {
    opacity: 1;
    transform: translateX(0) skewX(0deg);
    filter:
      contrast(1.2)
      brightness(1.15)
      drop-shadow(0 0 25px rgba(0, 212, 170, 0.5));
  }
  // Normal glow pulse
  25% {
    opacity: 1;
    transform: translateX(0) skewX(0deg);
    filter:
      contrast(1.2)
      brightness(1.2)
      drop-shadow(0 0 30px rgba(0, 212, 170, 0.7));
  }
  50% {
    opacity: 1;
    transform: translateX(0) skewX(0deg);
    filter:
      contrast(1.2)
      brightness(1.15)
      drop-shadow(0 0 25px rgba(0, 212, 170, 0.5));
  }
  75% {
    opacity: 1;
    transform: translateX(0) skewX(0deg);
    filter:
      contrast(1.25)
      brightness(1.18)
      drop-shadow(0 0 28px rgba(0, 212, 170, 0.6));
  }
  // --- Signal interference burst (87%-97%) ---
  87% {
    opacity: 1;
    transform: translateX(0) skewX(0deg);
    filter:
      contrast(1.2)
      brightness(1.15)
      drop-shadow(0 0 25px rgba(0, 212, 170, 0.5));
  }
  88% {
    opacity: 0.6;
    transform: translateX(6px) skewX(2deg);
    filter:
      contrast(1.5)
      brightness(1.3)
      saturate(1.8)
      drop-shadow(-3px 0 rgba(255, 0, 0, 0.6));
  }
  89% {
    opacity: 0.9;
    transform: translateX(-3px) skewX(-1deg);
    filter:
      contrast(1.3)
      brightness(1.2)
      drop-shadow(0 0 20px rgba(0, 212, 170, 0.5));
  }
  90% {
    opacity: 0.4;
    transform: translateX(4px) skewX(3deg);
    filter:
      contrast(1.6)
      brightness(1.4)
      saturate(2.0)
      drop-shadow(3px 0 rgba(0, 255, 255, 0.7));
  }
  // Complete disappearance flash
  91% {
    opacity: 0;
    transform: translateX(-8px) skewX(-4deg);
    filter:
      contrast(2.0)
      brightness(0.5)
      saturate(0.5);
  }
  92% {
    opacity: 0.85;
    transform: translateX(2px) skewX(1deg);
    filter:
      contrast(1.0)
      brightness(0.9)
      drop-shadow(0 0 15px rgba(0, 212, 170, 0.4));
  }
  93% {
    opacity: 1;
    transform: translateX(0) skewX(0deg);
    filter:
      contrast(1.2)
      brightness(1.15)
      drop-shadow(0 0 25px rgba(0, 212, 170, 0.5));
  }
  94% {
    opacity: 0.3;
    transform: translateX(-5px) skewX(-3deg);
    filter:
      contrast(1.8)
      brightness(1.5)
      saturate(2.5)
      drop-shadow(-3px 0 rgba(255, 0, 0, 0.8));
  }
  95% {
    opacity: 1;
    transform: translateX(3px) skewX(0deg);
    filter:
      contrast(1.2)
      brightness(1.15)
      drop-shadow(0 0 25px rgba(0, 212, 170, 0.5));
  }
  96% {
    opacity: 0.7;
    transform: translateX(-4px) skewX(2deg);
    filter:
      contrast(1.4)
      brightness(1.25)
      saturate(1.5)
      drop-shadow(3px 0 rgba(0, 255, 255, 0.6));
  }
  97% {
    opacity: 1;
    transform: translateX(0) skewX(0deg);
    filter:
      contrast(1.2)
      brightness(1.15)
      drop-shadow(0 0 25px rgba(0, 212, 170, 0.5));
  }
}

// Noise overlay on the image (not background)
.image-noise {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 3;
  opacity: 0.12;
  mix-blend-mode: overlay;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  animation: noiseFlicker 2s steps(4) infinite;
}

@keyframes noiseFlicker {
  0% { opacity: 0.1; }
  25% { opacity: 0.15; }
  50% { opacity: 0.08; }
  75% { opacity: 0.12; }
  100% { opacity: 0.1; }
}

// Scanline moving through the image - independent timing (3.7s, bottom-to-top)
.image-scanline {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(0, 212, 170, 0.3) 20%,
    rgba(0, 255, 200, 0.6) 50%,
    rgba(0, 212, 170, 0.3) 80%,
    transparent 100%
  );
  animation: scanDownPixelFace 3.7s linear infinite reverse;
  z-index: 4;
  pointer-events: none;
}

@keyframes scanDownPixelFace {
  0% {
    top: -2px;
    opacity: 0.8;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    top: 100%;
    opacity: 0.8;
  }
}

// Eye overlays for blink effect
.eye-overlay {
  position: absolute;
  width: 12px;
  height: 6px;
  background: rgba(0, 10, 20, 0.95);
  border-radius: 50%;
  transform-origin: center;
  animation: blink 4s ease-in-out infinite;
  opacity: 0;
  pointer-events: none;
  z-index: 5;

  // Left eye position
  &.left-eye {
    top: 38%;
    left: 38%;
  }

  // Right eye position
  &.right-eye {
    top: 38%;
    left: 55%;
  }
}

@keyframes blink {
  0%, 92%, 100% {
    opacity: 0;
    transform: scaleY(0);
  }
  94%, 98% {
    opacity: 1;
    transform: scaleY(1);
  }
}

// Mouth overlay for talking effect
.mouth-overlay {
  position: absolute;
  top: 58%;
  left: 47%;
  width: 18px;
  height: 4px;
  background: rgba(0, 10, 20, 0.9);
  border-radius: 2px;
  transform-origin: center;
  animation: talk 2s ease-in-out infinite;
  opacity: 0;
  pointer-events: none;
  z-index: 5;
}

@keyframes talk {
  0%, 100% {
    opacity: 0;
    transform: scaleY(0);
  }
  15%, 35%, 55%, 75% {
    opacity: 0.7;
    transform: scaleY(1);
  }
  25%, 45%, 65%, 85% {
    opacity: 0;
    transform: scaleY(0.3);
  }
}

.guardian-label {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: linear-gradient(180deg, rgba(0, 20, 30, 0.50) 0%, rgba(0, 10, 20, 0.55) 100%);
  border-top: 1px solid rgba(0, 212, 170, 0.3);
  font-family: $font-mono;
  font-size: 11px;
  letter-spacing: 2px;
  color: rgba(0, 212, 170, 0.5);
  z-index: 5;

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(0, 212, 170, 0.3);
  }

  &.active {
    color: #00d4aa;

    .status-dot {
      background: #00d4aa;
      box-shadow: 0 0 10px #00d4aa, 0 0 20px rgba(0, 212, 170, 0.5);
      animation: dotPulse 2s ease-in-out infinite;
    }
  }
}

@keyframes dotPulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

// --- 3.1 Glitch Fade: random appear/disappear effect ---
.guardian-wrapper.glitch-active {
  animation: glitchFade 0.3s steps(4) forwards;
}

@keyframes glitchFade {
  0% { opacity: 1; transform: translateX(0); }
  20% { opacity: 0.1; transform: translateX(-5px); }
  40% { opacity: 0.8; transform: translateX(3px); }
  60% { opacity: 0; transform: translateX(-2px); }
  80% { opacity: 0.9; transform: translateX(4px); }
  100% { opacity: 1; transform: translateX(0); }
}

// --- 3.2 Pixel Fragmentation: RGB chromatic aberration with clip-path stripes ---
.guardian-wrapper {
  &::before,
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: 6;
    background: inherit;
    opacity: 0;
  }

  // Red chromatic shift - horizontal stripe fragments
  &::before {
    mix-blend-mode: screen;
    filter: hue-rotate(90deg) saturate(2);
    will-change: transform, opacity;
    clip-path: polygon(
      0% 8%, 100% 8%, 100% 11%, 0% 11%,
      0% 22%, 100% 22%, 100% 24%, 0% 24%,
      0% 37%, 100% 37%, 100% 40%, 0% 40%,
      0% 55%, 100% 55%, 100% 57%, 0% 57%,
      0% 68%, 100% 68%, 100% 71%, 0% 71%,
      0% 82%, 100% 82%, 100% 85%, 0% 85%,
      0% 93%, 100% 93%, 100% 95%, 0% 95%
    );
    animation: fragmentShift 6s ease-in-out infinite;
  }

  // Cyan chromatic shift - offset stripe fragments
  &::after {
    mix-blend-mode: screen;
    filter: hue-rotate(-90deg) saturate(2);
    will-change: transform, opacity;
    clip-path: polygon(
      0% 5%, 100% 5%, 100% 7%, 0% 7%,
      0% 18%, 100% 18%, 100% 20%, 0% 20%,
      0% 32%, 100% 32%, 100% 35%, 0% 35%,
      0% 48%, 100% 48%, 100% 51%, 0% 51%,
      0% 63%, 100% 63%, 100% 65%, 0% 65%,
      0% 76%, 100% 76%, 100% 79%, 0% 79%,
      0% 88%, 100% 88%, 100% 91%, 0% 91%
    );
    animation: fragmentShiftReverse 6s ease-in-out infinite;
  }
}

@keyframes fragmentShift {
  0%, 85%, 100% {
    opacity: 0;
    transform: translateX(0);
  }
  88% {
    opacity: 0.6;
    transform: translateX(-4px);
  }
  90% {
    opacity: 0;
    transform: translateX(2px);
  }
  92% {
    opacity: 0.8;
    transform: translateX(-3px);
  }
  94% {
    opacity: 0;
    transform: translateX(0);
  }
  96% {
    opacity: 0.5;
    transform: translateX(-5px);
  }
  98% {
    opacity: 0;
    transform: translateX(0);
  }
}

@keyframes fragmentShiftReverse {
  0%, 83%, 100% {
    opacity: 0;
    transform: translateX(0);
  }
  86% {
    opacity: 0.5;
    transform: translateX(4px);
  }
  89% {
    opacity: 0;
    transform: translateX(-2px);
  }
  91% {
    opacity: 0.7;
    transform: translateX(3px);
  }
  93% {
    opacity: 0;
    transform: translateX(0);
  }
  95% {
    opacity: 0.6;
    transform: translateX(5px);
  }
  97% {
    opacity: 0;
    transform: translateX(0);
  }
}

// --- 3.4 Scanline RGB chromatic shift enhancement ---
.image-scanline {
  &::before,
  &::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    height: 1px;
    pointer-events: none;
  }

  // Red scanline offset
  &::before {
    top: -2px;
    background: linear-gradient(90deg,
      transparent 0%,
      rgba(255, 0, 0, 0.15) 20%,
      rgba(255, 0, 0, 0.35) 50%,
      rgba(255, 0, 0, 0.15) 80%,
      transparent 100%
    );
    transform: translateX(-3px);
  }

  // Blue scanline offset
  &::after {
    top: 2px;
    background: linear-gradient(90deg,
      transparent 0%,
      rgba(0, 100, 255, 0.15) 20%,
      rgba(0, 100, 255, 0.35) 50%,
      rgba(0, 100, 255, 0.15) 80%,
      transparent 100%
    );
    transform: translateX(3px);
  }
}
</style>
