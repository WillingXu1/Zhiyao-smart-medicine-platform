import { useState } from 'react'
import { Form, Input, Button, message } from 'antd'
import { UserOutlined, LockOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { login } from '../../services/api'
import useAdminStore from '../../stores/adminStore'
import './Login.css'

const Login = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const adminLogin = useAdminStore((state) => state.login)

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const res = await login(values)
      adminLogin(res.data.token, res.data)
      message.success('登录成功')
      navigate('/')
    } catch (error) {
      console.error('登录失败:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <SafetyCertificateOutlined className="logo-icon" />
          <h1>智健优选 - 管理后台</h1>
          <p>系统管理平台</p>
        </div>
        <Form name="login" onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>登录</Button>
          </Form.Item>
        </Form>
      </div>
    </div>
  )
}

export default Login
