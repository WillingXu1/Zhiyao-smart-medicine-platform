import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AdminInfo {
  userId: number
  username: string
  nickname: string
  name?: string
  avatar?: string
  email?: string
  phone?: string
  role: number
}

interface AdminState {
  token: string | null
  adminInfo: AdminInfo | null
  isLoggedIn: boolean
  login: (token: string, info: AdminInfo) => void
  logout: () => void
}

const useAdminStore = create<AdminState>()(
  persist(
    (set) => ({
      token: null,
      adminInfo: null,
      isLoggedIn: false,
      login: (token, adminInfo) => {
        localStorage.setItem('admin_token', token)
        set({ token, adminInfo, isLoggedIn: true })
      },
      logout: () => {
        localStorage.removeItem('admin_token')
        set({ token: null, adminInfo: null, isLoggedIn: false })
      },
    }),
    { name: 'admin-storage' }
  )
)

export default useAdminStore
