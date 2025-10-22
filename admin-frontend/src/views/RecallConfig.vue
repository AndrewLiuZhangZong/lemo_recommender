<template>
  <div class="recall-config-container">
    <el-card class="header-card">
      <h2>召回策略配置</h2>
      <p>可视化配置标签、作者、分类等召回策略权重</p>
    </el-card>

    <!-- 操作栏 -->
    <el-card style="margin-top: 20px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-select v-model="filterScenarioId" placeholder="筛选场景" clearable style="width: 200px" @change="loadConfigs">
            <el-option
              v-for="scenario in scenarios"
              :key="scenario.scenario_id"
              :label="scenario.scenario_name"
              :value="scenario.scenario_id"
            ></el-option>
          </el-select>
        </el-col>
        <el-col :span="12" style="text-align: right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon> 新建配置
          </el-button>
          <el-button @click="loadConfigs" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 配置列表 -->
    <el-card style="margin-top: 20px">
      <el-table :data="configs" v-loading="loading">
        <el-table-column prop="config_name" label="配置名称" width="180">
          <template #default="{ row }">
            <div>
              <strong>{{ row.config_name }}</strong>
              <el-tag v-if="row.is_default" type="success" size="small" style="margin-left: 8px">默认</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="scenario_id" label="场景" width="120"></el-table-column>

        <el-table-column prop="description" label="描述" min-width="200"></el-table-column>

        <el-table-column prop="strategies" label="策略权重" min-width="300">
          <template #default="{ row }">
            <div style="display: flex; flex-wrap: wrap; gap: 4px">
              <el-tag
                v-for="strategy in row.strategies"
                :key="strategy.strategy"
                :type="strategy.enabled ? 'primary' : 'info'"
                size="small"
              >
                {{ getStrategyName(strategy.strategy) }}: {{ (strategy.weight * 100).toFixed(0) }}%
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="toggleEnabled(row)"
            />
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? formatTime(row.created_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="editConfig(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button v-if="!row.is_default" type="success" size="small" link @click="setDefault(row._id)">
              <el-icon><Check /></el-icon> 设为默认
            </el-button>
            <el-button type="info" size="small" link @click="cloneConfig(row)">
              <el-icon><CopyDocument /></el-icon> 克隆
            </el-button>
            <el-button type="danger" size="small" link @click="deleteConfig(row._id)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑配置对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新建召回配置' : '编辑召回配置'"
      width="900px"
    >
      <el-form :model="configForm" label-width="100px">
        <el-form-item label="配置名称" required>
          <el-input v-model="configForm.config_name" placeholder="输入配置名称" />
        </el-form-item>
        
        <el-form-item label="场景" required>
          <el-select v-model="configForm.scenario_id" placeholder="选择场景" style="width: 100%">
            <el-option
              v-for="scenario in scenarios"
              :key="scenario.scenario_id"
              :label="scenario.scenario_name"
              :value="scenario.scenario_id"
            ></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="configForm.description" type="textarea" :rows="2" placeholder="配置描述" />
        </el-form-item>
        
        <el-form-item label="设为默认">
          <el-switch v-model="configForm.is_default" />
        </el-form-item>

        <el-divider content-position="left">召回策略权重配置</el-divider>

        <div v-for="(strategy, index) in configForm.strategies" :key="index" style="margin-bottom: 20px">
          <el-card shadow="never">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px">
              <div>
                <el-checkbox v-model="strategy.enabled">
                  <strong>{{ getStrategyName(strategy.strategy) }}</strong>
                </el-checkbox>
                <el-text size="small" type="info" style="margin-left: 10px">
                  {{ getStrategyDesc(strategy.strategy) }}
                </el-text>
              </div>
              <el-text type="primary" style="font-size: 16px">
                {{ (strategy.weight * 100).toFixed(0) }}%
              </el-text>
            </div>
            
            <el-slider
              v-model="strategy.weight"
              :min="0"
              :max="1"
              :step="0.05"
              :disabled="!strategy.enabled"
              @input="normalizeWeights"
            />
            
            <!-- 策略参数配置 -->
            <div v-if="strategy.enabled && strategy.params" style="margin-top: 10px; padding: 10px; background: #f5f7fa; border-radius: 4px">
              <el-text size="small" type="info">参数配置</el-text>
              <el-form :model="strategy.params" label-width="150px" size="small" style="margin-top: 10px">
                <el-form-item
                  v-for="(value, key) in strategy.params"
                  :key="key"
                  :label="key"
                >
                  <el-input-number
                    v-if="typeof value === 'number'"
                    v-model="strategy.params[key]"
                    :step="0.1"
                    size="small"
                  />
                  <el-input v-else v-model="strategy.params[key]" size="small" />
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </div>

        <el-alert
          v-if="!isWeightValid"
          type="warning"
          title="权重总和不为100%"
          :description="`当前启用策略权重总和为 ${(totalWeight * 100).toFixed(0)}%，请调整至100%`"
          show-icon
          :closable="false"
        />
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitConfig" :disabled="!isWeightValid" :loading="submitting">
          {{ dialogMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Edit, Delete, Check, CopyDocument } from '@element-plus/icons-vue'
import api from '../api'

const scenarios = ref([])
const configs = ref([])
const availableStrategies = ref([])
const loading = ref(false)
const submitting = ref(false)
const filterScenarioId = ref('')
const dialogVisible = ref(false)
const dialogMode = ref('create')
const currentConfigId = ref(null)

const configForm = ref({
  config_name: '',
  scenario_id: '',
  description: '',
  is_default: false,
  strategies: []
})

// 计算权重总和
const totalWeight = computed(() => {
  return configForm.value.strategies
    .filter(s => s.enabled)
    .reduce((sum, s) => sum + s.weight, 0)
})

// 验证权重是否有效
const isWeightValid = computed(() => {
  return Math.abs(totalWeight.value - 1.0) < 0.01
})

// 加载场景列表
const loadScenarios = async () => {
  try {
    const response = await api.get('/scenarios')
    scenarios.value = response.data.scenarios || []
  } catch (error) {
    console.error('加载场景列表失败:', error)
  }
}

// 加载可用策略列表
const loadAvailableStrategies = async () => {
  try {
    const response = await api.get('/recall-config/strategies/available')
    availableStrategies.value = response.data.strategies || []
  } catch (error) {
    console.error('加载策略列表失败:', error)
  }
}

// 加载配置列表
const loadConfigs = async () => {
  loading.value = true
  try {
    const params = filterScenarioId.value ? { scenario_id: filterScenarioId.value } : {}
    const response = await api.get('/recall-config', { params })
    configs.value = response.data.configs || []
  } catch (error) {
    ElMessage.error('加载配置列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 获取策略名称
const getStrategyName = (strategy) => {
  const strategyMap = {
    'hot_items': '热门物品',
    'collaborative_filtering': '协同过滤',
    'vector_search': '向量召回',
    'tag_based': '标签召回',
    'author_based': '作者召回',
    'category_based': '分类召回'
  }
  return strategyMap[strategy] || strategy
}

// 获取策略描述
const getStrategyDesc = (strategy) => {
  const found = availableStrategies.value.find(s => s.strategy === strategy)
  return found ? found.description : ''
}

// 标准化权重
const normalizeWeights = () => {
  const enabledStrategies = configForm.value.strategies.filter(s => s.enabled)
  if (enabledStrategies.length === 0) return
  
  // 如果总和接近1，不做调整
  if (Math.abs(totalWeight.value - 1.0) < 0.1) return
  
  // 否则，按比例调整
  const sum = totalWeight.value
  if (sum > 0) {
    enabledStrategies.forEach(s => {
      s.weight = s.weight / sum
    })
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogMode.value = 'create'
  currentConfigId.value = null
  
  // 初始化表单
  configForm.value = {
    config_name: '',
    scenario_id: filterScenarioId.value || '',
    description: '',
    is_default: false,
    strategies: availableStrategies.value.map(s => ({
      strategy: s.strategy,
      weight: s.default_weight,
      enabled: true,
      params: s.params ? Object.fromEntries(
        Object.entries(s.params).map(([key, param]) => [key, param.default])
      ) : {}
    }))
  }
  
  dialogVisible.value = true
}

// 编辑配置
const editConfig = (config) => {
  dialogMode.value = 'edit'
  currentConfigId.value = config._id
  
  configForm.value = {
    config_name: config.config_name,
    scenario_id: config.scenario_id,
    description: config.description || '',
    is_default: config.is_default,
    strategies: config.strategies.map(s => ({ ...s }))
  }
  
  dialogVisible.value = true
}

// 提交配置
const submitConfig = async () => {
  if (!configForm.value.config_name) {
    ElMessage.warning('请输入配置名称')
    return
  }
  
  if (!configForm.value.scenario_id) {
    ElMessage.warning('请选择场景')
    return
  }
  
  if (!isWeightValid.value) {
    ElMessage.warning('权重总和必须为100%')
    return
  }
  
  submitting.value = true
  
  try {
    if (dialogMode.value === 'create') {
      await api.post('/recall-config', configForm.value)
      ElMessage.success('创建成功')
    } else {
      await api.put(`/recall-config/${currentConfigId.value}`, configForm.value)
      ElMessage.success('更新成功')
    }
    
    dialogVisible.value = false
    await loadConfigs()
  } catch (error) {
    ElMessage.error('操作失败: ' + error.message)
  } finally {
    submitting.value = false
  }
}

// 切换启用状态
const toggleEnabled = async (config) => {
  try {
    await api.put(`/recall-config/${config._id}`, {
      enabled: config.enabled
    })
    ElMessage.success('状态已更新')
  } catch (error) {
    config.enabled = !config.enabled
    ElMessage.error('更新失败: ' + error.message)
  }
}

// 设为默认
const setDefault = async (configId) => {
  try {
    await api.put(`/recall-config/${configId}`, {
      is_default: true
    })
    ElMessage.success('已设为默认配置')
    await loadConfigs()
  } catch (error) {
    ElMessage.error('操作失败: ' + error.message)
  }
}

// 克隆配置
const cloneConfig = async (config) => {
  try {
    const { value: newName } = await ElMessageBox.prompt('请输入新配置名称', '克隆配置', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: config.config_name + ' (副本)'
    })
    
    if (newName) {
      await api.post(`/recall-config/${config._id}/clone?new_name=${encodeURIComponent(newName)}`)
      ElMessage.success('克隆成功')
      await loadConfigs()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('克隆失败: ' + error.message)
    }
  }
}

// 删除配置
const deleteConfig = async (configId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个配置吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/recall-config/${configId}`)
    ElMessage.success('删除成功')
    await loadConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadScenarios()
  loadAvailableStrategies()
  loadConfigs()
})
</script>

<style scoped>
.recall-config-container {
  padding: 20px;
}

.header-card h2 {
  margin: 0 0 10px 0;
  font-size: 24px;
}

.header-card p {
  margin: 0;
  color: #909399;
}
</style>

