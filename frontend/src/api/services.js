import axios from './axios'

export const authService = {
  login: (credentials) => axios.post('/auth/login/', credentials),
  register: (data) => axios.post('/auth/register/', data),
  getCurrentUser: () => axios.get('/auth/me/'),
}

export const dashboardService = {
  getStats: () => axios.get('/dashboard/stats/'),
}

export const dataSourceService = {
  getAll: (params) => axios.get('/data-sources/', { params }),
  getById: (id) => axios.get(`/data-sources/${id}/`),
  create: (data) => axios.post('/data-sources/', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
}

export const emissionRecordService = {
  getAll: (params) => axios.get('/emission-records/', { params }),
  getById: (id) => axios.get(`/emission-records/${id}/`),
  update: (id, data) => axios.patch(`/emission-records/${id}/`, data),
  approve: (id) => axios.post(`/emission-records/${id}/approve/`),
  reject: (id, notes) => axios.post(`/emission-records/${id}/reject/`, { notes }),
  lock: (id) => axios.post(`/emission-records/${id}/lock/`),
  bulkApprove: (recordIds) => axios.post('/emission-records/bulk_approve/', { record_ids: recordIds }),
}

export const auditLogService = {
  getAll: (params) => axios.get('/audit-logs/', { params }),
}

export const notificationService = {
  getAll: () => axios.get('/notifications/'),
  markRead: (id) => axios.post(`/notifications/${id}/mark_read/`),
  markAllRead: () => axios.post('/notifications/mark_all_read/'),
}
