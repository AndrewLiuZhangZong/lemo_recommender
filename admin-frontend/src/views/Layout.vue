<template>
  <el-container class="layout-container">
    <el-aside width="200px">
      <div class="logo">
        <h2>🚀 Lemo推荐</h2>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        class="el-menu-vertical"
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表板</span>
        </el-menu-item>
        <el-menu-item index="/scenarios">
          <el-icon><Setting /></el-icon>
          <span>场景管理</span>
        </el-menu-item>
        <el-menu-item index="/items">
          <el-icon><Document /></el-icon>
          <span>物品管理</span>
        </el-menu-item>
        <el-menu-item index="/experiments">
          <el-icon><Histogram /></el-icon>
          <span>AB实验</span>
        </el-menu-item>
        <el-menu-item index="/analytics">
          <el-icon><TrendCharts /></el-icon>
          <span>数据分析</span>
        </el-menu-item>
        <el-menu-item index="/jobs">
          <el-icon><Operation /></el-icon>
          <span>作业管理</span>
        </el-menu-item>
        <el-menu-item index="/model-training">
          <el-icon><MagicStick /></el-icon>
          <span>模型训练</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header>
        <div class="header-content">
          <span class="page-title">{{ $route.meta.title }}</span>
          <el-dropdown>
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>管理员</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人设置</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { Odometer, Setting, Document, Histogram, TrendCharts, Operation, MagicStick, User } from '@element-plus/icons-vue'
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.el-aside {
  background-color: #001529;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.el-menu-vertical {
  border-right: none;
  background-color: #001529;
}

.el-menu-item {
  color: rgba(255, 255, 255, 0.65);
}

.el-menu-item:hover,
.el-menu-item.is-active {
  background-color: #1890ff !important;
  color: #fff !important;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  padding: 0 24px;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.el-main {
  background-color: #f0f2f5;
  padding: 24px;
}
</style>

