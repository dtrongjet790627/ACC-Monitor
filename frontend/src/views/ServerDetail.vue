<template>
  <div class="server-detail-page">
    <div class="page-header">
      <div class="header-info">
        <router-link to="/" class="back-link">[&lt;] BACK</router-link>
        <h1 v-if="server">// {{ server.name }} - {{ server.fullName }}</h1>
        <h1 v-else>// SERVER NOT FOUND</h1>
      </div>
      <div v-if="server" class="server-status" :class="server.status">
        <div class="status-dot"></div>
        {{ server.status.toUpperCase() }}
      </div>
    </div>

    <div v-if="server" class="detail-content">
      <!-- 基本信息 -->
      <div class="info-section">
        <h2>SYSTEM INFORMATION</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-label">IP ADDRESS</div>
            <div class="info-value cyan">{{ server.ip }}</div>
          </div>
          <div class="info-card">
            <div class="info-label">CPU USAGE</div>
            <div class="info-value" :class="cpuClass">{{ server.cpuUsage }}%</div>
          </div>
          <div class="info-card">
            <div class="info-label">MEMORY USAGE</div>
            <div class="info-value" :class="memoryClass">{{ server.memoryUsage }}%</div>
          </div>
          <div class="info-card">
            <div class="info-label">DISK USAGE</div>
            <div class="info-value" :class="diskClass">{{ server.tablespaceUsage }}%</div>
          </div>
        </div>
      </div>

      <!-- 进程列表 -->
      <div class="process-section">
        <h2>RUNNING PROCESSES</h2>
        <table class="cyber-table">
          <thead>
            <tr>
              <th>Process Name</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(process, index) in server.processes" :key="index">
              <td>{{ process.name }}</td>
              <td>
                <span :class="'status-' + process.status">
                  {{ process.status.toUpperCase() }}
                </span>
              </td>
              <td>
                <button class="cyber-btn cyber-btn--ghost" style="padding: 6px 12px; font-size: 11px;">
                  RESTART
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else class="not-found">
      <div class="error-icon">[!]</div>
      <p>Server not found</p>
      <router-link to="/" class="cyber-btn">BACK TO DASHBOARD</router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useMonitorStore } from '@/stores/monitor'

const route = useRoute()
const monitorStore = useMonitorStore()

const server = computed(() => monitorStore.getServerById(route.params.id))

const cpuClass = computed(() => {
  if (!server.value) return ''
  const usage = server.value.cpuUsage
  if (usage >= 90) return 'red'
  if (usage >= 70) return 'orange'
  return 'green'
})

const memoryClass = computed(() => {
  if (!server.value) return ''
  const usage = server.value.memoryUsage
  if (usage >= 90) return 'red'
  if (usage >= 70) return 'orange'
  return 'green'
})

const diskClass = computed(() => {
  if (!server.value) return ''
  const usage = server.value.tablespaceUsage
  if (usage >= 90) return 'red'
  if (usage >= 70) return 'orange'
  return 'green'
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.server-detail-page {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 25px;
  background: $bg-card;
  border: 1px solid rgba($neon-cyan, 0.2);

  .back-link {
    color: $text-secondary;
    text-decoration: none;
    font-size: 12px;
    margin-bottom: 8px;
    display: inline-block;
    transition: color 0.3s ease;

    &:hover {
      color: $neon-cyan;
    }
  }

  h1 {
    font-size: 24px;
    color: $neon-cyan;
    text-transform: uppercase;
    letter-spacing: 3px;
    text-shadow: 0 0 20px rgba($neon-cyan, 0.5);
  }

  .server-status {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 20px;
    border-radius: 3px;
    font-size: 14px;
    font-weight: bold;
    letter-spacing: 2px;

    .status-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: currentColor;
      box-shadow: 0 0 15px currentColor;
    }

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

    &.error {
      background: rgba($neon-red, 0.2);
      border: 1px solid rgba($neon-red, 0.6);
      color: $neon-red;
    }
  }
}

.info-section, .process-section {
  margin-bottom: 30px;

  h2 {
    font-size: 14px;
    color: $neon-purple;
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba($neon-purple, 0.3);
    text-shadow: 0 0 10px rgba($neon-purple, 0.5);
  }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.info-card {
  background: $bg-card;
  border: 1px solid rgba($neon-cyan, 0.2);
  padding: 20px;
  text-align: center;

  .info-label {
    font-size: 11px;
    color: $text-secondary;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 10px;
  }

  .info-value {
    font-size: 28px;
    font-weight: bold;

    &.cyan { color: $neon-cyan; text-shadow: $glow-cyan; }
    &.green { color: $neon-green; text-shadow: $glow-green; }
    &.orange { color: $neon-orange; text-shadow: $glow-orange; }
    &.red { color: $neon-red; text-shadow: $glow-red; }
  }
}

.not-found {
  text-align: center;
  padding: 100px 20px;

  .error-icon {
    font-size: 64px;
    color: $neon-red;
    text-shadow: $glow-red;
    margin-bottom: 20px;
  }

  p {
    font-size: 18px;
    color: $text-secondary;
    margin-bottom: 30px;
  }
}

@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
