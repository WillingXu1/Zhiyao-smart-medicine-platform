import request from '../utils/request'

// 用户注册
export const register = (data: {
  username: string
  password: string
  phone: string
  nickname?: string
}) => {
  return request.post('/auth/register', data)
}

// 用户登录
export const login = (data: { username: string; password: string }) => {
  return request.post('/auth/login', data)
}

// 获取当前用户信息
export const getCurrentUser = () => {
  return request.get('/user/info')
}

// 修改密码
export const changePassword = (data: { oldPassword: string; newPassword: string }) => {
  return request.put('/user/password', data)
}
