import { useState, useEffect } from 'react'
import { List, Button, Modal, Form, Input, Radio, message, Empty, Card, Tag, Space, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, EnvironmentOutlined } from '@ant-design/icons'
import { getAddressList, addAddress, updateAddress, deleteAddress, setDefaultAddress } from '../../services/user'
import './index.css'

interface Address {
  id: number
  name: string
  phone: string
  province: string
  city: string
  district: string
  detail: string
  isDefault: boolean
}

const AddressPage = () => {
  const [addresses, setAddresses] = useState<Address[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingAddress, setEditingAddress] = useState<Address | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchAddresses()
  }, [])

  const fetchAddresses = async () => {
    try {
      setLoading(true)
      const res: any = await getAddressList()
      setAddresses(res.data || res || [])
    } catch (error) {
      console.error('获取地址失败', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingAddress(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (address: Address) => {
    setEditingAddress(address)
    form.setFieldsValue(address)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteAddress(id)
      message.success('删除成功')
      fetchAddresses()
    } catch (error: any) {
      message.error(error?.message || '删除失败')
    }
  }

  const handleSetDefault = async (id: number) => {
    try {
      await setDefaultAddress(id)
      message.success('设置成功')
      fetchAddresses()
    } catch (error: any) {
      message.error(error?.message || '设置失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      
      if (editingAddress) {
        await updateAddress(editingAddress.id, values)
        message.success('修改成功')
      } else {
        await addAddress(values)
        message.success('添加成功')
      }
      setModalVisible(false)
      fetchAddresses()
    } catch (error: any) {
      if (error?.errorFields) {
        // 表单验证失败
        return
      }
      message.error(error?.message || '操作失败')
    }
  }

  return (
    <div className="address-page">
      <div className="page-header">
        <h2>收货地址管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          新增地址
        </Button>
      </div>

      {addresses.length === 0 ? (
        <Empty description="暂无收货地址" style={{ marginTop: 100 }}>
          <Button type="primary" onClick={handleAdd}>添加地址</Button>
        </Empty>
      ) : (
        <List
          loading={loading}
          dataSource={addresses}
          renderItem={(item) => (
            <Card className="address-card" key={item.id}>
              <div className="address-content">
                <div className="address-info">
                  <div className="address-header">
                    <span className="name">{item.name}</span>
                    <span className="phone">{item.phone}</span>
                    {item.isDefault && <Tag color="orange">默认</Tag>}
                  </div>
                  <div className="address-detail">
                    <EnvironmentOutlined style={{ marginRight: 8 }} />
                    {item.province} {item.city} {item.district} {item.detail}
                  </div>
                </div>
                <div className="address-actions">
                  <Space>
                    {!item.isDefault && (
                      <Button size="small" onClick={() => handleSetDefault(item.id)}>
                        设为默认
                      </Button>
                    )}
                    <Button 
                      size="small" 
                      icon={<EditOutlined />}
                      onClick={() => handleEdit(item)}
                    >
                      编辑
                    </Button>
                    <Popconfirm
                      title="确定删除该地址吗？"
                      onConfirm={() => handleDelete(item.id)}
                    >
                      <Button size="small" danger icon={<DeleteOutlined />}>
                        删除
                      </Button>
                    </Popconfirm>
                  </Space>
                </div>
              </div>
            </Card>
          )}
        />
      )}

      <Modal
        title={editingAddress ? '编辑地址' : '新增地址'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={500}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="收货人"
            rules={[{ required: true, message: '请输入收货人姓名' }]}
          >
            <Input placeholder="请输入收货人姓名" />
          </Form.Item>
          <Form.Item
            name="phone"
            label="手机号"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' }
            ]}
          >
            <Input placeholder="请输入手机号" maxLength={11} />
          </Form.Item>
          <Form.Item
            name="province"
            label="省份"
            rules={[{ required: true, message: '请输入省份' }]}
          >
            <Input placeholder="请输入省份" />
          </Form.Item>
          <Form.Item
            name="city"
            label="城市"
            rules={[{ required: true, message: '请输入城市' }]}
          >
            <Input placeholder="请输入城市" />
          </Form.Item>
          <Form.Item
            name="district"
            label="区/县"
            rules={[{ required: true, message: '请输入区/县' }]}
          >
            <Input placeholder="请输入区/县" />
          </Form.Item>
          <Form.Item
            name="detail"
            label="详细地址"
            rules={[{ required: true, message: '请输入详细地址' }]}
          >
            <Input.TextArea placeholder="请输入详细地址（街道、门牌号等）" rows={3} />
          </Form.Item>
          <Form.Item
            name="isDefault"
            label="设为默认"
          >
            <Radio.Group>
              <Radio value={true}>是</Radio>
              <Radio value={false}>否</Radio>
            </Radio.Group>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default AddressPage
