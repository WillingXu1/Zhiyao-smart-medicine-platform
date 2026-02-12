import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, message } from 'antd'
import {
  DashboardOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
  SettingOutlined,
  LogoutOutlined,
  ShopOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import useMerchantStore from '../stores/merchantStore'
import './MainLayout.css'

const { Header, Sider, Content } = Layout

const MainLayout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const { merchantInfo, logout } = useMerchantStore()

  const menuItems: MenuProps['items'] = [
    { key: '/', icon: <DashboardOutlined />, label: '工作台' },
    { key: '/medicines', icon: <MedicineBoxOutlined />, label: '药品管理' },
    { key: '/orders', icon: <FileTextOutlined />, label: '订单管理' },
    { key: '/settings', icon: <SettingOutlined />, label: '店铺设置' },
  ]

  const userMenuItems: MenuProps['items'] = [
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
  ]

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => {
    navigate(key)
  }

  const handleUserMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      logout()
      message.success('已退出登录')
      navigate('/login')
    }
  }

  return (
    <Layout className="merchant-layout">
      <Sider trigger={null} collapsible collapsed={collapsed} theme="light" className="sider">
        <div className="logo">
          <ShopOutlined className="logo-icon" />
          {!collapsed && <span className="logo-text">商家中心</span>}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header className="header">
          <div className="header-left">
            {collapsed ? (
              <MenuUnfoldOutlined className="trigger" onClick={() => setCollapsed(false)} />
            ) : (
              <MenuFoldOutlined className="trigger" onClick={() => setCollapsed(true)} />
            )}
          </div>
          <div className="header-right">
            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }}>
              <div className="user-info">
                <Avatar icon={<ShopOutlined />} style={{ backgroundColor: '#667eea' }} />
                <span className="user-name">{merchantInfo?.name || '商家'}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content className="content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
