import { useEffect, useState } from 'react'
import { Table, Tabs, Tag, Button, Space, message, Typography, Modal } from 'antd'
import { EyeOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons'
import { getOrderList, acceptOrder, rejectOrder, getOrderDetail } from '../../services/api'

const { Title, Text } = Typography

interface Order {
  id: number
  orderNo: string
  totalAmount: number
  status: number
  receiverName: string
  receiverPhone: string
  receiverAddress: string
  createTime: string
  items: Array<{ medicineName: string; quantity: number; price: number }>
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

const OrderManage = () => {
  const [loading, setLoading] = useState(false)
  const [orders, setOrders] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [pageNum, setPageNum] = useState(1)
  const [activeTab, setActiveTab] = useState('all')
  const [detailVisible, setDetailVisible] = useState(false)
  const [currentOrder, setCurrentOrder] = useState<Order | null>(null)

  useEffect(() => {
    fetchOrders()
  }, [pageNum, activeTab])

  const fetchOrders = async () => {
    setLoading(true)
    try {
      const params: { status?: number; pageNum: number; pageSize: number } = { pageNum, pageSize: 10 }
      if (activeTab !== 'all') params.status = Number(activeTab)
      const res = await getOrderList(params)
      console.log('商家订单列表返回数据:', res.data)
      // 兼容多种数据结构
      const list = res.data?.records || res.data?.list || res.data || []
      const totalCount = res.data?.total || (Array.isArray(res.data) ? res.data.length : 0)
      setOrders(list)
      setTotal(totalCount)
    } catch (error) {
      console.error('获取订单列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAccept = async (id: number) => {
    try {
      await acceptOrder(id)
      message.success('已接单')
      fetchOrders()
    } catch (error) {
      console.error('接单失败:', error)
    }
  }

  const handleReject = async (id: number) => {
    try {
      const reason = '商家拒绝接单' // 可以后续改为弹窗输入
      await rejectOrder(id, reason)
      message.success('已拒单')
      fetchOrders()
    } catch (error) {
      console.error('拒单失败:', error)
    }
  }

  const handleViewDetail = async (id: number) => {
    try {
      const res = await getOrderDetail(id)
      console.log('订单详情返回数据:', res.data)
      // 确保 items字段存在，如果没有就用orderItems
      const orderDetail = {
        ...res.data,
        items: res.data?.items || res.data?.orderItems || []
      }
      setCurrentOrder(orderDetail)
      setDetailVisible(true)
    } catch (error) {
      console.error('获取订单详情失败:', error)
    }
  }

  const columns = [
    { title: '订单号', dataIndex: 'orderNo', width: 180 },
    { title: '收货人', dataIndex: 'receiverName', width: 100 },
    { title: '金额', dataIndex: 'totalAmount', width: 100, render: (v: number) => `¥${v?.toFixed(2)}` },
    { title: '状态', dataIndex: 'status', width: 100, render: (s: number) => <Tag color={statusMap[s]?.color}>{statusMap[s]?.text}</Tag> },
    { title: '下单时间', dataIndex: 'createTime', width: 180 },
    {
      title: '操作', width: 200, render: (_: unknown, record: Order) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => handleViewDetail(record.id)}>详情</Button>
          {record.status === 1 && (
            <>
              <Button type="link" icon={<CheckOutlined />} onClick={() => handleAccept(record.id)}>接单</Button>
              <Button type="link" danger icon={<CloseOutlined />} onClick={() => handleReject(record.id)}>拒单</Button>
            </>
          )}
        </Space>
      ),
    },
  ]

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: '1', label: '待接单' },
    { key: '3', label: '待配送' },
    { key: '4', label: '配送中' },
    { key: '5', label: '已完成' },
  ]

  return (
    <div>
      <Title level={4}>订单管理</Title>
      <Tabs activeKey={activeTab} onChange={(key) => { setActiveTab(key); setPageNum(1) }} items={tabItems} />
      <Table columns={columns} dataSource={orders} rowKey="id" loading={loading}
        pagination={{ current: pageNum, total, pageSize: 10, onChange: setPageNum, showTotal: (t) => `共 ${t} 条` }} />

      <Modal title="订单详情" open={detailVisible} onCancel={() => setDetailVisible(false)} footer={null} width={600}>
        {currentOrder && (
          <div>
            <p><strong>订单号：</strong>{currentOrder.orderNo}</p>
            <p><strong>状态：</strong><Tag color={statusMap[currentOrder.status]?.color}>{statusMap[currentOrder.status]?.text}</Tag></p>
            <p><strong>收货人：</strong>{currentOrder.receiverName} {currentOrder.receiverPhone}</p>
            <p><strong>地址：</strong>{currentOrder.receiverAddress}</p>
            <p><strong>下单时间：</strong>{currentOrder.createTime}</p>
            <Title level={5}>商品列表</Title>
            {currentOrder.items?.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Text>{item.medicineName}</Text>
                <Text>x{item.quantity}</Text>
                <Text>¥{(item.price * item.quantity).toFixed(2)}</Text>
              </div>
            ))}
            <div style={{ marginTop: 16, textAlign: 'right' }}>
              <Text strong style={{ fontSize: 18 }}>总计：¥{currentOrder.totalAmount?.toFixed(2)}</Text>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default OrderManage
