<template>
  <div class="page">
    <div class="page-header">
      <h2>系统设置</h2>
    </div>

    <div class="settings-card">
      <h3>当前配置</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="Hunter API Keys">
          <el-tag size="small" type="primary">{{ config.hunter_keys || 0 }} 个</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="GitHub Tokens">
          <el-tag size="small" type="success">{{ config.github_tokens || 0 }} 个</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="钉钉配置">
          <el-tag size="small" :type="config.dingtalk_configured ? 'success' : 'danger'">
            {{ config.dingtalk_configured ? '已配置' : '未配置' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="调度策略">
          <el-tag size="small">每日增量 + 每月全量</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="settings-card">
      <h3>关于本系统</h3>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="系统名称">资产测绘监控系统</el-descriptions-item>
        <el-descriptions-item label="版本">v2.1</el-descriptions-item>
        <el-descriptions-item label="技术栈">Vue3 + Element Plus + Flask + SQLite</el-descriptions-item>
        <el-descriptions-item label="数据平台">Hunter（主力）+ GitHub（补充）</el-descriptions-item>
      </el-descriptions>
    </div>

    <div class="settings-card">
      <h3>使用说明</h3>
      <el-alert type="info" :closable="false" show-icon>
        <template #title>
          <div style="line-height: 1.8">
            <strong>启动方式：</strong><br>
            1. 启动后端：<code style="background:#f5f5f5;padding:2px 6px;border-radius:4px">cd asset_monitor && python api_server.py</code><br>
            2. 启动前端：<code style="background:#f5f5f5;padding:2px 6px;border-radius:4px">cd frontend && npm run dev</code><br>
            3. 访问 <code style="background:#f5f5f5;padding:2px 6px;border-radius:4px">http://localhost:5173</code>
          </div>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const config = ref({
  hunter_keys: 1,
  github_tokens: 1,
  dingtalk_configured: false,
})
</script>

<style scoped>
.page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 20px;
  color: #1e3a5f;
}

.settings-card {
  background: white;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.settings-card h3 {
  font-size: 15px;
  color: #333;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}
</style>
