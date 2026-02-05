<template>
  <div class="alerts-page">
    <div class="page-header">
      <h1>// ALERT CENTER</h1>
      <div class="header-actions">
        <button class="cyber-btn cyber-btn--warning" @click="clearResolved">
          CLEAR RESOLVED
        </button>
        <router-link to="/" class="cyber-btn cyber-btn--ghost">
          BACK TO DASHBOARD
        </router-link>
      </div>
    </div>

    <!-- 告警统计 -->
    <div class="alert-stats">
      <div class="stat-item critical">
        <span class="stat-value">{{ criticalCount }}</span>
        <span class="stat-label">CRITICAL</span>
      </div>
      <div class="stat-item warning">
        <span class="stat-value">{{ warningCount }}</span>
        <span class="stat-label">WARNING</span>
      </div>
      <div class="stat-item info">
        <span class="stat-value">{{ infoCount }}</span>
        <span class="stat-label">INFO</span>
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="alerts-table-container">
      <table class="cyber-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Level</th>
            <th>Source</th>
            <th>Message</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="alert in monitorStore.alerts" :key="alert.id">
            <td class="time-cell">{{ alert.time }}</td>
            <td>
              <span class="alert-level" :class="alert.level">
                {{ alert.level.toUpperCase() }}
              </span>
            </td>
            <td class="source-cell">{{ alert.source }}</td>
            <td>{{ alert.message }}</td>
            <td>
              <button class="cyber-btn cyber-btn--ghost action-btn" @click="acknowledgeAlert(alert)">
                ACK
              </button>
              <button class="cyber-btn cyber-btn--ghost action-btn" @click="viewDetails(alert)">
                VIEW
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 告警详情弹窗 -->
    <CyberModal
      v-model="showDetailModal"
      title="ALERT DETAILS"
      width="550px"
      :show-footer="false"
    >
      <div v-if="selectedAlert" class="alert-detail">
        <div class="detail-row">
          <span class="label">TIME:</span>
          <span class="value">{{ selectedAlert.time }}</span>
        </div>
        <div class="detail-row">
          <span class="label">LEVEL:</span>
          <span class="value" :class="'alert-' + selectedAlert.level">
            {{ selectedAlert.level.toUpperCase() }}
          </span>
        </div>
        <div class="detail-row">
          <span class="label">SOURCE:</span>
          <span class="value source">{{ selectedAlert.source }}</span>
        </div>
        <div class="detail-row message">
          <span class="label">MESSAGE:</span>
          <span class="value">{{ selectedAlert.message }}</span>
        </div>
      </div>
    </CyberModal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useMonitorStore } from '@/stores/monitor'
import CyberModal from '@/components/CyberModal.vue'

const monitorStore = useMonitorStore()

const showDetailModal = ref(false)
const selectedAlert = ref(null)

const criticalCount = computed(() =>
  monitorStore.alerts.filter(a => a.level === 'critical').length
)
const warningCount = computed(() =>
  monitorStore.alerts.filter(a => a.level === 'warning').length
)
const infoCount = computed(() =>
  monitorStore.alerts.filter(a => a.level === 'info').length
)

function viewDetails(alert) {
  selectedAlert.value = alert
  showDetailModal.value = true
}

function acknowledgeAlert(alert) {
  console.log('Acknowledging alert:', alert.id)
}

function clearResolved() {
  console.log('Clearing resolved alerts')
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.alerts-page {
  padding: 20px;
  max-width: 1600px;
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

  .header-actions {
    display: flex;
    gap: 12px;
  }
}

.alert-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 30px;

  .stat-item {
    background: $bg-card;
    border: 1px solid rgba($neon-cyan, 0.2);
    padding: 20px;
    text-align: center;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
    }

    &.critical::before {
      background: $neon-red;
      box-shadow: 0 0 20px $neon-red;
    }

    &.warning::before {
      background: $neon-orange;
      box-shadow: 0 0 20px $neon-orange;
    }

    &.info::before {
      background: $neon-blue;
      box-shadow: 0 0 20px $neon-blue;
    }

    .stat-value {
      font-size: 36px;
      font-weight: bold;
      display: block;
      margin-bottom: 5px;
    }

    &.critical .stat-value { color: $neon-red; text-shadow: $glow-red; }
    &.warning .stat-value { color: $neon-orange; text-shadow: $glow-orange; }
    &.info .stat-value { color: $neon-blue; text-shadow: 0 0 20px $neon-blue; }

    .stat-label {
      font-size: 12px;
      color: $text-secondary;
      text-transform: uppercase;
      letter-spacing: 2px;
    }
  }
}

.alerts-table-container {
  background: $bg-card;
  border: 1px solid rgba($neon-cyan, 0.2);
  overflow: hidden;
}

.time-cell {
  color: $neon-cyan;
  font-weight: bold;
  text-shadow: 0 0 10px rgba($neon-cyan, 0.5);
  white-space: nowrap;
}

.source-cell {
  color: $neon-purple;
  font-weight: bold;
  text-shadow: 0 0 10px rgba($neon-purple, 0.5);
}

.alert-level {
  padding: 4px 12px;
  border-radius: 2px;
  font-size: 10px;
  font-weight: bold;
  letter-spacing: 1px;

  &.critical {
    background: rgba($neon-red, 0.2);
    border: 1px solid $neon-red;
    color: $neon-red;
  }

  &.warning {
    background: rgba($neon-orange, 0.2);
    border: 1px solid $neon-orange;
    color: $neon-orange;
  }

  &.info {
    background: rgba($neon-blue, 0.2);
    border: 1px solid $neon-blue;
    color: $neon-blue;
  }
}

.action-btn {
  padding: 4px 10px !important;
  font-size: 10px !important;
  margin-right: 8px;

  &:last-child {
    margin-right: 0;
  }
}

.alert-detail {
  .detail-row {
    display: flex;
    padding: 12px 0;
    border-bottom: 1px solid rgba($neon-cyan, 0.1);

    &:last-child {
      border-bottom: none;
    }

    &.message {
      flex-direction: column;
      gap: 8px;
    }

    .label {
      width: 100px;
      color: $text-secondary;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }

    .value {
      flex: 1;
      color: $text-primary;

      &.alert-critical { color: $neon-red; }
      &.alert-warning { color: $neon-orange; }
      &.alert-info { color: $neon-blue; }
      &.source { color: $neon-purple; }
    }
  }
}
</style>
