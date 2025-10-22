<template>
  <div class="jobs-container">
    <el-card class="header-card">
      <h2>作业管理中心</h2>
      <p>管理Flink实时作业、Celery任务、模型训练等</p>
    </el-card>

    <!-- 操作栏 -->
    <el-card style="margin-top: 20px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-select v-model="filterType" placeholder="筛选作业类型" clearable style="width: 200px" @change="loadJobs">
            <el-option label="全部" value=""></el-option>
            <el-option label="Flink作业" value="flink"></el-option>
            <el-option label="Celery任务" value="celery"></el-option>
            <el-option label="模型训练" value="model_training"></el-option>
          </el-select>
        </el-col>
        <el-col :span="12" style="text-align: right">
          <el-button type="primary" @click="loadJobs" :loading="loading">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
          <el-button type="success" @click="batchStart" :disabled="selectedJobs.length === 0">
            批量启动
          </el-button>
          <el-button type="danger" @click="batchStop" :disabled="selectedJobs.length === 0">
            批量停止
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 作业列表 -->
    <el-card style="margin-top: 20px">
      <el-table :data="jobs" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55"></el-table-column>
        
        <el-table-column prop="name" label="作业名称" min-width="180">
          <template #default="{ row }">
            <div>
              <strong>{{ row.name }}</strong>
              <div style="font-size: 12px; color: #909399">{{ row.description }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="job_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.job_type === 'flink'" type="primary">Flink</el-tag>
            <el-tag v-else-if="row.job_type === 'celery'" type="success">Celery</el-tag>
            <el-tag v-else-if="row.job_type === 'model_training'" type="warning">模型训练</el-tag>
            <el-tag v-else>其他</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'running'" type="success" effect="dark">
              <el-icon><VideoPlay /></el-icon> 运行中
            </el-tag>
            <el-tag v-else-if="row.status === 'stopped'" type="info">
              <el-icon><VideoPause /></el-icon> 已停止
            </el-tag>
            <el-tag v-else-if="row.status === 'starting'" type="warning">
              <el-icon><Loading /></el-icon> 启动中
            </el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger">
              <el-icon><CircleClose /></el-icon> 失败
            </el-tag>
            <el-tag v-else type="info">{{ row.status }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="pid" label="进程ID" width="100"></el-table-column>

        <el-table-column prop="start_time" label="启动时间" width="180">
          <template #default="{ row }">
            {{ row.start_time ? formatTime(row.start_time) : '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="restart_count" label="重启次数" width="100"></el-table-column>

        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status !== 'running'" 
              type="primary" 
              size="small" 
              @click="startJob(row.job_id)"
              :loading="row.loading"
            >
              <el-icon><VideoPlay /></el-icon> 启动
            </el-button>
            
            <el-button 
              v-if="row.status === 'running'" 
              type="warning" 
              size="small" 
              @click="stopJob(row.job_id)"
              :loading="row.loading"
            >
              <el-icon><VideoPause /></el-icon> 停止
            </el-button>
            
            <el-button 
              type="info" 
              size="small" 
              @click="restartJob(row.job_id)"
              :loading="row.loading"
            >
              <el-icon><Refresh /></el-icon> 重启
            </el-button>
            
            <el-button 
              type="primary" 
              size="small" 
              link
              @click="viewLogs(row.job_id)"
            >
              <el-icon><Document /></el-icon> 日志
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 日志查看对话框 -->
    <el-dialog v-model="logDialogVisible" title="作业日志" width="80%">
      <el-input
        v-model="jobLogs"
        type="textarea"
        :rows="20"
        readonly
        placeholder="暂无日志"
      ></el-input>
      <template #footer>
        <el-button @click="logDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, VideoPlay, VideoPause, CircleClose, Loading, Document } from '@element-plus/icons-vue'
import api from '../api'

const jobs = ref([])
const loading = ref(false)
const filterType = ref('')
const selectedJobs = ref([])
const logDialogVisible = ref(false)
const jobLogs = ref('')
let refreshTimer = null

// 加载作业列表
const loadJobs = async () => {
  loading.value = true
  try {
    const params = filterType.value ? { job_type: filterType.value } : {}
    const response = await api.get('/jobs/list', { params })
    jobs.value = response.data.jobs || []
  } catch (error) {
    ElMessage.error('加载作业列表失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 启动作业
const startJob = async (jobId) => {
  try {
    const job = jobs.value.find(j => j.job_id === jobId)
    if (job) job.loading = true
    
    await api.post('/jobs/start', { job_id: jobId })
    ElMessage.success('作业已启动')
    await loadJobs()
  } catch (error) {
    ElMessage.error('启动失败: ' + error.message)
  } finally {
    const job = jobs.value.find(j => j.job_id === jobId)
    if (job) job.loading = false
  }
}

// 停止作业
const stopJob = async (jobId, force = false) => {
  try {
    const job = jobs.value.find(j => j.job_id === jobId)
    if (job) job.loading = true
    
    await api.post('/jobs/stop', { job_id: jobId, force })
    ElMessage.success('作业已停止')
    await loadJobs()
  } catch (error) {
    ElMessage.error('停止失败: ' + error.message)
  } finally {
    const job = jobs.value.find(j => j.job_id === jobId)
    if (job) job.loading = false
  }
}

// 重启作业
const restartJob = async (jobId) => {
  try {
    const job = jobs.value.find(j => j.job_id === jobId)
    if (job) job.loading = true
    
    await api.post(`/jobs/restart/${jobId}`)
    ElMessage.success('作业已重启')
    await loadJobs()
  } catch (error) {
    ElMessage.error('重启失败: ' + error.message)
  } finally {
    const job = jobs.value.find(j => j.job_id === jobId)
    if (job) job.loading = false
  }
}

// 批量启动
const batchStart = async () => {
  const jobIds = selectedJobs.value.map(j => j.job_id)
  try {
    await api.post('/jobs/batch/start', jobIds)
    ElMessage.success('批量启动完成')
    await loadJobs()
  } catch (error) {
    ElMessage.error('批量启动失败: ' + error.message)
  }
}

// 批量停止
const batchStop = async () => {
  const jobIds = selectedJobs.value.map(j => j.job_id)
  try {
    await api.post('/jobs/batch/stop', { job_ids: jobIds })
    ElMessage.success('批量停止完成')
    await loadJobs()
  } catch (error) {
    ElMessage.error('批量停止失败: ' + error.message)
  }
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedJobs.value = selection
}

// 查看日志
const viewLogs = (jobId) => {
  logDialogVisible.value = true
  jobLogs.value = '日志功能开发中...\n\n可以通过以下命令查看日志:\n\ntail -f logs/flink_jobs.log'
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN')
}

// 自动刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    loadJobs()
  }, 5000) // 每5秒刷新
}

onMounted(() => {
  loadJobs()
  startAutoRefresh()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.jobs-container {
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

