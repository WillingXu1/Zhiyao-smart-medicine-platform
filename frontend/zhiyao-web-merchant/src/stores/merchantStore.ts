import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface MerchantInfo {
  merchantId: number
  name: string
  phone: string
  address: string
  status: number
}

interface MerchantState {
  token: string | null
  merchantInfo: MerchantInfo | null
  isLoggedIn: boolean
  login: (token: string, info: MerchantInfo) => void
  logout: () => void
}

const useMerchantStore = create<MerchantState>()(
  persist(
    (set) => ({
      token: null,
      merchantInfo: null,
      isLoggedIn: false,
      login: (token, merchantInfo) => {
        localStorage.setItem('merchant_token', token)
        set({ token, merchantInfo, isLoggedIn: true })
      },
      logout: () => {
        localStorage.removeItem('merchant_token')
        set({ token: null, merchantInfo: null, isLoggedIn: false })
      },
    }),
    { name: 'merchant-storage' }
  )
)

export default useMerchantStore
