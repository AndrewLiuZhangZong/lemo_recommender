<template>
  <div>
    <el-card>
      <el-form :inline="true">
        <el-form-item label="场景">
          <el-select v-model="selectedScenario" style="width: 200px" @change="loadData">
            <el-option v-for="s in scenarios" :key="s.scenario_id" 
                       :label="s.name" :value="s.scenario_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-select v-model="days" style="width: 120px" @change="loadData">
            <el-option label="最近7天" :value="7" />
            <el-option label="最近30天" :value="30" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :span="12">
        <el-card>
          <template #header>物品分类分布</template>
          <div ref="categoryChart" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>用户活跃时段</template>
          <div ref="hourChart" style="height: 300px"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi, scenarioApi } from '../api'
import * as echarts from 'echarts'

const scenarios = ref([])
const selectedScenario = ref('')
const days = ref(7)
const categoryChart = ref(null)
const hourChart = ref(null)

onMounted(async () => {
  scenarios.value = await scenarioApi.list()
  if (scenarios.value.length > 0) {
    selectedScenario.value = scenarios.value[0].scenario_id
    await loadData()
  }
  initCharts()
})

async function loadData() {
  if (!selectedScenario.value) return
  
  try {
    const distribution = await adminApi.itemDistribution(selectedScenario.value)
    const behavior = await adminApi.userBehavior(selectedScenario.value, days.value)
    
    updateCategoryChart(distribution.category_distribution)
    updateHourChart(behavior.hour_distribution)
  } catch (error) {
    console.error('加载失败:', error)
  }
}

function initCharts() {
  echarts.init(categoryChart.value)
  echarts.init(hourChart.value)
}

function updateCategoryChart(data) {
  const chart = echarts.getInstanceByDom(categoryChart.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: '60%',
      data: data.map(d => ({ name: d.category, value: d.count }))
    }]
  })
}

function updateHourChart(data) {
  const chart = echarts.getInstanceByDom(hourChart.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map(d => d.hour + ':00') },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      data: data.map(d => d.count),
      itemStyle: { color: '#1890ff' }
    }]
  })
}
</script>

