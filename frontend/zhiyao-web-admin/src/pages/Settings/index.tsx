import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Form, Input, Button, message, Tabs, Row, Col, Avatar, Upload, InputNumber, Typography, Divider } from 'antd'
import { UserOutlined, LockOutlined, SettingOutlined, UploadOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'
import useAdminStore from '../../stores/adminStore'
import { updateProfile, changePassword, getPlatformConfig, savePlatformConfig } from '../../services/api'
import request from '../../utils/request'

const { Title, Text } = Typography
const { TabPane } = Tabs

// 个人信息设置
const ProfileSettings = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [avatarUrl, setAvatarUrl] = useState('')
  const adminInfo = useAdminStore((state) => state.adminInfo)
  const login = useAdminStore((state) => state.login)
  const token = useAdminStore((state) => state.token)

  const fetchProfile = async () => {
    try {
      const res = await request.get('/admin/info')
      if (res.data) {
        setAvatarUrl(res.data.avatar || '')
        form.setFieldsValue({
          username: res.data.username || 'admin',
          name: res.data.name || '系统管理员',
          email: res.data.email || '',
          phone: res.data.phone || '',
        })
      }
    } catch (error) {
      console.error('获取个人信息失败:', error)
    }
  }

  // 页面加载时获取最新的个人信息
  useEffect(() => {
    fetchProfile()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // 头像上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/upload/avatar',
    showUploadList: false,
    beforeUpload: (file) => {
      const isImage = file.type.startsWith('image/')
      if (!isImage) {
        message.error('只能上传图片文件!')
        return false
      }
      const isLt2M = file.size / 1024 / 1024 < 2
      if (!isLt2M) {
        message.error('图片大小不能超过2MB!')
        return false
      }
      return true
    },
    onChange: async (info) => {
      if (info.file.status === 'done') {
        const url = info.file.response?.data?.url
        if (url) {
          setAvatarUrl(url)
          // 保存头像到服务器
          try {
            await updateProfile({ avatar: url })
            message.success('头像更换成功')
            fetchProfile()
          } catch (error) {
            message.error('头像保存失败')
          }
        }
      } else if (info.file.status === 'error') {
        message.error('头像上传失败')
      }
    },
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      const res = await updateProfile(values)
      // 如果后端返回了更新后的数据，直接使用
      if (res.data && typeof res.data === 'object' && res.data.name) {
        setAvatarUrl(res.data.avatar || '')
        form.setFieldsValue({
          username: res.data.username || 'admin',
          name: res.data.name || '系统管理员',
          email: res.data.email || '',
          phone: res.data.phone || '',
        })
      } else {
        // 否则重新获取
        await fetchProfile()
      }
      message.success('个人信息更新成功')
    } catch (error: any) {
      console.error('更新失败:', error)
      message.error(error.message || '更新失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="个人信息" bordered={false}>
      <Row gutter={48}>
        <Col span={6} style={{ textAlign: 'center' }}>
          <Avatar size={100} icon={<UserOutlined />} src={avatarUrl || adminInfo?.avatar} />
          <div style={{ marginTop: 16 }}>
            <Upload {...uploadProps}>
              <Button icon={<UploadOutlined />}>更换头像</Button>
            </Upload>
          </div>
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            {adminInfo?.name || '系统管理员'}
          </Text>
        </Col>
        <Col span={18}>
          <Form form={form} layout="vertical" onFinish={handleSubmit}>
            <Row gutter={24}>
              <Col span={12}>
                <Form.Item label="用户名" name="username">
                  <Input disabled prefix={<UserOutlined />} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="姓名" name="name" rules={[{ required: true, message: '请输入姓名' }]}>
                  <Input placeholder="请输入姓名" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="邮箱" name="email" rules={[{ type: 'email', message: '请输入有效邮箱' }]}>
                  <Input placeholder="请输入邮箱" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="手机号" name="phone">
                  <Input placeholder="请输入手机号" />
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
  const logout = useAdminStore((state) => state.logout)

  const handleSubmit = async (values: any) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }
    setLoading(true)
    try {
      await changePassword(values)
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

// 平台配置
const PlatformSettings = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const res = await getPlatformConfig()
      if (res.data) {
        form.setFieldsValue(res.data)
      }
    } catch (error) {
      console.error('获取配置失败:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      await savePlatformConfig(values)
      message.success('平台配置保存成功')
    } catch (error) {
      message.error('保存失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="平台配置" bordered={false}>
      <Form form={form} layout="vertical" onFinish={handleSubmit}
        initialValues={{ platformName: '智健优选', contactPhone: '400-888-8888', deliveryFee: 5, minOrderAmount: 20, deliveryRange: 5 }}>
        
        <Divider orientation="left">基本信息</Divider>
        <Row gutter={24}>
          <Col span={12}>
            <Form.Item label="平台名称" name="platformName" rules={[{ required: true, message: '请输入平台名称' }]}>
              <Input placeholder="请输入平台名称" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="客服电话" name="contactPhone">
              <Input placeholder="请输入客服电话" />
            </Form.Item>
          </Col>
        </Row>

        <Divider orientation="left">配送设置</Divider>
        <Row gutter={24}>
          <Col span={8}>
            <Form.Item label="基础配送费(元)" name="deliveryFee" rules={[{ required: true, message: '请输入配送费' }]}>
              <InputNumber min={0} precision={2} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="起送金额(元)" name="minOrderAmount" rules={[{ required: true, message: '请输入起送金额' }]}>
              <InputNumber min={0} precision={2} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="配送范围(公里)" name="deliveryRange" rules={[{ required: true, message: '请输入配送范围' }]}>
              <InputNumber min={1} max={50} style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>保存配置</Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

// 设置页面主组件
const Settings = () => {
  return (
    <div>
      <Title level={4}>系统设置</Title>
      <Tabs defaultActiveKey="profile" items={[
        { key: 'profile', label: <span><UserOutlined />个人信息</span>, children: <ProfileSettings /> },
        { key: 'password', label: <span><LockOutlined />修改密码</span>, children: <PasswordSettings /> },
        { key: 'platform', label: <span><SettingOutlined />平台配置</span>, children: <PlatformSettings /> },
      ]} />
    </div>
  )
}

export default Settings
