import { useState } from 'react'
import { Form, Input, Button, message } from 'antd'
import { PhoneOutlined, LockOutlined, ShopOutlined } from '@ant-design/icons'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../../services/api'
import useMerchantStore from '../../stores/merchantStore'
import './Login.css'

const Login = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const merchantLogin = useMerchantStore((state) => state.login)

  const onFinish = async (values: { phone: string; password: string }) => {
    setLoading(true)
    try {
      const res = await login(values)
      merchantLogin(res.data.token, res.data)
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
          <ShopOutlined className="logo-icon" />
          <h1>智健优选 - 商家中心</h1>
          <p>商家入驻管理平台</p>
        </div>
        <Form name="login" onFinish={onFinish} size="large">
          <Form.Item
            name="phone"
            rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
            ]}
          >
            <Input prefix={<PhoneOutlined />} placeholder="手机号" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
          <div style={{ textAlign: 'center' }}>
            还没有账号？<Link to="/register">立即入驻</Link>
          </div>
        </Form>
      </div>
    </div>
  )
}

export default Login
