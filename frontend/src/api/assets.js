import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export const assetApi = {
  getAssets(params) {
    return http.get('/assets', { params })
  },
  getStats() {
    return http.get('/stats')
  },
  exportExcel(params) {
    return http.get('/export/excel', { params, responseType: 'blob' })
  },
  exportCsv(params) {
    return http.get('/export/csv', { params, responseType: 'blob' })
  },
  runCollect(formData) {
    return http.post('/collect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  runDetect(data) {
    return http.post('/detect', data)
  },
  getSettings() {
    return http.get('/settings')
  },
  saveSettings(data) {
    return http.post('/settings', data)
  },
}

// 兼容命名导出（让旧代码也能跑）
export const getAssets = (params) => assetApi.getAssets(params)
export const getStats = () => assetApi.getStats()
export const exportAssetsExcel = (params) => assetApi.exportExcel(params)
export const exportAssetsCsv = (params) => assetApi.exportCsv(params)
export const triggerHunterCollect = (data) => assetApi.runCollect(data)
export const triggerHunterAlert = (data) => assetApi.runDetect(data)
export const getSettings = () => assetApi.getSettings()
export const saveSettings = (data) => assetApi.saveSettings(data)
