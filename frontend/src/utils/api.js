import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('rg_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('rg_token')
      localStorage.removeItem('rg_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api

export const authApi = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
}

export const transactionsApi = {
  list: (params) => api.get('/transactions', { params }),
  summary: () => api.get('/transactions/summary'),
  get: (id) => api.get(`/transactions/${id}`),
  upload: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/transactions/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  updateStatus: (id, status) => api.patch(`/transactions/${id}/status`, null, { params: { status } }),
}

export const alertsApi = {
  list: (params) => api.get('/alerts', { params }),
  count: () => api.get('/alerts/count'),
  get: (id) => api.get(`/alerts/${id}`),
  update: (id, status) => api.patch(`/alerts/${id}`, { status }),
}

export const casesApi = {
  list: (params) => api.get('/cases', { params }),
  get: (id) => api.get(`/cases/${id}`),
  create: (data) => api.post('/cases', data),
  update: (id, data) => api.patch(`/cases/${id}`, data),
  addComment: (id, content) => api.post(`/cases/${id}/comments`, { content }),
  delete: (id) => api.delete(`/cases/${id}`),
}

export const usersApi = {
  list: () => api.get('/users'),
  get: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.patch(`/users/${id}`, data),
  deactivate: (id) => api.delete(`/users/${id}`),
}

export const dashboardApi = {
  stats: () => api.get('/dashboard'),
  auditLogs: (params) => api.get('/audit-logs', { params }),
}
