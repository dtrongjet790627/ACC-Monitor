<template>
  <div class="alert-console">
    <!-- 顶部扫描线 -->
    <div class="top-scanner"></div>

    <div class="alert-header">
      <h3>
        <div class="alert-icon"></div>
        ALERT CONSOLE
      </h3>
      <div class="alert-count">
        <span class="count-pulse"></span>
        {{ alerts.length }} ALERTS
      </div>
    </div>

    <div class="alert-body">
      <div class="alert-scroll" ref="scrollContainer">
        <div
          v-for="(alert, index) in displayAlerts"
          :key="alert.id"
          class="alert-item"
          :style="{ animationDelay: (index % 5) * 0.1 + 's' }"
          @click="handleAlertClick(alert)"
        >
          <span class="alert-time">{{ alert.time }}</span>
          <span class="alert-level" :class="alert.level">
            <span class="level-indicator"></span>
            {{ alert.level.toUpperCase() }}
          </span>
          <span class="alert-message">{{ alert.message }}</span>
          <span class="alert-source">[{{ alert.source }}]</span>
        </div>
      </div>
    </div>

    <!-- 底部渐变遮罩 -->
    <div class="bottom-fade"></div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  alerts: {
    type: Array,
    default: () => []
  },
  autoScroll: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['alert-click'])

const scrollContainer = ref(null)

// 复制两份实现无缝滚动
const displayAlerts = computed(() => {
  if (props.autoScroll) {
    return [...props.alerts, ...props.alerts]
  }
  return props.alerts
})

function handleAlertClick(alert) {
  emit('alert-click', alert)
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.alert-console {
  background: $bg-card;
  border: 1px solid rgba($neon-red, 0.3);
  overflow: hidden;
  position: relative;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8);
}

// 顶部扫描线
.top-scanner {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, transparent, $neon-red, transparent);
  transform: translateX(-100%);
  animation: scannerMove 3s linear infinite;
  will-change: transform;
  z-index: 10;
}

@keyframes scannerMove {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: rgba($neon-red, 0.1);
  border-bottom: 1px solid rgba($neon-red, 0.2);

  h3 {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 13px;
    font-weight: 400;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: $neon-red;
  }
}

.alert-icon {
  width: 10px;
  height: 10px;
  background: $neon-red;
  border-radius: 50%;
  animation: iconPulse 1.5s ease-in-out infinite;
  will-change: opacity, transform;
}

@keyframes iconPulse {
  0%, 100% { opacity: 0.6; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.2); }
}

.alert-count {
  background: $neon-red;
  color: #fff;
  padding: 5px 14px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: bold;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 8px;

  .count-pulse {
    width: 6px;
    height: 6px;
    background: #fff;
    border-radius: 50%;
    animation: countPulse 1s ease-in-out infinite;
    will-change: opacity;
  }
}

@keyframes countPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.alert-body {
  height: 200px;
  overflow-y: auto;
  position: relative;
  background: rgba(0, 0, 0, 0.5);
  font-family: $font-mono;
}

.alert-scroll {
  padding: 15px 20px;
}

.alert-item {
  display: flex;
  gap: 15px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
  animation: itemFadeIn 0.3s ease-out forwards;
  will-change: transform;

  &:hover {
    background: rgba($neon-cyan, 0.05);
    transform: translateX(5px);
  }
}

@keyframes itemFadeIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.alert-time {
  color: $neon-cyan;
  white-space: nowrap;
  font-weight: bold;
}

.alert-level {
  padding: 2px 10px;
  border-radius: 2px;
  font-size: 10px;
  text-transform: uppercase;
  white-space: nowrap;
  font-weight: bold;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 6px;

  .level-indicator {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: currentColor;
    will-change: opacity;
  }

  &.critical {
    background: rgba($neon-red, 0.2);
    color: $neon-red;
    border: 1px solid rgba($neon-red, 0.5);

    .level-indicator {
      animation: levelBlink 0.8s ease-in-out infinite;
    }
  }

  &.warning {
    background: rgba($neon-orange, 0.15);
    color: $neon-orange;
    border: 1px solid rgba($neon-orange, 0.5);

    .level-indicator {
      animation: levelBlink 1.2s ease-in-out infinite;
    }
  }

  &.info {
    background: rgba($neon-blue, 0.15);
    color: $neon-blue;
    border: 1px solid rgba($neon-blue, 0.5);
  }
}

@keyframes levelBlink {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.alert-message {
  flex: 1;
  color: $text-secondary;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.alert-source {
  color: $neon-purple;
  white-space: nowrap;
  font-weight: bold;
}

// 底部渐变遮罩
.bottom-fade {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 30px;
  background: linear-gradient(transparent, rgba(5, 5, 25, 0.9));
  pointer-events: none;
}
</style>
