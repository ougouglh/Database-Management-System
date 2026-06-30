<template>
  <div class="admin-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <router-link to="/home" class="sidebar-logo">
          <el-icon :size="28" color="#40a9ff"><Box /></el-icon>
          <span>数据管理系统</span>
        </router-link>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section">数据管理</div>
        <router-link
          v-for="item in mainNav"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="active"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </router-link>

        <div class="nav-section">数据操作</div>
        <router-link
          v-for="item in opNav"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          active-class="active"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="sidebar-status">
          <span class="status-dot"></span>
          <span>系统在线</span>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <header class="header">
        <div class="header-content">
          <h1 class="title">
            <el-icon class="title-icon" :size="24" color="#1890ff"><Box /></el-icon>
            内网数据导入导出系统
          </h1>
          <p class="subtitle">barcode_base_info_69_top96_incre_allplatform_name 表数据管理</p>
        </div>
        <div class="system-info">
          <el-dropdown trigger="click" @command="handleUserCmd">
            <span class="user-info">
              <el-icon :size="16"><User /></el-icon>
              <span class="username">{{ username }}</span>
              <el-icon :size="12"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <span class="status-badge">
            <span class="status-dot"></span>
            系统在线
          </span>
        </div>
      </header>

      <div class="content-wrapper">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Box,
  Grid,
  Document,
  Upload,
  Download,
  Filter,
  EditPen,
  User,
  ArrowDown,
  SwitchButton
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const username = computed(() => {
  return userStore.userInfo?.username || localStorage.getItem('username') || 'admin'
})

const mainNav = [
  { path: '/home', title: '功能导航', icon: Grid },
  { path: '/data', title: '汇总表查看', icon: Document }
]

const opNav = [
  { path: '/import', title: '数据导入', icon: Upload },
  { path: '/export', title: '数据导出', icon: Download },
  { path: '/filter', title: '筛选导出', icon: Filter },
  { path: '/logs', title: '操作日志', icon: EditPen }
]

const handleUserCmd = async (cmd) => {
  if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        type: 'warning',
        confirmButtonText: '退出',
        cancelButtonText: '取消'
      })
      await userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    } catch {
      // 用户取消
    }
  }
}
</script>

<style lang="scss" scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

/* ===== Sidebar ===== */
.sidebar {
  width: 256px;
  background: #001529;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #ffffff;
  font-size: 18px;
  font-weight: 600;
  text-decoration: none;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 24px;
  margin: 4px 16px;
  color: rgba(255, 255, 255, 0.65);
  text-decoration: none;
  border-radius: 6px;
  transition: all 0.2s;
  cursor: pointer;
  font-size: 14px;
}

.nav-item:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

.nav-item.active {
  background: rgba(24, 144, 255, 0.15);
  color: #1890ff;
}

.nav-section {
  padding: 16px 24px 4px;
  color: rgba(255, 255, 255, 0.45);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sidebar-footer {
  padding: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-status {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #52c41a;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(82, 196, 26, 0.7); }
  50% { opacity: 0.8; box-shadow: 0 0 0 4px rgba(82, 196, 26, 0); }
}

/* ===== Main Content ===== */
.main-content {
  margin-left: 256px;
  flex: 1;
  min-height: 100vh;
  background: #f0f2f5;
}

.header {
  background: #ffffff;
  padding: 16px 40px;
  margin-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content {
  flex: 1;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 0;
  line-height: 1.35;
}

.subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-left: 32px;
}

.system-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 6px;
  color: var(--color-text-primary);
  transition: background 0.2s;

  &:hover {
    background: var(--color-bg-tertiary);
  }
}

.username {
  font-size: 14px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
  border: 1px solid rgba(82, 196, 26, 0.2);
}

.content-wrapper {
  padding: 0 40px 24px;
}
</style>
