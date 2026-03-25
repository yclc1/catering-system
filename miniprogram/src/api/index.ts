import { request } from '../utils/request'

// 登录
export const login = (data: { username: string; password: string }) =>
  request({ url: '/api/auth/login', method: 'POST', data })

// 用餐登记
export const createMeal = (data: any) =>
  request({ url: '/api/meals', method: 'POST', data })

export const getMeals = (params?: any) =>
  request({ url: '/api/meals', method: 'GET', data: params })

// 费用审批
export const getExpenses = (params?: any) =>
  request({ url: '/api/expenses', method: 'GET', data: params })

export const approveExpense = (id: number, data: any) =>
  request({ url: `/api/expenses/${id}/approve`, method: 'POST', data })

// 采购
export const getPurchases = (params?: any) =>
  request({ url: '/api/purchases', method: 'GET', data: params })

export const createPurchase = (data: any) =>
  request({ url: '/api/purchases', method: 'POST', data })

// 库存
export const getInventory = (params?: any) =>
  request({ url: '/api/inventory', method: 'GET', data: params })

// 客户
export const getCustomers = () =>
  request({ url: '/api/customers', method: 'GET' })

// 供应商
export const getSuppliers = () =>
  request({ url: '/api/suppliers', method: 'GET' })
