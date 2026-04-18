import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Typography, Spin } from 'antd'
import { ShoppingCartOutlined, DollarOutlined, MedicineBoxOutlined, RiseOutlined } from '@ant-design/icons'
import { getStatistics, getOrderList } from '../../services/api'
import './Dashboard.css'

const { Title } = Typography

interface Statistics {
  todayOrders: number
  todayRevenue: number
  totalMedicines: number
  monthRevenue: number
}

interface Order {
  id: number
  orderNo: string
  totalAmount: number
  status: number
  createTime: string
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

const Dashboard = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Statistics>({ todayOrders: 0, todayRevenue: 0, totalMedicines: 0, monthRevenue: 0 })
  const [orders, setOrders] = useState<Order[]>([])

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [statsRes, ordersRes] = await Promise.all([
        getStatistics().catch(() => ({ data: {} })),
        getOrderList({ pageNum: 1, pageSize: 5, status: 1 }).catch(() => ({ data: { records: [], list: [] } })),
      ])
      setStats(statsRes.data || {})
      const orderList = ordersRes.data?.records || ordersRes.data?.list || []
      setOrders(Array.isArray(orderList) ? orderList : [])
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: '订单号', dataIndex: 'orderNo', key: 'orderNo' },
    { title: '金额', dataIndex: 'totalAmount', key: 'totalAmount', render: (v: number) => `¥${v?.toFixed(2)}` },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: number) => <Tag color={statusMap[s]?.color}>{statusMap[s]?.text}</Tag> },
    { title: '时间', dataIndex: 'createTime', key: 'createTime' },
  ]

  return (
    <div className="dashboard">
      <Title level={4}>工作台</Title>
      <Spin spinning={loading}>
        <Row gutter={16} className="stat-row">
          <Col span={6}>
            <Card>
              <Statistic title="今日订单" value={stats.todayOrders} prefix={<ShoppingCartOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="今日收入" value={stats.todayRevenue} prefix={<DollarOutlined />} precision={2} suffix="元" />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="在售药品" value={stats.totalMedicines} prefix={<MedicineBoxOutlined />} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="本月收入" value={stats.monthRevenue} prefix={<RiseOutlined />} precision={2} suffix="元" />
            </Card>
          </Col>
        </Row>

        <Card title="待处理订单" className="order-card">
          <Table columns={columns} dataSource={orders} rowKey="id" pagination={false} locale={{ emptyText: '暂无待处理订单' }} />
        </Card>
      </Spin>
    </div>
  )
}

export default Dashboard
