<template>
  <div class="guardian-container">
    <!-- Corner decorations -->
    <div class="corner-decor top-left"></div>
    <div class="corner-decor top-right"></div>
    <div class="corner-decor bottom-left"></div>
    <div class="corner-decor bottom-right"></div>

    <!-- Glow effect behind image -->
    <div class="guardian-glow"></div>

    <!-- Guardian image -->
    <img
      src="@/assets/hacker-guardian.png"
      alt="System Guardian"
      class="guardian-image"
    />

    <!-- Scanline effect -->
    <div class="face-scanline"></div>

    <!-- Status label -->
    <div class="guardian-label" :class="{ active: isOnline }">
      <span class="status-dot"></span>
      <span class="status-text">SYSTEM GUARDIAN {{ isOnline ? 'ONLINE' : 'OFFLINE' }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  isOnline: {
    type: Boolean,
    default: true
  }
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
  // Semi-transparent background for matrix rain visibility
  background: linear-gradient(180deg, rgba(0, 10, 20, 0.70) 0%, rgba(0, 5, 15, 0.75) 100%);
  border: 1px solid rgba(0, 212, 170, 0.3);
  border-radius: 8px;
  overflow: hidden;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
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

.guardian-glow {
  position: absolute;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at center 40%, rgba(0, 212, 170, 0.25) 0%, rgba(0, 255, 200, 0.1) 30%, transparent 70%);
  pointer-events: none;
  animation: glowPulse 3s ease-in-out infinite;
}

@keyframes glowPulse {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}

.guardian-image {
  position: relative;
  z-index: 2;
  width: 100%;
  height: auto;
  max-height: 220px;
  object-fit: contain;
  filter: drop-shadow(0 0 20px rgba(0, 212, 170, 0.5)) drop-shadow(0 0 40px rgba(0, 255, 200, 0.3));
}

.face-scanline {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(0, 212, 170, 0.3) 20%,
    rgba(0, 255, 200, 0.6) 50%,
    rgba(0, 212, 170, 0.3) 80%,
    transparent 100%
  );
  animation: scanMove 4s linear infinite;
  z-index: 3;
  opacity: 0.8;
}

@keyframes scanMove {
  0% { top: 0; opacity: 0.8; }
  50% { opacity: 0.5; }
  100% { top: calc(100% - 40px); opacity: 0.8; }
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
  background: linear-gradient(180deg, rgba(0, 20, 30, 0.9) 0%, rgba(0, 10, 20, 0.95) 100%);
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
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}
</style>
