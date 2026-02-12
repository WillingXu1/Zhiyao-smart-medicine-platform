import request from '../utils/request'

// 创建订单
export const createOrder = (data: {
  addressId: number
  receiverName: string
  receiverPhone: string
  receiverAddress: string
  items: Array<{ medicineId: number; quantity: number }>
  remark?: string
}) => {
  return request.post('/orders', data)
}

// 获取订单列表
export const getOrderList = (params: { status?: number; pageNum?: number; pageSize?: number }) => {
  return request.get('/orders', { params })
}

// 获取订单详情
export const getOrderDetail = (id: number) => {
  return request.get(`/orders/${id}`)
}

// 取消订单
export const cancelOrder = (id: number, reason: string) => {
  return request.put(`/orders/${id}/cancel`, null, { params: { reason } })
}

// 支付订单
export const payOrder = (id: number) => {
  return request.post(`/orders/${id}/pay`)
}

// 确认收货
export const confirmReceive = (id: number) => {
  return request.put(`/orders/${id}/confirm`)
}
