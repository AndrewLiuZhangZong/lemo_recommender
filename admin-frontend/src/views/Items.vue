<template>
  <div>
    <el-card>
      <template #header>
        <div class="card-header">
          <span>物品列表</span>
          <el-space>
            <el-button type="primary" @click="showDialog = true">
              <el-icon><Plus /></el-icon>
              新建物品
            </el-button>
            <el-button @click="showBatchDialog = true">
              <el-icon><Upload /></el-icon>
              批量导入
            </el-button>
          </el-space>
        </div>
      </template>

      <el-form :inline="true" class="filter-form">
        <el-form-item label="场景">
          <el-select v-model="filters.scenario_id" style="width: 200px" @change="loadItems">
            <el-option label="全部" value="" />
            <el-option v-for="s in scenarios" :key="s.scenario_id" 
                       :label="s.name" :value="s.scenario_id" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadItems">查询</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="items" v-loading="loading">
        <el-table-column prop="item_id" label="物品ID" width="180" />
        <el-table-column prop="scenario_id" label="场景" width="150" />
        <el-table-column label="标题">
          <template #default="{ row }">
            {{ row.metadata.title || row.metadata.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="分类">
          <template #default="{ row }">
            {{ row.metadata.category || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString('zh-CN') }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建对话框 -->
    <el-dialog v-model="showDialog" title="新建物品" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="物品ID">
          <el-input v-model="form.item_id" />
        </el-form-item>
        <el-form-item label="场景">
          <el-select v-model="form.scenario_id" style="width: 100%">
            <el-option v-for="s in scenarios" :key="s.scenario_id" 
                       :label="s.name" :value="s.scenario_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.metadata.title" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="form.metadata.category" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="form.metadata.author" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="showBatchDialog" title="批量导入" width="600px">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        请输入JSON格式的物品数据（数组）
      </el-alert>
      <el-input v-model="batchData" type="textarea" :rows="12" 
                placeholder='[{"item_id": "item_001", "scenario_id": "vlog_main_feed", "metadata": {...}}]' />
      <template #footer>
        <el-button @click="showBatchDialog = false">取消</el-button>
        <el-button type="primary" @click="submitBatch">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { itemApi, scenarioApi } from '../api'
import { ElMessage } from 'element-plus'
import { Plus, Upload } from '@element-plus/icons-vue'

const items = ref([])
const scenarios = ref([])
const loading = ref(false)
const showDialog = ref(false)
const showBatchDialog = ref(false)
const filters = ref({ scenario_id: '' })
const batchData = ref('')
const form = ref({
  item_id: '',
  scenario_id: '',
  metadata: {
    title: '',
    category: '',
    author: ''
  }
})

onMounted(async () => {
  scenarios.value = await scenarioApi.list()
  loadItems()
})

async function loadItems() {
  loading.value = true
  try {
    items.value = await itemApi.list(filters.value)
  } finally {
    loading.value = false
  }
}

async function submitForm() {
  try {
    await itemApi.create({
      ...form.value,
      tenant_id: 'demo_tenant',
      created_at: new Date().toISOString()
    })
    ElMessage.success('创建成功')
    showDialog.value = false
    loadItems()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

async function submitBatch() {
  try {
    const data = JSON.parse(batchData.value)
    await itemApi.batchImport({ items: data })
    ElMessage.success(`成功导入 ${data.length} 条数据`)
    showBatchDialog.value = false
    loadItems()
  } catch (error) {
    ElMessage.error('导入失败：' + error.message)
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.filter-form {
  margin-bottom: 16px;
}
</style>

