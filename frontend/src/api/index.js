import client from './client'

export const authApi = {
  login: (data) => client.post('/auth/login', data),
}

export const transactionsApi = {
  list: (params) => client.get('/transactions', { params }),
  get: (id) => client.get(`/transactions/${id}`),
  create: (data) => client.post('/transactions', data),
  update: (id, data) => client.put(`/transactions/${id}`, data),
  delete: (id) => client.delete(`/transactions/${id}`),
}

export const usersApi = {
  list: (params) => client.get('/users', { params }),
  get: (id) => client.get(`/users/${id}`),
  create: (data) => client.post('/users', data),
  update: (id, data) => client.put(`/users/${id}`, data),
  delete: (id) => client.delete(`/users/${id}`),
}

export const organizationsApi = {
  list: (params) => client.get('/organizations', { params }),
  get: (id) => client.get(`/organizations/${id}`),
  create: (data) => client.post('/organizations', data),
  update: (id, data) => client.put(`/organizations/${id}`, data),
  delete: (id) => client.delete(`/organizations/${id}`),
}

export const auditLogsApi = {
  list: (params) => client.get('/audit-logs', { params }),
}

export const healthApi = {
  check: () => client.get('/health'),
}
