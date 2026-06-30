<template>
  <div class="data-section">
    <div class="data-header">
      <h2 class="data-title">汇总数据表</h2>
      <div class="data-actions">
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
    </div>

    <div class="table-stats">
      <div class="stat-item">
        <span class="stat-label">总记录数:</span>
        <span class="stat-value">{{ totalRecords.toLocaleString() }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">最后更新:</span>
        <span class="stat-value">{{ lastUpdate || '-' }}</span>
      </div>
      <div class="stat-item stat-search">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索商品条码、名称..."
          clearable
          @keyup.enter="performSearch"
          @clear="performSearch"
        >
          <template #append>
            <el-button @click="performSearch">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>
    </div>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      height="65vh"
      style="width: 100%"
    >
      <el-table-column type="index" label="序号" width="70" :index="indexMethod" fixed />
      <el-table-column prop="item_barcode" label="item_barcode" min-width="140" show-overflow-tooltip fixed />
      <el-table-column prop="item_name" label="item_name" min-width="180" show-overflow-tooltip />
      <el-table-column prop="old_cat_name" label="old_cat_name" min-width="140" show-overflow-tooltip />
      <el-table-column prop="new_cat_name" label="new_cat_name" min-width="140" show-overflow-tooltip />
      <el-table-column prop="msy_item_name" label="msy_item_name" min-width="160" show-overflow-tooltip />
      <el-table-column prop="msy_cat_name" label="msy_cat_name" min-width="140" show-overflow-tooltip />
      <el-table-column prop="eb_item_name" label="eb_item_name" min-width="160" show-overflow-tooltip />
      <el-table-column prop="eb_cat_name" label="eb_cat_name" min-width="140" show-overflow-tooltip />
      <el-table-column prop="eb_size" label="eb_size" min-width="100" show-overflow-tooltip />
      <el-table-column prop="mt_item_name" label="mt_item_name" min-width="160" show-overflow-tooltip />
      <el-table-column prop="mt_cat_name" label="mt_cat_name" min-width="140" show-overflow-tooltip />
      <el-table-column prop="mt_size" label="mt_size" min-width="100" show-overflow-tooltip />
      <el-table-column prop="gs1_item_name" label="gs1_item_name" min-width="160" show-overflow-tooltip />
      <el-table-column label="new_name" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="editable-field" @click="openEditModal(row)">
            {{ row.new_name || '-' }}
            <el-icon class="edit-icon" :size="14"><EditPen /></el-icon>
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="valid_flag" label="valid_flag" width="100" />
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="totalRecords"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>

    <!-- Edit Modal -->
    <el-dialog
      v-model="editModalVisible"
      title="编辑 new_name"
      width="500px"
      @close="resetEditForm"
    >
      <el-form :model="editForm" label-width="140px">
        <el-form-item label="item_barcode (商品条码):">
          <el-input v-model="editForm.item_barcode" readonly />
        </el-form-item>
        <el-form-item label="new_name (新商品名称):">
          <el-input v-model="editForm.new_name" placeholder="请输入新的商品名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editModalVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search, EditPen } from '@element-plus/icons-vue'
import { dataApi } from '@/api/data'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const totalRecords = ref(0)
const lastUpdate = ref('')
const currentPage = ref(1)
const pageSize = ref(50)
const searchKeyword = ref('')

const editModalVisible = ref(false)
const editForm = ref({ item_barcode: '', new_name: '' })

const indexMethod = (index) => {
  return (currentPage.value - 1) * pageSize.value + index + 1
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await dataApi.getDataList({
      page: currentPage.value,
      pageSize: pageSize.value,
      keyword: searchKeyword.value || undefined
    })
    tableData.value = res.data || []
    totalRecords.value = res.total || 0
    lastUpdate.value = res.lastUpdate
      ? new Date(res.lastUpdate).toLocaleString('zh-CN')
      : '-'
  } catch (err) {
    tableData.value = []
    totalRecords.value = 0
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  currentPage.value = 1
  searchKeyword.value = ''
  loadData()
}

const performSearch = () => {
  currentPage.value = 1
  loadData()
}

const openEditModal = (row) => {
  editForm.value = {
    item_barcode: row.item_barcode,
    new_name: row.new_name || ''
  }
  editModalVisible.value = true
}

const resetEditForm = () => {
  editForm.value = { item_barcode: '', new_name: '' }
}

const saveEdit = async () => {
  const newName = editForm.value.new_name.trim()
  if (!newName) {
    ElMessage.warning('请输入新的商品名称')
    return
  }
  saving.value = true
  try {
    await dataApi.updateData(editForm.value.item_barcode, newName)
    ElMessage.success('更新成功')
    editModalVisible.value = false
    await loadData()
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.data-section {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #f0f0f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.data-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 8px;
}

.data-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.table-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding: 8px 16px;
  background: var(--color-bg-tertiary);
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  align-items: center;
}

.stat-item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 500;
}

.stat-value {
  color: var(--color-text-primary);
  font-weight: 600;
  font-size: 14px;
}

.stat-search {
  margin-left: auto;
  min-width: 320px;
}

.editable-field {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #1890ff;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  transition: background 0.2s;

  &:hover {
    background: rgba(24, 144, 255, 0.1);
  }
}

.edit-icon {
  opacity: 0.65;
  transition: opacity 0.2s;
}

.editable-field:hover .edit-icon {
  opacity: 1;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
