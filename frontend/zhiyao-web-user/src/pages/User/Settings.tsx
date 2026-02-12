import { useState, useEffect } from 'react'
import { Card, Form, Input, Button, message, Tabs, Row, Col, Avatar, Upload, Typography } from 'antd'
import { UserOutlined, LockOutlined, CameraOutlined, MailOutlined, PhoneOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import useUserStore from '../../stores/userStore'
import { updateUserInfo, changePassword, uploadAvatar, getUserInfo } from '../../services/user'
import type { UploadProps } from 'antd'
import './Settings.css'

const { Title, Text } = Typography

// 个人信息设置
const ProfileSettings = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [avatarLoading, setAvatarLoading] = useState(false)
  const { userInfo, setUserInfo } = useUserStore()

  // 加载时获取最新用户信息
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const res: any = await getUserInfo()
        const data = res.data || res
        if (data && userInfo) {
          setUserInfo({ ...userInfo, email: data.email || null })
          form.setFieldsValue({
            nickname: data.nickname || userInfo.nickname,
            email: data.email || '',
            phone: data.username || userInfo.username,
          })
        }
      } catch (e) {
        console.error('获取用户信息失败:', e)
      }
    }
    fetchUserInfo()
  }, [])

  // 头像上传处理
  const handleAvatarUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options
    setAvatarLoading(true)
    try {
      const res: any = await uploadAvatar(file as File)
      // 后端返回格式: { url: "..." } 或 { data: { url: "..." } }
      const avatarUrl = res?.url || res?.data?.url || res?.data || res
      // 更新用户信息（头像）
      await updateUserInfo({ avatar: avatarUrl })
      if (userInfo) {
        setUserInfo({ ...userInfo, avatar: avatarUrl })
      }
      message.success('头像上传成功')
      onSuccess?.(res)
    } catch (error: any) {
      message.error(error?.message || '头像上传失败')
      onError?.(error)
    } finally {
      setAvatarLoading(false)
    }
  }

  // 限制上传文件类型和大小
  const beforeUpload = (file: File) => {
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
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      const res: any = await updateUserInfo({
        nickname: values.nickname,
        email: values.email,
      })
      // 更新本地用户信息
      if (userInfo) {
        setUserInfo({ ...userInfo, nickname: values.nickname })
      }
      message.success('个人信息更新成功')
    } catch (error: any) {
      message.error(error?.message || '更新失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="个人信息" bordered={false} className="settings-card">
      <Row gutter={48}>
        <Col xs={24} sm={6} className="avatar-col">
          <div className="avatar-section">
            <Avatar size={100} icon={<UserOutlined />} src={userInfo?.avatar} className="user-avatar" />
            <Upload 
              showUploadList={false} 
              customRequest={handleAvatarUpload}
              beforeUpload={beforeUpload}
              accept="image/*"
            >
              <Button icon={<CameraOutlined />} className="upload-btn" loading={avatarLoading}>
                {avatarLoading ? '上传中...' : '更换头像'}
              </Button>
            </Upload>
            <Text className="username">{userInfo?.nickname || '用户'}</Text>
            <Text type="secondary">{userInfo?.username || ''}</Text>
          </div>
        </Col>
        <Col xs={24} sm={18}>
          <Form 
            form={form} 
            layout="vertical" 
            onFinish={handleSubmit}
            initialValues={{ 
              nickname: userInfo?.nickname || '', 
              email: userInfo?.email || '', 
              phone: userInfo?.username || '' 
            }}
            className="settings-form"
          >
            <Row gutter={24}>
              <Col xs={24} sm={12}>
                <Form.Item label="昵称" name="nickname" rules={[{ required: true, message: '请输入昵称' }]}>
                  <Input prefix={<UserOutlined />} placeholder="请输入昵称" />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item label="邮箱" name="email" rules={[{ type: 'email', message: '请输入有效邮箱' }]}>
                  <Input prefix={<MailOutlined />} placeholder="请输入邮箱" />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12}>
                <Form.Item label="手机号" name="phone">
                  <Input prefix={<PhoneOutlined />} placeholder="请输入手机号" disabled />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} className="submit-btn">保存修改</Button>
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
  const { logout } = useUserStore()

  const handleSubmit = async (values: any) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的密码不一致')
      return
    }
    setLoading(true)
    try {
      await changePassword({
        oldPassword: values.oldPassword,
        newPassword: values.newPassword,
      })
      message.success('密码修改成功，请重新登录')
      form.resetFields()
      // 密码修改成功后登出并跳转到登录页
      setTimeout(() => {
        logout()
        navigate('/login')
      }, 1500)
    } catch (error: any) {
      message.error(error?.message || '密码修改失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="修改密码" bordered={false} className="settings-card">
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
          <Button type="primary" htmlType="submit" loading={loading} className="submit-btn">确认修改</Button>
        </Form.Item>
      </Form>
    </Card>
  )
}

// 设置页面主组件
const Settings = () => {
  return (
    <div className="settings-page">
      <Title level={4}>账号设置</Title>
      <Tabs 
        defaultActiveKey="profile" 
        className="settings-tabs"
        items={[
          { key: 'profile', label: <span><UserOutlined />个人信息</span>, children: <ProfileSettings /> },
          { key: 'password', label: <span><LockOutlined />修改密码</span>, children: <PasswordSettings /> },
        ]} 
      />
    </div>
  )
}

export default Settings
