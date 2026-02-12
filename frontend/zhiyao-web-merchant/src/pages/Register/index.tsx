import { useState } from 'react'
import { Form, Input, Button, message, Steps, Upload, TimePicker } from 'antd'
import type { UploadFile, UploadProps } from 'antd'
import dayjs from 'dayjs'
import { PhoneOutlined, LockOutlined, ShopOutlined, UploadOutlined, EnvironmentOutlined } from '@ant-design/icons'
import { useNavigate, Link } from 'react-router-dom'
import { registerMerchant } from '../../services/api'
import '../Login/Login.css'

const { Step } = Steps

const Register = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [current, setCurrent] = useState(0)
  const [form] = Form.useForm()
  const [businessLicenseUrl, setBusinessLicenseUrl] = useState('')
  const [drugLicenseUrl, setDrugLicenseUrl] = useState('')

  // 上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    action: '/api/upload/merchant',
    showUploadList: true,
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
  }

  const onFinish = async (values: any) => {
    setLoading(true)
    try {
      // 处理上传文件，提取URL
      const submitData = {
        ...values,
        businessLicense: businessLicenseUrl || '',
        pharmacistLicense: drugLicenseUrl || '',
      }
      await registerMerchant(submitData)
      message.success('注册申请已提交，请等待审核')
      navigate('/login')
    } catch (error) {
      console.error('注册失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const next = async () => {
    try {
      if (current === 0) {
        await form.validateFields(['phone', 'password', 'confirmPassword'])
      } else if (current === 1) {
        await form.validateFields(['name', 'address', 'businessHours'])
      }
      setCurrent(current + 1)
    } catch (error) {
      // 验证失败
    }
  }

  const prev = () => setCurrent(current - 1)

  const stepTitles = ['账号信息', '店铺信息', '资质上传']

  return (
    <div className="login-container">
      <div className="login-box" style={{ width: 500 }}>
        <div className="login-header">
          <ShopOutlined className="logo-icon" />
          <h1>商家入驻申请</h1>
          <p>填写信息完成入驻申请</p>
        </div>
        
        <Steps current={current} size="small" style={{ marginBottom: 24 }}>
          {stepTitles.map(title => <Step key={title} title={title} />)}
        </Steps>

        <Form form={form} name="register" onFinish={onFinish} layout="vertical">
          {/* 使用display隐藏而非条件渲染，确保所有字段值都能提交 */}
          <div style={{ display: current === 0 ? 'block' : 'none' }}>
            <Form.Item name="phone" rules={[
              { required: true, message: '请输入手机号' },
              { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号' },
            ]}>
              <Input prefix={<PhoneOutlined />} placeholder="手机号" />
            </Form.Item>
            <Form.Item name="password" rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位' }
            ]}>
              <Input.Password prefix={<LockOutlined />} placeholder="密码" />
            </Form.Item>
            <Form.Item name="confirmPassword" rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) return Promise.resolve()
                  return Promise.reject(new Error('两次密码不一致'))
                },
              }),
            ]}>
              <Input.Password prefix={<LockOutlined />} placeholder="确认密码" />
            </Form.Item>
          </div>
          <div style={{ display: current === 1 ? 'block' : 'none' }}>
            <Form.Item name="name" rules={[{ required: true, message: '请输入店铺名称' }]}>
              <Input prefix={<ShopOutlined />} placeholder="店铺名称" />
            </Form.Item>
            <Form.Item name="address" rules={[{ required: true, message: '请输入店铺地址' }]}>
              <Input prefix={<EnvironmentOutlined />} placeholder="店铺地址" />
            </Form.Item>
            <Form.Item 
              name="businessHours" 
              label="营业时间"
              rules={[{ required: true, message: '请选择营业时间' }]}
              getValueFromEvent={(times) => {
                if (times && times[0] && times[1]) {
                  return `${times[0].format('HH:mm')}-${times[1].format('HH:mm')}`
                }
                return ''
              }}
              getValueProps={(value) => {
                if (value && typeof value === 'string' && value.includes('-')) {
                  const [start, end] = value.split('-')
                  return { value: [dayjs(start, 'HH:mm'), dayjs(end, 'HH:mm')] }
                }
                return { value: [dayjs('09:00', 'HH:mm'), dayjs('22:00', 'HH:mm')] }
              }}
            >
              <TimePicker.RangePicker 
                format="HH:mm" 
                placeholder={['开始时间', '结束时间']}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </div>
          <div style={{ display: current === 2 ? 'block' : 'none', minHeight: 200 }}>
            <Form.Item label="营业执照（可选）">
              <Upload
                {...uploadProps}
                listType="picture-card"
                maxCount={1}
                onChange={(info) => {
                  console.log('上传状态:', info.file.status, info.file.response)
                  if (info.file.status === 'done') {
                    const url = info.file.response?.data?.url
                    if (url) {
                      setBusinessLicenseUrl(url)
                      message.success('营业执照上传成功')
                    } else {
                      message.error('上传失败，未获取到图片地址')
                    }
                  } else if (info.file.status === 'error') {
                    message.error(`上传失败: ${info.file.response?.message || '未知错误'}`)
                  }
                }}
              >
                <div><UploadOutlined /><div style={{ marginTop: 8 }}>上传</div></div>
              </Upload>
            </Form.Item>
            <Form.Item label="药品经营许可证（可选）">
              <Upload
                {...uploadProps}
                listType="picture-card"
                maxCount={1}
                onChange={(info) => {
                  console.log('上传状态:', info.file.status, info.file.response)
                  if (info.file.status === 'done') {
                    const url = info.file.response?.data?.url
                    if (url) {
                      setDrugLicenseUrl(url)
                      message.success('许可证上传成功')
                    } else {
                      message.error('上传失败，未获取到图片地址')
                    }
                  } else if (info.file.status === 'error') {
                    message.error(`上传失败: ${info.file.response?.message || '未知错误'}`)
                  }
                }}
              >
                <div><UploadOutlined /><div style={{ marginTop: 8 }}>上传</div></div>
              </Upload>
            </Form.Item>
            <p style={{ color: '#999', fontSize: 12 }}>资质文件可在审核前补充上传</p>
          </div>
          
          <div style={{ marginTop: 24 }}>
            {current > 0 && (
              <Button style={{ marginRight: 8 }} onClick={prev}>上一步</Button>
            )}
            {current < stepTitles.length - 1 && (
              <Button type="primary" onClick={next}>下一步</Button>
            )}
            {current === stepTitles.length - 1 && (
              <Button type="primary" htmlType="submit" loading={loading}>提交申请</Button>
            )}
          </div>
        </Form>

        <div style={{ marginTop: 16, textAlign: 'center' }}>
          已有账号？<Link to="/login">立即登录</Link>
        </div>
      </div>
    </div>
  )
}

export default Register
