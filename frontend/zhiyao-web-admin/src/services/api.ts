import request from '../utils/request'

// 管理员登录
export const login = (data: { username: string; password: string }) => {
  return request.post('/auth/admin/login', data)
}

// 统计数据
export const getStatistics = () => {
  return request.get('/admin/statistics')
}

// 用户管理
export const getUserList = (params: { pageNum?: number; pageSize?: number; keyword?: string }) => {
  return request.get('/admin/users', { params })
}

export const updateUserStatus = (id: number, status: number) => {
  return request.put(`/admin/users/${id}/status`, null, { params: { status } })
}

// 商家管理
export const getMerchantList = (params: { pageNum?: number; pageSize?: number; status?: number }) => {
  return request.get('/admin/merchants', { params })
}

export const auditMerchant = (id: number, status: number, reason?: string) => {
  return request.put(`/admin/merchants/${id}/audit`, { status, reason })
}

// 药品管理
export const getCategories = () => {
  return request.get('/medicines/categories')
}

export const getMedicineList = (params: { pageNum?: number; pageSize?: number; keyword?: string }) => {
  return request.get('/admin/medicines', { params })
}

export const auditMedicine = (id: number, status: number, reason?: string, categoryId?: number) => {
  return request.put(`/admin/medicines/${id}/audit`, { status, reason, categoryId })
}

// 订单管理
export const getOrderList = (params: { pageNum?: number; pageSize?: number; status?: number }) => {
  return request.get('/admin/orders', { params })
}

export const getOrderDetail = (id: number) => {
  return request.get(`/admin/orders/${id}`)
}

// 系统设置
export const updateProfile = (data: { name?: string; email?: string; phone?: string; avatar?: string }) => {
  return request.put('/admin/profile', data)
}

export const changePassword = (data: { oldPassword: string; newPassword: string; confirmPassword: string }) => {
  return request.put('/admin/password', data)
}

export const getPlatformConfig = () => {
  return request.get('/admin/config')
}

export const savePlatformConfig = (data: {
  platformName?: string
  contactPhone?: string
  deliveryFee?: number
  minOrderAmount?: number
  deliveryRange?: number
}) => {
  return request.put('/admin/config', data)
}
