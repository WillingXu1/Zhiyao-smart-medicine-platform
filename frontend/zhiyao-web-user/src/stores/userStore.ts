import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import useCartStore from './cartStore'

interface UserInfo {
  userId: number
  username: string
  nickname: string
  avatar: string | null
  email: string | null
  role: number
}

interface UserState {
  token: string | null
  userInfo: UserInfo | null
  isLoggedIn: boolean
  setToken: (token: string) => void
  setUserInfo: (userInfo: UserInfo) => void
  login: (token: string, userInfo: UserInfo) => void
  logout: () => void
}

const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      token: null,
      userInfo: null,
      isLoggedIn: false,

      setToken: (token: string) => {
        localStorage.setItem('token', token)
        set({ token, isLoggedIn: true })
      },

      setUserInfo: (userInfo: UserInfo) => {
        set({ userInfo })
      },

      login: (token: string, userInfo: UserInfo) => {
        localStorage.setItem('token', token)
        set({ token, userInfo, isLoggedIn: true })
        // 切换购物车到当前用户
        useCartStore.getState().switchUser(userInfo.userId)
      },

      logout: () => {
        localStorage.removeItem('token')
        // 清空购物车用户
        useCartStore.getState().switchUser(null)
        set({ token: null, userInfo: null, isLoggedIn: false })
      },
    }),
    {
      name: 'user-storage',
      partialize: (state) => ({ token: state.token, userInfo: state.userInfo, isLoggedIn: state.isLoggedIn }),
    }
  )
)

export default useUserStore
