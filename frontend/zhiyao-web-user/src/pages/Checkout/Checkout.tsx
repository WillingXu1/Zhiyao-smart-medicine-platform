import { useState, useEffect } from 'react'
import { Card, Form, Input, Button, Typography, Divider, message, Row, Col, Tag, Radio, Empty, Space, Spin } from 'antd'
import { EnvironmentOutlined, MedicineBoxOutlined, PlusOutlined, RightOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import useCartStore from '../../stores/cartStore'
import { createOrder } from '../../services/order'
import { getAddressList } from '../../services/user'
import './Checkout.css'

const { Title, Text } = Typography
const { TextArea } = Input

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

const Checkout = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [addresses, setAddresses] = useState<Address[]>([])
  const [selectedAddressId, setSelectedAddressId] = useState<number | null>(null)
  const [addressLoading, setAddressLoading] = useState(true)
  

  const { getCheckedItems, getTotalPrice, clearCheckedItems } = useCartStore()
  const checkedItems = getCheckedItems()
  const totalPrice = getTotalPrice()
  const deliveryFee = 0 // 免配送费
  const finalPrice = totalPrice + deliveryFee

  // 获取地址列表
  useEffect(() => {
    fetchAddresses()
  }, [])

  const fetchAddresses = async () => {
    try {
      setAddressLoading(true)
      const res: any = await getAddressList()
      const addressList = res.data || res || []
      setAddresses(Array.isArray(addressList) ? addressList : [])
      // 默认选中默认地址，如果没有默认地址则选中第一个
      const list = Array.isArray(addressList) ? addressList : []
      const defaultAddr = list.find((addr: Address) => addr.isDefault)
      if (defaultAddr) {
        setSelectedAddressId(defaultAddr.id)
      } else if (list.length > 0) {
        setSelectedAddressId(list[0].id)
      }
    } catch (error) {
      console.error('获取地址列表失败:', error)
    } finally {
      setAddressLoading(false)
    }
  }

  const selectedAddress = addresses.find(addr => addr.id === selectedAddressId)

  const handleSubmit = async (values: { remark?: string }) => {
    if (checkedItems.length === 0) {
      message.warning('请选择商品')
      return
    }

    if (!selectedAddressId || !selectedAddress) {
      message.warning('请选择收货地址')
      return
    }

    setLoading(true)
    try {
      const orderData = {
        receiverName: selectedAddress.name,
        receiverPhone: selectedAddress.phone,
        receiverAddress: `${selectedAddress.province} ${selectedAddress.city} ${selectedAddress.district} ${selectedAddress.detail}`,
        remark: values.remark,
        addressId: selectedAddressId,
        items: checkedItems.map((item) => ({
          medicineId: item.medicineId,
          quantity: item.quantity,
        })),
      }
      const res = await createOrder(orderData)
      message.success('下单成功')
      clearCheckedItems()
      // 后端返回的data就是orderId
      const orderId = res.data
      if (orderId && !isNaN(Number(orderId))) {
        navigate(`/order/${orderId}`)
      } else {
        message.error('订单创建异常，请到订单列表查看')
        navigate('/orders')
      }
    } catch (error) {
      console.error('下单失败:', error)
    } finally {
      setLoading(false)
    }
  }

  if (checkedItems.length === 0) {
    return (
      <div className="checkout-page">
        <Card className="empty-checkout" bordered={false}>
          <Title level={4}>没有选中的商品</Title>
          <Button type="primary" onClick={() => navigate('/cart')}>
            返回购物车
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="checkout-page">
      <Title level={3} className="page-title">确认订单</Title>

      <Row gutter={24}>
        <Col xs={24} lg={16}>
          {/* 收货信息 */}
          <Card 
            className="address-card" 
            title={<><EnvironmentOutlined /> 收货地址</>} 
            bordered={false}
            extra={
              addresses.length > 0 && (
                <Button 
                  type="link" 
                  onClick={() => navigate('/address')}
                  icon={<RightOutlined />}
                >
                  管理地址
                </Button>
              )
            }
          >
            {addressLoading ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin tip="加载地址中..." />
              </div>
            ) : addresses.length === 0 ? (
              <Empty 
                description="暂无收货地址" 
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => navigate('/address')}
                >
                  添加收货地址
                </Button>
              </Empty>
            ) : (
              <Radio.Group 
                value={selectedAddressId} 
                onChange={(e) => setSelectedAddressId(e.target.value)}
                className="address-radio-group"
              >
                <Space direction="vertical" style={{ width: '100%' }}>
                  {addresses.map((addr) => (
                    <Radio key={addr.id} value={addr.id} className="address-radio-item">
                      <div className="address-select-item">
                        <div className="address-select-header">
                          <span className="address-name">{addr.name}</span>
                          <span className="address-phone">{addr.phone}</span>
                          {addr.isDefault && <Tag color="orange">默认</Tag>}
                        </div>
                        <div className="address-select-detail">
                          {addr.province} {addr.city} {addr.district} {addr.detail}
                        </div>
                      </div>
                    </Radio>
                  ))}
                </Space>
              </Radio.Group>
            )}
          </Card>

          {/* 订单备注 */}
          <Card className="remark-card" title="订单备注" bordered={false}>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              initialValues={{ remark: '' }}
            >
              <Form.Item name="remark">
                <TextArea rows={3} placeholder="如有特殊要求请备注（选填）" />
              </Form.Item>
            </Form>
          </Card>

          {/* 商品清单 */}
          <Card className="items-card" title="商品清单" bordered={false}>
            {checkedItems.map((item) => (
              <div key={item.medicineId} className="checkout-item">
                <div className="item-image">
                  {item.image ? (
                    <img src={item.image} alt={item.name} />
                  ) : (
                    <MedicineBoxOutlined style={{ fontSize: 40, color: '#10B981' }} />
                  )}
                </div>
                <div className="item-info">
                  <div className="item-name">
                    {item.isPrescription === 1 && <Tag color="red">处方药</Tag>}
                    {item.name}
                  </div>
                  <Text type="secondary">{item.specification}</Text>
                </div>
                <div className="item-price-qty">
                  <span className="item-price">¥{item.price.toFixed(2)}</span>
                  <span className="item-qty">x{item.quantity}</span>
                </div>
                <div className="item-subtotal">
                  ¥{(item.price * item.quantity).toFixed(2)}
                </div>
              </div>
            ))}
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* 订单汇总 */}
          <Card className="summary-card" bordered={false}>
            <Title level={4}>订单汇总</Title>
            <Divider />
            <div className="summary-row">
              <span>商品金额</span>
              <span>¥{totalPrice.toFixed(2)}</span>
            </div>
            <div className="summary-row">
              <span>配送费</span>
              <span className="free-delivery">免运费</span>
            </div>
            <Divider />
            <div className="summary-row total">
              <span>应付总额</span>
              <span className="final-price">¥{finalPrice.toFixed(2)}</span>
            </div>

            <Button
              type="primary"
              size="large"
              block
              loading={loading}
              className="submit-order-btn"
              onClick={() => form.submit()}
            >
              提交订单
            </Button>

            <div className="checkout-tips">
              <Text type="secondary">
                提交订单即表示您同意我们的服务条款
              </Text>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Checkout
