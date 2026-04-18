import { useState, useEffect } from 'react'
import { Card, Row, Col, Button, Empty, message, Typography, Tag, Spin } from 'antd'
import { HeartFilled, ShoppingCartOutlined, DeleteOutlined, MedicineBoxOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import useCartStore from '../../stores/cartStore'
import { getFavorites, removeFavorite } from '../../services/user'
import './Favorites.css'

const { Title, Text } = Typography

interface FavoriteItem {
  id: number
  medicineId: number
  name: string
  image?: string
  price: number
  originalPrice?: number
  specification?: string
  merchantName?: string
  stock: number
  status: number
  isPrescription: number
}

const Favorites = () => {
  const navigate = useNavigate()
  const [favorites, setFavorites] = useState<FavoriteItem[]>([])
  const [loading, setLoading] = useState(true)
  const addToCart = useCartStore((state) => state.addItem)

  useEffect(() => {
    fetchFavorites()
  }, [])

  const fetchFavorites = async () => {
    try {
      setLoading(true)
      const res: any = await getFavorites()
      setFavorites(res.data || res || [])
    } catch (error) {
      console.error('获取收藏列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRemove = async (medicineId: number) => {
    try {
      await removeFavorite(medicineId)
      setFavorites(favorites.filter(item => item.medicineId !== medicineId))
      message.success('已取消收藏')
    } catch (error) {
      message.error('取消收藏失败')
    }
  }

  const handleAddToCart = (item: FavoriteItem) => {
    if (item.status === 0 || item.stock === 0) {
      message.warning('该商品已下架或缺货')
      return
    }
    addToCart({
      medicineId: item.medicineId,
      name: item.name,
      image: item.image || '',
      price: item.price,
      quantity: 1,
      stock: item.stock,
      specification: item.specification || '',
      isPrescription: item.isPrescription,
    })
    message.success('已加入购物车')
  }

  return (
    <div className="favorites-page">
      <Card 
        title={
          <span>
            我的收藏
            <Text type="secondary" style={{ marginLeft: 8, fontSize: 14, fontWeight: 'normal' }}>
              共 {favorites.length} 件商品
            </Text>
          </span>
        }
        bordered={false}
        className="favorites-card"
      >
        <Spin spinning={loading}>
          {favorites.length === 0 && !loading ? (
          <Empty 
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="暂无收藏商品"
            style={{ padding: '40px 0' }}
          >
            <Button type="primary" onClick={() => navigate('/medicines')} className="go-shop-btn">
              去逛逛
            </Button>
          </Empty>
        ) : (
          <Row gutter={[16, 16]}>
            {favorites.map((item) => (
              <Col xs={24} sm={12} lg={8} key={item.id}>
                <div className={`favorite-item ${item.status === 0 ? 'unavailable' : ''}`}>
                  <div className="item-image" onClick={() => navigate(`/medicine/${item.medicineId}`)}>
                    {item.image ? (
                      <img src={item.image} alt={item.name} />
                    ) : (
                      <MedicineBoxOutlined className="placeholder-icon" />
                    )}
                    {item.status === 0 && <div className="unavailable-mask">已下架</div>}
                  </div>
                  <div className="item-info">
                    <div className="item-name" onClick={() => navigate(`/medicine/${item.medicineId}`)}>
                      {item.name}
                    </div>
                    <div className="item-spec">{item.specification || ''}</div>
                    <div className="item-price">
                      <span className="current-price">¥{item.price?.toFixed(2)}</span>
                      {item.originalPrice && item.originalPrice > item.price && (
                        <span className="original-price">¥{item.originalPrice.toFixed(2)}</span>
                      )}
                    </div>
                  </div>
                  <div className="item-actions">
                    <Button 
                      type="primary"
                      size="small"
                      icon={<ShoppingCartOutlined />}
                      onClick={() => handleAddToCart(item)}
                      disabled={item.status === 0 || item.stock === 0}
                      className="cart-btn"
                    >
                      加入购物车
                    </Button>
                    <Button 
                      type="text"
                      size="small"
                      danger 
                      icon={<DeleteOutlined />}
                      onClick={() => handleRemove(item.medicineId)}
                    >
                      取消
                    </Button>
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        )}
      </Spin>
    </Card>
    </div>
  )
}

export default Favorites
