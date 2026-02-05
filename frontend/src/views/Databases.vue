<template>
  <div class="databases-page">
    <div class="page-header">
      <h1>// DATABASE MONITORING</h1>
      <router-link to="/" class="cyber-btn cyber-btn--ghost">
        BACK TO DASHBOARD
      </router-link>
    </div>

    <div class="databases-grid">
      <div
        v-for="server in monitorStore.servers"
        :key="server.id"
        class="database-card"
        :class="{ warning: server.tablespaceUsage >= 70, critical: server.tablespaceUsage >= 90 }"
      >
        <div class="card-header">
          <div class="db-info">
            <h3>{{ server.name }}_DB</h3>
            <span class="ip">{{ server.ip }}</span>
          </div>
          <div class="db-status" :class="getStatusClass(server.tablespaceUsage)">
            {{ getStatusText(server.tablespaceUsage) }}
          </div>
        </div>

        <div class="tablespace-section">
          <h4>TABLESPACE USAGE</h4>
          <div class="cyber-progress">
            <div
              class="cyber-progress-fill"
              :class="getProgressClass(server.tablespaceUsage)"
              :style="{ width: server.tablespaceUsage + '%' }"
            ></div>
            <span class="cyber-progress-text">{{ server.tablespaceUsage }}%</span>
          </div>
        </div>

        <div class="db-metrics">
          <div class="metric">
            <span class="metric-label">CONNECTIONS</span>
            <span class="metric-value">{{ Math.floor(Math.random() * 50) + 10 }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">ACTIVE SESSIONS</span>
            <span class="metric-value">{{ Math.floor(Math.random() * 20) + 5 }}</span>
          </div>
        </div>

        <div class="card-actions">
          <button class="cyber-btn cyber-btn--ghost">VIEW DETAILS</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useMonitorStore } from '@/stores/monitor'

const monitorStore = useMonitorStore()

function getStatusClass(usage) {
  if (usage >= 90) return 'critical'
  if (usage >= 70) return 'warning'
  return 'normal'
}

function getStatusText(usage) {
  if (usage >= 90) return 'CRITICAL'
  if (usage >= 70) return 'WARNING'
  return 'NORMAL'
}

function getProgressClass(usage) {
  if (usage >= 90) return 'cyber-progress-fill--critical'
  if (usage >= 70) return 'cyber-progress-fill--high'
  if (usage >= 50) return 'cyber-progress-fill--medium'
  return 'cyber-progress-fill--low'
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.databases-page {
  padding: 20px;
  max-width: 1800px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: $bg-card;
  border: 1px solid rgba($neon-cyan, 0.2);

  h1 {
    font-size: 24px;
    color: $neon-cyan;
    text-transform: uppercase;
    letter-spacing: 4px;
    text-shadow: 0 0 20px rgba($neon-cyan, 0.5);
  }
}

.databases-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 25px;
}

.database-card {
  background: $bg-card;
  border: 1px solid rgba($neon-cyan, 0.2);
  padding: 25px;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: $neon-green;
    box-shadow: 0 0 15px $neon-green;
  }

  &.warning::before {
    background: $neon-orange;
    box-shadow: 0 0 15px $neon-orange;
  }

  &.critical::before {
    background: $neon-red;
    box-shadow: 0 0 15px $neon-red;
    animation: criticalPulse 1s ease-in-out infinite;
  }
}

@keyframes criticalPulse {
  0%, 100% { box-shadow: 0 0 15px $neon-red; }
  50% { box-shadow: 0 0 30px $neon-red; }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba($neon-cyan, 0.15);

  h3 {
    font-size: 16px;
    color: $neon-cyan;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 5px;
  }

  .ip {
    font-size: 13px;
    color: $text-secondary;
  }
}

.db-status {
  padding: 6px 14px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: bold;
  letter-spacing: 1px;

  &.normal {
    background: rgba($neon-green, 0.15);
    border: 1px solid rgba($neon-green, 0.5);
    color: $neon-green;
  }

  &.warning {
    background: rgba($neon-orange, 0.15);
    border: 1px solid rgba($neon-orange, 0.5);
    color: $neon-orange;
  }

  &.critical {
    background: rgba($neon-red, 0.2);
    border: 1px solid rgba($neon-red, 0.6);
    color: $neon-red;
  }
}

.tablespace-section {
  margin-bottom: 20px;

  h4 {
    font-size: 11px;
    color: $text-secondary;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 10px;
  }
}

.db-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 20px;

  .metric {
    text-align: center;
    padding: 12px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba($neon-cyan, 0.1);

    .metric-label {
      display: block;
      font-size: 10px;
      color: $text-secondary;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 5px;
    }

    .metric-value {
      font-size: 20px;
      color: $neon-cyan;
      font-weight: bold;
      text-shadow: 0 0 10px rgba($neon-cyan, 0.5);
    }
  }
}

.card-actions {
  text-align: center;
}
</style>
