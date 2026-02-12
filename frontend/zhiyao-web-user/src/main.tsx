import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './styles/index.css'

// Ant Design 主题配置 - 健康绿色主题
const theme = {
  token: {
    colorPrimary: '#10B981', // 翠绿色 - 健康、生命力
    colorSuccess: '#10B981',
    colorInfo: '#3B82F6',    // 科技蓝 - 专业、可信赖
    colorWarning: '#F59E0B', // 警示橙 - 用药提醒
    colorError: '#EF4444',
    borderRadius: 8,
    fontSize: 14,
  },
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider locale={zhCN} theme={theme}>
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)
