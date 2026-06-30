<template>
  <div class="log-page">
    <el-card>
      <template #header>
        <div class="page-header">
          <h2>操作日志</h2>
          <el-space>
            <el-button :icon="Refresh" @click="fetchLogs">刷新</el-button>
            <el-button :icon="Download" :loading="exportLoading" @click="exportLogs">导出</el-button>
          </el-space>
        </div>
      </template>

      <!-- 筛选条件 -->
      <div class="filter-bar">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-select v-model="filters.operationType" placeholder="操作类型" clearable>
              <el-option label="全部" value="" />
              <el-option label="登录" value="login" />
              <el-option label="导入" value="import" />
              <el-option label="导出" value="export" />
              <el-option label="查看" value="view" />
              <el-option label="编辑" value="edit" />
              <el-option label="删除" value="delete" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select v-model="filters.status" placeholder="执行状态" clearable>
              <el-option label="全部" value="" />
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
            </el-select>
          </el-col>
          <el-col :span="8">
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="handleFilter">查询</el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 统计信息 -->
      <div class="stats-bar">
        <el-space :size="24">
          <div class="stat-item">
            <span class="stat-label">今日操作</span>
            <span class="stat-value">{{ stats.todayCount }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">本周操作</span>
            <span class="stat-value">{{ stats.weekCount }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">成功率</span>
            <span class="stat-value success">{{ stats.successRate }}%</span>
          </div>
        </el-space>
      </div>

      <!-- 日志表格 -->
      <el-table
        v-loading="loading"
        :data="logData"
        stripe
        size="small"
        @row-click="handleRowClick"
      >
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-content">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="操作ID">
                  {{ row.id }}
                </el-descriptions-item>
                <el-descriptions-item label="用户ID">
                  {{ row.user_id }}
                </el-descriptions-item>
                <el-descriptions-item label="IP地址">
                  {{ row.ip_address || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="影响行数">
                  {{ row.affected_rows || 0 }}
                </el-descriptions-item>
                <el-descriptions-item label="错误信息" :span="2">
                  {{ row.error_message || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="User Agent" :span="2">
                  <span class="ua-text">{{ row.user_agent || '-' }}</span>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column label="操作类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getOperationTypeColor(row.operation_type)" size="small">
              {{ getOperationTypeText(row.operation_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="table_name" label="操作表" width="180" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">
              {{ row.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="affected_rows" label="影响行数" width="100" />
        <el-table-column prop="created_at" label="操作时间" width="180" />
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100]"
          :total="totalRecords"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Download } from '@element-plus/icons-vue'
import { logApi } from '@/api/log'

const loading = ref(false)
const logData = ref([])
const totalRecords = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  operationType: '',
  status: '',
  dateRange: null
})

const stats = reactive({
  todayCount: 0,
  weekCount: 0,
  successRate: 0
})

// 获取日志数据
const fetchLogs = async () => {
  loading.value = true

  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value,
      operation_type: filters.operationType || undefined,
      status: filters.status || undefined
    }

    const res = await logApi.getOperationLogs(params)

    if (res.success) {
      logData.value = res.data
      totalRecords.value = res.total

      // 更新统计
      const successCount = res.data.filter(item => item.status === 'success').length
      stats.successRate = res.total > 0
        ? Math.round((successCount / res.total) * 100)
        : 0
    } else {
      ElMessage.error('加载日志失败')
    }
  } catch (error) {
    console.error('加载日志失败:', error)
    ElMessage.error('加载日志失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 筛选
const handleFilter = () => {
  currentPage.value = 1
  fetchLogs()
}

// 分页
const handlePageChange = (page) => {
  currentPage.value = page
  fetchLogs()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchLogs()
}

// 导出
const exportLoading = ref(false)
const exportLogs = async () => {
  exportLoading.value = true
  try {
    const params = {
      operation_type: filters.operationType || undefined,
      status: filters.status || undefined
    }
    const blob = await logApi.exportLogs(params)
    const d = new Date()
    const pad = (n) => String(n).padStart(2, '0')
    const stamp = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `operation_logs_${stamp}.xlsx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    ElMessage.success('日志导出成功')
  } catch (err) {
    ElMessage.error('导出失败: ' + (err.message || '未知错误'))
  } finally {
    exportLoading.value = false
  }
}

// 行点击
const handleRowClick = (row) => {
  console.log('点击行:', row)
}

// 获取操作类型颜色
const getOperationTypeColor = (type) => {
  const map = {
    login: 'info',
    import: 'success',
    export: 'warning',
    view: '',
    edit: 'primary',
    delete: 'danger',
    logout: 'info'
  }
  return map[type] || ''
}

// 获取操作类型文本
const getOperationTypeText = (type) => {
  const map = {
    login: '登录',
    import: '导入',
    export: '导出',
    view: '查看',
    edit: '编辑',
    delete: '删除',
    logout: '登出'
  }
  return map[type] || type
}

onMounted(() => {
  fetchLogs()
})
</script>

<style lang="scss" scoped>
.log-page {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;

  h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }
}

.filter-bar {
  margin-bottom: 16px;
}

.stats-bar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 16px;
  background: var(--color-bg-tertiary);
  border-radius: 8px;

  .stat-item {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .stat-label {
      font-size: 12px;
      color: var(--color-text-secondary);
    }

    .stat-value {
      font-size: 18px;
      font-weight: 600;
      color: var(--color-text-primary);

      &.success {
        color: var(--color-success);
      }
    }
  }
}

.expand-content {
  padding: 16px;
}

.ua-text {
  font-size: 12px;
  color: var(--color-text-secondary);
  word-break: break-all;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

:deep(.el-table__row) {
  cursor: pointer;

  &:hover {
    background: rgba(24, 144, 255, 0.04);
  }
}
</style>
