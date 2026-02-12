import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Typography, Spin } from 'antd'
import { UserOutlined, ShopOutlined, MedicineBoxOutlined, FileTextOutlined, DollarOutlined, RiseOutlined, CarOutlined } from '@ant-design/icons'
import { getStatistics } from '../../services/api'

const { Title } = Typography

interface Stats {
  totalUsers: number
  totalMerchants: number
  totalMedicines: number
  totalOrders: number
  todayOrders: number
  todayRevenue: number
  monthRevenue: number
  totalRiders?: number
  onlineRiders?: number
  pendingOrders?: number
  deliveringOrders?: number
}

const Dashboard = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Stats>({
    totalUsers: 0,
    totalMerchants: 0,
    totalMedicines: 0,
    totalOrders: 0,
    todayOrders: 0,
    todayRevenue: 0,
    monthRevenue: 0,
    totalRiders: 0,
    onlineRiders: 0,
    pendingOrders: 0,
    deliveringOrders: 0
  })

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const res = await getStatistics().catch(() => ({ data: {} }))
      setStats(res.data || {})
    } catch (error) {
      console.error('获取统计数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Title level={4}>数据统计</Title>
      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col span={6}>
            <Card><Statistic title="总用户数" value={stats.totalUsers} prefix={<UserOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="入驻商家" value={stats.totalMerchants} prefix={<ShopOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="骑手数量" value={stats.totalRiders || 0} prefix={<CarOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="在线骑手" value={stats.onlineRiders || 0} prefix={<CarOutlined />} valueStyle={{ color: '#3f8600' }} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="药品数量" value={stats.totalMedicines} prefix={<MedicineBoxOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="总订单数" value={stats.totalOrders} prefix={<FileTextOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="待处理" value={stats.pendingOrders || 0} prefix={<FileTextOutlined />} valueStyle={{ color: '#faad14' }} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="配送中" value={stats.deliveringOrders || 0} prefix={<FileTextOutlined />} valueStyle={{ color: '#1890ff' }} /></Card>
          </Col>
          <Col span={8}>
            <Card><Statistic title="今日订单" value={stats.todayOrders} prefix={<FileTextOutlined />} valueStyle={{ color: '#3f8600' }} /></Card>
          </Col>
          <Col span={8}>
            <Card><Statistic title="今日收入" value={stats.todayRevenue} prefix={<DollarOutlined />} precision={2} suffix="元" valueStyle={{ color: '#cf1322' }} /></Card>
          </Col>
          <Col span={8}>
            <Card><Statistic title="本月收入" value={stats.monthRevenue} prefix={<RiseOutlined />} precision={2} suffix="元" valueStyle={{ color: '#1890ff' }} /></Card>
          </Col>
        </Row>
      </Spin>
    </div>
  )
}

export default Dashboard
