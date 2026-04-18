import { useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Home from './pages/Home'
import Login from './pages/Login'
import MedicineList from './pages/Medicine/MedicineList'
import MedicineDetail from './pages/Medicine/MedicineDetail'
import Cart from './pages/Cart/Cart'
import Checkout from './pages/Checkout/Checkout'
import OrderList from './pages/Order/OrderList'
import OrderDetail from './pages/Order/OrderDetail'
import UserCenter from './pages/User/UserCenter'
import Favorites from './pages/User/Favorites'
import Settings from './pages/User/Settings'
import AddressPage from './pages/Address'
import Consult from './pages/Consult'
import useUserStore from './stores/userStore'
import useCartStore from './stores/cartStore'

function App() {
  const { userInfo, isLoggedIn } = useUserStore()
  const switchUser = useCartStore((state) => state.switchUser)

  // 页面刷新时初始化购物车
  useEffect(() => {
    if (isLoggedIn && userInfo?.userId) {
      switchUser(userInfo.userId)
    }
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Home />} />
          <Route path="medicines" element={<MedicineList />} />
          <Route path="medicine/:id" element={<MedicineDetail />} />
          <Route path="cart" element={<Cart />} />
          <Route path="checkout" element={<Checkout />} />
          <Route path="orders" element={<OrderList />} />
          <Route path="order/:id" element={<OrderDetail />} />
          <Route path="user" element={<UserCenter />} />
          <Route path="user/favorites" element={<Favorites />} />
          <Route path="user/settings" element={<Settings />} />
          <Route path="user/address" element={<AddressPage />} />
          <Route path="address" element={<AddressPage />} />
          <Route path="consult" element={<Consult />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
