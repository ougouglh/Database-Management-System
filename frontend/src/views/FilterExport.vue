<template>
  <div class="filter-export-page">
    <div class="page-header">
      <h2 class="page-title">筛选导出 / 批量更新</h2>
      <p class="page-desc">按自定义条件筛选数据，导出或批量更新字段</p>
    </div>

    <el-card shadow="never" class="filter-card">
      <template #header>
        <div class="card-header">
          <el-icon :size="20" color="#1890ff"><Filter /></el-icon>
          <span>筛选条件</span>
          <el-button text type="primary" @click="resetFilters">重置</el-button>
        </div>
      </template>

      <el-form :model="filters" label-position="top">
        <el-row :gutter="16">
          <el-col :xs="24" :md="8">
            <el-form-item label="表名">
              <el-select v-model="filters.table" placeholder="请选择表" style="width: 100%">
                <el-option
                  v-for="t in tables"
                  :key="t"
                  :label="t"
                  :value="t"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="关键字">
              <el-input v-model="filters.keyword" placeholder="按 item_barcode / item_name 模糊搜索" clearable />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :md="8">
            <el-form-item label="数量限制">
              <el-input-number v-model="filters.limit" :min="0" :step="100" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="WHERE 条件（可选）">
          <el-input
            v-model="filters.where"
            type="textarea"
            :rows="3"
            placeholder="例: new_name IS NULL OR platform LIKE '%淘宝%'"
          />
        </el-form-item>

        <div class="actions">
          <el-button :loading="loading" @click="handleQuery">
            <el-icon><Search /></el-icon> 查询
          </el-button>
          <el-button :loading="exportLoading" @click="handleExport">
            <el-icon><Download /></el-icon> 导出结果
          </el-button>
          <el-button type="primary" :loading="updateLoading" @click="openUpdateDialog">
            <el-icon><EditPen /></el-icon> 批量更新
          </el-button>
        </div>
      </el-form>
    </el-card>

    <el-card shadow="never" class="result-card">
      <template #header>
        <div class="card-header">
          <el-icon :size="18" color="#52c41a"><DataAnalysis /></el-icon>
          <span>查询结果（{{ result.length }} 条）</span>
          <el-tag v-if="lastSql" type="info" size="small" class="sql-tag">SQL: {{ lastSql }}</el-tag>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="result"
        border
        stripe
        size="small"
        max-height="500"
      >
        <el-table-column type="index" label="#" width="60" fixed />
        <el-table-column
          v-for="col in resultColumns"
          :key="col"
          :prop="col"
          :label="col"
          min-width="140"
          show-overflow-tooltip
        />
        <el-table-column v-if="!resultColumns.length" label="（请先执行查询）">
          <template #default>
            <span class="empty">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="updateDialogVisible"
      title="批量更新预览"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-alert
        v-if="updatePreview"
        :type="updatePreview.affected > 0 ? 'warning' : 'info'"
        :closable="false"
        show-icon
        class="update-alert"
      >
        <template #title>
          将更新 <strong>{{ updatePreview.affected }}</strong> 条数据
        </template>
        <div v-if="updatePreview.sample?.length" class="sample-list">
          <div class="sample-title">样本（前 5 条）：</div>
          <div v-for="(s, i) in updatePreview.sample" :key="i" class="sample-item">
            <el-tag size="small">{{ s.item_barcode }}</el-tag>
            <span class="sample-value">{{ s.new_name || '(空)' }}</span>
            <el-icon><Right /></el-icon>
            <span class="sample-new">{{ updateForm.value }}</span>
          </div>
        </div>
      </el-alert>

      <el-form :model="updateForm" label-position="top" style="margin-top: 16px">
        <el-form-item label="更新字段">
          <el-select v-model="updateForm.field" style="width: 100%">
            <el-option label="new_name" value="new_name" />
            <el-option label="platform" value="platform" />
            <el-option label="category" value="category" />
            <el-option label="brand" value="brand" />
          </el-select>
        </el-form-item>
        <el-form-item label="新值">
          <el-input v-model="updateForm.value" placeholder="请输入新值" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="updateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="updateLoading" @click="handleUpdate">
          确认更新
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Filter,
  Search,
  Download,
  EditPen,
  DataAnalysis,
  Right
} from '@element-plus/icons-vue'
import { dataApi } from '@/api/data'

const tables = ref([])
const result = ref([])
const resultColumns = ref([])
const lastSql = ref('')
const loading = ref(false)
const exportLoading = ref(false)
const updateLoading = ref(false)

const filters = reactive({
  table: '',
  keyword: '',
  where: '',
  limit: 0
})

const updateDialogVisible = ref(false)
const updatePreview = ref(null)
const updateForm = reactive({
  field: 'new_name',
  value: ''
})

const fetchTables = async () => {
  try {
    const res = await dataApi.getTables()
    tables.value = res.tables || res || []
    if (tables.value.length) {
      filters.table = tables.value[0]
    }
  } catch (err) {
    ElMessage.warning('获取表列表失败: ' + (err.message || '未知错误'))
  }
}

const buildPayload = () => ({
  table: filters.table,
  keyword: filters.keyword || undefined,
  where: filters.where || undefined,
  limit: filters.limit > 0 ? filters.limit : undefined
})

const handleQuery = async () => {
  if (!filters.table) {
    ElMessage.warning('请先选择表')
    return
  }
  loading.value = true
  try {
    const res = await dataApi.previewQuery(buildPayload())
    result.value = res.data || []
    resultColumns.value = res.columns || (result.value[0] ? Object.keys(result.value[0]) : [])
    lastSql.value = res.sql || ''
    ElMessage.success(`查询到 ${result.value.length} 条数据`)
  } catch (err) {
    ElMessage.error('查询失败: ' + (err.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

const buildFilename = (ext) => {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  const stamp = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
  return `filter_${filters.table || 'data'}_${stamp}.${ext}`
}

const handleExport = async () => {
  if (!filters.table) {
    ElMessage.warning('请先选择表')
    return
  }
  exportLoading.value = true
  try {
    const blob = await dataApi.exportQuery({ ...buildPayload(), format: 'xlsx' })
    downloadBlob(blob, buildFilename('xlsx'))
    ElMessage.success('导出成功')
  } catch (err) {
    ElMessage.error('导出失败: ' + (err.message || '未知错误'))
  } finally {
    exportLoading.value = false
  }
}

const openUpdateDialog = async () => {
  if (!filters.table) {
    ElMessage.warning('请先选择表')
    return
  }
  updateForm.value = ''
  updatePreview.value = null
  updateDialogVisible.value = true
  updateLoading.value = true
  try {
    const res = await dataApi.previewUpdate(buildPayload())
    updatePreview.value = res
  } catch (err) {
    ElMessage.error('更新预览失败: ' + (err.message || '未知错误'))
    updateDialogVisible.value = false
  } finally {
    updateLoading.value = false
  }
}

const handleUpdate = async () => {
  if (!updateForm.value) {
    ElMessage.warning('请输入新值')
    return
  }
  if (!updatePreview.value?.affected) {
    ElMessage.info('没有命中数据，无需更新')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认将 ${updatePreview.value.affected} 条数据的 ${updateForm.field} 更新为 "${updateForm.value}" ？`,
      '批量更新',
      { type: 'warning', confirmButtonText: '确认更新', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  updateLoading.value = true
  try {
    const res = await dataApi.executeUpdate({
      ...buildPayload(),
      field: updateForm.field,
      value: updateForm.value
    })
    ElMessage.success(`更新成功，影响 ${res.affected || updatePreview.value.affected} 条`)
    updateDialogVisible.value = false
    handleQuery()
  } catch (err) {
    ElMessage.error('更新失败: ' + (err.message || '未知错误'))
  } finally {
    updateLoading.value = false
  }
}

const resetFilters = () => {
  filters.keyword = ''
  filters.where = ''
  filters.limit = 0
  result.value = []
  resultColumns.value = []
  lastSql.value = ''
}

onMounted(() => {
  fetchTables()
})
</script>

<style lang="scss" scoped>
.filter-export-page {
  max-width: 1280px;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.page-desc {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.filter-card,
.result-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
  color: var(--color-text-primary);

  .el-button {
    margin-left: auto;
  }
}

.sql-tag {
  margin-left: auto;
  font-family: Consolas, Monaco, monospace;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.update-alert {
  .sample-list {
    margin-top: 8px;
  }
  .sample-title {
    font-size: 12px;
    color: var(--color-text-secondary);
    margin-bottom: 6px;
  }
  .sample-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    margin: 4px 0;
  }
  .sample-value,
  .sample-new {
    color: var(--color-text-primary);
  }
  .sample-new {
    color: #1890ff;
    font-weight: 600;
  }
}

.empty {
  color: var(--color-text-tertiary);
}
</style>
