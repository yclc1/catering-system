import axios from 'axios'
import type { AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { TOKEN_KEY, REFRESH_TOKEN_KEY } from '@/utils/constants'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let pendingRequests: Array<(token: string) => void> = []

request.interceptors.response.use(
  (response: AxiosResponse) => response.data,
  async (error) => {
    const { response, config } = error

    if (response?.status === 401 && !config._retry) {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (!refreshToken) {
        goLogin()
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((token: string) => {
            config.headers.Authorization = `Bearer ${token}`
            resolve(request(config))
          })
        })
      }

      isRefreshing = true
      config._retry = true

      try {
        const res = await axios.post('/api/auth/refresh', { refresh_token: refreshToken })
        const newToken = res.data.access_token
        localStorage.setItem(TOKEN_KEY, newToken)
        if (res.data.refresh_token) {
          localStorage.setItem(REFRESH_TOKEN_KEY, res.data.refresh_token)
        }
        pendingRequests.forEach((cb) => cb(newToken))
        pendingRequests = []
        config.headers.Authorization = `Bearer ${newToken}`
        return request(config)
      } catch {
        goLogin()
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    const msg = response?.data?.detail || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)

function goLogin() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  router.push('/login')
}

export default request
