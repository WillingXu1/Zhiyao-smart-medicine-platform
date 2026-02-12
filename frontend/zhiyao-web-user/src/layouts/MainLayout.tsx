import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Input, Button, Avatar, Dropdown, Badge, message } from 'antd'
import { 
  SearchOutlined, 
  ShoppingCartOutlined, 
  UserOutlined,
  HomeOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
  CustomerServiceOutlined
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import useUserStore from '../stores/userStore'
import useCartStore from '../stores/cartStore'
import './MainLayout.css'

const { Header, Content, Footer } = Layout

const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { isLoggedIn, userInfo, logout } = useUserStore()
  const cartCount = useCartStore((state) => state.getTotalCount())

  const menuItems: MenuProps['items'] = [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/medicines', icon: <MedicineBoxOutlined />, label: '药品分类' },
    { key: '/orders', icon: <FileTextOutlined />, label: '我的订单' },
    { key: '/consult', icon: <CustomerServiceOutlined />, label: '用药咨询' },
  ]

  const userMenuItems: MenuProps['items'] = isLoggedIn
    ? [
        { key: 'profile', label: '个人中心' },
        { key: 'orders', label: '我的订单' },
        { type: 'divider' },
        { key: 'logout', label: '退出登录', danger: true },
      ]
    : [
        { key: 'login', label: '登录' },
        { key: 'register', label: '注册' },
      ]

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key)
  }

  const handleUserMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      logout()
      message.success('已退出登录')
      navigate('/')
    } else if (key === 'profile') {
      navigate('/user')
    } else if (key === 'orders') {
      navigate('/orders')
    } else if (key === 'login' || key === 'register') {
      navigate('/login')
    }
  }

  const handleSearch = (value: string) => {
    if (value.trim()) {
      navigate(`/medicines?keyword=${encodeURIComponent(value.trim())}`)
    }
  }

  return (
    <Layout className="main-layout">
      <Header className="header">
        <div className="header-content">
          <div className="logo" onClick={() => navigate('/')}>
            <MedicineBoxOutlined className="logo-icon" />
            <span className="logo-text">知药</span>
          </div>
          
          <div className="search-box">
            <Input.Search
              placeholder="搜索药品名称、功效..." 
              prefix={<SearchOutlined />}
              size="large"
              className="search-input"
              onSearch={handleSearch}
              enterButton
            />
          </div>

          <Menu
            mode="horizontal"
            items={menuItems}
            onClick={handleMenuClick}
            className="nav-menu"
            selectedKeys={[location.pathname]}
          />

          <div className="header-actions">
            <Badge count={cartCount} size="small">
              <Button 
                type="text" 
                icon={<ShoppingCartOutlined />}
                className="cart-btn"
                onClick={() => navigate('/cart')}
              >
                购物车
              </Button>
            </Badge>

            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }} placement="bottomRight">
              <div className="user-trigger">
                <Avatar icon={<UserOutlined />} src={userInfo?.avatar} className="user-avatar" />
                {isLoggedIn && <span className="user-name">{userInfo?.nickname || userInfo?.username}</span>}
              </div>
            </Dropdown>
          </div>
        </div>
      </Header>

      <Content className="content">
        <Outlet />
      </Content>

      <Footer className="footer">
        <div className="footer-content">
          <p>知药 - 您的健康用药专家</p>
          <p>© 2026 知药 All Rights Reserved</p>
        </div>
      </Footer>
    </Layout>
  )
}

export default MainLayout
