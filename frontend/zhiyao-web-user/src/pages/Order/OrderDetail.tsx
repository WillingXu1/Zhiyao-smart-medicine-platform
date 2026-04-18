import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Row, Col, Tag, Button, Spin, Typography, Divider, Steps, message, Popconfirm } from 'antd'
import { 
  EnvironmentOutlined, 
  PhoneOutlined, 
  UserOutlined,
  MedicineBoxOutlined,
  LeftOutlined
} from '@ant-design/icons'
import { getOrderDetail, cancelOrder, payOrder, confirmReceive } from '../../services/order'
import './OrderDetail.css'

const { Title, Text } = Typography

interface OrderItem {
  medicineId: number
  medicineName: string
  specification: string
  price: number
  quantity: number
  image: string
}

interface Order {
  id: number
  orderNo: string
  status: number
  totalAmount: number
  payAmount: number
  deliveryFee: number
  receiverName: string
  receiverPhone: string
  receiverAddress: string
  remark: string
  createTime: string
  payTime: string | null
  deliveryTime: string | null
  completeTime: string | null
  items: OrderItem[]
  riderName: string | null
  riderPhone: string | null
}

const statusMap: Record<number, { text: string; color: string }> = {
  0: { text: '待支付', color: 'orange' },
  1: { text: '待接单', color: 'blue' },
  2: { text: '商家拒单', color: 'red' },
  3: { text: '待配送', color: 'cyan' },
  4: { text: '配送中', color: 'purple' },
  5: { text: '已完成', color: 'green' },
  6: { text: '已取消', color: 'default' },
}

const OrderDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [order, setOrder] = useState<Order | null>(null)

  useEffect(() => {
    if (id) {
      const orderId = Number(id)
      // 检查ID是否有效
      if (!isNaN(orderId) && orderId > 0) {
        fetchOrderDetail(orderId)
      } else {
        message.error('ID无效')
        navigate('/orders')
      }
    } else {
      message.error('ID不能为空')
      navigate('/orders')
    }
  }, [id, navigate])

  const fetchOrderDetail = async (orderId: number) => {
    try {
      setLoading(true)
      const res = await getOrderDetail(orderId)
      setOrder(res.data)
    } catch (error) {
      console.error('获取订单详情失败:', error)
      message.error('获取订单详情失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async () => {
    if (!order) return
    try {
      await cancelOrder(order.id, '用户主动取消')
      message.success('订单已取消')
      fetchOrderDetail(order.id)
    } catch (error) {
      console.error('取消订单失败:', error)
    }
  }

  const handlePay = async () => {
    if (!order) return
    try {
      await payOrder(order.id)
      message.success('支付成功')
      fetchOrderDetail(order.id)
    } catch (error) {
      console.error('支付失败:', error)
    }
  }

  const handleConfirm = async () => {
    if (!order) return
    try {
      await confirmReceive(order.id)
      message.success('已确认收货')
      fetchOrderDetail(order.id)
    } catch (error) {
      console.error('确认收货失败:', error)
    }
  }

  const getStepCurrent = (status: number) => {
    if (status === 4) return 0 // 已取消
    return status
  }

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" />
      </div>
    )
  }

  if (!order) {
    return (
      <div className="error-container">
        <Title level={4}>订单不存在</Title>
        <Button type="primary" onClick={() => navigate('/orders')}>
          返回订单列表
        </Button>
      </div>
    )
  }

  return (
    <div className="order-detail-page">
      {/* 订单状态 */}
      <Card className="status-card" bordered={false}>
        <div className="status-header">
          <Tag color={statusMap[order.status]?.color} className="status-tag">
            {statusMap[order.status]?.text}
          </Tag>
          <span className="order-no">订单号：{order.orderNo}</span>
        </div>

        {order.status !== 4 && (
          <Steps
            className="order-steps"
            current={getStepCurrent(order.status)}
            items={[
              { title: '待付款', description: order.createTime },
              { title: '待发货', description: order.payTime || '' },
              { title: '配送中', description: order.deliveryTime || '' },
              { title: '已完成', description: order.completeTime || '' },
            ]}
          />
        )}

        <div className="status-actions">
          {order.status === 0 && (
            <>
              <Button type="primary" size="large" onClick={handlePay}>
                立即支付
              </Button>
              <Popconfirm
                title="确定取消订单吗？"
                onConfirm={handleCancel}
                okText="确定"
                cancelText="取消"
              >
                <Button size="large">取消订单</Button>
              </Popconfirm>
            </>
          )}
          {order.status === 2 && (
            <Button type="primary" size="large" onClick={handleConfirm}>
              确认收货
            </Button>
          )}
        </div>
      </Card>

      <Row gutter={16}>
        <Col xs={24} lg={16}>
          {/* 收货信息 */}
          <Card className="info-card" title="收货信息" bordered={false}>
            <div className="info-row">
              <UserOutlined className="info-icon" />
              <span>{order.receiverName}</span>
            </div>
            <div className="info-row">
              <PhoneOutlined className="info-icon" />
              <span>{order.receiverPhone}</span>
            </div>
            <div className="info-row">
              <EnvironmentOutlined className="info-icon" />
              <span>{order.receiverAddress}</span>
            </div>
            {order.remark && (
              <div className="info-row remark">
                <span>备注：{order.remark}</span>
              </div>
            )}
          </Card>

          {/* 配送信息 */}
          {order.status === 2 && order.riderName && (
            <Card className="info-card" title="配送信息" bordered={false}>
              <div className="info-row">
                <UserOutlined className="info-icon" />
                <span>骑手：{order.riderName}</span>
              </div>
              <div className="info-row">
                <PhoneOutlined className="info-icon" />
                <span>电话：{order.riderPhone}</span>
              </div>
            </Card>
          )}

          {/* 商品清单 */}
          <Card className="items-card" title="商品清单" bordered={false}>
            {order.items?.map((item, index) => (
              <div key={index} className="order-item">
                <div className="item-image">
                  {item.image ? (
                    <img src={item.image} alt={item.medicineName} />
                  ) : (
                    <MedicineBoxOutlined style={{ fontSize: 40, color: '#10B981' }} />
                  )}
                </div>
                <div className="item-info">
                  <div className="item-name">{item.medicineName}</div>
                  <Text type="secondary">{item.specification}</Text>
                </div>
                <div className="item-price-qty">
                  <span className="item-price">¥{item.price?.toFixed(2)}</span>
                  <span className="item-qty">x{item.quantity}</span>
                </div>
                <div className="item-subtotal">
                  ¥{(item.price * item.quantity).toFixed(2)}
                </div>
              </div>
            ))}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* 金额汇总 */}
          <Card className="summary-card" bordered={false}>
            <Title level={4}>订单金额</Title>
            <Divider />
            <div className="summary-row">
              <span>商品总额</span>
              <span>¥{order.totalAmount?.toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>配送费</span>
              <span className="free-delivery">
                {order.deliveryFee === 0 ? '免运费' : `¥${order.deliveryFee?.toFixed(2)}`}
              </span>
            </div>
            <Divider />
            <div className="summary-row total">
              <span>实付金额</span>
              <span className="final-price">¥{order.payAmount?.toFixed(2)}</span>
            </div>
          </Card>
        </Col>
      </Row>

      <Button
        className="back-button"
        icon={<LeftOutlined />}
        onClick={() => navigate('/orders')}
      >
        返回订单列表
      </Button>
    </div>
  )
}

export default OrderDetail
