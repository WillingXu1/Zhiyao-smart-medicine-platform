import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import UserManage from './pages/User'
import MerchantManage from './pages/Merchant'
import MedicineManage from './pages/Medicine'
import OrderManage from './pages/Order'
import RiderManage from './pages/Rider'
import Settings from './pages/Settings'
import useAdminStore from './stores/adminStore'

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const isLoggedIn = useAdminStore((state) => state.isLoggedIn)
  return isLoggedIn ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><MainLayout /></PrivateRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="users" element={<UserManage />} />
          <Route path="merchants" element={<MerchantManage />} />
          <Route path="medicines" element={<MedicineManage />} />
          <Route path="orders" element={<OrderManage />} />
          <Route path="riders" element={<RiderManage />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
