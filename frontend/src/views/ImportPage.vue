<template>
  <div class="import-page">
    <div class="page-header">
      <h2 class="page-title">数据导入</h2>
      <p class="page-desc">上传 Excel/CSV 文件，将数据导入到汇总表中</p>
    </div>

    <el-card shadow="never" class="upload-card">
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        :auto-upload="false"
        :show-file-list="false"
        :accept="'.xlsx,.xls,.csv'"
        :on-change="handleFileChange"
      >
        <el-icon class="upload-icon" :size="56" color="#909399"><UploadFilled /></el-icon>
        <div class="upload-text">{{ selectedFile ? `已选择: ${selectedFile.name}` : '点击或拖拽文件到此处上传' }}</div>
        <div class="upload-hint">支持 .xlsx, .xls, .csv 格式</div>
      </el-upload>

      <el-alert
        title="文件要求"
        type="info"
        :closable="false"
        show-icon
        class="requirements"
      >
        <ul>
          <li>文件必须包含 <code>item_barcode</code> 和 <code>new_name</code> 两列</li>
          <li>第一行应为列名</li>
          <li>导入时仅更新 <code>new_name</code> 字段，其他字段保持不变</li>
        </ul>
      </el-alert>

      <div v-if="status" class="status-block" :class="`status-${status.type}`">
        <div v-html="status.html"></div>
      </div>
    </el-card>

    <div class="actions">
      <el-button :disabled="!selectedFile || validating" :loading="validating" @click="validateFile">
        <el-icon><CircleCheck /></el-icon> 校验数据
      </el-button>
      <el-button
        type="primary"
        :disabled="!selectedFile || importing"
        :loading="importing"
        @click="importFile"
      >
        <el-icon><Upload /></el-icon> 开始导入
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Upload, CircleCheck } from '@element-plus/icons-vue'
import { dataApi } from '@/api/data'
import { useRouter } from 'vue-router'

const router = useRouter()
const uploadRef = ref()
const selectedFile = ref(null)
const validating = ref(false)
const importing = ref(false)
const status = ref(null)

const handleFileChange = (file) => {
  const validExts = ['.xlsx', '.xls', '.csv']
  const ext = '.' + (file.name.split('.').pop() || '').toLowerCase()
  if (!validExts.includes(ext)) {
    ElMessage.error('不支持的文件格式，请上传 Excel 或 CSV 文件')
    selectedFile.value = null
    return false
  }
  selectedFile.value = file.raw
  status.value = null
  return true
}

const renderStatus = (result) => {
  let html = `<strong>校验完成！</strong><br>总记录: ${result.total} 条<br>`
  const errColor = result.errors > 0 ? '#cf1322' : '#389e0d'
  const warnColor = result.warnings > 0 ? '#d48806' : '#389e0d'
  html += `<span style="color:${errColor};">错误: ${result.errors} 条</span><br>`
  html += `<span style="color:${warnColor};">警告: ${result.warnings} 条</span>`

  if (result.errorDetails?.length) {
    html += '<br><details style="margin-top: 8px;"><summary>查看错误详情</summary>'
    result.errorDetails.forEach((e) => {
      html += `<div style="font-size:12px;margin-top:4px;">行${e.row}: ${e.field} = '${e.value}' - ${e.message}</div>`
    })
    html += '</details>'
  }
  if (result.warningDetails?.length) {
    html += '<details style="margin-top: 8px;"><summary>查看警告详情</summary>'
    result.warningDetails.forEach((w) => {
      html += `<div style="font-size:12px;margin-top:4px;">行${w.row}: ${w.field} = '${w.value}' - ${w.message}</div>`
    })
    html += '</details>'
  }

  status.value = {
    type: result.canImport ? 'success' : 'error',
    html
  }
  ElMessage[result.canImport ? 'success' : 'error'](
    `校验完成！${result.errors} 个错误，${result.warnings} 个警告`
  )
}

const validateFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  validating.value = true
  status.value = { type: 'info', html: '<strong>正在校验数据，请稍候...</strong>' }
  try {
    const result = await dataApi.validateFile(selectedFile.value)
    renderStatus(result)
  } catch (err) {
    status.value = {
      type: 'error',
      html: `<strong>校验失败</strong><br>${err.message || '未知错误'}`
    }
  } finally {
    validating.value = false
  }
}

const importFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  importing.value = true
  status.value = { type: 'info', html: '<strong>正在导入，请稍候...</strong>' }
  try {
    const result = await dataApi.importData(selectedFile.value)
    status.value = {
      type: 'success',
      html: `<strong>导入成功！</strong><br>总计: ${result.total} 条<br>成功: ${result.success} 条<br>失败: ${result.failed} 条`
    }
    ElMessage.success(`导入成功！共 ${result.success} 条数据`)
    setTimeout(() => {
      selectedFile.value = null
      status.value = null
      router.push('/data')
    }, 1500)
  } catch (err) {
    status.value = {
      type: 'error',
      html: `<strong>导入失败</strong><br>${err.message || '未知错误'}`
    }
  } finally {
    importing.value = false
  }
}
</script>

<style lang="scss" scoped>
.import-page {
  max-width: 800px;
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

.upload-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  padding: 48px 24px;
  border: 2px dashed #d9d9d9;
  border-radius: 12px;
  background: var(--color-bg-tertiary);
  transition: all 0.3s;

  &:hover {
    border-color: #1890ff;
    background: rgba(24, 144, 255, 0.04);
  }
}

.upload-icon {
  color: #909399;
  margin-bottom: 12px;
}

.upload-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.upload-hint {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

.requirements {
  margin: 16px 0;

  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  li {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin: 4px 0;
    padding-left: 1rem;
    position: relative;
    line-height: 1.6;
  }
  li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: #1890ff;
    font-weight: 600;
  }
  code {
    background: #fff;
    padding: 0 6px;
    border-radius: 3px;
    font-family: Consolas, Monaco, monospace;
    font-size: 12px;
    color: #1890ff;
    border: 1px solid rgba(24, 144, 255, 0.2);
  }
}

.status-block {
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 13px;
  margin-top: 12px;

  &.status-success {
    background: rgba(82, 196, 26, 0.1);
    color: #389e0d;
    border: 1px solid rgba(82, 196, 26, 0.3);
  }
  &.status-error {
    background: rgba(255, 77, 79, 0.1);
    color: #cf1322;
    border: 1px solid rgba(255, 77, 79, 0.3);
  }
  &.status-info {
    background: rgba(24, 144, 255, 0.1);
    color: #096dd9;
    border: 1px solid rgba(24, 144, 255, 0.3);
  }
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
