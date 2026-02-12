import request from '../utils/request'

// 搜索药品
export const searchMedicines = (params: {
  keyword?: string
  categoryId?: number
  merchantId?: number
  isPrescription?: number
  sortBy?: string
  sortOrder?: string
  pageNum?: number
  pageSize?: number
}) => {
  return request.get('/medicines', { params })
}

// 获取药品详情
export const getMedicineDetail = (id: number) => {
  return request.get(`/medicines/${id}`)
}

// 获取药品分类
export const getCategories = () => {
  return request.get('/medicines/categories')
}

// 获取热销药品
export const getHotMedicines = (limit: number = 10) => {
  return request.get('/medicines/hot', { params: { limit } })
}

// 根据分类获取药品
export const getMedicinesByCategory = (categoryId: number, pageNum: number = 1, pageSize: number = 10) => {
  return request.get(`/medicines/category/${categoryId}`, { params: { pageNum, pageSize } })
}
