<template>
  <div class="ops-detail-container">
    <!-- Top Bar -->
    <header class="ops-top-bar">
      <div class="bar-left">
        <button class="back-btn" @click="$router.push('/oracle-ops')">
          <span class="bracket">[</span>
          <span class="arrow">&lt;</span>
          <span class="bracket">]</span>
        </button>
        <div class="page-title">
          <span class="title-icon">&#9671;</span>
          <span class="title-text">{{ serverConfig.shortName }} TABLESPACE DETAIL</span>
          <span class="server-ip-badge">{{ serverConfig.ip }}</span>
        </div>
      </div>
      <div class="bar-right">
        <div class="time-range-selector">
          <button
            v-for="opt in timeRangeOptions"
            :key="opt.days"
            class="range-btn"
            :class="{ active: selectedDays === opt.days }"
            @click="selectedDays = opt.days; loadTrends()"
          >{{ opt.label }}</button>
        </div>
        <button class="refresh-btn" @click="loadAll" :disabled="store.tablespacesLoading">
          <span class="bracket">[</span>
          <span :class="{ 'spin': store.tablespacesLoading }">&#8635;</span>
          <span class="bracket">]</span>
        </button>
      </div>
    </header>

    <!-- Main content: two columns -->
    <div class="detail-layout">
      <!-- Left: Chart area -->
      <div class="chart-area">
        <!-- Usage bar chart -->
        <div class="chart-card">
          <div class="chart-title">
            <span class="ct-icon">&#9632;</span>
            TABLESPACE USAGE
          </div>
          <div ref="barChartRef" class="chart-container"></div>
        </div>

        <!-- Trend line chart -->
        <div class="chart-card">
          <div class="chart-title">
            <span class="ct-icon">&#9632;</span>
            USAGE TREND ({{ selectedDays }}D)
          </div>
          <div ref="lineChartRef" class="chart-container"></div>
        </div>
      </div>

      <!-- Right: Table -->
      <div class="table-area">
        <div class="table-card">
          <div class="table-title">
            <span class="ct-icon">&#9632;</span>
            TABLESPACE DATA
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>TABLESPACE</th>
                <th>USED MB</th>
                <th>MAX MB</th>
                <th>USAGE</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="ts in filteredTablespaces"
                :key="ts.tablespace_name"
                :class="getRowClass(getDisplayPct(ts))"
              >
                <td class="ts-name-cell">
                  {{ ts.tablespace_name }}
                  <span v-if="ts.current_file_pct != null" class="current-file-tag">FILE</span>
                </td>
                <td class="number-cell">{{ formatMB(getDisplayUsedMB(ts)) }}</td>
                <td class="number-cell">{{ formatMB(getDisplayMaxMB(ts)) }}</td>
                <td class="usage-cell">
                  <div class="usage-bar-wrapper">
                    <div
                      class="usage-bar-fill"
                      :class="getBarClass(getDisplayPct(ts))"
                      :style="{ width: Math.min(getDisplayPct(ts), 100) + '%' }"
                    ></div>
                    <span class="usage-text">{{ getDisplayPct(ts).toFixed(1) }}%</span>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredTablespaces.length === 0">
                <td colspan="4" class="empty-cell">NO DATA AVAILABLE</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { useOracleOpsStore, ORACLE_SERVER_CONFIG } from '@/stores/oracle_ops'

const route = useRoute()
const store = useOracleOpsStore()

const serverId = computed(() => route.params.id)
const serverConfig = computed(() => ORACLE_SERVER_CONFIG[serverId.value] || { shortName: serverId.value, ip: '' })

const selectedDays = ref(7)
const timeRangeOptions = [
  { label: '24H', days: 1 },
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
]

const barChartRef = ref(null)
const lineChartRef = ref(null)
let barChart = null
let lineChart = null

// Filtered tablespaces for this server
const filteredTablespaces = computed(() => {
  return store.tablespaces.filter(ts => ts.server_id === serverId.value)
})

// Helpers
function formatMB(val) {
  if (!val && val !== 0) return 'N/A'
  if (val >= 1024) return (val / 1024).toFixed(1) + ' GB'
  return val.toFixed(1)
}

function getRowClass(pct) {
  if (pct >= 95) return 'row-critical'
  if (pct >= 85) return 'row-warning'
  return ''
}

function getBarClass(pct) {
  if (pct >= 95) return 'bar-critical'
  if (pct >= 85) return 'bar-warning'
  return 'bar-normal'
}

// For business tablespaces (ACC_DATA, IPLANT_*_DATA), display current active file usage
// instead of total usage across all data files. Historical files being full is expected.
function isBusinessTablespace(tsName) {
  if (!tsName) return false
  const upper = tsName.toUpperCase()
  if (upper.includes('ACC_DATA')) return true
  if (upper.startsWith('IPLANT_') && upper.endsWith('_DATA')) return true
  return false
}

function getDisplayPct(ts) {
  if (isBusinessTablespace(ts.tablespace_name) && ts.current_file_pct != null) {
    return ts.current_file_pct
  }
  return ts.usage_pct || 0
}

function getDisplayUsedMB(ts) {
  if (isBusinessTablespace(ts.tablespace_name) && ts.current_file_used_mb != null) {
    return ts.current_file_used_mb
  }
  return ts.used_mb
}

function getDisplayMaxMB(ts) {
  if (isBusinessTablespace(ts.tablespace_name) && ts.current_file_max_mb != null) {
    return ts.current_file_max_mb
  }
  return ts.max_mb
}

// Chart rendering
function renderBarChart() {
  if (!barChartRef.value) return
  if (!barChart) {
    barChart = echarts.init(barChartRef.value)
  }

  const data = filteredTablespaces.value
  const names = data.map(ts => ts.tablespace_name)
  const values = data.map(ts => getDisplayPct(ts))
  const colors = values.map(v => {
    if (v >= 95) return '#ff0055'
    if (v >= 85) return '#ff6b35'
    return '#00d4aa'
  })

  barChart.setOption({
    grid: { left: 120, right: 30, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#6c757d', fontFamily: 'Consolas', formatter: '{value}%' },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.2)' } },
      splitLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.05)' } },
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: '#00d4aa', fontFamily: 'Consolas', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.2)' } },
    },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({
        value: v,
        itemStyle: { color: colors[i] }
      })),
      barWidth: 14,
      label: {
        show: true,
        position: 'right',
        color: '#ffffff',
        fontFamily: 'Consolas',
        fontSize: 11,
        formatter: '{c}%'
      }
    }],
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 10, 10, 0.95)',
      borderColor: 'rgba(0, 212, 170, 0.3)',
      textStyle: { color: '#00d4aa', fontFamily: 'Consolas', fontSize: 12 },
      formatter: (params) => {
        const p = params[0]
        return `${p.name}<br/>Usage: ${p.value.toFixed(1)}%`
      }
    },
    animation: true,
    animationDuration: 800,
  })
}

function renderLineChart() {
  if (!lineChartRef.value) return
  if (!lineChart) {
    lineChart = echarts.init(lineChartRef.value)
  }

  const trendData = store.trends.filter(t => t.server_id === serverId.value)

  if (trendData.length === 0) {
    lineChart.setOption({
      title: {
        text: 'No trend data available',
        left: 'center',
        top: 'center',
        textStyle: { color: '#6c757d', fontFamily: 'Consolas', fontSize: 13 }
      }
    })
    return
  }

  // Cyberpunk color palette for lines
  const lineColors = ['#00d4aa', '#0099ff', '#ff6b35', '#9d4edd', '#ff0080', '#ffd700', '#00ff41', '#ff0055']

  const series = trendData.map((ts, idx) => ({
    name: ts.tablespace_name,
    type: 'line',
    data: ts.data_points.map(dp => [dp.time, dp.usage_pct]),
    smooth: true,
    lineStyle: { width: 2, color: lineColors[idx % lineColors.length] },
    itemStyle: { color: lineColors[idx % lineColors.length] },
    symbol: 'circle',
    symbolSize: 4,
    showSymbol: false,
  }))

  lineChart.setOption({
    grid: { left: 60, right: 30, top: 40, bottom: 50 },
    legend: {
      type: 'scroll',
      top: 5,
      textStyle: { color: '#6c757d', fontFamily: 'Consolas', fontSize: 10 },
      pageTextStyle: { color: '#6c757d' },
      pageIconColor: '#00d4aa',
    },
    xAxis: {
      type: 'time',
      axisLabel: { color: '#6c757d', fontFamily: 'Consolas', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.2)' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#6c757d', fontFamily: 'Consolas', formatter: '{value}%' },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.2)' } },
      splitLine: { lineStyle: { color: 'rgba(0, 212, 170, 0.05)' } },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 10, 10, 0.95)',
      borderColor: 'rgba(0, 212, 170, 0.3)',
      textStyle: { color: '#00d4aa', fontFamily: 'Consolas', fontSize: 11 },
    },
    series,
    animation: true,
    animationDuration: 800,
  }, true)
}

// Data loading
async function loadAll() {
  await Promise.all([
    store.fetchTablespaces(serverId.value),
    loadTrends(),
  ])
  await nextTick()
  renderBarChart()
}

async function loadTrends() {
  await store.fetchTrends(serverId.value, selectedDays.value)
  await nextTick()
  renderLineChart()
}

// Watch for tablespace data changes
watch(() => store.tablespaces, () => {
  nextTick(() => renderBarChart())
}, { deep: true })

watch(() => store.trends, () => {
  nextTick(() => renderLineChart())
}, { deep: true })

let resizeHandler = null

onMounted(() => {
  loadAll()
  resizeHandler = () => {
    barChart?.resize()
    lineChart?.resize()
  }
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  barChart?.dispose()
  lineChart?.dispose()
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
})
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.ops-detail-container {
  height: 100vh;
  padding: 16px 24px;
  overflow-y: auto;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba($neon-green, 0.3); border-radius: 2px; }
}

// ============ Top Bar ============
.ops-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  margin-bottom: 20px;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba($neon-green, 0.3);
}

.bar-left, .bar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn, .refresh-btn {
  background: none;
  border: 1px solid rgba($neon-green, 0.3);
  color: $neon-green;
  padding: 4px 10px;
  cursor: pointer;
  font-family: $font-mono;
  font-size: 14px;
  transition: all 0.2s;

  &:hover { background: rgba($neon-green, 0.1); border-color: $neon-green; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }

  .bracket { opacity: 0.5; }
  .spin { display: inline-block; animation: spin 1s linear infinite; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;

  .title-icon { color: $neon-cyan; font-size: 16px; }
  .title-text {
    font-family: $font-terminal;
    font-size: 15px;
    color: $neon-green;
    letter-spacing: 2px;
  }
}

.server-ip-badge {
  font-family: $font-mono;
  font-size: 10px;
  color: $text-secondary;
  padding: 2px 8px;
  border: 1px solid rgba($text-secondary, 0.3);
  margin-left: 8px;
}

.time-range-selector {
  display: flex;
  gap: 4px;
}

.range-btn {
  background: none;
  border: 1px solid rgba($neon-green, 0.2);
  color: rgba($neon-green, 0.5);
  font-family: $font-mono;
  font-size: 11px;
  padding: 3px 10px;
  cursor: pointer;
  letter-spacing: 1px;
  transition: all 0.2s;

  &:hover {
    border-color: rgba($neon-green, 0.5);
    color: $neon-green;
  }

  &.active {
    background: rgba($neon-green, 0.1);
    border-color: $neon-green;
    color: $neon-green;
  }
}

// ============ Layout ============
.detail-layout {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 16px;
}

// ============ Charts ============
.chart-card, .table-card {
  background: $bg-card;
  border: 1px solid rgba($neon-green, 0.15);
  padding: 16px;
  margin-bottom: 16px;
}

.chart-title, .table-title {
  font-family: $font-terminal;
  font-size: 12px;
  color: $neon-green;
  letter-spacing: 2px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba($neon-green, 0.1);

  .ct-icon {
    color: $neon-cyan;
    margin-right: 6px;
    font-size: 10px;
  }
}

.chart-container {
  width: 100%;
  height: 280px;
}

// ============ Table ============
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-family: $font-mono;
  font-size: 11px;

  th {
    color: $text-secondary;
    font-size: 10px;
    letter-spacing: 1px;
    text-align: left;
    padding: 6px 8px;
    border-bottom: 1px solid rgba($neon-green, 0.15);
  }

  td {
    padding: 6px 8px;
    border-bottom: 1px solid rgba($neon-green, 0.05);
    color: rgba($text-white, 0.8);
  }

  tr:hover {
    background: rgba($neon-green, 0.03);
  }

  .row-warning td { color: $neon-orange; }
  .row-critical td { color: $neon-red; }
}

.ts-name-cell {
  font-size: 10px;
  letter-spacing: 0.5px;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  .current-file-tag {
    display: inline-block;
    font-size: 8px;
    padding: 0 3px;
    margin-left: 4px;
    color: $neon-cyan;
    border: 1px solid rgba($neon-cyan, 0.4);
    background: rgba($neon-cyan, 0.08);
    letter-spacing: 0.5px;
    vertical-align: middle;
  }
}

.number-cell {
  text-align: right;
  white-space: nowrap;
}

.usage-cell {
  width: 120px;
}

.usage-bar-wrapper {
  position: relative;
  height: 16px;
  background: rgba($neon-green, 0.05);
  overflow: hidden;
}

.usage-bar-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  transition: width 0.5s ease;

  &.bar-normal { background: rgba($neon-green, 0.3); }
  &.bar-warning { background: rgba($neon-orange, 0.3); }
  &.bar-critical { background: rgba($neon-red, 0.3); }
}

.usage-text {
  position: relative;
  z-index: 1;
  font-size: 10px;
  color: $text-white;
  padding: 0 4px;
  line-height: 16px;
}

.empty-cell {
  text-align: center;
  color: $text-secondary;
  padding: 20px;
  font-size: 12px;
  letter-spacing: 2px;
}

// ============ Responsive ============
@media (max-width: 1000px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }
}
</style>
