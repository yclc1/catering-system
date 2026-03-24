import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { TOKEN_KEY } from '@/utils/constants'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '工作台', icon: 'Odometer' },
      },
      // 供应商
      {
        path: 'suppliers',
        name: 'Suppliers',
        component: () => import('@/views/suppliers/index.vue'),
        meta: { title: '供应商管理', icon: 'OfficeBuilding', permission: 'supplier:list' },
      },
      // 商品
      {
        path: 'products',
        name: 'Products',
        component: () => import('@/views/products/index.vue'),
        meta: { title: '商品管理', icon: 'Goods', permission: 'product:list' },
      },
      // 采购
      {
        path: 'purchases',
        name: 'Purchases',
        component: () => import('@/views/purchases/index.vue'),
        meta: { title: '采购管理', icon: 'ShoppingCart', permission: 'purchase:list' },
      },
      // 库存
      {
        path: 'inventory',
        name: 'Inventory',
        component: () => import('@/views/inventory/index.vue'),
        meta: { title: '库存管理', icon: 'Box', permission: 'inventory:list' },
      },
      // 客户
      {
        path: 'customers',
        name: 'Customers',
        component: () => import('@/views/customers/index.vue'),
        meta: { title: '客户管理', icon: 'User', permission: 'customer:list' },
      },
      // 用餐登记
      {
        path: 'meals',
        name: 'Meals',
        component: () => import('@/views/customers/meals.vue'),
        meta: { title: '用餐登记', icon: 'Bowl', permission: 'meal:list' },
      },
      // 客户结算
      {
        path: 'settlements',
        name: 'Settlements',
        component: () => import('@/views/customers/settlements.vue'),
        meta: { title: '月度结算', icon: 'Tickets', permission: 'settlement:list' },
      },
      // 收款账户
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('@/views/accounts/index.vue'),
        meta: { title: '收款账户', icon: 'Wallet', permission: 'account:list' },
      },
      // 收付款
      {
        path: 'payments',
        name: 'Payments',
        component: () => import('@/views/accounts/payments.vue'),
        meta: { title: '收付款记录', icon: 'Money', permission: 'payment:list' },
      },
      // 供应商对账
      {
        path: 'reconciliations',
        name: 'Reconciliations',
        component: () => import('@/views/reconciliation/index.vue'),
        meta: { title: '供应商对账', icon: 'Document', permission: 'reconciliation:list' },
      },
      // 费用审批
      {
        path: 'expenses',
        name: 'Expenses',
        component: () => import('@/views/expenses/index.vue'),
        meta: { title: '费用审批', icon: 'CreditCard', permission: 'expense:list' },
      },
      // 车辆
      {
        path: 'vehicles',
        name: 'Vehicles',
        component: () => import('@/views/vehicles/index.vue'),
        meta: { title: '车辆管理', icon: 'Van', permission: 'vehicle:list' },
      },
      // 合同
      {
        path: 'contracts',
        name: 'Contracts',
        component: () => import('@/views/contracts/index.vue'),
        meta: { title: '合同管理', icon: 'Notebook', permission: 'contract:list' },
      },
      // 统计
      {
        path: 'statistics',
        name: 'Statistics',
        component: () => import('@/views/statistics/index.vue'),
        meta: { title: '统计分析', icon: 'TrendCharts', permission: 'statistics:view' },
      },
      // 用户管理
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/index.vue'),
        meta: { title: '用户管理', icon: 'UserFilled', permission: 'user:list' },
      },
      // 角色管理
      {
        path: 'roles',
        name: 'Roles',
        component: () => import('@/views/users/roles.vue'),
        meta: { title: '角色管理', icon: 'Lock', permission: 'role:list' },
      },
      // 审计日志
      {
        path: 'audit-logs',
        name: 'AuditLogs',
        component: () => import('@/views/audit/index.vue'),
        meta: { title: '审计日志', icon: 'List', permission: 'audit:list' },
      },
      // 月结管理
      {
        path: 'monthly-close',
        name: 'MonthlyClose',
        component: () => import('@/views/audit/monthlyClose.vue'),
        meta: { title: '月结管理', icon: 'Calendar', permission: 'monthly_close:close' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

NProgress.configure({ showSpinner: false })

router.beforeEach(async (to, _from, next) => {
  NProgress.start()
  document.title = `${to.meta.title || ''} - 团膳管理系统`

  if (to.meta.public) {
    next()
    return
  }

  const token = localStorage.getItem(TOKEN_KEY)
  if (!token) {
    next('/login')
    return
  }

  // Check route-level permission
  const requiredPermission = to.meta.permission as string | undefined
  if (requiredPermission) {
    const userStore = useUserStore()
    // Ensure user info is loaded
    if (!userStore.userInfo) {
      try {
        await userStore.fetchUserInfo()
      } catch {
        next('/login')
        return
      }
    }
    if (!userStore.hasPermission(requiredPermission)) {
      next('/dashboard')
      return
    }
  }

  next()
})

router.afterEach(() => {
  NProgress.done()
})

export default router
