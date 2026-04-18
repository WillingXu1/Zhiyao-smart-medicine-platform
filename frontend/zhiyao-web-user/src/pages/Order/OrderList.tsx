import { useEffect, useState } from 'react'
import { Card, Tabs, Table, Tag, Button, Empty, Spin, Typography, message, Popconfirm } from 'antd'
import { useNavigate } from 'react-router-dom'
import { getOrderList, cancelOrder, payOrder, confirmReceive } from '../../services/order'
import './OrderList.css'

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
  receiverName: string
  receiverPhone: string
  receiverAddress: string
  createTime: string
  payTime: string | null
  deliveryTime: string | null
  completeTime: string | null
  items: OrderItem[]
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

const OrderList = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [orders, setOrders] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [activeTab, setActiveTab] = useState('all')
  const [pageNum, setPageNum] = useState(1)
  const pageSize = 10

  useEffect(() => {
    fetchOrders()
  }, [activeTab, pageNum])

  const fetchOrders = async () => {
    try {
      setLoading(true)
      const params: { status?: number; pageNum: number; pageSize: number } = {
        pageNum,
        pageSize,
      }
      if (activeTab !== 'all') {
        params.status = Number(activeTab)
      }
      const res = await getOrderList(params)
      // 兼容多种数据结构：records、list或直接数组
      const orderList = res.data?.records || res.data?.list || res.data || []
      setOrders(Array.isArray(orderList) ? orderList : [])
      setTotal(res.data?.total || 0)
    } catch (error) {
      console.error('获取订单列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = async (id: number) => {
    try {
      await cancelOrder(id, '用户主动取消')
      message.success('订单已取消')
      fetchOrders()
    } catch (error) {
      console.error('取消订单失败:', error)
    }
  }

  const handlePay = async (id: number) => {
    try {
      await payOrder(id)
      message.success('支付成功')
      fetchOrders()
    } catch (error) {
      console.error('支付失败:', error)
    }
  }

  const handleConfirm = async (id: number) => {
    try {
      await confirmReceive(id)
      message.success('已确认收货')
      fetchOrders()
    } catch (error) {
      console.error('确认收货失败:', error)
    }
  }

  const columns = [
    {
      title: '订单信息',
      dataIndex: 'orderNo',
      render: (_: string, record: Order) => (
        <div className="order-info" onClick={() => navigate(`/order/${record.id}`)}>
          <div className="order-no">订单号：{record.orderNo}</div>
          <div className="order-time">
            <Text type="secondary">{record.createTime}</Text>
          </div>
        </div>
      ),
    },
    {
      title: '商品',
      dataIndex: 'items',
      width: 300,
      render: (items: OrderItem[]) => (
        <div className="order-items">
          {items?.slice(0, 2).map((item, index) => (
            <div key={index} className="order-item-row">
              <Text ellipsis className="item-name">{item.medicineName}</Text>
              <Text type="secondary" className="item-qty">x{item.quantity}</Text>
            </div>
          ))}
          {items?.length > 2 && (
            <Text type="secondary">...等{items.length}件商品</Text>
          )}
        </div>
      ),
    },
    {
      title: '金额',
      dataIndex: 'payAmount',
      width: 120,
      render: (amount: number) => (
        <span className="order-amount">¥{amount?.toFixed(2)}</span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      render: (status: number) => (
        <Tag color={statusMap[status]?.color}>{statusMap[status]?.text}</Tag>
      ),
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 180,
      render: (_: unknown, record: Order) => (
        <div className="order-actions">
          <Button type="link" onClick={() => navigate(`/order/${record.id}`)}>
            查看详情
          </Button>
          {record.status === 0 && (
            <>
              <Button type="primary" size="small" onClick={() => handlePay(record.id)}>
                立即支付
              </Button>
              <Popconfirm
                title="确定取消订单吗？"
                onConfirm={() => handleCancel(record.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button size="small" danger>取消</Button>
              </Popconfirm>
            </>
          )}
          {record.status === 4 && (
            <Button type="primary" size="small" onClick={() => handleConfirm(record.id)}>
              确认收货
            </Button>
          )}
        </div>
      ),
    },
  ]

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: '0', label: '待支付' },
    { key: '1', label: '待接单' },
    { key: '3', label: '待配送' },
    { key: '4', label: '配送中' },
    { key: '5', label: '已完成' },
  ]

  return (
    <div className="order-list-page">
      <Title level={3} className="page-title">我的订单</Title>

      <Card className="order-list-card" bordered={false}>
        <Tabs
          activeKey={activeTab}
          onChange={(key) => {
            setActiveTab(key)
            setPageNum(1)
          }}
          items={tabItems}
        />

        <Spin spinning={loading}>
          {orders.length > 0 ? (
            <Table
              columns={columns}
              dataSource={orders}
              rowKey="id"
              pagination={{
                current: pageNum,
                pageSize,
                total,
                onChange: setPageNum,
                showTotal: (total) => `共 ${total} 条订单`,
              }}
            />
          ) : (
            <Empty description="暂无订单" />
          )}
        </Spin>
      </Card>
    </div>
  )
}

export default OrderList
