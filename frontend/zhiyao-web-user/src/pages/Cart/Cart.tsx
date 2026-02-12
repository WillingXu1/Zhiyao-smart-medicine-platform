import { Card, Table, Button, InputNumber, Checkbox, Empty, Typography, Tag, message, Popconfirm } from 'antd'
import { DeleteOutlined, MedicineBoxOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import useCartStore, { CartItem } from '../../stores/cartStore'
import useUserStore from '../../stores/userStore'
import './Cart.css'

const { Title, Text } = Typography

const Cart = () => {
  const navigate = useNavigate()
  const isLoggedIn = useUserStore((state) => state.isLoggedIn)
  const { items, removeItem, updateQuantity, toggleCheck, toggleCheckAll, getTotalPrice, clearCheckedItems } = useCartStore()

  const isAllChecked = items.length > 0 && items.every((item) => item.checked)
  const hasCheckedItems = items.some((item) => item.checked)
  const checkedCount = items.filter((item) => item.checked).length

  const handleCheckout = () => {
    if (!isLoggedIn) {
      message.warning('请先登录')
      navigate('/login')
      return
    }
    if (!hasCheckedItems) {
      message.warning('请选择要结算的商品')
      return
    }
    navigate('/checkout')
  }

  const columns = [
    {
      title: (
        <Checkbox
          checked={isAllChecked}
          onChange={(e) => toggleCheckAll(e.target.checked)}
        >
          全选
        </Checkbox>
      ),
      dataIndex: 'checked',
      width: 80,
      render: (_: boolean, record: CartItem) => (
        <Checkbox checked={record.checked} onChange={() => toggleCheck(record.medicineId)} />
      ),
    },
    {
      title: '药品信息',
      dataIndex: 'name',
      render: (_: string, record: CartItem) => (
        <div className="cart-item-info" onClick={() => navigate(`/medicine/${record.medicineId}`)}>
          <div className="cart-item-image">
            {record.image ? (
              <img src={record.image} alt={record.name} />
            ) : (
              <MedicineBoxOutlined style={{ fontSize: 40, color: '#10B981' }} />
            )}
          </div>
          <div className="cart-item-detail">
            <div className="cart-item-name">
              {record.isPrescription === 1 && <Tag color="red">处方药</Tag>}
              {record.name}
            </div>
            <Text type="secondary">{record.specification}</Text>
          </div>
        </div>
      ),
    },
    {
      title: '单价',
      dataIndex: 'price',
      width: 120,
      render: (price: number) => <span className="item-price">¥{price.toFixed(2)}</span>,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      width: 150,
      render: (quantity: number, record: CartItem) => (
        <InputNumber
          min={1}
          max={record.stock}
          value={quantity}
          onChange={(val) => updateQuantity(record.medicineId, val || 1)}
        />
      ),
    },
    {
      title: '小计',
      dataIndex: 'subtotal',
      width: 120,
      render: (_: unknown, record: CartItem) => (
        <span className="item-subtotal">¥{(record.price * record.quantity).toFixed(2)}</span>
      ),
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 80,
      render: (_: unknown, record: CartItem) => (
        <Popconfirm
          title="确定删除该商品吗？"
          onConfirm={() => removeItem(record.medicineId)}
          okText="确定"
          cancelText="取消"
        >
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <div className="cart-page">
      <Title level={3} className="page-title">购物车</Title>

      {items.length > 0 ? (
        <>
          <Card className="cart-table-card" bordered={false}>
            <Table
              columns={columns}
              dataSource={items}
              rowKey="medicineId"
              pagination={false}
            />
          </Card>

          {/* 结算栏 */}
          <Card className="checkout-bar" bordered={false}>
            <div className="checkout-content">
              <div className="checkout-left">
                <Checkbox
                  checked={isAllChecked}
                  onChange={(e) => toggleCheckAll(e.target.checked)}
                >
                  全选
                </Checkbox>
                <Popconfirm
                  title="确定删除选中的商品吗？"
                  onConfirm={clearCheckedItems}
                  okText="确定"
                  cancelText="取消"
                  disabled={!hasCheckedItems}
                >
                  <Button type="link" danger disabled={!hasCheckedItems}>
                    删除选中
                  </Button>
                </Popconfirm>
              </div>
              <div className="checkout-right">
                <div className="checkout-info">
                  <span>已选择 <strong>{checkedCount}</strong> 件商品</span>
                  <span className="checkout-total">
                    合计：<span className="total-price">¥{getTotalPrice().toFixed(2)}</span>
                  </span>
                </div>
                <Button
                  type="primary"
                  size="large"
                  className="checkout-button"
                  disabled={!hasCheckedItems}
                  onClick={handleCheckout}
                >
                  去结算
                </Button>
              </div>
            </div>
          </Card>
        </>
      ) : (
        <Card className="empty-cart" bordered={false}>
          <Empty
            description="购物车是空的"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={() => navigate('/medicines')}>
              去选购药品
            </Button>
          </Empty>
        </Card>
      )}
    </div>
  )
}

export default Cart
