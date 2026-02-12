import { useEffect, useState } from 'react'
import { Table, Button, Input, Space, Tag, Modal, Form, InputNumber, Switch, message, Popconfirm, Typography, Tooltip, Select, Tabs, Row, Col, Upload } from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined, UploadOutlined } from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd'
import { getMedicineList, addMedicine, updateMedicine, deleteMedicine, updateMedicineStatus, getMedicineCategories } from '../../services/api'

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
  manufacturer?: string
  approvalNumber?: string
  price: number
  originalPrice?: number
  stock: number
  image?: string
  images?: string
  status: number
  isPrescription: number
  auditStatus: number  // 0-待审核 1-已通过 2-已拒绝
  auditRemark?: string  // 审核拒绝原因
  efficacy?: string
  dosage?: string
  adverseReactions?: string
  contraindications?: string
  precautions?: string
  riskTips?: string
  categoryId?: number
}

const MedicineManage = () => {
  const [loading, setLoading] = useState(false)
  const [medicines, setMedicines] = useState<Medicine[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [total, setTotal] = useState(0)
  const [pageNum, setPageNum] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [imageUrl, setImageUrl] = useState<string>('')
  const [imageFileList, setImageFileList] = useState<UploadFile[]>([])
  const [imagesFileList, setImagesFileList] = useState<UploadFile[]>([])

  useEffect(() => {
    fetchCategories()
  }, [])

  useEffect(() => {
    fetchMedicines()
  }, [pageNum])

  const fetchCategories = async () => {
    try {
      const res = await getMedicineCategories()
      setCategories(res.data || [])
    } catch (error) {
      console.error('获取分类失败:', error)
    }
  }

  const fetchMedicines = async () => {
    setLoading(true)
    try {
      const res = await getMedicineList({ pageNum, pageSize: 10, keyword })
      setMedicines(res.data?.records || [])
      setTotal(res.data?.total || 0)
    } catch (error) {
      console.error('获取药品列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPageNum(1)
    fetchMedicines()
  }

  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    setImageUrl('')
    setImageFileList([])
    setImagesFileList([])
    setModalVisible(true)
  }

  const handleEdit = (record: Medicine) => {
    setEditingId(record.id)
    // 映射字段：isPrescription需要转为boolean
    form.setFieldsValue({
      ...record,
      isPrescription: record.isPrescription === 1
    })
    // 设置图片文件列表
    if (record.image) {
      setImageUrl(record.image)
      setImageFileList([{
        uid: '-1',
        name: 'image.png',
        status: 'done',
        url: record.image,
      }])
    } else {
      setImageUrl('')
      setImageFileList([])
    }
    // 设置多图片文件列表
    if (record.images) {
      const urls = record.images.split(',').filter(Boolean)
      setImagesFileList(urls.map((url, index) => ({
        uid: String(-index - 2),
        name: `image${index + 1}.png`,
        status: 'done' as const,
        url,
      })))
    } else {
      setImagesFileList([])
    }
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteMedicine(id)
      message.success('删除成功')
      fetchMedicines()
    } catch (error: any) {
      message.error(error.response?.data?.message || '删除失败')
    }
  }

  const handleStatusChange = async (id: number, checked: boolean) => {
    try {
      await updateMedicineStatus(id, checked ? 1 : 0)
      message.success('状态更新成功')
      fetchMedicines()
    } catch (error: any) {
      message.error(error.response?.data?.message || '状态更新失败')
    }
  }

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields()
      // 添加图片URL
      values.image = imageUrl
      // 添加多图片URL
      values.images = imagesFileList.map(f => f.url || f.response?.data?.url).filter(Boolean).join(',')
      if (editingId) {
        await updateMedicine(editingId, values)
        message.success('更新成功')
      } else {
        await addMedicine(values)
        message.success('添加成功')
      }
      setModalVisible(false)
      fetchMedicines()
    } catch (error) {
      console.error('保存失败:', error)
    }
  }

  // 主图上传配置
  const imageUploadProps: UploadProps = {
    name: 'file',
    action: '/api/upload/image',
    listType: 'picture-card',
    maxCount: 1,
    fileList: imageFileList,
    beforeUpload: (file) => {
      const isImage = file.type.startsWith('image/')
      if (!isImage) {
        message.error('只能上传图片文件!')
        return false
      }
      const isLt5M = file.size / 1024 / 1024 < 5
      if (!isLt5M) {
        message.error('图片大小不能超过5MB!')
        return false
      }
      return true
    },
    onChange: (info) => {
      setImageFileList(info.fileList)
      if (info.file.status === 'done') {
        const url = info.file.response?.data?.url
        if (url) {
          setImageUrl(url)
          message.success('主图上传成功')
        }
      } else if (info.file.status === 'error') {
        message.error('主图上传失败')
      }
    },
    onRemove: () => {
      setImageUrl('')
    },
  }

  // 多图上传配置
  const imagesUploadProps: UploadProps = {
    name: 'file',
    action: '/api/upload/image',
    listType: 'picture-card',
    multiple: true,
    maxCount: 5,
    fileList: imagesFileList,
    beforeUpload: (file) => {
      const isImage = file.type.startsWith('image/')
      if (!isImage) {
        message.error('只能上传图片文件!')
        return false
      }
      const isLt5M = file.size / 1024 / 1024 < 5
      if (!isLt5M) {
        message.error('图片大小不能超过5MB!')
        return false
      }
      return true
    },
    onChange: (info) => {
      setImagesFileList(info.fileList)
      if (info.file.status === 'done') {
        message.success('图片上传成功')
      } else if (info.file.status === 'error') {
        message.error('图片上传失败')
      }
    },
  }

  const auditStatusMap: Record<number, { text: string; color: string }> = {
    0: { text: '待审核', color: 'orange' },
    1: { text: '已通过', color: 'green' },
    2: { text: '已拒绝', color: 'red' },
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '药品名称', dataIndex: 'name', width: 180 },
    { title: '规格', dataIndex: 'specification', width: 100 },
    { title: '价格', dataIndex: 'price', width: 80, render: (v: number) => `¥${v?.toFixed(2)}` },
    { title: '库存', dataIndex: 'stock', width: 60 },
    { title: '处方药', dataIndex: 'isPrescription', width: 70, render: (v: number) => v === 1 ? <Tag color="red">是</Tag> : <Tag>否</Tag> },
    { title: '审核状态', dataIndex: 'auditStatus', width: 100, render: (v: number, record: Medicine) => {
      const status = auditStatusMap[v] || auditStatusMap[0]
      // 如果被拒绝且有拒绝原因，显示 Tooltip
      if (v === 2 && record.auditRemark) {
        return (
          <Tooltip title={`拒绝原因：${record.auditRemark}`}>
            <Tag color={status.color} style={{ cursor: 'pointer' }}>
              {status.text} <ExclamationCircleOutlined />
            </Tag>
          </Tooltip>
        )
      }
      return <Tag color={status.color}>{status.text}</Tag>
    }},
    { title: '上架状态', dataIndex: 'status', width: 100, render: (v: number, record: Medicine) => {
      // 只有审核通过的药品才能操作上下架
      if (record.auditStatus !== 1) {
        return <Tag>待审核</Tag>
      }
      return <Switch checked={v === 1} onChange={(checked) => handleStatusChange(record.id, checked)} checkedChildren="上架" unCheckedChildren="下架" />
    }},
    {
      title: '操作', width: 150, render: (_: unknown, record: Medicine) => (
        <Space>
          {record.auditStatus === 2 ? (
            <Tooltip title="编辑后将重新提交审核">
              <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>重新提交</Button>
            </Tooltip>
          ) : (
            <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>编辑</Button>
          )}
          {record.status === 1 ? (
            <Button type="link" danger disabled>删除</Button>
          ) : (
            <Popconfirm title="确定删除吗？" onConfirm={() => handleDelete(record.id)}>
              <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Title level={4}>药品管理</Title>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Input placeholder="搜索药品名称" value={keyword} onChange={(e) => setKeyword(e.target.value)} onPressEnter={handleSearch} style={{ width: 200 }} />
          <Button icon={<SearchOutlined />} onClick={handleSearch}>搜索</Button>
        </Space>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>添加药品</Button>
      </div>

      <Table columns={columns} dataSource={medicines} rowKey="id" loading={loading}
        pagination={{ current: pageNum, total, pageSize: 10, onChange: setPageNum, showTotal: (t) => `共 ${t} 条` }} />

      <Modal 
        title={editingId ? '编辑药品' : '添加药品'} 
        open={modalVisible} 
        onOk={handleModalOk} 
        onCancel={() => setModalVisible(false)} 
        width={800}
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
      >
        <Form form={form} layout="vertical">
          <Tabs
            defaultActiveKey="basic"
            items={[
              {
                key: 'basic',
                label: '基本信息',
                children: (
                  <>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item name="name" label="药品名称" rules={[{ required: true, message: '请输入药品名称' }]}>
                          <Input placeholder="请输入药品名称" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="commonName" label="通用名">
                          <Input placeholder="请输入通用名" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item name="categoryId" label="药品分类" rules={[{ required: true, message: '请选择药品分类' }]}>
                          <Select placeholder="请选择药品分类">
                            {categories.map(cat => (
                              <Select.Option key={cat.id} value={cat.id}>{cat.name}</Select.Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="specification" label="规格" rules={[{ required: true, message: '请输入规格' }]}>
                          <Input placeholder="如: 0.3g*20粒" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item name="manufacturer" label="生产厂家">
                          <Input placeholder="请输入生产厂家" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="approvalNumber" label="批准文号">
                          <Input placeholder="请输入批准文号" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={16}>
                      <Col span={8}>
                        <Form.Item name="price" label="售价" rules={[{ required: true, message: '请输入价格' }]}>
                          <InputNumber min={0} precision={2} style={{ width: '100%' }} placeholder="售价" addonBefore="¥" />
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item name="originalPrice" label="原价">
                          <InputNumber min={0} precision={2} style={{ width: '100%' }} placeholder="原价（可选）" addonBefore="¥" />
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item name="stock" label="库存" rules={[{ required: true, message: '请输入库存' }]}>
                          <InputNumber min={0} style={{ width: '100%' }} placeholder="库存数量" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item label="药品主图">
                          <Upload {...imageUploadProps}>
                            {imageFileList.length < 1 && (
                              <div>
                                <UploadOutlined />
                                <div style={{ marginTop: 8 }}>上传主图</div>
                              </div>
                            )}
                          </Upload>
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="isPrescription" label="是否处方药" valuePropName="checked" initialValue={false}>
                          <Switch checkedChildren="处方药" unCheckedChildren="非处方" />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Form.Item label="药品详情图（最多5张）">
                      <Upload {...imagesUploadProps}>
                        {imagesFileList.length < 5 && (
                          <div>
                            <PlusOutlined />
                            <div style={{ marginTop: 8 }}>上传图片</div>
                          </div>
                        )}
                      </Upload>
                    </Form.Item>
                  </>
                ),
              },
              {
                key: 'detail',
                label: '药品说明',
                children: (
                  <>
                    <Form.Item name="efficacy" label="功效说明">
                      <TextArea rows={3} placeholder="请输入功效说明/适应症" />
                    </Form.Item>
                    <Form.Item name="dosage" label="用法用量">
                      <TextArea rows={3} placeholder="请输入用法用量" />
                    </Form.Item>
                    <Form.Item name="adverseReactions" label="不良反应">
                      <TextArea rows={3} placeholder="请输入不良反应" />
                    </Form.Item>
                    <Form.Item name="contraindications" label="禁忌">
                      <TextArea rows={3} placeholder="请输入禁忌事项" />
                    </Form.Item>
                    <Form.Item name="precautions" label="注意事项">
                      <TextArea rows={3} placeholder="请输入注意事项" />
                    </Form.Item>
                    <Form.Item name="riskTips" label="用药风险提示">
                      <TextArea rows={3} placeholder="请输入用药风险提示" />
                    </Form.Item>
                  </>
                ),
              },
            ]}
          />
        </Form>
      </Modal>
    </div>
  )
}

export default MedicineManage
