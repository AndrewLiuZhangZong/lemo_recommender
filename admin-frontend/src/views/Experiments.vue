<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>AB实验列表</span>
          <el-button type="primary" @click="showDialog = true">
            <el-icon><Plus /></el-icon>
            新建实验
          </el-button>
        </div>
      </template>

      <el-table :data="experiments" v-loading="loading">
        <el-table-column prop="experiment_id" label="实验ID" width="180" />
        <el-table-column prop="name" label="实验名称" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="变体数" width="80">
          <template #default="{ row }">
            {{ row.variants.length }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button size="small" @click="viewResults(row)" v-if="row.status === 'running'">
              查看结果
            </el-button>
            <el-button size="small" type="success" @click="startExp(row)" 
                       v-if="row.status === 'draft'">
              启动
            </el-button>
            <el-button size="small" type="warning" @click="stopExp(row)" 
                       v-if="row.status === 'running'">
              停止
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建对话框（简化） -->
    <el-dialog v-model="showDialog" title="新建实验" width="700px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="实验ID">
          <el-input v-model="form.experiment_id" />
        </el-form-item>
        <el-form-item label="实验名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="场景">
          <el-select v-model="form.scenario_id" style="width: 100%">
            <el-option v-for="s in scenarios" :key="s.scenario_id" 
                       :label="s.name" :value="s.scenario_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="实验假设">
          <el-input v-model="form.hypothesis" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 结果对话框 -->
    <el-dialog v-model="showResultDialog" title="实验结果" width="800px">
      <el-table :data="results">
        <el-table-column prop="variant_id" label="变体" width="120" />
        <el-table-column prop="sample_size" label="样本量" />
        <el-table-column label="CTR">
          <template #default="{ row }">
            {{ (row.metrics.ctr * 100).toFixed(2) }}%
          </template>
        </el-table-column>
        <el-table-column label="提升">
          <template #default="{ row }">
            <span :class="row.lift.ctr > 0 ? 'text-success' : 'text-danger'">
              {{ row.lift.ctr ? row.lift.ctr.toFixed(2) + '%' : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="显著性">
          <template #default="{ row }">
            <el-tag :type="row.is_significant ? 'success' : 'info'">
              {{ row.is_significant ? '显著' : '不显著' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { experimentApi, scenarioApi } from '../api'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const experiments = ref([])
const scenarios = ref([])
const results = ref([])
const loading = ref(false)
const showDialog = ref(false)
const showResultDialog = ref(false)
const form = ref({
  experiment_id: '',
  name: '',
  scenario_id: '',
  hypothesis: '',
  variants: [
    { variant_id: 'control', name: '对照组', traffic_percentage: 50, config: {} },
    { variant_id: 'treatment', name: '实验组', traffic_percentage: 50, config: {} }
  ],
  metrics: {
    primary_metric: 'ctr',
    secondary_metrics: ['avg_watch_duration'],
    guardrail_metrics: []
  }
})

onMounted(async () => {
  scenarios.value = await scenarioApi.list()
  loadExperiments()
})

async function loadExperiments() {
  loading.value = true
  try {
    experiments.value = await experimentApi.list()
  } finally {
    loading.value = false
  }
}

function statusType(status) {
  const map = { draft: 'info', running: 'success', completed: '', paused: 'warning' }
  return map[status] || 'info'
}

function statusText(status) {
  const map = { draft: '草稿', running: '运行中', completed: '已完成', paused: '已暂停' }
  return map[status] || status
}

async function submitForm() {
  try {
    await experimentApi.create({
      ...form.value,
      tenant_id: 'demo_tenant',
      created_by: 'admin',
      traffic_split_method: 'user_id_hash'
    })
    ElMessage.success('创建成功')
    showDialog.value = false
    loadExperiments()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

async function startExp(row) {
  try {
    await experimentApi.start(row.experiment_id)
    ElMessage.success('启动成功')
    loadExperiments()
  } catch (error) {
    ElMessage.error('启动失败')
  }
}

async function stopExp(row) {
  try {
    await experimentApi.stop(row.experiment_id)
    ElMessage.success('停止成功')
    loadExperiments()
  } catch (error) {
    ElMessage.error('停止失败')
  }
}

async function viewResults(row) {
  try {
    results.value = await experimentApi.results(row.experiment_id)
    showResultDialog.value = true
  } catch (error) {
    ElMessage.error('加载结果失败')
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.text-success { color: #67c23a; }
.text-danger { color: #f56c6c; }
</style>

