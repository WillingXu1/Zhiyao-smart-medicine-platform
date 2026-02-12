import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios'
import { message } from 'antd'

const request: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

request.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    if (res.code === 200) return res
    if (res.code === 401) {
      localStorage.removeItem('admin_token')
      message.error('登录已过期，请重新登录')
      window.location.href = '/login'
      return Promise.reject(new Error('未登录'))
    }
    message.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message))
  },
  (error) => {
    message.error(error.response?.data?.message || '网络错误')
    return Promise.reject(error)
  }
)

export default request
