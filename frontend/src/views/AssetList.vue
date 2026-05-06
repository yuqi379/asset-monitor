<template>
  <div class="asset-list">
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

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="搜索资产关键词"
        style="width: 140px"
        size="small"
        clearable
      />
      <el-select v-model="platform" placeholder="选择平台" clearable size="small" style="width: 110px">
        <el-option label="全部" value="" />
        <el-option label="Hunter" value="hunter" />
        <el-option label="GitHub" value="github" />
      </el-select>
      <el-button type="primary" size="small" @click="loadAssets">搜索</el-button>
      <el-button size="small" @click="exportExcel">导出Excel</el-button>
      <el-button type="primary" size="small" @click="openCollectDialog">触发采集</el-button>
      <el-button type="danger" size="small" @click="openAlertDialog">触发预警</el-button>
    </div>

    <!-- 资产表格 -->
    <el-table :data="assets" stripe style="width: 100%" v-loading="loading">
      <el-table-column prop="asset_id" label="ID" width="80" />
      <el-table-column prop="url" label="URL" min-width="200" show-overflow-tooltip />
      <el-table-column prop="title" label="标题" min-width="150" show-overflow-tooltip />
      <el-table-column prop="platform" label="平台" width="100">
        <template #default="{ row }">
          <el-tag :type="row.platform === 'hunter' ? '' : 'success'" size="small">
            {{ row.platform === 'hunter' ? 'Hunter' : 'GitHub' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="ip" label="IP" width="140" />
      <el-table-column prop="country" label="国家" width="80" />
      <el-table-column prop="province" label="省份" width="80" />
      <el-table-column prop="industry" label="行业" width="120" show-overflow-tooltip />
      <el-table-column prop="tags" label="标签" width="150" show-overflow-tooltip />
      <el-table-column prop="create_time" label="发现时间" width="160" />
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        background
        layout="prev, pager, next, total"
        :total="total"
        :page-size="20"
        v-model:current-page="page"
        @current-change="loadAssets"
      />
    </div>

    <!-- 采集弹窗 -->
    <el-dialog v-model="collectVisible" title="触发采集" width="500px">
      <el-form :model="collectForm" label-width="90px">
        <el-form-item label="平台">
          <el-select v-model="collectForm.platform" style="width: 100%">
            <el-option label="Hunter" value="hunter" />
            <el-option label="GitHub" value="github" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="collectForm.keyword" placeholder="多个关键词用逗号分隔" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="collectVisible = false">取消</el-button>
        <el-button type="primary" @click="triggerCollect">确认采集</el-button>
      </template>
    </el-dialog>

    <!-- 预警弹窗 -->
    <el-dialog v-model="alertVisible" title="触发预警" width="500px">
      <el-form :model="alertForm" label-width="90px">
        <el-form-item label="预警类型">
          <el-select v-model="alertForm.type" style="width: 100%">
            <el-option label="邮件" value="email" />
            <el-option label="钉钉" value="dingtalk" />
            <el-option label="飞书" value="feishu" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="alertForm.keyword" placeholder="触发预警的关键词" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="alertVisible = false">取消</el-button>
        <el-button type="primary" @click="doTriggerAlert">确认预警</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { assetApi } from '@/api/assets'

const assets = ref([])
const loading = ref(false)
const keyword = ref('')
const platform = ref('')
const page = ref(1)
const total = ref(0)
const stats = ref({ total: 0, week_new: 0, today_new: 0, platforms: 0 })
const collectVisible = ref(false)
const alertVisible = ref(false)
const collectForm = ref({ platform: 'hunter', keyword: '' })
const alertForm = ref({ type: 'email', keyword: '' })

async function loadAssets() {
  loading.value = true
  try {
    const res = await assetApi.getAssets({ keyword: keyword.value, platform: platform.value, page: page.value, page_size: 20 })
    // API 返回数组，转为前端期望的字段名
    const list = Array.isArray(res.data) ? res.data : (res.data?.list || [])
    assets.value = list.map(item => ({
      asset_id: item.id,
      title: item.web_title || item.title,
      url: item.url,
      platform: item.platform,
      ip: item.ip,
      country: item.city,
      province: item.province,
      industry: item.industry || '',
      tags: item.matched_fields || '',
      create_time: item.found_date,
    }))
    total.value = list.length
    stats.value = { total: list.length, week_new: 0, today_new: 0, platforms: 1 }
  } catch {
    ElMessage.error('加载资产失败')
  } finally {
    loading.value = false
  }
}

function exportExcel() {
  assetApi.exportExcel({ keyword: keyword.value, platform: platform.value })
}

function openCollectDialog() {
  collectForm.value = { platform: 'hunter', keyword: '' }
  collectVisible.value = true
}

async function triggerCollect() {
  try {
    await assetApi.runCollect(collectForm.value)
    ElMessage.success('采集已触发')
    collectVisible.value = false
  } catch {
    ElMessage.error('触发失败')
  }
}

function openAlertDialog() {
  alertForm.value = { type: 'email', keyword: '' }
  alertVisible.value = true
}

async function doTriggerAlert() {
  try {
    await assetApi.runDetect(alertForm.value)
    ElMessage.success('预警已触发')
    alertVisible.value = false
  } catch {
    ElMessage.error('触发失败')
  }
}

onMounted(() => {
  loadAssets()
})
</script>

<style scoped>
.asset-list {
  padding: 20px;
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
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  align-items: center;
}

:deep(.el-table .cell) {
  text-align: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
