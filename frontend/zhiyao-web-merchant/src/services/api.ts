import request from '../utils/request'

// 商家注册
export const registerMerchant = (data: {
  phone: string
  password: string
  name: string
  address: string
  businessHours: string
  businessLicense?: string
  pharmacistLicense?: string
}) => {
  return request.post('/merchant/auth/register', data)
}

// 商家登录
export const login = (data: { phone: string; password: string }) => {
  return request.post('/merchant/auth/login', data)
}

// 获取商家信息
export const getMerchantInfo = () => {
  return request.get('/merchant/info')
}

// 获取店铺统计数据
export const getStatistics = () => {
  return request.get('/merchant/statistics')
}

// 药品管理
export const getMedicineCategories = () => {
  return request.get('/medicines/categories')
}

export const getMedicineList = (params: { pageNum?: number; pageSize?: number; keyword?: string }) => {
  return request.get('/merchant/medicines', { params })
}

export const addMedicine = (data: Record<string, unknown>) => {
  return request.post('/merchant/medicines', data)
}

export const updateMedicine = (id: number, data: Record<string, unknown>) => {
  return request.put(`/merchant/medicines/${id}`, data)
}

export const deleteMedicine = (id: number) => {
  return request.delete(`/merchant/medicines/${id}`)
}

export const updateMedicineStatus = (id: number, status: number) => {
  return request.put(`/merchant/medicines/${id}/status`, null, { params: { status } })
}

// 订单管理
export const getOrderList = (params: { status?: number; pageNum?: number; pageSize?: number }) => {
  return request.get('/merchant/orders', { params })
}

export const getOrderDetail = (id: number) => {
  return request.get(`/merchant/orders/${id}`)
}

// 商家接单
export const acceptOrder = (id: number) => {
  return request.put(`/merchant/orders/${id}/accept`)
}

// 商家拒单
export const rejectOrder = (id: number, reason: string) => {
  return request.put(`/merchant/orders/${id}/reject`, null, { params: { reason } })
}
