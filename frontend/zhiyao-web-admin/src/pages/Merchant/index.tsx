import { useEffect, useState } from 'react'
import { Table, Tabs, Tag, Button, Space, message, Typography, Modal, Input, Descriptions, Image } from 'antd'
import { CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons'
import { getMerchantList, auditMerchant } from '../../services/api'
import request from '../../utils/request'

const { Title, Text } = Typography
const { TextArea } = Input

interface Merchant {
  id: number
  name: string
  phone: string
  address: string
  status: number
  createTime: string
  businessHours?: string
  logo?: string
  deliveryFee?: number
  minOrderAmount?: number
  deliveryRange?: number
  rating?: number
  auditRemark?: string
  businessLicenseImage?: string
  drugLicenseImage?: string
}

const statusMap: Record<number, { text: string; color: string }> = {
  0: { text: '待审核', color: 'orange' },
  1: { text: '已通过', color: 'green' },
  2: { text: '已拒绝', color: 'red' },
}

const MerchantManage = () => {
  const [loading, setLoading] = useState(false)
  const [merchants, setMerchants] = useState<Merchant[]>([])
  const [total, setTotal] = useState(0)
  const [pageNum, setPageNum] = useState(1)
  const [activeTab, setActiveTab] = useState('all')
  const [rejectVisible, setRejectVisible] = useState(false)
  const [rejectId, setRejectId] = useState<number | null>(null)
  const [rejectReason, setRejectReason] = useState('')
  const [detailVisible, setDetailVisible] = useState(false)
  const [currentMerchant, setCurrentMerchant] = useState<Merchant | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  useEffect(() => { fetchMerchants() }, [pageNum, activeTab])

  const fetchMerchants = async () => {
    setLoading(true)
    try {
      const params: { pageNum: number; pageSize: number; status?: number } = { pageNum, pageSize: 10 }
      if (activeTab !== 'all') params.status = Number(activeTab)
      const res = await getMerchantList(params)
      console.log('商家列表返回数据:', res.data)
      // 兼容多种数据结构
      const list = res.data?.records || res.data?.list || res.data || []
      const totalCount = res.data?.total || (Array.isArray(res.data) ? res.data.length : 0)
      setMerchants(list)
      setTotal(totalCount)
    } catch (error) {
      console.error('获取商家列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (id: number) => {
    try {
      await auditMerchant(id, 1)
      message.success('审核通过')
      fetchMerchants()
    } catch (error) {
      console.error('审核失败:', error)
    }
  }

  const handleReject = async () => {
    if (!rejectId) return
    try {
      await auditMerchant(rejectId, 2, rejectReason)
      message.success('已拒绝')
      setRejectVisible(false)
      setRejectReason('')
      fetchMerchants()
    } catch (error) {
      console.error('拒绝失败:', error)
    }
  }

  const handleViewDetail = async (record: Merchant) => {
    setDetailVisible(true)
    setDetailLoading(true)
    try {
      // 直接使用列表中的数据，如果需要更详细的信息可以调用详情接口
      setCurrentMerchant(record)
    } catch (error) {
      console.error('获取商家详情失败:', error)
      message.error('获取商家详情失败')
    } finally {
      setDetailLoading(false)
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '商家名称', dataIndex: 'name', width: 150 },
    { title: '联系电话', dataIndex: 'phone', width: 130 },
    { title: '地址', dataIndex: 'address', width: 200 },
    { title: '状态', dataIndex: 'status', width: 100, render: (s: number) => <Tag color={statusMap[s]?.color}>{statusMap[s]?.text}</Tag> },
    { title: '申请时间', dataIndex: 'createTime', width: 180 },
    { title: '操作', width: 180, render: (_: unknown, record: Merchant) => (
      <Space>
        {record.status === 0 && (
          <>
            <Button type="link" icon={<CheckOutlined />} onClick={() => handleApprove(record.id)}>通过</Button>
            <Button type="link" danger icon={<CloseOutlined />} onClick={() => { setRejectId(record.id); setRejectVisible(true) }}>拒绝</Button>
          </>
        )}
        <Button type="link" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)}>详情</Button>
      </Space>
    )},
  ]

  const tabItems = [
    { key: 'all', label: '全部' },
    { key: '0', label: '待审核' },
    { key: '1', label: '已通过' },
    { key: '2', label: '已拒绝' },
  ]

  return (
    <div>
      <Title level={4}>商家管理</Title>
      <Tabs activeKey={activeTab} onChange={(k) => { setActiveTab(k); setPageNum(1) }} items={tabItems} />
      <Table columns={columns} dataSource={merchants} rowKey="id" loading={loading}
        pagination={{ current: pageNum, total, pageSize: 10, onChange: setPageNum, showTotal: (t) => `共 ${t} 条` }} />

      <Modal title="拒绝原因" open={rejectVisible} onOk={handleReject} onCancel={() => setRejectVisible(false)}>
        <TextArea rows={4} value={rejectReason} onChange={(e) => setRejectReason(e.target.value)} placeholder="请输入拒绝原因" />
      </Modal>

      <Modal 
        title="商家详情" 
        open={detailVisible} 
        onCancel={() => setDetailVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailVisible(false)}>关闭</Button>
        ]}
        width={700}
      >
        {currentMerchant && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="商家ID">{currentMerchant.id}</Descriptions.Item>
            <Descriptions.Item label="商家名称">{currentMerchant.name}</Descriptions.Item>
            <Descriptions.Item label="联系电话">{currentMerchant.phone}</Descriptions.Item>
            <Descriptions.Item label="审核状态">
              <Tag color={statusMap[currentMerchant.status]?.color}>
                {statusMap[currentMerchant.status]?.text}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="店铺地址" span={2}>{currentMerchant.address}</Descriptions.Item>
            <Descriptions.Item label="营业时间">{currentMerchant.businessHours || '-'}</Descriptions.Item>
            <Descriptions.Item label="申请时间">{currentMerchant.createTime}</Descriptions.Item>
            <Descriptions.Item label="营业执照" span={2}>
              {currentMerchant.businessLicenseImage ? (
                <Image 
                  src={currentMerchant.businessLicenseImage} 
                  width={150} 
                  placeholder={true}
                  fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgesW8AIWDDh6AAAAVmVYSWZNTQAqAAAACAABh2kABAAAAAEAAAAaAAAAAAADkoYABwAAABIAAABEoAIABAAAAAEAAADCoAMABAAAAAEAAADDAAAAAEFTQ0lJAAAAU2NyZWVuc2hvdL/9R9AAAAAdaVRYdFNvZnR3YXJlAAAAAABTY3JlZW5zaG90IFRvb2z/RNAaAAADNElEQVR4Ae3VsQ0AIBDA0Oz/NJmBARBuACG//AAAAKq1vvl19QEAAAD//wMA"
                />
              ) : <Text type="secondary">未上传</Text>}
            </Descriptions.Item>
            <Descriptions.Item label="药品经营许可证" span={2}>
              {currentMerchant.drugLicenseImage ? (
                <Image 
                  src={currentMerchant.drugLicenseImage} 
                  width={150} 
                  placeholder={true}
                  fallback="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAMIAAADDCAYAAADQvc6UAAABRWlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGASSSwoyGFhYGDIzSspCnJ3UoiIjFJgf8LAwSDCIMogwMCcmFxc4BgQ4ANUwgCjUcG3awyMIPqyLsis7PPOq3QdDFcvjV3jOD1boQVTPQrgSkktTgbSf4A4LbmgqISBgTEFyFYuLykAsTuAbJEioKOA7DkgdjqEvQHEToKwj4DVhAQ5A9k3gGyB5IxEoBmML4BsnSQk8XQkNtReEOBxcfXxUQg1Mjc0dyHgXNJBSWpFCYh2zi+oLMpMzyhRcASGUqqCZ16yno6CkYGRAQMDKMwhqj/fAIcloxgHQqxAjIHBEugw5sUIsSQpBobtQPdLciLEVJYzMPBHMDBsayhILEqEO4DxG0txmrERhM29nYGBddr//5/DGRjYNRkY/l7////39v///y4Dmn+LgeHW8AIWDDh6AAAAVmVYSWZNTQAqAAAACAABh2kABAAAAAEAAAAaAAAAAAADkoYABwAAABIAAABEoAIABAAAAAEAAADCoAMABAAAAAEAAADDAAAAAEFTQ0lJAAAAU2NyZWVuc2hvdL/9R9AAAAAdaVRYdFNvZnR3YXJlAAAAAABTY3JlZW5zaG90IFRvb2z/RNAaAAADNElEQVR4Ae3VsQ0AIBDA0Oz/NJmBARBuACG//AAAAKq1vvl19QEAAAD//wMA"
                />
              ) : <Text type="secondary">未上传</Text>}
            </Descriptions.Item>
            {currentMerchant.status === 2 && currentMerchant.auditRemark && (
              <Descriptions.Item label="拒绝原因" span={2}>
                <Text type="danger">{currentMerchant.auditRemark}</Text>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default MerchantManage
