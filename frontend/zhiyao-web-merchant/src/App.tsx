import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import MedicineManage from './pages/Medicine'
import OrderManage from './pages/Order'
import Settings from './pages/Settings'
import useMerchantStore from './stores/merchantStore'

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const isLoggedIn = useMerchantStore((state) => state.isLoggedIn)
  return isLoggedIn ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/" element={<PrivateRoute><MainLayout /></PrivateRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="medicines" element={<MedicineManage />} />
          <Route path="orders" element={<OrderManage />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
