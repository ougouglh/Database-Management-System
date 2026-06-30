<template>
  <div class="home-page">
    <div class="welcome-banner">
      <div class="welcome-text">
        <h2>欢迎使用内网数据导入导出系统</h2>
        <p>支持 Excel/CSV 文件导入、自定义条件筛选、批量更新与导出</p>
      </div>
      <el-icon class="welcome-icon" :size="80"><Box /></el-icon>
    </div>

    <div class="cards-grid">
      <div
        v-for="card in cards"
        :key="card.path"
        class="nav-card"
        :class="`card-${card.variant}`"
        @click="goTo(card.path)"
      >
        <div class="card-icon">
          <el-icon :size="24"><component :is="card.icon" /></el-icon>
        </div>
        <h3 class="card-title">{{ card.title }}</h3>
        <p class="card-description">{{ card.description }}</p>
        <div class="card-footer">
          <span class="card-action">点击进入 →</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import {
  Box,
  Upload,
  Download,
  Document,
  Filter
} from '@element-plus/icons-vue'

const router = useRouter()

const cards = [
  {
    path: '/import',
    title: '数据导入',
    description: '上传 Excel/CSV 文件导入数据',
    icon: Upload,
    variant: 'import'
  },
  {
    path: '/export',
    title: '数据导出',
    description: '一键导出全部数据为 Excel/CSV',
    icon: Download,
    variant: 'export'
  },
  {
    path: '/data',
    title: '汇总表查看',
    description: '分页查看与搜索汇总数据',
    icon: Document,
    variant: 'view'
  },
  {
    path: '/filter',
    title: '数据筛选导出',
    description: '自定义条件筛选 / 批量更新',
    icon: Filter,
    variant: 'filter'
  }
]

const goTo = (path) => {
  router.push(path)
}
</script>

<style lang="scss" scoped>
.home-page {
  padding: 0;
}

.welcome-banner {
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: #fff;
  border-radius: 12px;
  padding: 32px 40px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.2);

  .welcome-text {
    h2 {
      font-size: 22px;
      font-weight: 600;
      margin-bottom: 8px;
    }
    p {
      font-size: 14px;
      opacity: 0.9;
    }
  }

  .welcome-icon {
    opacity: 0.3;
  }
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.nav-card {
  --card-accent: #1890ff;
  --card-accent-light: rgba(24, 144, 255, 0.15);
  --card-accent-lighter: rgba(24, 144, 255, 0.08);
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--card-accent);
    transform: scaleX(0);
    transition: transform 0.3s;
  }

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    border-color: var(--card-accent);

    &::before {
      transform: scaleX(1);
    }

    .card-icon {
      transform: scale(1.1) rotate(5deg);
    }
  }
}

.card-icon {
  width: 40px;
  height: 40px;
  margin-bottom: 16px;
  color: var(--card-accent);
  transition: transform 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--card-accent-light) 0%, var(--card-accent-lighter) 100%);
  border-radius: 8px;
  padding: 8px;
}

.card-import {
  --card-accent: #1890ff;
  --card-accent-light: rgba(24, 144, 255, 0.15);
  --card-accent-lighter: rgba(24, 144, 255, 0.08);
}

.card-export {
  --card-accent: #52c41a;
  --card-accent-light: rgba(82, 196, 26, 0.15);
  --card-accent-lighter: rgba(82, 196, 26, 0.08);
}

.card-view {
  --card-accent: #faad14;
  --card-accent-light: rgba(250, 173, 20, 0.15);
  --card-accent-lighter: rgba(250, 173, 20, 0.08);
}

.card-filter {
  --card-accent: #722ed1;
  --card-accent-light: rgba(114, 46, 209, 0.15);
  --card-accent-lighter: rgba(114, 46, 209, 0.08);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 4px;
  line-height: 1.4;
}

.card-description {
  color: var(--color-text-secondary);
  margin-bottom: 16px;
  font-size: 13px;
  line-height: 1.5;
  min-height: 40px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.card-action {
  color: var(--card-accent);
  font-weight: 500;
  font-size: 14px;
}
</style>
