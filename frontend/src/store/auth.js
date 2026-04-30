import { defineStore } from 'pinia'
import { authApi } from '@/utils/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('rg_user') || 'null'),
    token: localStorage.getItem('rg_token') || null,
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin',
    isAnalyst: (s) => ['admin', 'analyst'].includes(s.user?.role),
    isInvestigator: (s) => ['admin', 'investigator'].includes(s.user?.role),
  },
  actions: {
    async login(email, password) {
      const { data } = await authApi.login(email, password)
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem('rg_token', data.access_token)
      localStorage.setItem('rg_user', JSON.stringify(data.user))
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('rg_token')
      localStorage.removeItem('rg_user')
    },
  },
})
