import request from '../utils/request'

// 获取用户信息
export const getUserInfo = () => {
  return request.get('/user/info')
}

// 更新用户信息
export const updateUserInfo = (data: { nickname?: string; avatar?: string; email?: string }) => {
  return request.put('/user/info', data)
}

// 修改密码
export const changePassword = (data: { oldPassword: string; newPassword: string }) => {
  return request.put('/user/password', data)
}

// 获取收货地址列表
export const getAddressList = () => {
  return request.get('/user/addresses')
}

// 添加收货地址
export const addAddress = (data: {
  name: string
  phone: string
  province: string
  city: string
  district: string
  detail: string
  isDefault?: boolean
}) => {
  return request.post('/user/addresses', data)
}

// 更新收货地址
export const updateAddress = (id: number, data: {
  name?: string
  phone?: string
  province?: string
  city?: string
  district?: string
  detail?: string
  isDefault?: boolean
}) => {
  return request.put(`/user/addresses/${id}`, data)
}

// 删除收货地址
export const deleteAddress = (id: number) => {
  return request.delete(`/user/addresses/${id}`)
}

// 设置默认地址
export const setDefaultAddress = (id: number) => {
  return request.put(`/user/addresses/${id}/default`)
}

// 获取收藏列表
export const getFavorites = () => {
  return request.get('/user/favorites')
}

// 添加收藏
export const addFavorite = (medicineId: number) => {
  return request.post(`/user/favorites/${medicineId}`)
}

// 取消收藏
export const removeFavorite = (medicineId: number) => {
  return request.delete(`/user/favorites/${medicineId}`)
}

// 上传头像
export const uploadAvatar = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/upload/avatar', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
