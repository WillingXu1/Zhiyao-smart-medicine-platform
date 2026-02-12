import { useState } from 'react'
import { Form, Input, Button, message, Tabs } from 'antd'
import { UserOutlined, LockOutlined, PhoneOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../../services/auth'
import useUserStore from '../../stores/userStore'
import './Login.css'

const Login = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('login')
  const userLogin = useUserStore((state) => state.login)

  // 登录表单提交
  const onLoginFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const res = await login(values)
      userLogin(res.data.token, res.data)
      message.success('登录成功')
      navigate('/')
    } catch (error) {
      console.error('登录失败:', error)
    } finally {
      setLoading(false)
    }
  }

  // 注册表单提交
  const onRegisterFinish = async (values: {
    username: string
    password: string
    phone: string
    nickname: string
  }) => {
    setLoading(true)
    try {
      await register(values)
      message.success('注册成功，请登录')
      setActiveTab('login')
    } catch (error) {
      console.error('注册失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const items = [
    {
      key: 'login',
      label: '账号登录',
      children: (
        <Form
          name="login"
          className="login-form"
          onFinish={onLoginFinish}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名/手机号' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名/手机号"
            />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className="login-button"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'register',
      label: '新用户注册',
      children: (
        <Form
          name="register"
          className="login-form"
          onFinish={onRegisterFinish}
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 4, max: 20, message: '用户名长度4-20位' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
            />
          </Form.Item>
          <Form.Item
            name="phone"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
            ]}
          >
            <Input
              prefix={<PhoneOutlined />}
              placeholder="手机号"
            />
          </Form.Item>
          <Form.Item
            name="nickname"
            rules={[{ required: true, message: '请输入昵称' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="昵称"
            />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, max: 20, message: '密码长度6-20位' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
            />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="确认密码"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className="login-button"
              loading={loading}
              block
            >
              注册
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ]

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <div className="login-logo">
            <span className="logo-icon">💊</span>
            <span className="logo-text">知药</span>
          </div>
          <p className="login-subtitle">您身边的智慧药房</p>
        </div>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={items}
          centered
        />
      </div>
    </div>
  )
}

export default Login
