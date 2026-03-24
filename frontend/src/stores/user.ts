import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import { TOKEN_KEY, REFRESH_TOKEN_KEY } from '@/utils/constants'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const userInfo = ref<any>(null)
  const permissions = ref<string[]>([])

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.roles?.includes('admin'))

  function hasPermission(perm: string): boolean {
    if (isAdmin.value) return true
    return permissions.value.includes(perm)
  }

  async function login(username: string, password: string) {
    const res: any = await authApi.login({ username, password })
    token.value = res.access_token
    localStorage.setItem(TOKEN_KEY, res.access_token)
    localStorage.setItem(REFRESH_TOKEN_KEY, res.refresh_token)
    await fetchUserInfo()
  }

  async function fetchUserInfo() {
    try {
      const res: any = await authApi.me()
      userInfo.value = res
      permissions.value = res.permissions || []
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    permissions.value = []
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    router.push('/login')
  }

  return { token, userInfo, permissions, isLoggedIn, isAdmin, hasPermission, login, fetchUserInfo, logout }
})
