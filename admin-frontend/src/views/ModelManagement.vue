<template>
  <div class="model-management-container">
    <el-card class="header-card">
      <h2>排序模型管理</h2>
      <p>上传、部署、切换排序模型</p>
    </el-card>

    <!-- 操作栏 -->
    <el-card style="margin-top: 20px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-select v-model="filterScenarioId" placeholder="筛选场景" clearable style="width: 150px; margin-right: 10px" @change="loadModels">
            <el-option
              v-for="scenario in scenarios"
              :key="scenario.scenario_id"
              :label="scenario.scenario_name"
              :value="scenario.scenario_id"
            ></el-option>
          </el-select>
          
          <el-select v-model="filterStatus" placeholder="筛选状态" clearable style="width: 150px" @change="loadModels">
            <el-option label="已部署" value="deployed"></el-option>
            <el-option label="已训练" value="trained"></el-option>
            <el-option label="已上传" value="uploaded"></el-option>
            <el-option label="已归档" value="archived"></el-option>
          </el-select>
        </el-col>
        <el-col :span="12" style="text-align: right">
          <el-button type="primary" @click="showUploadDialog">
            <el-icon><Upload /></el-icon> 上传模型
          </el-button>
          <el-button @click="loadModels" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 模型列表 -->
    <el-card style="margin-top: 20px">
      <el-table :data="models" v-loading="loading">
        <el-table-column prop="model_name" label="模型名称" width="180">
          <template #default="{ row }">
            <div>
              <strong>{{ row.model_name || row.model_type }}</strong>
              <el-tag v-if="isOnline(row._id)" type="success" size="small" style="margin-left: 8px">在线</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="scenario_id" label="场景" width="120"></el-table-column>

        <el-table-column prop="model_type" label="模型类型" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.model_type === 'wide_deep'" type="primary">Wide & Deep</el-tag>
            <el-tag v-else-if="row.model_type === 'deepfm'" type="success">DeepFM</el-tag>
            <el-tag v-else-if="row.model_type === 'two_tower'" type="warning">Two-Tower</el-tag>
            <el-tag v-else>{{ row.model_type }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'deployed'" type="success">已部署</el-tag>
            <el-tag v-else-if="row.status === 'trained'" type="primary">已训练</el-tag>
            <el-tag v-else-if="row.status === 'uploaded'" type="info">已上传</el-tag>
            <el-tag v-else-if="row.status === 'archived'" type="info">已归档</el-tag>
            <el-tag v-else>{{ row.status }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="模型指标" min-width="200">
          <template #default="{ row }">
            <div v-if="row.metrics && Object.keys(row.metrics).length > 0">
              <el-text size="small" v-for="(value, key) in getMainMetrics(row.metrics)" :key="key">
                {{ key }}: {{ value }}
              </el-text>
            </div>
            <el-text v-else size="small" type="info">-</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="trained_at" label="训练时间" width="180">
          <template #default="{ row }">
            {{ row.trained_at ? formatTime(row.trained_at) : '-' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'trained' || row.status === 'uploaded'"
              type="success"
              size="small"
              link
              @click="deployModel(row)"
            >
              <el-icon><Upload /></el-icon> 部署
            </el-button>
            
            <el-button
              v-if="row.status === 'deployed' && !isOnline(row._id)"
              type="primary"
              size="small"
              link
              @click="switchModel(row)"
            >
              <el-icon><Switch /></el-icon> 切换
            </el-button>
            
            <el-button
              v-if="row.status === 'deployed'"
              type="warning"
              size="small"
              link
              @click="archiveModel(row._id)"
            >
              <el-icon><Box /></el-icon> 归档
            </el-button>
            
            <el-button
              type="primary"
              size="small"
              link
              @click="viewModelDetail(row)"
            >
              <el-icon><View /></el-icon> 详情
            </el-button>
            
            <el-button
              v-if="row.status !== 'deployed'"
              type="danger"
              size="small"
              link
              @click="deleteModel(row._id)"
            >
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 上传模型对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传模型" width="600px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="场景" required>
          <el-select v-model="uploadForm.scenario_id" placeholder="选择场景" style="width: 100%">
            <el-option
              v-for="scenario in scenarios"
              :key="scenario.scenario_id"
              :label="scenario.scenario_name"
              :value="scenario.scenario_id"
            ></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型类型" required>
          <el-select v-model="uploadForm.model_type" placeholder="选择模型类型" style="width: 100%">
            <el-option label="Wide & Deep" value="wide_deep"></el-option>
            <el-option label="DeepFM" value="deepfm"></el-option>
            <el-option label="Two-Tower" value="two_tower"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="模型名称" required>
          <el-input v-model="uploadForm.model_name" placeholder="输入模型名称" />
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="模型描述" />
        </el-form-item>
        
        <el-form-item label="模型文件" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".pt,.pth,.onnx,.pb"
            :on-change="handleFileChange"
          >
            <el-button>选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持的格式: .pt, .pth (PyTorch), .onnx (ONNX), .pb (TensorFlow)
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">上传</el-button>
      </template>
    </el-dialog>

    <!-- 模型详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="模型详情" width="700px">
      <el-descriptions v-if="currentModel" :column="2" border>
        <el-descriptions-item label="模型名称" :span="2">{{ currentModel.model_name }}</el-descriptions-item>
        <el-descriptions-item label="模型类型">{{ currentModel.model_type }}</el-descriptions-item>
        <el-descriptions-item label="场景">{{ currentModel.scenario_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentModel.status)">{{ currentModel.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="训练时间">{{ formatTime(currentModel.trained_at) }}</el-descriptions-item>
        
        <el-descriptions-item label="描述" :span="2">
          {{ currentModel.description || '-' }}
        </el-descriptions-item>
        
        <el-descriptions-item label="训练配置" :span="2">
          <pre style="margin: 0">{{ JSON.stringify(currentModel.config || {}, null, 2) }}</pre>
        </el-descriptions-item>
        
        <el-descriptions-item label="模型指标" :span="2">
          <pre style="margin: 0">{{ JSON.stringify(currentModel.metrics || {}, null, 2) }}</pre>
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
import { Upload, Refresh, View, Delete, Switch, Box } from '@element-plus/icons-vue'
import api from '../api'

const scenarios = ref([])
const models = ref([])
const loading = ref(false)
const uploading = ref(false)
const filterScenarioId = ref('')
const filterStatus = ref('')
const uploadDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const currentModel = ref(null)
const uploadFile = ref(null)

const uploadForm = ref({
  scenario_id: '',
  model_type: '',
  model_name: '',
  description: ''
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

// 加载模型列表
const loadModels = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterScenarioId.value) params.scenario_id = filterScenarioId.value
    if (filterStatus.value) params.status = filterStatus.value
    
    const response = await api.get('/model-management/list', { params })
    models.value = response.data.models || []
  } catch (error) {
    ElMessage.error('加载模型列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 检查是否为在线模型
const isOnline = (modelId) => {
  const scenario = scenarios.value.find(s => s.online_model_id === modelId)
  return !!scenario
}

// 获取主要指标
const getMainMetrics = (metrics) => {
  const mainMetrics = {}
  if (metrics.val_auc) mainMetrics['AUC'] = metrics.val_auc.toFixed(4)
  if (metrics.val_loss) mainMetrics['Loss'] = metrics.val_loss.toFixed(4)
  if (metrics.recall_at_10) mainMetrics['Recall@10'] = metrics.recall_at_10.toFixed(4)
  return mainMetrics
}

// 显示上传对话框
const showUploadDialog = () => {
  uploadDialogVisible.value = true
  uploadForm.value = {
    scenario_id: filterScenarioId.value || '',
    model_type: '',
    model_name: '',
    description: ''
  }
  uploadFile.value = null
}

// 处理文件选择
const handleFileChange = (file) => {
  uploadFile.value = file.raw
}

// 提交上传
const submitUpload = async () => {
  if (!uploadForm.value.scenario_id || !uploadForm.value.model_type || !uploadForm.value.model_name) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  if (!uploadFile.value) {
    ElMessage.warning('请选择模型文件')
    return
  }
  
  uploading.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)
    formData.append('scenario_id', uploadForm.value.scenario_id)
    formData.append('model_type', uploadForm.value.model_type)
    formData.append('model_name', uploadForm.value.model_name)
    if (uploadForm.value.description) {
      formData.append('description', uploadForm.value.description)
    }
    
    await api.post('/model-management/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    ElMessage.success('模型上传成功')
    uploadDialogVisible.value = false
    await loadModels()
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    uploading.value = false
  }
}

// 部署模型
const deployModel = async (model) => {
  try {
    await ElMessageBox.confirm('确定要部署这个模型吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    
    await api.post('/model-management/deploy', {
      model_id: model._id,
      scenario_id: model.scenario_id
    })
    
    ElMessage.success('模型已部署')
    await loadModels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('部署失败: ' + error.message)
    }
  }
}

// 切换模型
const switchModel = async (model) => {
  try {
    await ElMessageBox.confirm('确定要切换到这个模型吗？切换后会立即生效。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.post('/model-management/switch', {
      scenario_id: model.scenario_id,
      model_id: model._id
    })
    
    ElMessage.success('模型已切换')
    await loadScenarios() // 重新加载场景以更新在线模型
    await loadModels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('切换失败: ' + error.message)
    }
  }
}

// 归档模型
const archiveModel = async (modelId) => {
  try {
    await ElMessageBox.confirm('确定要归档这个模型吗？归档后将下线。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await api.post(`/model-management/${modelId}/archive`)
    ElMessage.success('模型已归档')
    await loadModels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('归档失败: ' + error.message)
    }
  }
}

// 删除模型
const deleteModel = async (modelId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个模型吗？此操作不可恢复。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'danger'
    })
    
    await api.delete(`/model-management/${modelId}`)
    ElMessage.success('模型已删除')
    await loadModels()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

// 查看模型详情
const viewModelDetail = async (model) => {
  currentModel.value = model
  detailDialogVisible.value = true
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
    'deployed': 'success',
    'trained': 'primary',
    'uploaded': 'info',
    'archived': 'info'
  }
  return typeMap[status] || 'info'
}

onMounted(() => {
  loadScenarios()
  loadModels()
})
</script>

<style scoped>
.model-management-container {
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

