import { useEffect, useState } from 'react'
import { Table, Input, Button, Space, Tag, message, Typography, Modal, Form, Select, Descriptions } from 'antd'
import { SearchOutlined, CheckOutlined, CloseOutlined, EyeOutlined } from '@ant-design/icons'
import { getMedicineList, auditMedicine, getCategories } from '../../services/api'

const { Title } = Typography
const { TextArea } = Input

interface Category {
  id: number
  name: string
}

interface Medicine {
  id: number
  name: string
  commonName?: string
  specification: string
  price: number
  originalPrice?: number
  stock: number
  merchantName: string
  status: number       // 上架状态：0-下架 1-上架
  auditStatus: number  // 审核状态：0-待审核 1-已通过 2-已拒绝
  isPrescription: number
  categoryId?: number
  manufacturer?: string
  approvalNumber?: string
  image?: string
  efficacy?: string
  dosage?: string
  adverseReactions?: string
  contraindications?: string
  precautions?: string
  riskTips?: string
}

const auditStatusMap: Record<number, { text: string; color: string }> = {
  0: { text: '待审核', color: 'orange' },
  1: { text: '已通过', color: 'green' },
  2: { text: '已拒绝', color: 'red' },
}

const statusMap: Record<number, { text: string; color: string }> = {
  0: { text: '下架', color: 'default' },
  1: { text: '上架', color: 'green' },
}

const MedicineManage = () => {
  const [loading, setLoading] = useState(false)
  const [medicines, setMedicines] = useState<Medicine[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [total, setTotal] = useState(0)
  const [pageNum, setPageNum] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [auditModalVisible, setAuditModalVisible] = useState(false)
  const [detailModalVisible, setDetailModalVisible] = useState(false)
  const [currentMedicine, setCurrentMedicine] = useState<Medicine | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchCategories()
  }, [])

  useEffect(() => { fetchMedicines() }, [pageNum])

  const fetchCategories = async () => {
    try {
      const res = await getCategories()
      setCategories(res.data || [])
    } catch (error) {
      console.error('获取分类失败:', error)
    }
  }

  const fetchMedicines = async () => {
    setLoading(true)
    try {
      const res = await getMedicineList({ pageNum, pageSize: 10, keyword })
      console.log('药品列表返回数据:', res.data)
      // 兼容多种数据结构
      const list = res.data?.records || res.data?.list || res.data || []
      const totalCount = res.data?.total || (Array.isArray(res.data) ? res.data.length : 0)
      setMedicines(list)
      setTotal(totalCount)
    } catch (error) {
      console.error('获取药品列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => { setPageNum(1); fetchMedicines() }

  const openAuditModal = (record: Medicine) => {
    setCurrentMedicine(record)
    form.setFieldsValue({
      categoryId: record.categoryId,
      reason: ''
    })
    setAuditModalVisible(true)
  }

  const openDetailModal = (record: Medicine) => {
    setCurrentMedicine(record)
    setDetailModalVisible(true)
  }

  const handleAudit = async (id: number, status: number) => {
    try {
      const values = await form.validateFields()
      await auditMedicine(id, status, values.reason, values.categoryId)
      message.success(status === 1 ? '已通过' : '已拒绝')
      setAuditModalVisible(false)
      fetchMedicines()
    } catch (error) {
      console.error('审核失败:', error)
    }
  }

  const getCategoryName = (categoryId?: number) => {
    const cat = categories.find(c => c.id === categoryId)
    return cat?.name || '未分类'
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '药品名称', dataIndex: 'name', width: 160 },
    { title: '分类', dataIndex: 'categoryId', width: 100, render: (v: number) => getCategoryName(v) },
    { title: '规格', dataIndex: 'specification', width: 100 },
    { title: '价格', dataIndex: 'price', width: 80, render: (v: number) => `¥${v?.toFixed(2)}` },
    { title: '库存', dataIndex: 'stock', width: 60 },
    { title: '商家', dataIndex: 'merchantName', width: 120 },
    { title: '处方药', dataIndex: 'isPrescription', width: 70, render: (v: number) => v === 1 ? <Tag color="red">是</Tag> : <Tag>否</Tag> },
    { title: '审核状态', dataIndex: 'auditStatus', width: 90, render: (s: number) => <Tag color={auditStatusMap[s]?.color}>{auditStatusMap[s]?.text}</Tag> },
    { title: '上架状态', dataIndex: 'status', width: 80, render: (s: number) => <Tag color={statusMap[s]?.color}>{statusMap[s]?.text}</Tag> },
    { title: '操作', width: 180, render: (_: unknown, record: Medicine) => (
      <Space>
        <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => openDetailModal(record)}>详情</Button>
        {record.auditStatus === 0 ? (
          <Button type="primary" size="small" onClick={() => openAuditModal(record)}>审核</Button>
        ) : (
          <Tag color={auditStatusMap[record.auditStatus]?.color}>{auditStatusMap[record.auditStatus]?.text}</Tag>
        )}
      </Space>
    )},
  ]

  return (
    <div>
      <Title level={4}>药品管理</Title>
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Input placeholder="搜索药品名称" value={keyword} onChange={(e) => setKeyword(e.target.value)} onPressEnter={handleSearch} style={{ width: 200 }} />
          <Button icon={<SearchOutlined />} onClick={handleSearch}>搜索</Button>
        </Space>
      </div>
      <Table columns={columns} dataSource={medicines} rowKey="id" loading={loading}
        pagination={{ current: pageNum, total, pageSize: 10, onChange: setPageNum, showTotal: (t) => `共 ${t} 条` }} />

      {/* 药品详情弹窗 */}
      <Modal
        title="药品详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={<Button onClick={() => setDetailModalVisible(false)}>关闭</Button>}
        width={700}
      >
        {currentMedicine && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="药品ID">{currentMedicine.id}</Descriptions.Item>
            <Descriptions.Item label="审核状态">
              <Tag color={auditStatusMap[currentMedicine.auditStatus]?.color}>
                {auditStatusMap[currentMedicine.auditStatus]?.text}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="药品名称">{currentMedicine.name}</Descriptions.Item>
            <Descriptions.Item label="通用名">{currentMedicine.commonName || '-'}</Descriptions.Item>
            <Descriptions.Item label="分类">{getCategoryName(currentMedicine.categoryId)}</Descriptions.Item>
            <Descriptions.Item label="规格">{currentMedicine.specification}</Descriptions.Item>
            <Descriptions.Item label="售价">¥{currentMedicine.price?.toFixed(2)}</Descriptions.Item>
            <Descriptions.Item label="原价">{currentMedicine.originalPrice ? `¥${currentMedicine.originalPrice.toFixed(2)}` : '-'}</Descriptions.Item>
            <Descriptions.Item label="库存">{currentMedicine.stock}</Descriptions.Item>
            <Descriptions.Item label="商家">{currentMedicine.merchantName}</Descriptions.Item>
            <Descriptions.Item label="生产厂家" span={2}>{currentMedicine.manufacturer || '-'}</Descriptions.Item>
            <Descriptions.Item label="批准文号" span={2}>{currentMedicine.approvalNumber || '-'}</Descriptions.Item>
            <Descriptions.Item label="处方药">{currentMedicine.isPrescription === 1 ? '是' : '否'}</Descriptions.Item>
            <Descriptions.Item label="上架状态">
              <Tag color={statusMap[currentMedicine.status]?.color}>{statusMap[currentMedicine.status]?.text}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="功效说明" span={2}>{currentMedicine.efficacy || '-'}</Descriptions.Item>
            <Descriptions.Item label="用法用量" span={2}>{currentMedicine.dosage || '-'}</Descriptions.Item>
            <Descriptions.Item label="不良反应" span={2}>{currentMedicine.adverseReactions || '-'}</Descriptions.Item>
            <Descriptions.Item label="禁忌" span={2}>{currentMedicine.contraindications || '-'}</Descriptions.Item>
            <Descriptions.Item label="注意事项" span={2}>{currentMedicine.precautions || '-'}</Descriptions.Item>
            <Descriptions.Item label="用药风险提示" span={2}>{currentMedicine.riskTips || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 审核弹窗 */}
      <Modal
        title="药品审核"
        open={auditModalVisible}
        onCancel={() => setAuditModalVisible(false)}
        footer={null}
        width={600}
      >
        {currentMedicine && (
          <>
            <Descriptions bordered column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="药品名称">{currentMedicine.name}</Descriptions.Item>
              <Descriptions.Item label="规格">{currentMedicine.specification}</Descriptions.Item>
              <Descriptions.Item label="价格">¥{currentMedicine.price?.toFixed(2)}</Descriptions.Item>
              <Descriptions.Item label="库存">{currentMedicine.stock}</Descriptions.Item>
              <Descriptions.Item label="商家">{currentMedicine.merchantName}</Descriptions.Item>
              <Descriptions.Item label="处方药">{currentMedicine.isPrescription === 1 ? '是' : '否'}</Descriptions.Item>
              <Descriptions.Item label="生产厂家" span={2}>{currentMedicine.manufacturer || '-'}</Descriptions.Item>
            </Descriptions>
            
            <Form form={form} layout="vertical">
              <Form.Item name="categoryId" label="药品分类（可修改）">
                <Select placeholder="请选择药品分类">
                  {categories.map(cat => (
                    <Select.Option key={cat.id} value={cat.id}>{cat.name}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item name="reason" label="审核意见（拒绝时必填）">
                <TextArea rows={3} placeholder="请输入审核意见（拒绝时必填）" />
              </Form.Item>
            </Form>
            
            <div style={{ textAlign: 'right', marginTop: 16 }}>
              <Space>
                <Button onClick={() => setAuditModalVisible(false)}>取消</Button>
                <Button danger icon={<CloseOutlined />} onClick={() => handleAudit(currentMedicine.id, 2)}>拒绝</Button>
                <Button type="primary" icon={<CheckOutlined />} onClick={() => handleAudit(currentMedicine.id, 1)}>通过</Button>
              </Space>
            </div>
          </>
        )}
      </Modal>
    </div>
  )
}

export default MedicineManage
