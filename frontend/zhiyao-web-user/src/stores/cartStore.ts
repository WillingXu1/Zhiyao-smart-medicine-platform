import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface CartItem {
  medicineId: number
  name: string
  specification: string
  price: number
  image: string
  quantity: number
  stock: number
  isPrescription: number
  checked: boolean
}

interface CartState {
  userId: number | null
  items: CartItem[]
  setUserId: (userId: number | null) => void
  addItem: (item: Omit<CartItem, 'checked'>) => void
  removeItem: (medicineId: number) => void
  updateQuantity: (medicineId: number, quantity: number) => void
  toggleCheck: (medicineId: number) => void
  toggleCheckAll: (checked: boolean) => void
  clearCart: () => void
  clearCheckedItems: () => void
  getCheckedItems: () => CartItem[]
  getTotalPrice: () => number
  getTotalCount: () => number
  switchUser: (userId: number | null) => void
}

// 从 localStorage 加载指定用户的购物车
const loadUserCart = (userId: number | null): CartItem[] => {
  if (!userId) return []
  try {
    const data = localStorage.getItem(`cart-storage-${userId}`)
    if (data) {
      const parsed = JSON.parse(data)
      return parsed.state?.items || []
    }
  } catch (e) {
    console.error('Failed to load cart:', e)
  }
  return []
}

// 保存指定用户的购物车
const saveUserCart = (userId: number | null, items: CartItem[]) => {
  if (!userId) return
  try {
    const data = JSON.stringify({ state: { userId, items } })
    localStorage.setItem(`cart-storage-${userId}`, data)
  } catch (e) {
    console.error('Failed to save cart:', e)
  }
}

const useCartStore = create<CartState>()(
  (set, get) => ({
    userId: null,
    items: [],

    setUserId: (userId) => {
      set({ userId })
    },

    switchUser: (userId) => {
      // 保存当前用户购物车
      const currentUserId = get().userId
      if (currentUserId) {
        saveUserCart(currentUserId, get().items)
      }
      // 加载新用户购物车
      const items = loadUserCart(userId)
      set({ userId, items })
    },

    addItem: (item) => {
      const userId = get().userId
      if (!userId) return // 未登录不允许添加
      set((state) => {
        const existingItem = state.items.find((i) => i.medicineId === item.medicineId)
        let newItems: CartItem[]
        if (existingItem) {
          newItems = state.items.map((i) =>
            i.medicineId === item.medicineId
              ? { ...i, quantity: Math.min(i.quantity + item.quantity, i.stock) }
              : i
          )
        } else {
          newItems = [...state.items, { ...item, checked: true }]
        }
        saveUserCart(userId, newItems)
        return { items: newItems }
      })
    },

    removeItem: (medicineId) => {
      const userId = get().userId
      set((state) => {
        const newItems = state.items.filter((i) => i.medicineId !== medicineId)
        if (userId) saveUserCart(userId, newItems)
        return { items: newItems }
      })
    },

    updateQuantity: (medicineId, quantity) => {
      const userId = get().userId
      set((state) => {
        const newItems = state.items.map((i) =>
          i.medicineId === medicineId ? { ...i, quantity: Math.max(1, Math.min(quantity, i.stock)) } : i
        )
        if (userId) saveUserCart(userId, newItems)
        return { items: newItems }
      })
    },

    toggleCheck: (medicineId) => {
      const userId = get().userId
      set((state) => {
        const newItems = state.items.map((i) =>
          i.medicineId === medicineId ? { ...i, checked: !i.checked } : i
        )
        if (userId) saveUserCart(userId, newItems)
        return { items: newItems }
      })
    },

    toggleCheckAll: (checked) => {
      const userId = get().userId
      set((state) => {
        const newItems = state.items.map((i) => ({ ...i, checked }))
        if (userId) saveUserCart(userId, newItems)
        return { items: newItems }
      })
    },

    clearCart: () => {
      const userId = get().userId
      if (userId) saveUserCart(userId, [])
      set({ items: [] })
    },

    clearCheckedItems: () => {
      const userId = get().userId
      set((state) => {
        const newItems = state.items.filter((i) => !i.checked)
        if (userId) saveUserCart(userId, newItems)
        return { items: newItems }
      })
    },

    getCheckedItems: () => {
      return get().items.filter((i) => i.checked)
    },

    getTotalPrice: () => {
      return get().items
        .filter((i) => i.checked)
        .reduce((total, item) => total + item.price * item.quantity, 0)
    },

    getTotalCount: () => {
      return get().items.reduce((total, item) => total + item.quantity, 0)
    },
  })
)

export default useCartStore
