<template>
  <div class="feature-config-container">
    <el-card class="header-card">
      <h2>实时特征配置</h2>
      <p>管理实时特征计算规则，配置Flink特征工程作业</p>
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
            <strong>{{ row.config_name }}</strong>
          </template>
        </el-table-column>

        <el-table-column prop="scenario_id" label="场景" width="120"></el-table-column>

        <el-table-column prop="description" label="描述" min-width="200"></el-table-column>

        <el-table-column prop="feature_rules" label="特征数量" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.feature_rules.length }} 个</el-tag>
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

        <el-table-column prop="deployed" label="已部署" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.deployed" type="success">是</el-tag>
            <el-tag v-else type="info">否</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? formatTime(row.created_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="editConfig(row)">
              <el-icon><Edit /></el-icon> 编辑
            </el-button>
            <el-button type="success" size="small" link @click="deployConfig(row._id)">
              <el-icon><Upload /></el-icon> 部署
            </el-button>
            <el-button type="info" size="small" link @click="viewDetail(row)">
              <el-icon><View /></el-icon> 详情
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
      :title="dialogMode === 'create' ? '新建特征配置' : '编辑特征配置'"
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

        <el-divider content-position="left">
          特征规则
          <el-button type="primary" size="small" @click="addFeatureRule" style="margin-left: 10px">
            <el-icon><Plus /></el-icon> 添加
          </el-button>
        </el-divider>

        <div v-for="(rule, index) in configForm.feature_rules" :key="index" style="margin-bottom: 20px">
          <el-card shadow="never">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px">
              <el-checkbox v-model="rule.enabled">
                <strong>特征 #{{ index + 1 }}</strong>
              </el-checkbox>
              <el-button type="danger" size="small" link @click="removeFeatureRule(index)">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </div>
            
            <el-form :model="rule" label-width="120px" size="small">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="特征名称">
                    <el-input v-model="rule.feature_name" placeholder="feature_name" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="特征类型">
                    <el-select v-model="rule.feature_type" placeholder="选择类型" style="width: 100%">
                      <el-option label="计数 (count)" value="count"></el-option>
                      <el-option label="求和 (sum)" value="sum"></el-option>
                      <el-option label="平均值 (avg)" value="avg"></el-option>
                      <el-option label="比率 (ratio)" value="ratio"></el-option>
                      <el-option label="列表 (list)" value="list"></el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="聚合窗口">
                    <el-select v-model="rule.aggregation_window" placeholder="选择窗口" style="width: 100%">
                      <el-option label="5分钟" value="5m"></el-option>
                      <el-option label="1小时" value="1h"></el-option>
                      <el-option label="1天" value="1d"></el-option>
                      <el-option label="7天" value="7d"></el-option>
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="源字段">
                    <el-input v-model="rule.source_field" placeholder="field_name" />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </el-card>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitConfig" :loading="submitting">
          {{ dialogMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="特征配置详情" width="800px">
      <el-descriptions v-if="currentConfig" :column="2" border>
        <el-descriptions-item label="配置名称" :span="2">{{ currentConfig.config_name }}</el-descriptions-item>
        <el-descriptions-item label="场景">{{ currentConfig.scenario_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentConfig.enabled ? 'success' : 'info'">
            {{ currentConfig.enabled ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="已部署">
          <el-tag :type="currentConfig.deployed ? 'success' : 'info'">
            {{ currentConfig.deployed ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatTime(currentConfig.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ currentConfig.description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="特征规则" :span="2">
          <el-table :data="currentConfig.feature_rules" size="small">
            <el-table-column prop="feature_name" label="特征名称" width="180"></el-table-column>
            <el-table-column prop="feature_type" label="类型" width="100"></el-table-column>
            <el-table-column prop="aggregation_window" label="窗口" width="100"></el-table-column>
            <el-table-column prop="source_field" label="源字段" width="150"></el-table-column>
            <el-table-column prop="enabled" label="启用" width="80">
              <template #default="{ row }">
                <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
                  {{ row.enabled ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Edit, Delete, View, Upload } from '@element-plus/icons-vue'
import api from '../api'

const scenarios = ref([])
const configs = ref([])
const loading = ref(false)
const submitting = ref(false)
const filterScenarioId = ref('')
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const dialogMode = ref('create')
const currentConfigId = ref(null)
const currentConfig = ref(null)

const configForm = ref({
  config_name: '',
  scenario_id: '',
  description: '',
  feature_rules: []
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

// 加载配置列表
const loadConfigs = async () => {
  loading.value = true
  try {
    const params = filterScenarioId.value ? { scenario_id: filterScenarioId.value } : {}
    const response = await api.get('/feature-config', { params })
    configs.value = response.data.configs || []
  } catch (error) {
    ElMessage.error('加载配置列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogMode.value = 'create'
  currentConfigId.value = null
  
  configForm.value = {
    config_name: '',
    scenario_id: filterScenarioId.value || '',
    description: '',
    feature_rules: []
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
    feature_rules: config.feature_rules.map(r => ({ ...r }))
  }
  
  dialogVisible.value = true
}

// 添加特征规则
const addFeatureRule = () => {
  configForm.value.feature_rules.push({
    feature_name: '',
    feature_type: 'count',
    aggregation_window: '1h',
    source_field: '',
    filter_condition: null,
    enabled: true
  })
}

// 删除特征规则
const removeFeatureRule = (index) => {
  configForm.value.feature_rules.splice(index, 1)
}

// 提交配置
const submitConfig = async () => {
  if (!configForm.value.config_name || !configForm.value.scenario_id) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  if (configForm.value.feature_rules.length === 0) {
    ElMessage.warning('请至少添加一个特征规则')
    return
  }
  
  submitting.value = true
  
  try {
    if (dialogMode.value === 'create') {
      await api.post('/feature-config', configForm.value)
      ElMessage.success('创建成功')
    } else {
      await api.put(`/feature-config/${currentConfigId.value}`, configForm.value)
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
    await api.put(`/feature-config/${config._id}`, {
      enabled: config.enabled
    })
    ElMessage.success('状态已更新')
  } catch (error) {
    config.enabled = !config.enabled
    ElMessage.error('更新失败: ' + error.message)
  }
}

// 部署配置
const deployConfig = async (configId) => {
  try {
    await ElMessageBox.confirm('确定要部署这个配置到Flink作业吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.post(`/feature-config/${configId}/deploy`)
    ElMessage.success('配置已部署')
    await loadConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('部署失败: ' + error.message)
    }
  }
}

// 查看详情
const viewDetail = (config) => {
  currentConfig.value = config
  detailDialogVisible.value = true
}

// 删除配置
const deleteConfig = async (configId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个配置吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/feature-config/${configId}`)
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
  loadConfigs()
})
</script>

<style scoped>
.feature-config-container {
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

