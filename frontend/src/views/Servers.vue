<template>
  <div class="servers-page">
    <div class="page-header">
      <h1>// SERVER MANAGEMENT</h1>
      <router-link to="/" class="cyber-btn cyber-btn--ghost">
        BACK TO DASHBOARD
      </router-link>
    </div>

    <div class="servers-list">
      <ServerCard
        v-for="server in monitorStore.servers"
        :key="server.id"
        :server="server"
        @click="goToDetail"
      />
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useMonitorStore } from '@/stores/monitor'
import ServerCard from '@/components/ServerCard.vue'

const router = useRouter()
const monitorStore = useMonitorStore()

function goToDetail(server) {
  router.push(`/servers/${server.id}`)
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.servers-page {
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

.servers-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
  gap: 25px;
}
</style>
