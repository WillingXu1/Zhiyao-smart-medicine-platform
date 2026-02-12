import { useEffect, useState } from 'react'
import { Card, Row, Col, Carousel, Typography, Tag, Spin } from 'antd'
import { 
  MedicineBoxOutlined, 
  ThunderboltOutlined,
  SafetyCertificateOutlined,
  TruckOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { getCategories, getHotMedicines } from '../services/medicine'
import './Home.css'

const { Title, Text } = Typography

// 轮播图数据
const banners = [
  { id: 1, title: '冬季健康守护', desc: '感冒药品特惠专区', color: '#10B981' },
  { id: 2, title: '慢病管理专区', desc: '长期用药更优惠', color: '#3B82F6' },
  { id: 3, title: '新用户专享', desc: '首单立减20元', color: '#F59E0B' },
]

interface Category {
  id: number
  name: string
  icon: string
}

interface Medicine {
  id: number
  name: string
  specification: string
  price: number
  originalPrice: number
  image: string
  isPrescription: number
}

const defaultCategories: Category[] = [
  { id: 1, name: '感冒发烧', icon: '🤒' },
  { id: 2, name: '肠胃用药', icon: '💊' },
  { id: 3, name: '皮肤用药', icon: '🧴' },
  { id: 4, name: '心脑血管', icon: '❤️' },
  { id: 5, name: '糖尿病用药', icon: '🩸' },
  { id: 6, name: '维生素', icon: '🍊' },
  { id: 7, name: '儿童用药', icon: '👶' },
  { id: 8, name: '更多分类', icon: '📋' },
]

const Home: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [categories, setCategories] = useState<Category[]>(defaultCategories)
  const [hotMedicines, setHotMedicines] = useState<Medicine[]>([])

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [catRes, hotRes] = await Promise.all([
        getCategories().catch(() => ({ data: [] })),
        getHotMedicines(8).catch(() => ({ data: [] }))
      ])
      if (catRes.data?.length > 0) {
        setCategories(catRes.data)
      }
      if (hotRes.data?.length > 0) {
        setHotMedicines(hotRes.data)
      }
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCategoryClick = (categoryId: number) => {
    navigate(`/medicines?categoryId=${categoryId}`)
  }

  const handleMedicineClick = (id: number) => {
    navigate(`/medicine/${id}`)
  }
  return (
    <div className="home-page">
      {/* 特色服务 */}
      <div className="service-bar">
        <div className="service-item">
          <ThunderboltOutlined className="service-icon" />
          <span>30分钟送达</span>
        </div>
        <div className="service-item">
          <SafetyCertificateOutlined className="service-icon" />
          <span>正品保障</span>
        </div>
        <div className="service-item">
          <MedicineBoxOutlined className="service-icon" />
          <span>专业药师</span>
        </div>
        <div className="service-item">
          <TruckOutlined className="service-icon" />
          <span>免费配送</span>
        </div>
      </div>

      <div className="home-content">
        {/* 轮播图 */}
        <Carousel autoplay className="banner-carousel">
          {banners.map(banner => (
            <div key={banner.id}>
              <div className="banner-item" style={{ background: banner.color }}>
                <Title level={2} style={{ color: '#fff', margin: 0 }}>{banner.title}</Title>
                <Text style={{ color: 'rgba(255,255,255,0.9)', fontSize: 16 }}>{banner.desc}</Text>
              </div>
            </div>
          ))}
        </Carousel>

        {/* 药品分类 */}
        <Card className="category-card" title="药品分类" bordered={false}>
          <Row gutter={[16, 16]}>
            {categories.map(cat => (
              <Col span={6} key={cat.id}>
                <div className="category-item" onClick={() => handleCategoryClick(cat.id)}>
                  <span className="category-icon">{cat.icon}</span>
                  <span className="category-name">{cat.name}</span>
                </div>
              </Col>
            ))}
          </Row>
        </Card>

        {/* 热销药品 */}
        <Card className="hot-medicine-card" title="热销药品" bordered={false}>
          <Spin spinning={loading}>
            <Row gutter={[16, 16]}>
              {hotMedicines.length > 0 ? hotMedicines.map(med => (
                <Col xs={12} sm={8} md={6} lg={4} xl={3} key={med.id}>
                  <Card className="medicine-item" hoverable onClick={() => handleMedicineClick(med.id)}>
                    <div className="medicine-img">
                      {med.image ? (
                        <img src={med.image} alt={med.name} />
                      ) : (
                        <MedicineBoxOutlined style={{ fontSize: 36, color: '#10B981' }} />
                      )}
                    </div>
                    <div className="medicine-info">
                      {med.isPrescription === 1 && <Tag color="red" style={{ fontSize: 10 }}>处方</Tag>}
                      {med.isPrescription === 0 && <Tag color="green" style={{ fontSize: 10 }}>非处方</Tag>}
                      <Title level={5} className="medicine-name">{med.name}</Title>
                      <Text type="secondary" className="medicine-spec">{med.specification}</Text>
                      <div className="medicine-price">
                        <span className="current-price">¥{med.price}</span>
                        {med.originalPrice && <span className="original-price">¥{med.originalPrice}</span>}
                      </div>
                    </div>
                  </Card>
                </Col>
              )) : (
                <Col span={24}>
                  <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                    暂无热销药品
                  </div>
                </Col>
              )}
            </Row>
          </Spin>
        </Card>
      </div>
    </div>
  )
}

export default Home
