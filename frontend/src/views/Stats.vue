<template>
  <div class="stats-page">
    <h2 class="page-title">数据统计</h2>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-label">资产总数</div>
        <div class="stat-value">{{ stats.total }}</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-label">本周新增</div>
        <div class="stat-value">{{ stats.week_new }}</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-label">今日新增</div>
        <div class="stat-value">{{ stats.today_new }}</div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-label">平台总数</div>
        <div class="stat-value">{{ stats.platforms }}</div>
      </el-card>
    </div>

    <!-- 平台分布 & 省份分布 -->
    <div class="charts-row">
      <el-card class="chart-card" shadow="hover">
        <h3 class="card-title">平台分布</h3>
        <div class="platform-list">
          <div class="platform-item" v-for="item in platformStats" :key="item.name">
            <span class="platform-name">{{ item.name }}</span>
            <el-progress :percentage="item.percent" :color="item.color" />
            <span class="platform-count">{{ item.count }}</span>
          </div>
        </div>
      </el-card>
      <el-card class="chart-card" shadow="hover">
        <h3 class="card-title">省份分布 Top10</h3>
        <div class="province-list">
          <div class="province-item" v-for="(count, province) in topProvinces" :key="province">
            <span class="province-name">{{ province }}</span>
            <el-progress :percentage="count / stats.total * 100" color="#409eff" />
            <span class="province-count">{{ count }}</span>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 行业分布 -->
    <el-card class="chart-card full-width" shadow="hover">
      <h3 class="card-title">行业分布</h3>
      <div class="industry-list">
        <div class="industry-item" v-for="(count, industry) in industryStats" :key="industry">
          <span class="industry-name">{{ industry }}</span>
          <el-progress :percentage="count / stats.total * 100" color="#67c23a" />
          <span class="industry-count">{{ count }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { assetApi } from '@/api/assets'

const stats = ref({ total: 0, week_new: 0, today_new: 0, platforms: 0 })
const platformStats = ref([])
const topProvinces = ref({})
const industryStats = ref({})

async function loadStats() {
  try {
    const res = await getStats()
    stats.value = res.data.stats || { total: 0, week_new: 0, today_new: 0, platforms: 0 }
    platformStats.value = res.data.platform_stats || []
    topProvinces.value = res.data.top_provinces || {}
    industryStats.value = res.data.industry_stats || {}
  } catch {}
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.stats-page {
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
}

.stat-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.charts-row {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  flex: 1;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.platform-list,
.province-list,
.industry-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.platform-item,
.province-item,
.industry-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.platform-name,
.province-name,
.industry-name {
  width: 100px;
  font-size: 13px;
  color: #606266;
  flex-shrink: 0;
}

.platform-count,
.province-count,
.industry-count {
  font-size: 13px;
  color: #909399;
  width: 50px;
  text-align: right;
  flex-shrink: 0;
}

.full-width {
  margin-bottom: 20px;
}

:deep(.el-progress) {
  flex: 1;
}
</style>
