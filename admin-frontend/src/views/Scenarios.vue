<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>场景列表</span>
          <el-button type="primary" @click="showDialog = true">
            <el-icon><Plus /></el-icon>
            新建场景
          </el-button>
        </div>
      </template>

      <el-table :data="scenarios" v-loading="loading">
        <el-table-column prop="scenario_id" label="场景ID" width="180" />
        <el-table-column prop="name" label="场景名称" />
        <el-table-column prop="scenario_type" label="场景类型" />
        <el-table-column label="创建时间">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editScenario(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteScenario(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editMode ? '编辑场景' : '新建场景'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="场景ID">
          <el-input v-model="form.scenario_id" :disabled="editMode" />
        </el-form-item>
        <el-form-item label="场景名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="场景类型">
          <el-select v-model="form.scenario_type" style="width: 100%">
            <el-option label="短视频 (vlog)" value="vlog" />
            <el-option label="新闻 (news)" value="news" />
            <el-option label="电商 (ecommerce)" value="ecommerce" />
            <el-option label="自定义 (custom)" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { scenarioApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

const scenarios = ref([])
const loading = ref(false)
const showDialog = ref(false)
const editMode = ref(false)
const form = ref({
  scenario_id: '',
  name: '',
  scenario_type: 'vlog',
  description: '',
  config: {
    recall_strategies: [
      { name: 'hot_items', weight: 0.3 },
      { name: 'collaborative_filtering', weight: 0.4 },
      { name: 'vector_search', weight: 0.3 }
    ]
  }
})

onMounted(() => {
  loadScenarios()
})

async function loadScenarios() {
  loading.value = true
  try {
    scenarios.value = await scenarioApi.list()
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function editScenario(row) {
  form.value = { ...row }
  editMode.value = true
  showDialog.value = true
}

async function deleteScenario(row) {
  try {
    await ElMessageBox.confirm('确认删除该场景？', '提示', { type: 'warning' })
    await scenarioApi.delete(row.scenario_id)
    ElMessage.success('删除成功')
    loadScenarios()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function submitForm() {
  try {
    if (editMode.value) {
      await scenarioApi.update(form.value.scenario_id, form.value)
    } else {
      await scenarioApi.create({
        ...form.value,
        tenant_id: 'demo_tenant',
        created_at: new Date().toISOString()
      })
    }
    ElMessage.success(editMode.value ? '更新成功' : '创建成功')
    showDialog.value = false
    loadScenarios()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>

