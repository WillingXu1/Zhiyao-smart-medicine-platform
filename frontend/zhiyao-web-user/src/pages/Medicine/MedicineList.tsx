import { useEffect, useState } from 'react'
import { Card, Row, Col, Input, Select, Pagination, Tag, Spin, Empty, Typography } from 'antd'
import { MedicineBoxOutlined, SearchOutlined } from '@ant-design/icons'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { searchMedicines, getCategories } from '../../services/medicine'
import './MedicineList.css'

const { Title, Text } = Typography

interface Medicine {
  id: number
  name: string
  specification: string
  price: number
  originalPrice: number
  image: string
  isPrescription: number
  manufacturer: string
  stock: number
}

interface Category {
  id: number
  name: string
}

const MedicineList = () => {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const [loading, setLoading] = useState(true)
  const [medicines, setMedicines] = useState<Medicine[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [total, setTotal] = useState(0)

  const [keyword, setKeyword] = useState(searchParams.get('keyword') || '')
  const [categoryId, setCategoryId] = useState<number | undefined>(
    searchParams.get('categoryId') ? Number(searchParams.get('categoryId')) : undefined
  )
  const [sortBy, setSortBy] = useState('default')
  const [pageNum, setPageNum] = useState(1)
  const pageSize = 12

  useEffect(() => {
    fetchCategories()
    // 初始化时从 URL 读取参数
    const urlKeyword = searchParams.get('keyword') || ''
    const urlCategoryId = searchParams.get('categoryId') ? Number(searchParams.get('categoryId')) : undefined
    if (urlKeyword) setKeyword(urlKeyword)
    if (urlCategoryId) setCategoryId(urlCategoryId)
  }, [])

  // 监听URL参数变化，同步到状态
  useEffect(() => {
    const newKeyword = searchParams.get('keyword') || ''
    const newCategoryId = searchParams.get('categoryId') ? Number(searchParams.get('categoryId')) : undefined
    setKeyword(newKeyword)
    setCategoryId(newCategoryId)
    setPageNum(1)
  }, [searchParams])

  // 当筛选条件变化时重新获取数据
  useEffect(() => {
    fetchMedicines()
  }, [keyword, categoryId, sortBy, pageNum])

  const fetchCategories = async () => {
    try {
      const res = await getCategories()
      const categoryList = res.data || []
      console.log('分类数据:', categoryList) // 调试日志
      setCategories(categoryList)
    } catch (error) {
      console.error('获取分类失败:', error)
    }
  }

  const fetchMedicines = async () => {
    try {
      setLoading(true)
      const params: Record<string, unknown> = {
        pageNum,
        pageSize,
      }
      if (keyword) params.keyword = keyword
      if (categoryId) params.categoryId = categoryId
      if (sortBy !== 'default') {
        const [sort, order] = sortBy.split('_')
        params.sortBy = sort
        params.sortOrder = order
      }

      console.log('搜索参数:', params) // 调试日志
      const res = await searchMedicines(params)
      console.log('搜索结果:', res.data) // 调试日志
      // 后端返回 PageResult，字段是 records 不是 list
      setMedicines(res.data?.records || [])
      setTotal(res.data?.total || 0)
    } catch (error) {
      console.error('获取药品列表失败:', error)
      setMedicines([])
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    setPageNum(1)
    const params: Record<string, string> = {}
    if (keyword) params.keyword = keyword
    if (categoryId) params.categoryId = String(categoryId)
    setSearchParams(params)
    // 不需要手动调用fetchMedicines，useEffect会监听到变化并触发
  }

  const handleCategoryChange = (value: number | undefined) => {
    console.log('分类变更:', value) // 调试日志
    setCategoryId(value)
    setPageNum(1)
    // 更新URL参数
    const params: Record<string, string> = {}
    if (keyword) params.keyword = keyword
    if (value !== undefined && value !== null) params.categoryId = String(value)
    setSearchParams(params)
  }

  const handleSortChange = (value: string) => {
    setSortBy(value)
    setPageNum(1)
  }

  const handleMedicineClick = (id: number) => {
    navigate(`/medicine/${id}`)
  }

  return (
    <div className="medicine-list-page">
      {/* 搜索栏 */}
      <Card className="search-bar" bordered={false}>
        <div className="search-row">
          <Input
            className="search-input"
            placeholder="搜索药品名称、症状、功效"
            prefix={<SearchOutlined />}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={handleSearch}
            allowClear
          />
          <Select
            className="category-select"
            placeholder="药品分类"
            allowClear
            value={categoryId}
            onChange={handleCategoryChange}
            options={categories.map(c => ({ label: c.name, value: c.id }))}
          />
          <Select
            className="sort-select"
            value={sortBy}
            onChange={handleSortChange}
            options={[
              { label: '综合排序', value: 'default' },
              { label: '价格从低到高', value: 'price_asc' },
              { label: '价格从高到低', value: 'price_desc' },
              { label: '销量优先', value: 'sales_desc' },
            ]}
          />
        </div>
      </Card>

      {/* 药品列表 */}
      <Card className="medicine-list-card" bordered={false}>
        <Spin spinning={loading}>
          {medicines.length > 0 ? (
            <>
              <Row gutter={[16, 16]}>
                {medicines.map((med) => (
                  <Col xs={24} sm={12} md={8} lg={6} key={med.id}>
                    <Card
                      className="medicine-card"
                      hoverable
                      onClick={() => handleMedicineClick(med.id)}
                      cover={
                        med.image ? (
                          <img alt={med.name} src={med.image} className="medicine-cover" />
                        ) : (
                          <div className="medicine-cover-placeholder">
                            <MedicineBoxOutlined style={{ fontSize: 64, color: '#10B981' }} />
                          </div>
                        )
                      }
                    >
                      <div className="medicine-card-body">
                        <div className="medicine-tags">
                          {med.isPrescription === 1 && <Tag color="red">处方药</Tag>}
                          {med.isPrescription === 0 && <Tag color="green">非处方药</Tag>}
                          {med.stock <= 10 && med.stock > 0 && <Tag color="orange">库存紧张</Tag>}
                          {med.stock === 0 && <Tag color="default">暂时缺货</Tag>}
                        </div>
                        <Title level={5} className="medicine-name" ellipsis={{ rows: 2 }}>
                          {med.name}
                        </Title>
                        <Text type="secondary" className="medicine-spec">
                          {med.specification}
                        </Text>
                        <Text type="secondary" className="medicine-manufacturer" ellipsis>
                          {med.manufacturer}
                        </Text>
                        <div className="medicine-price-row">
                          <span className="current-price">¥{med.price?.toFixed(2)}</span>
                          {med.originalPrice && med.originalPrice > med.price && (
                            <span className="original-price">¥{med.originalPrice.toFixed(2)}</span>
                          )}
                        </div>
                      </div>
                    </Card>
                  </Col>
                ))}
              </Row>
              <div className="pagination-wrapper">
                <Pagination
                  current={pageNum}
                  pageSize={pageSize}
                  total={total}
                  showSizeChanger={false}
                  showQuickJumper
                  showTotal={(total) => `共 ${total} 件药品`}
                  onChange={(page) => setPageNum(page)}
                />
              </div>
            </>
          ) : (
            <Empty description="暂无药品数据" />
          )}
        </Spin>
      </Card>
    </div>
  )
}

export default MedicineList
