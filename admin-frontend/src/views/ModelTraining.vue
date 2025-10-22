<template>
  <div class="model-training-container">
    <el-card class="header-card">
      <h2>模型训练管理</h2>
      <p>一键触发Wide&Deep、DeepFM、Two-Tower模型训练</p>
    </el-card>

    <!-- 新建训练任务 -->
    <el-card style="margin-top: 20px">
      <h3 style="margin-top: 0">创建训练任务</h3>
      <el-form :model="trainForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="场景">
              <el-select v-model="trainForm.scenario_id" placeholder="选择场景" style="width: 100%">
                <el-option
                  v-for="scenario in scenarios"
                  :key="scenario.scenario_id"
                  :label="scenario.scenario_name"
                  :value="scenario.scenario_id"
                ></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="模型类型">
              <el-select v-model="trainForm.model_type" placeholder="选择模型" style="width: 100%" @change="loadConfigTemplate">
                <el-option label="Wide & Deep" value="wide_deep"></el-option>
                <el-option label="DeepFM" value="deepfm"></el-option>
                <el-option label="Two-Tower（双塔）" value="two_tower"></el-option>
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="">
              <el-button type="primary" @click="showConfigDialog" :disabled="!trainForm.scenario_id || !trainForm.model_type">
                <el-icon><Setting /></el-icon> 配置参数
              </el-button>
              <el-button type="success" @click="startTraining" :disabled="!trainForm.scenario_id || !trainForm.model_type" :loading="trainSubmitting">
                <el-icon><VideoPlay /></el-icon> 开始训练
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 训练任务列表 -->
    <el-card style="margin-top: 20px">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px">
        <h3 style="margin: 0">训练任务列表</h3>
        <el-button @click="loadTasks" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>

      <el-table :data="tasks" v-loading="loading">
        <el-table-column prop="task_id" label="任务ID" width="280">
          <template #default="{ row }">
            <el-text size="small" type="info">{{ row.task_id }}</el-text>
          </template>
        </el-table-column>
        
        <el-table-column prop="model_type" label="模型类型" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.model_type === 'wide_deep'" type="primary">Wide & Deep</el-tag>
            <el-tag v-else-if="row.model_type === 'deepfm'" type="success">DeepFM</el-tag>
            <el-tag v-else-if="row.model_type === 'two_tower'" type="warning">Two-Tower</el-tag>
            <el-tag v-else>{{ row.model_type }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="scenario_id" label="场景" width="120"></el-table-column>

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'completed'" type="success">
              <el-icon><Check /></el-icon> 完成
            </el-tag>
            <el-tag v-else-if="row.status === 'running'" type="primary" effect="dark">
              <el-icon><Loading /></el-icon> 运行中
            </el-tag>
            <el-tag v-else-if="row.status === 'pending'" type="info">
              <el-icon><Clock /></el-icon> 等待中
            </el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger">
              <el-icon><Close /></el-icon> 失败
            </el-tag>
            <el-tag v-else type="info">{{ row.status }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? formatTime(row.created_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="指标" min-width="200">
          <template #default="{ row }">
            <div v-if="row.result && row.result.metrics">
              <el-text size="small">
                Loss: {{ row.result.metrics.val_loss?.toFixed(4) || '-' }}
              </el-text>
              <br>
              <el-text size="small" v-if="row.result.metrics.val_auc">
                AUC: {{ row.result.metrics.val_auc.toFixed(4) }}
              </el-text>
              <el-text size="small" v-if="row.result.metrics.recall_at_10">
                Recall@10: {{ row.result.metrics.recall_at_10.toFixed(4) }}
              </el-text>
            </div>
            <el-text v-else size="small" type="info">-</el-text>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="viewTaskDetail(row)">
              <el-icon><View /></el-icon> 详情
            </el-button>
            <el-button 
              v-if="row.status === 'pending' || row.status === 'running'" 
              type="danger" 
              size="small" 
              link 
              @click="cancelTask(row.task_id)"
            >
              <el-icon><Close /></el-icon> 取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 训练配置对话框 -->
    <el-dialog v-model="configDialogVisible" title="训练参数配置" width="600px">
      <el-form :model="trainForm.config" label-width="120px">
        <el-form-item label="训练轮数">
          <el-input-number v-model="trainForm.config.epochs" :min="1" :max="100" />
        </el-form-item>
        <el-form-item label="批量大小">
          <el-input-number v-model="trainForm.config.batch_size" :min="32" :max="1024" :step="32" />
        </el-form-item>
        <el-form-item label="学习率">
          <el-input-number v-model="trainForm.config.learning_rate" :min="0.0001" :max="0.1" :step="0.0001" :precision="4" />
        </el-form-item>
        
        <!-- Wide & Deep 专属参数 -->
        <template v-if="trainForm.model_type === 'wide_deep'">
          <el-divider content-position="left">Wide & Deep 参数</el-divider>
          <el-form-item label="Wide维度">
            <el-input-number v-model="trainForm.config.wide_dim" :min="10" :max="1000" />
          </el-form-item>
          <el-form-item label="Dropout">
            <el-input-number v-model="trainForm.config.dropout" :min="0" :max="0.9" :step="0.1" :precision="1" />
          </el-form-item>
        </template>
        
        <!-- DeepFM 专属参数 -->
        <template v-if="trainForm.model_type === 'deepfm'">
          <el-divider content-position="left">DeepFM 参数</el-divider>
          <el-form-item label="Embedding维度">
            <el-input-number v-model="trainForm.config.embedding_dim" :min="8" :max="256" />
          </el-form-item>
          <el-form-item label="Dropout">
            <el-input-number v-model="trainForm.config.dropout" :min="0" :max="0.9" :step="0.1" :precision="1" />
          </el-form-item>
        </template>
        
        <!-- Two-Tower 专属参数 -->
        <template v-if="trainForm.model_type === 'two_tower'">
          <el-divider content-position="left">Two-Tower 参数</el-divider>
          <el-form-item label="Embedding维度">
            <el-input-number v-model="trainForm.config.embedding_dim" :min="32" :max="512" />
          </el-form-item>
          <el-form-item label="温度系数">
            <el-input-number v-model="trainForm.config.temperature" :min="0.01" :max="1" :step="0.01" :precision="2" />
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="configDialogVisible = false">确定</el-button>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="训练任务详情" width="700px">
      <el-descriptions v-if="currentTask" :column="2" border>
        <el-descriptions-item label="任务ID" :span="2">{{ currentTask.task_id }}</el-descriptions-item>
        <el-descriptions-item label="模型类型">{{ currentTask.model_type }}</el-descriptions-item>
        <el-descriptions-item label="场景">{{ currentTask.scenario_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentTask.status)">{{ currentTask.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentTask.created_at) }}</el-descriptions-item>
        
        <el-descriptions-item label="训练配置" :span="2">
          <pre style="margin: 0">{{ JSON.stringify(currentTask.config || {}, null, 2) }}</pre>
        </el-descriptions-item>
        
        <el-descriptions-item v-if="currentTask.result" label="训练结果" :span="2">
          <pre style="margin: 0">{{ JSON.stringify(currentTask.result, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, VideoPlay, Setting, View, Close, Check, Clock, Loading } from '@element-plus/icons-vue'
import api from '../api'

const scenarios = ref([])
const tasks = ref([])
const loading = ref(false)
const trainSubmitting = ref(false)
const configDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const currentTask = ref(null)
let refreshTimer = null

const trainForm = ref({
  scenario_id: '',
  model_type: '',
  config: {
    epochs: 10,
    batch_size: 256,
    learning_rate: 0.001
  }
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

// 加载配置模板
const loadConfigTemplate = async () => {
  if (!trainForm.value.model_type) return
  
  try {
    const response = await api.get(`/model-training/config/template?model_type=${trainForm.value.model_type}`)
    trainForm.value.config = response.data
  } catch (error) {
    console.error('加载配置模板失败:', error)
  }
}

// 显示配置对话框
const showConfigDialog = () => {
  configDialogVisible.value = true
}

// 开始训练
const startTraining = async () => {
  if (!trainForm.value.scenario_id || !trainForm.value.model_type) {
    ElMessage.warning('请选择场景和模型类型')
    return
  }
  
  trainSubmitting.value = true
  
  try {
    await api.post('/model-training/train', trainForm.value)
    ElMessage.success('训练任务已提交')
    await loadTasks()
    
    // 重置表单
    trainForm.value = {
      scenario_id: '',
      model_type: '',
      config: {
        epochs: 10,
        batch_size: 256,
        learning_rate: 0.001
      }
    }
  } catch (error) {
    ElMessage.error('提交失败: ' + error.message)
  } finally {
    trainSubmitting.value = false
  }
}

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const response = await api.get('/model-training/tasks?limit=50')
    tasks.value = response.data.tasks || []
  } catch (error) {
    ElMessage.error('加载任务列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 查看任务详情
const viewTaskDetail = async (task) => {
  try {
    const response = await api.get(`/model-training/tasks/${task.task_id}`)
    currentTask.value = response.data
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载详情失败: ' + error.message)
  }
}

// 取消任务
const cancelTask = async (taskId) => {
  try {
    await ElMessageBox.confirm('确定要取消这个训练任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.delete(`/model-training/tasks/${taskId}`)
    ElMessage.success('任务已取消')
    await loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消失败: ' + error.message)
    }
  }
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    'completed': 'success',
    'running': 'primary',
    'pending': 'info',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

// 自动刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    loadTasks()
  }, 10000) // 每10秒刷新
}

onMounted(() => {
  loadScenarios()
  loadTasks()
  startAutoRefresh()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.model-training-container {
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

