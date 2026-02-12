import { Card, Row, Col, Avatar, Typography, Menu, Button, message } from 'antd'
import {
  UserOutlined,
  ShoppingCartOutlined,
  FileTextOutlined,
  HeartOutlined,
  EnvironmentOutlined,
  SettingOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { useNavigate, Outlet, useLocation } from 'react-router-dom'
import useUserStore from '../../stores/userStore'
import './UserCenter.css'

const { Title, Text } = Typography

const UserCenter = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { userInfo, isLoggedIn, logout } = useUserStore()

  if (!isLoggedIn) {
    return (
      <div className="user-center-page">
        <Card className="login-prompt-card" bordered={false}>
          <Title level={4}>请先登录</Title>
          <Button type="primary" onClick={() => navigate('/login')}>
            去登录
          </Button>
        </Card>
      </div>
    )
  }

  const handleLogout = () => {
    logout()
    message.success('已退出登录')
    navigate('/')
  }

  const menuItems = [
    {
      key: '/user',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: '/orders',
      icon: <FileTextOutlined />,
      label: '我的订单',
    },
    {
      key: '/cart',
      icon: <ShoppingCartOutlined />,
      label: '购物车',
    },
    {
      key: '/user/favorites',
      icon: <HeartOutlined />,
      label: '我的收藏',
    },
    {
      key: '/user/address',
      icon: <EnvironmentOutlined />,
      label: '收货地址',
    },
    {
      key: '/user/settings',
      icon: <SettingOutlined />,
      label: '账号设置',
    },
  ]

  return (
    <div className="user-center-page">
      <Row gutter={24}>
        <Col xs={24} lg={6}>
          {/* 用户信息卡片 */}
          <Card className="user-card" bordered={false}>
            <div className="user-info">
              <Avatar size={80} icon={<UserOutlined />} src={userInfo?.avatar} />
              <div className="user-detail">
                <Title level={4} className="user-name">
                  {userInfo?.nickname || userInfo?.username}
                </Title>
                <Text type="secondary">{userInfo?.username}</Text>
              </div>
            </div>
          </Card>

          {/* 侧边菜单 */}
          <Card className="menu-card" bordered={false}>
            <Menu
              mode="vertical"
              selectedKeys={[location.pathname]}
              items={menuItems}
              onClick={({ key }) => navigate(key)}
            />
            <div className="logout-wrapper">
              <Button
                type="text"
                danger
                icon={<LogoutOutlined />}
                onClick={handleLogout}
                block
              >
                退出登录
              </Button>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={18}>
          {/* 右侧内容区 */}
          <Card className="content-card" bordered={false}>
            {location.pathname === '/user' ? (
              <div className="user-profile">
                <Title level={4}>个人信息</Title>
                <div className="profile-form">
                  <div className="profile-row">
                    <span className="label">用户名</span>
                    <span className="value">{userInfo?.username}</span>
                  </div>
                  <div className="profile-row">
                    <span className="label">昵称</span>
                    <span className="value">{userInfo?.nickname || '-'}</span>
                  </div>
                  <div className="profile-row">
                    <span className="label">用户ID</span>
                    <span className="value">{userInfo?.userId}</span>
                  </div>
                  <div className="profile-row">
                    <span className="label">账号类型</span>
                    <span className="value">普通用户</span>
                  </div>
                </div>
                <Button type="primary" style={{ marginTop: 24 }} onClick={() => navigate('/user/settings')}>
                  编辑资料
                </Button>
              </div>
            ) : (
              <Outlet />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default UserCenter
