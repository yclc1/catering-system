import request from './request'

// Auth
export const authApi = {
  login: (data: { username: string; password: string }) => request.post('/auth/login', data),
  refresh: (data: { refresh_token: string }) => request.post('/auth/refresh', data),
  me: () => request.get('/auth/me'),
  changePassword: (data: { old_password: string; new_password: string }) => request.put('/auth/me/password', data),
}

// Users
export const userApi = {
  list: (params?: any) => request.get('/users', { params }),
  get: (id: number) => request.get(`/users/${id}`),
  create: (data: any) => request.post('/users', data),
  update: (id: number, data: any) => request.put(`/users/${id}`, data),
  delete: (id: number) => request.delete(`/users/${id}`),
  dropdown: () => request.get('/users/dropdown/list'),
}

// Roles
export const roleApi = {
  list: () => request.get('/roles'),
  create: (data: any) => request.post('/roles', data),
  update: (id: number, data: any) => request.put(`/roles/${id}`, data),
  delete: (id: number) => request.delete(`/roles/${id}`),
  permissions: () => request.get('/permissions'),
}

// Suppliers
export const supplierApi = {
  list: (params?: any) => request.get('/suppliers', { params }),
  get: (id: number) => request.get(`/suppliers/${id}`),
  create: (data: any) => request.post('/suppliers', data),
  update: (id: number, data: any) => request.put(`/suppliers/${id}`, data),
  delete: (id: number) => request.delete(`/suppliers/${id}`),
  dropdown: () => request.get('/suppliers/dropdown'),
}

// Product Categories
export const productCategoryApi = {
  list: () => request.get('/product-categories'),
  create: (data: any) => request.post('/product-categories', data),
  dropdown: () => request.get('/product-categories/dropdown'),
}

// Products
export const productApi = {
  list: (params?: any) => request.get('/products', { params }),
  get: (id: number) => request.get(`/products/${id}`),
  create: (data: any) => request.post('/products', data),
  update: (id: number, data: any) => request.put(`/products/${id}`, data),
  delete: (id: number) => request.delete(`/products/${id}`),
  dropdown: () => request.get('/products/dropdown'),
  priceHistory: (id: number) => request.get(`/products/${id}/price-history`),
}

// Customers
export const customerApi = {
  list: (params?: any) => request.get('/customers', { params }),
  get: (id: number) => request.get(`/customers/${id}`),
  create: (data: any) => request.post('/customers', data),
  update: (id: number, data: any) => request.put(`/customers/${id}`, data),
  delete: (id: number) => request.delete(`/customers/${id}`),
  dropdown: () => request.get('/customers/dropdown'),
}

// Meals
export const mealApi = {
  list: (params?: any) => request.get('/meals', { params }),
  create: (data: any) => request.post('/meals', data),
  update: (id: number, data: any) => request.put(`/meals/${id}`, data),
  delete: (id: number) => request.delete(`/meals/${id}`),
}

// Settlements
export const settlementApi = {
  list: (params?: any) => request.get('/settlements', { params }),
  generate: (data: any) => request.post('/settlements/generate', data),
  update: (id: number, data: any) => request.put(`/settlements/${id}`, data),
  confirm: (id: number) => request.post(`/settlements/${id}/confirm`),
  export: (id: number) => request.get(`/settlements/${id}/export`, { responseType: 'blob' }),
}

// Purchase Orders
export const purchaseApi = {
  list: (params?: any) => request.get('/purchases', { params }),
  get: (id: number) => request.get(`/purchases/${id}`),
  create: (data: any) => request.post('/purchases', data),
  update: (id: number, data: any) => request.put(`/purchases/${id}`, data),
  delete: (id: number) => request.delete(`/purchases/${id}`),
  confirm: (id: number) => request.post(`/purchases/${id}/confirm`),
}

// Inventory
export const inventoryApi = {
  list: (params?: any) => request.get('/inventory/transactions', { params }),
  get: (id: number) => request.get(`/inventory/transactions/${id}`),
  create: (data: any) => request.post('/inventory/transactions', data),
  stock: (params?: any) => request.get('/inventory/stock', { params }),
}

// Payment Accounts
export const accountApi = {
  list: (params?: any) => request.get('/accounts', { params }),
  get: (id: number) => request.get(`/accounts/${id}`),
  create: (data: any) => request.post('/accounts', data),
  update: (id: number, data: any) => request.put(`/accounts/${id}`, data),
  delete: (id: number) => request.delete(`/accounts/${id}`),
  dropdown: () => request.get('/accounts/dropdown'),
}

// Payment Records
export const paymentApi = {
  list: (params?: any) => request.get('/payments', { params }),
  get: (id: number) => request.get(`/payments/${id}`),
  create: (data: any) => request.post('/payments', data),
  update: (id: number, data: any) => request.put(`/payments/${id}`, data),
  delete: (id: number) => request.delete(`/payments/${id}`),
}

// Reconciliation
export const reconciliationApi = {
  list: (params?: any) => request.get('/reconciliations/suppliers', { params }),
  generate: (data: any) => request.post('/reconciliations/suppliers/generate', data),
  confirm: (id: number) => request.post(`/reconciliations/suppliers/${id}/confirm`),
  details: (id: number) => request.get(`/reconciliations/suppliers/${id}/transactions`),
  export: (id: number) => request.get(`/reconciliations/suppliers/${id}/export`, { responseType: 'blob' }),
}

// Expenses
export const expenseApi = {
  list: (params?: any) => request.get('/expenses', { params }),
  get: (id: number) => request.get(`/expenses/${id}`),
  create: (data: any) => request.post('/expenses', data),
  approve: (id: number) => request.post(`/expenses/${id}/approve`),
  reject: (id: number, data: any) => request.post(`/expenses/${id}/reject`, data),
}

// Expense Categories
export const expenseCategoryApi = {
  list: () => request.get('/expense-categories'),
  create: (data: any) => request.post('/expense-categories', data),
  dropdown: () => request.get('/expense-categories/dropdown'),
}

// Vehicles
export const vehicleApi = {
  list: (params?: any) => request.get('/vehicles', { params }),
  get: (id: number) => request.get(`/vehicles/${id}`),
  create: (data: any) => request.post('/vehicles', data),
  update: (id: number, data: any) => request.put(`/vehicles/${id}`, data),
  delete: (id: number) => request.delete(`/vehicles/${id}`),
  reminders: () => request.get('/vehicles/reminders'),
  maintenanceList: (id: number) => request.get(`/vehicles/${id}/maintenance`),
  createMaintenance: (id: number, data: any) => request.post(`/vehicles/${id}/maintenance`, data),
  insuranceList: (id: number) => request.get(`/vehicles/${id}/insurance`),
  createInsurance: (id: number, data: any) => request.post(`/vehicles/${id}/insurance`, data),
}

// Contracts
export const contractApi = {
  list: (params?: any) => request.get('/contracts', { params }),
  get: (id: number) => request.get(`/contracts/${id}`),
  create: (data: any) => request.post('/contracts', data),
  update: (id: number, data: any) => request.put(`/contracts/${id}`, data),
  delete: (id: number) => request.delete(`/contracts/${id}`),
  reminders: () => request.get('/contracts/reminders'),
}

// Statistics
export const statisticsApi = {
  dashboard: () => request.get('/statistics/dashboard'),
  monthlySales: (params: any) => request.get('/statistics/monthly-sales', { params }),
  categoryUsage: (params: any) => request.get('/statistics/category-usage', { params }),
  customerRevenue: (params: any) => request.get('/statistics/customer-revenue', { params }),
}

// Audit
export const auditApi = {
  list: (params?: any) => request.get('/audit-logs', { params }),
}

// Monthly Close
export const monthlyCloseApi = {
  list: () => request.get('/monthly-closes'),
  close: (data: any) => request.post('/monthly-closes', data),
  reopen: (id: number, data: any) => request.post(`/monthly-closes/${id}/reopen`, data),
}
