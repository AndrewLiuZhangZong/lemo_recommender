<template>
  <div class="dashboard">
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6" v-for="stat in stats" :key="stat.title">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" :style="{ backgroundColor: stat.color }">
              <component :is="stat.icon" />
            </div>
            <div class="stat-info">
              <div class="stat-title">{{ stat.title }}</div>
              <div class="stat-value">{{ stat.value }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="charts-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>推荐量趋势</span>
          </template>
          <div ref="trendChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>CTR趋势</span>
          </template>
          <div ref="ctrChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '../api'
import * as echarts from 'echarts'
import { DataAnalysis, User, Document, TrendCharts } from '@element-plus/icons-vue'

const stats = ref([
  { title: '推荐请求', value: '0', icon: DataAnalysis, color: '#1890ff' },
  { title: '活跃用户', value: '0', icon: User, color: '#52c41a' },
  { title: '物品总数', value: '0', icon: Document, color: '#faad14' },
  { title: 'CTR', value: '0%', icon: TrendCharts, color: '#f5222d' }
])

const trendChart = ref(null)
const ctrChart = ref(null)

onMounted(async () => {
  await loadDashboard()
  initCharts()
})

async function loadDashboard() {
  try {
    const data = await adminApi.dashboard({ days: 7 })
    stats.value[0].value = data.metrics.recommendation_count.toLocaleString()
    stats.value[1].value = data.metrics.active_users.toLocaleString()
    stats.value[2].value = data.metrics.total_items.toLocaleString()
    stats.value[3].value = (data.metrics.ctr * 100).toFixed(2) + '%'

    const trends = await adminApi.trends({ days: 7 })
    updateCharts(trends.trends)
  } catch (error) {
    console.error('加载失败:', error)
  }
}

function initCharts() {
  const trend = echarts.init(trendChart.value)
  const ctr = echarts.init(ctrChart.value)

  trend.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: [] },
    yAxis: { type: 'value' },
    series: [
      { name: '曝光', type: 'line', data: [], smooth: true },
      { name: '点击', type: 'line', data: [], smooth: true }
    ]
  })

  ctr.setOption({
    tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
    xAxis: { type: 'category', data: [] },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [{ name: 'CTR', type: 'line', data: [], smooth: true, areaStyle: {} }]
  })
}

function updateCharts(trends) {
  const dates = trends.map(t => t.date)
  const impressions = trends.map(t => t.impression)
  const clicks = trends.map(t => t.click)
  const ctrs = trends.map(t => (t.ctr * 100).toFixed(2))

  const trendInstance = echarts.getInstanceByDom(trendChart.value)
  trendInstance.setOption({
    xAxis: { data: dates },
    series: [{ data: impressions }, { data: clicks }]
  })

  const ctrInstance = echarts.getInstanceByDom(ctrChart.value)
  ctrInstance.setOption({
    xAxis: { data: dates },
    series: [{ data: ctrs }]
  })
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.stat-info {
  flex: 1;
}

.stat-title {
  font-size: 14px;
  color: #999;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
}
</style>

