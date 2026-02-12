import { useState, useEffect } from 'react'
import { Table, Card, Button, Space, Tag, Modal, Input, message, Popconfirm, Descriptions } from 'antd'
import { SearchOutlined, CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import request from '../../utils/request'

interface Rider {
  id: number
  userId: number
  realName: string
  phone: string
  idCard: string
  status: number
  auditStatus: number
  todayOrders: number
  totalOrders: number
  todayIncome: number
  totalIncome: number
  createTime: string
}

const RiderManage = () => {
  const [riders, setRiders] = useState<Rider[]>([])
  const [loading, setLoading] = useState(false)
  const [keyword, setKeyword] = useState('')
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [detailVisible, setDetailVisible] = useState(false)
  const [currentRider, setCurrentRider] = useState<Rider | null>(null)

  const fetchRiders = async (page = 1) => {
    setLoading(true)
    try {
      const res = await request.get('/admin/riders', {
        params: { page, size: pagination.pageSize, keyword }
      })
      const data = res.data?.records || res.data?.data?.records || []
      const total = res.data?.total || res.data?.data?.total || 0
      setRiders(data)
      setPagination(prev => ({ ...prev, current: page, total }))
    } catch (error) {
      console.error('获取骑手列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRiders()
  }, [])

  const handleSearch = () => {
    fetchRiders(1)
  }

  const handleAudit = async (riderId: number, status: number) => {
    try {
      await request.put(`/admin/riders/${riderId}/audit`, { status })
      message.success(status === 1 ? '审核通过' : '已拒绝')
      fetchRiders(pagination.current)
    } catch (error) {
      message.error('操作失败')
    }
  }

  const handleToggleStatus = async (riderId: number, currentStatus: number) => {
    try {
      const newStatus = currentStatus === 1 ? 0 : 1
      await request.put(`/admin/riders/${riderId}/status`, { status: newStatus })
      message.success(newStatus === 1 ? '已启用' : '已禁用')
      fetchRiders(pagination.current)
    } catch (error) {
      message.error('操作失败')
    }
  }

  const showDetail = (rider: Rider) => {
    setCurrentRider(rider)
    setDetailVisible(true)
  }

  const columns: ColumnsType<Rider> = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '姓名', dataIndex: 'realName', width: 100 },
    { title: '手机号', dataIndex: 'phone', width: 120 },
    { title: '身份证号', dataIndex: 'idCard', width: 180 },
    {
      title: '审核状态', dataIndex: 'auditStatus', width: 100,
      render: (status: number) => {
        const map: Record<number, { color: string; text: string }> = {
          0: { color: 'orange', text: '待审核' },
          1: { color: 'green', text: '已通过' },
          2: { color: 'red', text: '已拒绝' }
        }
        return <Tag color={map[status]?.color}>{map[status]?.text}</Tag>
      }
    },
    {
      title: '账号状态', dataIndex: 'status', width: 100,
      render: (status: number) => (
        <Tag color={status === 1 ? 'green' : 'default'}>
          {status === 1 ? '正常' : '禁用'}
        </Tag>
      )
    },
    { title: '今日订单', dataIndex: 'todayOrders', width: 90 },
    { title: '累计订单', dataIndex: 'totalOrders', width: 90 },
    {
      title: '操作', width: 200, fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} onClick={() => showDetail(record)}>详情</Button>
          {record.auditStatus === 0 && (
            <>
              <Popconfirm title="确定通过审核？" onConfirm={() => handleAudit(record.id, 1)}>
                <Button size="small" type="primary" icon={<CheckOutlined />}>通过</Button>
              </Popconfirm>
              <Popconfirm title="确定拒绝？" onConfirm={() => handleAudit(record.id, 2)}>
                <Button size="small" danger icon={<CloseOutlined />}>拒绝</Button>
              </Popconfirm>
            </>
          )}
          {record.auditStatus === 1 && (
            <Popconfirm
              title={`确定${record.status === 1 ? '禁用' : '启用'}该骑手？`}
              onConfirm={() => handleToggleStatus(record.id, record.status)}
            >
              <Button size="small" danger={record.status === 1}>
                {record.status === 1 ? '禁用' : '启用'}
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: 24 }}>
      <Card title="骑手管理">
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="搜索姓名/手机号"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 200 }}
            allowClear
          />
          <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch}>搜索</Button>
        </Space>

        <Table
          columns={columns}
          dataSource={riders}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1100 }}
          pagination={{
            ...pagination,
            showSizeChanger: false,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page) => fetchRiders(page)
          }}
        />
      </Card>

      <Modal
        title="骑手详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={600}
      >
        {currentRider && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="ID">{currentRider.id}</Descriptions.Item>
            <Descriptions.Item label="用户ID">{currentRider.userId}</Descriptions.Item>
            <Descriptions.Item label="姓名">{currentRider.realName}</Descriptions.Item>
            <Descriptions.Item label="手机号">{currentRider.phone}</Descriptions.Item>
            <Descriptions.Item label="身份证号" span={2}>{currentRider.idCard}</Descriptions.Item>
            <Descriptions.Item label="审核状态">
              <Tag color={currentRider.auditStatus === 1 ? 'green' : currentRider.auditStatus === 0 ? 'orange' : 'red'}>
                {currentRider.auditStatus === 0 ? '待审核' : currentRider.auditStatus === 1 ? '已通过' : '已拒绝'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="账号状态">
              <Tag color={currentRider.status === 1 ? 'green' : 'default'}>
                {currentRider.status === 1 ? '正常' : '禁用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="今日订单">{currentRider.todayOrders || 0}</Descriptions.Item>
            <Descriptions.Item label="累计订单">{currentRider.totalOrders || 0}</Descriptions.Item>
            <Descriptions.Item label="今日收入">¥{currentRider.todayIncome || 0}</Descriptions.Item>
            <Descriptions.Item label="累计收入">¥{currentRider.totalIncome || 0}</Descriptions.Item>
            <Descriptions.Item label="注册时间" span={2}>{currentRider.createTime}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default RiderManage
