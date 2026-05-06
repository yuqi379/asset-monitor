import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const BASE_URL = '/api'

export const useAssetStore = defineStore('assets', () => {
  const assets = ref([])
  const loading = ref(false)
  const total = ref(0)
  const stats = ref({ total: 0, by_platform: [], by_province: [] })

  const fetchAssets = async (params = {}) => {
    loading.value = true
    try {
      const res = await axios.get(`${BASE_URL}/assets`, { params })
      assets.value = res.data
      total.value = res.data.length
    } finally {
      loading.value = false
    }
  }

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${BASE_URL}/stats`)
      stats.value = res.data
    } catch (e) {
      console.error('获取统计失败', e)
    }
  }

  return { assets, loading, total, stats, fetchAssets, fetchStats }
})
