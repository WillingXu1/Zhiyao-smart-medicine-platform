import { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, message } from 'antd'
import {
  DashboardOutlined,
  UserOutlined,
  ShopOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
  SettingOutlined,
  LogoutOutlined,
  SafetyCertificateOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import useAdminStore from '../stores/adminStore'
import './MainLayout.css'

const { Header, Sider, Content } = Layout

const MainLayout = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const { adminInfo, logout } = useAdminStore()

  const menuItems: MenuProps['items'] = [
    { key: '/', icon: <DashboardOutlined />, label: '数据统计' },
    { key: '/users', icon: <UserOutlined />, label: '用户管理' },
    { key: '/merchants', icon: <ShopOutlined />, label: '商家管理' },
    { key: '/riders', icon: <TeamOutlined />, label: '骑手管理' },
    { key: '/medicines', icon: <MedicineBoxOutlined />, label: '药品管理' },
    { key: '/orders', icon: <FileTextOutlined />, label: '订单管理' },
    { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
  ]

  const userMenuItems: MenuProps['items'] = [
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
  ]

  const handleMenuClick: MenuProps['onClick'] = ({ key }) => navigate(key)

  const handleUserMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      logout()
      message.success('已退出登录')
      navigate('/login')
    }
  }

  return (
    <Layout className="admin-layout">
      <Sider trigger={null} collapsible collapsed={collapsed} theme="dark" className="sider">
        <div className="logo">
          <SafetyCertificateOutlined className="logo-icon" />
          {!collapsed && <span className="logo-text">管理后台</span>}
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={[location.pathname]} items={menuItems} onClick={handleMenuClick} />
      </Sider>
      <Layout>
        <Header className="header">
          <div className="header-left">
            {collapsed ? <MenuUnfoldOutlined className="trigger" onClick={() => setCollapsed(false)} />
              : <MenuFoldOutlined className="trigger" onClick={() => setCollapsed(true)} />}
          </div>
          <div className="header-right">
            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }}>
              <div className="user-info">
                <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1e3a5f' }} />
                <span className="user-name">{adminInfo?.nickname || adminInfo?.username || '管理员'}</span>
              </div>
            </Dropdown>
          </div>
        </Header>
        <Content className="content"><Outlet /></Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
