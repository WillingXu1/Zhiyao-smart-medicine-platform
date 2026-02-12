import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Row, Col, Button, InputNumber, Tag, Spin, Divider, Typography, message, Descriptions, Breadcrumb } from 'antd'
import { ShoppingCartOutlined, HeartOutlined, HeartFilled, MedicineBoxOutlined, HomeOutlined, LeftOutlined } from '@ant-design/icons'
import { getMedicineDetail } from '../../services/medicine'
import { addFavorite, removeFavorite } from '../../services/user'
import useUserStore from '../../stores/userStore'
import useCartStore from '../../stores/cartStore'
import './MedicineDetail.css'

const { Title, Text, Paragraph } = Typography

interface Medicine {
  id: number
  name: string
  commonName?: string          // 通用名
  specification: string
  price: number
  originalPrice?: number
  image?: string
  images?: string               // 图片列表JSON
  isPrescription: number
  manufacturer?: string
  approvalNumber?: string       // 批准文号
  stock: number
  sales?: number                // 销量
  categoryId?: number
  efficacy?: string             // 功效说明
  dosage?: string               // 用法用量
  adverseReactions?: string     // 不良反应
  contraindications?: string    // 禁忌
  precautions?: string          // 注意事项
  riskTips?: string             // 用药风险提示
}

const MedicineDetail = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isLoggedIn = useUserStore((state) => state.isLoggedIn)
  const addToCart = useCartStore((state) => state.addItem)

  const [loading, setLoading] = useState(true)
  const [medicine, setMedicine] = useState<Medicine | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [isFavorite, setIsFavorite] = useState(false)
  const [favoriteLoading, setFavoriteLoading] = useState(false)

  useEffect(() => {
    if (id) {
      const medicineId = Number(id)
      if (!isNaN(medicineId) && medicineId > 0) {
        fetchMedicineDetail(medicineId)
      } else {
        message.error('药品ID无效')
        navigate('/medicines')
      }
    } else {
      message.error('药品ID不能为空')
      navigate('/medicines')
    }
  }, [id, navigate])

  const fetchMedicineDetail = async (medicineId: number) => {
    try {
      setLoading(true)
      const res = await getMedicineDetail(medicineId)
      setMedicine(res.data)
    } catch (error) {
      console.error('获取药品详情失败:', error)
      message.error('获取药品详情失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAddToCart = () => {
    if (!medicine) return
    
    addToCart({
      medicineId: medicine.id,
      name: medicine.name,
      specification: medicine.specification || '',
      price: medicine.price,
      image: medicine.image || '',
      quantity: quantity,
      stock: medicine.stock,
      isPrescription: medicine.isPrescription,
    })
    message.success(`已加入购物车 x${quantity}`)
  }

  const handleBuyNow = () => {
    if (!isLoggedIn) {
      message.warning('请先登录')
      navigate('/login')
      return
    }
    // TODO: 立即购买跳转下单页
    navigate(`/checkout?medicineId=${id}&quantity=${quantity}`)
  }

  const handleToggleFavorite = async () => {
    if (!isLoggedIn) {
      message.warning('请先登录')
      navigate('/login')
      return
    }
    if (!medicine) return
    
    setFavoriteLoading(true)
    try {
      if (isFavorite) {
        await removeFavorite(medicine.id)
        setIsFavorite(false)
        message.success('已取消收藏')
      } else {
        await addFavorite(medicine.id)
        setIsFavorite(true)
        message.success('收藏成功')
      }
    } catch (error) {
      message.error(isFavorite ? '取消收藏失败' : '收藏失败')
    } finally {
      setFavoriteLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" />
      </div>
    )
  }

  if (!medicine) {
    return (
      <div className="error-container">
        <Title level={4}>药品不存在</Title>
        <Button type="primary" onClick={() => navigate('/medicines')}>
          返回药品列表
        </Button>
      </div>
    )
  }

  return (
    <div className="medicine-detail-page">
      {/* 面包屑 */}
      <Breadcrumb
        className="breadcrumb"
        items={[
          { href: '/', title: <><HomeOutlined /> 首页</> },
          { href: '/medicines', title: '药品列表' },
          { title: medicine.name },
        ]}
      />

      {/* 药品基本信息 */}
      <Card className="medicine-info-card" bordered={false}>
        <Row gutter={32}>
          <Col xs={24} md={10}>
            <div className="medicine-image">
              {medicine.image ? (
                <img src={medicine.image} alt={medicine.name} />
              ) : (
                <div className="image-placeholder">
                  <MedicineBoxOutlined style={{ fontSize: 120, color: '#10B981' }} />
                </div>
              )}
            </div>
          </Col>
          <Col xs={24} md={14}>
            <div className="medicine-main-info">
              <div className="medicine-header">
                {medicine.isPrescription === 1 && (
                  <Tag color="red" className="prescription-tag">处方药</Tag>
                )}
                {medicine.isPrescription === 0 && (
                  <Tag color="green" className="prescription-tag">非处方药</Tag>
                )}
                <Title level={3} className="medicine-name">{medicine.name}</Title>
                {medicine.commonName && (
                  <Text type="secondary" className="generic-name">{medicine.commonName}</Text>
                )}
              </div>

              <div className="price-section">
                <span className="label">价格</span>
                <span className="current-price">¥{medicine.price?.toFixed(2)}</span>
                {medicine.originalPrice && medicine.originalPrice > medicine.price && (
                  <span className="original-price">¥{medicine.originalPrice.toFixed(2)}</span>
                )}
              </div>

              <Divider />

              <div className="info-row">
                <span className="label">规格</span>
                <span className="value">{medicine.specification || '-'}</span>
              </div>
              <div className="info-row">
                <span className="label">生产厂家</span>
                <span className="value">{medicine.manufacturer || '-'}</span>
              </div>
              <div className="info-row">
                <span className="label">批准文号</span>
                <span className="value">{medicine.approvalNumber || '-'}</span>
              </div>
              <div className="info-row">
                <span className="label">库存</span>
                <span className={`value ${medicine.stock <= 10 ? 'stock-warning' : ''}`}>
                  {medicine.stock > 0 ? `${medicine.stock}件` : '暂时缺货'}
                </span>
              </div>

              <Divider />

              <div className="quantity-row">
                <span className="label">数量</span>
                <InputNumber
                  min={1}
                  max={medicine.stock}
                  value={quantity}
                  onChange={(val) => setQuantity(val || 1)}
                  disabled={medicine.stock === 0}
                />
              </div>

              <div className="action-buttons">
                <Button
                  size="large"
                  icon={<ShoppingCartOutlined />}
                  onClick={handleAddToCart}
                  disabled={medicine.stock === 0}
                >
                  加入购物车
                </Button>
                <Button
                  type="primary"
                  size="large"
                  onClick={handleBuyNow}
                  disabled={medicine.stock === 0}
                >
                  立即购买
                </Button>
                <Button 
                  size="large" 
                  icon={isFavorite ? <HeartFilled style={{ color: '#ff4d4f' }} /> : <HeartOutlined />}
                  onClick={handleToggleFavorite}
                  loading={favoriteLoading}
                >
                  {isFavorite ? '已收藏' : '收藏'}
                </Button>
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 药品详细说明 */}
      <Card className="medicine-desc-card" title="药品说明" bordered={false}>
        <Descriptions column={1} bordered>
          <Descriptions.Item label="批准文号">{medicine.approvalNumber || '-'}</Descriptions.Item>
          <Descriptions.Item label="功效说明/适应症">
            <Paragraph>{medicine.efficacy || '-'}</Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="用法用量">
            <Paragraph>{medicine.dosage || '-'}</Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="不良反应">
            <Paragraph>{medicine.adverseReactions || '-'}</Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="禁忌">
            <Paragraph>{medicine.contraindications || '-'}</Paragraph>
          </Descriptions.Item>
          <Descriptions.Item label="注意事项">
            <Paragraph>{medicine.precautions || '-'}</Paragraph>
          </Descriptions.Item>
          {medicine.riskTips && (
            <Descriptions.Item label="用药风险提示">
              <Paragraph style={{ color: '#ef4444' }}>{medicine.riskTips}</Paragraph>
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* 返回按钮 */}
      <Button
        className="back-button"
        icon={<LeftOutlined />}
        onClick={() => navigate(-1)}
      >
        返回
      </Button>
    </div>
  )
}

export default MedicineDetail
