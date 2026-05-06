<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-text">
          <h1>资产测绘系统</h1>
        </div>
      </div>
      <el-menu
        :default-active="$route.name"
        router
        class="sidebar-menu"
        background-color="#1e3a5f"
        text-color="#b0c4d8"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/">
          <el-icon><Grid /></el-icon>
          <span>资产列表</span>
        </el-menu-item>
        <el-menu-item index="/stats">
          <el-icon><DataAnalysis /></el-icon>
          <span>数据统计</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 主内容 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { Grid, DataAnalysis, Setting } from '@element-plus/icons-vue'
</script>

<style scoped>
.app-container {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 160px;
  background: linear-gradient(180deg, #1e3a5f 0%, #2d5a87 100%);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.logo {
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.logo-text {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo-text h1 {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  line-height: 1.2;
}

.sidebar-menu {
  border-right: none;
  flex: 1;
}

.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
  font-size: 14px;
}

.sidebar-menu .el-menu-item:hover {
  background: rgba(255,255,255,0.08);
}

.sidebar-menu .el-menu-item.is-active {
  background: rgba(94, 184, 255, 0.2);
}

.main-content {
  flex: 1;
  overflow: auto;
}
</style>
