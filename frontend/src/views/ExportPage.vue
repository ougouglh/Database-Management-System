<template>
  <div class="export-page">
    <div class="page-header">
      <h2 class="page-title">数据导出</h2>
      <p class="page-desc">将汇总表数据导出为 Excel 或 CSV 文件</p>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="export-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="20" color="#52c41a"><Download /></el-icon>
              <span>快速导出</span>
            </div>
          </template>

          <el-form label-position="top">
            <el-form-item label="导出格式">
              <el-radio-group v-model="quickFormat">
                <el-radio-button value="xlsx">Excel (.xlsx)</el-radio-button>
                <el-radio-button value="csv">CSV (.csv)</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="导出范围">
              <el-radio-group v-model="quickScope">
                <el-radio value="all">全部数据</el-radio>
                <el-radio value="current">当前页</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item v-if="quickScope === 'current'" label="搜索关键字">
              <el-input v-model="quickKeyword" placeholder="可选：按 item_barcode / item_name 过滤" clearable />
            </el-form-item>

            <div class="actions">
              <el-button type="primary" :loading="quickLoading" @click="handleQuickExport">
                <el-icon><Download /></el-icon> 开始导出
              </el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="export-card">
          <template #header>
            <div class="card-header">
              <el-icon :size="20" color="#1890ff"><Setting /></el-icon>
              <span>自定义 SQL 导出</span>
            </div>
          </template>

          <el-form label-position="top">
            <el-form-item label="选择表">
              <el-select v-model="customTable" placeholder="请选择要导出的表" style="width: 100%" @change="handleTableChange">
                <el-option
                  v-for="t in tables"
                  :key="t"
                  :label="t"
                  :value="t"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="WHERE 条件">
              <el-input
                v-model="customWhere"
                type="textarea"
                :rows="4"
                placeholder="例如: item_barcode LIKE 'A%' AND new_name IS NOT NULL"
              />
            </el-form-item>

            <el-form-item label="LIMIT（可选）">
              <el-input-number v-model="customLimit" :min="0" :step="100" placeholder="0 表示不限制" />
              <span class="form-hint">设置 0 表示导出全部命中数据</span>
            </el-form-item>

            <el-form-item label="导出格式">
              <el-radio-group v-model="customFormat">
                <el-radio-button value="xlsx">Excel</el-radio-button>
                <el-radio-button value="csv">CSV</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <div class="actions">
              <el-button :loading="previewLoading" @click="handlePreview">
                <el-icon><View /></el-icon> 预览 SQL
              </el-button>
              <el-button type="primary" :loading="customLoading" @click="handleCustomExport">
                <el-icon><Download /></el-icon> 执行导出
              </el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-card v-if="previewData.length" shadow="never" class="preview-card">
      <template #header>
        <div class="card-header">
          <el-icon :size="18" color="#1890ff"><View /></el-icon>
          <span>预览结果（{{ previewData.length }} 条）</span>
          <el-button text type="primary" @click="previewData = []">关闭预览</el-button>
        </div>
      </template>
      <el-table :data="previewData" border stripe size="small" max-height="320">
        <el-table-column
          v-for="col in previewColumns"
          :key="col"
          :prop="col"
          :label="col"
          min-width="120"
          show-overflow-tooltip
        />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Setting, View } from '@element-plus/icons-vue'
import { dataApi } from '@/api/data'

const quickFormat = ref('xlsx')
const quickScope = ref('all')
const quickKeyword = ref('')
const quickLoading = ref(false)

const tables = ref([])
const customTable = ref('')
const customWhere = ref('')
const customLimit = ref(0)
const customFormat = ref('xlsx')
const customLoading = ref(false)

const previewData = ref([])
const previewColumns = ref([])
const previewLoading = ref(false)

const fetchTables = async () => {
  try {
    const res = await dataApi.getTables()
    tables.value = res.tables || res || []
    if (tables.value.length && !customTable.value) {
      customTable.value = tables.value[0]
    }
  } catch (err) {
    ElMessage.warning('获取表列表失败: ' + (err.message || '未知错误'))
  }
}

const handleTableChange = () => {
  previewData.value = []
  previewColumns.value = []
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
  return `barcode_export_${stamp}.${ext}`
}

const handleQuickExport = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要导出${quickScope.value === 'all' ? '全部' : '当前页'}数据为 ${quickFormat.value.toUpperCase()} 吗？`,
      '导出确认',
      { type: 'info', confirmButtonText: '开始导出', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  quickLoading.value = true
  try {
    const params = {
      format: quickFormat.value,
      scope: quickScope.value
    }
    if (quickScope.value === 'current' && quickKeyword.value) {
      params.keyword = quickKeyword.value
    }
    const blob = await dataApi.exportData(params)
    downloadBlob(blob, buildFilename(quickFormat.value))
    ElMessage.success('导出成功')
  } catch (err) {
    ElMessage.error('导出失败: ' + (err.message || '未知错误'))
  } finally {
    quickLoading.value = false
  }
}

const handlePreview = async () => {
  if (!customTable.value) {
    ElMessage.warning('请先选择表')
    return
  }
  previewLoading.value = true
  try {
    const res = await dataApi.previewQuery({
      table: customTable.value,
      where: customWhere.value || '',
      limit: customLimit.value > 0 ? customLimit.value : undefined
    })
    previewData.value = res.data || []
    previewColumns.value = res.columns || (previewData.value[0] ? Object.keys(previewData.value[0]) : [])
    if (!previewData.value.length) {
      ElMessage.info('未查询到数据')
    } else {
      ElMessage.success(`命中 ${previewData.value.length} 条数据`)
    }
  } catch (err) {
    ElMessage.error('预览失败: ' + (err.message || '未知错误'))
  } finally {
    previewLoading.value = false
  }
}

const handleCustomExport = async () => {
  if (!customTable.value) {
    ElMessage.warning('请先选择表')
    return
  }
  try {
    await ElMessageBox.confirm(
      '将按当前条件导出数据，是否继续？',
      '导出确认',
      { type: 'info', confirmButtonText: '开始导出', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  customLoading.value = true
  try {
    const blob = await dataApi.exportQuery({
      table: customTable.value,
      where: customWhere.value || '',
      limit: customLimit.value > 0 ? customLimit.value : undefined,
      format: customFormat.value
    })
    downloadBlob(blob, buildFilename(customFormat.value))
    ElMessage.success('导出成功')
  } catch (err) {
    ElMessage.error('导出失败: ' + (err.message || '未知错误'))
  } finally {
    customLoading.value = false
  }
}

onMounted(() => {
  fetchTables()
})
</script>

<style lang="scss" scoped>
.export-page {
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

.export-card {
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

.preview-card {
  border-radius: 12px;
  margin-top: 16px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 8px;
}

.form-hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--color-text-tertiary);
}
</style>
