import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Form, Input, Button, message, Tabs, Row, Col, Avatar, Upload, Typography, Divider, TimePicker } from 'antd'
import { ShopOutlined, LockOutlined, SettingOutlined, UploadOutlined, PlusOutlined } from '@ant-design/icons'
import type { UploadProps, UploadFile } from 'antd'
import useMerchantStore from '../../stores/merchantStore'
import request from '../../utils/request'
import dayjs from 'dayjs'

const { Title, Text } = Typography

// 店铺信息设置
const ShopSettings = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [logoUrl, setLogoUrl] = useState('')
  const merchantInfo = useMerchantStore((state) => state.merchantInfo)

  useEffect(() => {
    fetchShopInfo()
  }, [])

  const fetchShopInfo = async () => {
    try {
      const res = await request.get('/merchant/info')
      if (res.data) {
        const data = res.data
        setLogoUrl(data.logo || '')
        // 解析营业时间
        let openTime: dayjs.Dayjs | undefined = undefined
        let closeTime: dayjs.Dayjs | undefined = undefined
        if (data.openTime && data.closeTime) {
          openTime = dayjs(data.openTime, 'HH:mm')
          closeTime = dayjs(data.closeTime, 'HH:mm')
        }
        form.setFieldsValue({
          name: data.name || '',
          phone: data.phone || '',
          address: data.address || '',
          description: data.description || '',
          businessHours: openTime && closeTime ? [openTime, closeTime] : undefined,
        })
      }
    } catch (error) {
      console.error('获取店铺信息失败:', error)
    }
  }

  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/upload/merchant',
    showUploadList: false,
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
      if (info.file.status === 'done') {
        const url = info.file.response?.data?.url
        if (url) {
          setLogoUrl(url)
          message.success('Logo上传成功')
        }
      } else if (info.file.status === 'error') {
        message.error('Logo上传失败')
      }
    },
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      // 处理营业时间
      let openTime = ''
      let closeTime = ''
      if (values.businessHours && values.businessHours[0] && values.businessHours[1]) {
        openTime = values.businessHours[0].format('HH:mm')
        closeTime = values.businessHours[1].format('HH:mm')
      }
      
      // 构建提交数据，排除businessHours数组字段
      const submitData = {
        name: values.name,
        phone: values.phone,
        address: values.address,
        description: values.description,
        logo: logoUrl,
        openTime,
        closeTime,
      }
      
      await request.put('/merchant/info', submitData)
      message.success('店铺信息更新成功')
      fetchShopInfo()
    } catch (error) {
      message.error('更新失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="店铺信息" bordered={false}>
      <Row gutter={48}>
        <Col span={6} style={{ textAlign: 'center' }}>
          <Avatar size={100} icon={<ShopOutlined />} src={logoUrl} />
          <div style={{ marginTop: 16 }}>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>更换Logo</Button>
            </Upload>
          </div>
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            {merchantInfo?.name || '我的店铺'}
          </Text>
        </Col>
        <Col span={18}>
          <Form form={form} layout="vertical" onFinish={handleSubmit}>
            <Row gutter={24}>
              <Col span={12}>
                <Form.Item label="店铺名称" name="name" rules={[{ required: true, message: '请输入店铺名称' }]}>
                  <Input placeholder="请输入店铺名称" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="联系电话" name="phone" rules={[{ required: true, message: '请输入联系电话' }]}>
                  <Input placeholder="请输入联系电话" />
                </Form.Item>
              </Col>
              <Col span={24}>
                <Form.Item label="店铺地址" name="address" rules={[{ required: true, message: '请输入店铺地址' }]}>
                  <Input placeholder="请输入店铺地址" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="营业时间" name="businessHours">
                  <TimePicker.RangePicker format="HH:mm" placeholder={['开始时间', '结束时间']} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={24}>
                <Form.Item label="店铺简介" name="description">
                  <Input.TextArea rows={3} placeholder="请输入店铺简介" />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>保存修改</Button>
            </Form.Item>
          </Form>
        </Col>
      </Row>
    </Card>
  )
}

// 修改密码
const PasswordSettings = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const logout = useMerchantStore((state) => state.logout)

  const handleSubmit = async (values: any) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }
    setLoading(true)
    try {
      await request.put('/merchant/password', values)
      message.success('密码修改成功，请重新登录')
      form.resetFields()
      // 退出登录并跳转到登录页面
      logout()
      navigate('/login')
    } catch (error: any) {
      message.error(error.response?.data?.message || '密码修改失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="修改密码" bordered={false}>
      <Form form={form} layout="vertical" onFinish={handleSubmit} style={{ maxWidth: 400 }}>
        <Form.Item label="当前密码" name="oldPassword" rules={[{ required: true, message: '请输入当前密码' }]}>
          <Input.Password prefix={<LockOutlined />} placeholder="请输入当前密码" />
        </Form.Item>
        <Form.Item label="新密码" name="newPassword" rules={[
          { required: true, message: '请输入新密码' },
          { min: 6, message: '密码至少6位' }
        ]}>
          <Input.Password prefix={<LockOutlined />} placeholder="请输入新密码" />
        </Form.Item>
        <Form.Item label="确认新密码" name="confirmPassword" rules={[
          { required: true, message: '请确认新密码' },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('newPassword') === value) return Promise.resolve()
              return Promise.reject(new Error('两次输入的密码不一致'))
            },
          }),
        ]}>
          <Input.Password prefix={<LockOutlined />} placeholder="请再次输入新密码" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>确认修改</Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

// 设置页面主组件
const Settings = () => {
  return (
    <div>
      <Title level={4}>店铺设置</Title>
      <Tabs defaultActiveKey="shop" items={[
        { key: 'shop', label: <span><ShopOutlined />店铺信息</span>, children: <ShopSettings /> },
        { key: 'password', label: <span><LockOutlined />修改密码</span>, children: <PasswordSettings /> },
      ]} />
    </div>
  )
}

export default Settings
