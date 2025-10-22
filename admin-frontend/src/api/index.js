import axios from 'axios'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'X-Tenant-Id': 'demo_tenant',
    'X-User-Id': 'admin',
    'X-Request-Id': () => `req_${Date.now()}`
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    if (typeof config.headers['X-Request-Id'] === 'function') {
      config.headers['X-Request-Id'] = config.headers['X-Request-Id']()
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
request.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API错误:', error)
    return Promise.reject(error)
  }
)

// 场景API
export const scenarioApi = {
  list: () => request.get('/scenarios'),
  get: (id) => request.get(`/scenarios/${id}`),
  create: (data) => request.post('/scenarios', data),
  update: (id, data) => request.put(`/scenarios/${id}`, data),
  delete: (id) => request.delete(`/scenarios/${id}`)
}

// 物品API
export const itemApi = {
  list: (params) => request.get('/items', { params }),
  create: (data) => request.post('/items', data),
  batchImport: (data) => request.post('/items/batch', data)
}

// 实验API
export const experimentApi = {
  list: (params) => request.get('/experiments', { params }),
  get: (id) => request.get(`/experiments/${id}`),
  create: (data) => request.post('/experiments', data),
  start: (id) => request.post(`/experiments/${id}/start`),
  stop: (id) => request.post(`/experiments/${id}/stop`),
  results: (id) => request.get(`/experiments/${id}/results`)
}

// 管理后台API
export const adminApi = {
  dashboard: (params) => request.get('/admin/dashboard/overview', { params }),
  trends: (params) => request.get('/admin/dashboard/trends', { params }),
  itemDistribution: (scenarioId) => request.get('/admin/items/distribution', { 
    params: { scenario_id: scenarioId } 
  }),
  userBehavior: (scenarioId, days = 7) => request.get('/admin/users/behavior-analysis', { 
    params: { scenario_id: scenarioId, days } 
  }),
  exportData: (data) => request.post('/admin/data/export', null, { params: data })
}

export default request

