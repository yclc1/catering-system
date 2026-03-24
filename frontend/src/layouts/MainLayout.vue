<template>
  <el-container class="main-layout">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo" @click="$router.push('/')">
        <span v-if="!sidebarCollapsed">团膳管理</span>
        <span v-else>膳</span>
      </div>
      <el-scrollbar>
        <el-menu
          :default-active="$route.path"
          :collapse="sidebarCollapsed"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <template v-for="item in menuItems" :key="item.path">
            <el-sub-menu v-if="item.children" :index="item.path">
              <template #title>
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.title }}</span>
              </template>
              <el-menu-item
                v-for="child in item.children"
                :key="child.path"
                :index="child.path"
              >
                {{ child.title }}
              </el-menu-item>
            </el-sub-menu>
            <el-menu-item v-else :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="appStore.toggleSidebar">
            <Fold v-if="!sidebarCollapsed" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="$route.meta.title">{{ $route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              {{ userStore.userInfo?.real_name || userStore.userInfo?.username || '用户' }}
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>

  <!-- Change Password Dialog -->
  <el-dialog v-model="pwdVisible" title="修改密码" width="400px">
    <el-form :model="pwdForm" label-width="80px">
      <el-form-item label="旧密码">
        <el-input v-model="pwdForm.old_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="pwdForm.new_password" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="pwdVisible = false">取消</el-button>
      <el-button type="primary" @click="changePassword">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { Fold, Expand, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { useAppStore } from '@/stores/app'
import { authApi } from '@/api'

const userStore = useUserStore()
const appStore = useAppStore()
const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)

const pwdVisible = ref(false)
const pwdForm = ref({ old_password: '', new_password: '' })

onMounted(() => {
  if (!userStore.userInfo) {
    userStore.fetchUserInfo()
  }
})

interface MenuItem {
  path: string
  title: string
  icon?: string
  permission?: string
  children?: MenuItem[]
}

const allMenuItems: MenuItem[] = [
  { path: '/dashboard', title: '工作台', icon: 'Odometer' },
  {
    path: '/procurement', title: '采购库存', icon: 'ShoppingCart',
    children: [
      { path: '/suppliers', title: '供应商管理', permission: 'supplier:list' },
      { path: '/products', title: '商品管理', permission: 'product:list' },
      { path: '/purchases', title: '采购管理', permission: 'purchase:list' },
      { path: '/inventory', title: '库存管理', permission: 'inventory:list' },
    ],
  },
  {
    path: '/customer-mgmt', title: '客户用餐', icon: 'Bowl',
    children: [
      { path: '/customers', title: '客户管理', permission: 'customer:list' },
      { path: '/meals', title: '用餐登记', permission: 'meal:list' },
      { path: '/settlements', title: '月度结算', permission: 'settlement:list' },
    ],
  },
  {
    path: '/finance', title: '财务管理', icon: 'Money',
    children: [
      { path: '/accounts', title: '收款账户', permission: 'account:list' },
      { path: '/payments', title: '收付款记录', permission: 'payment:list' },
      { path: '/reconciliations', title: '供应商对账', permission: 'reconciliation:list' },
    ],
  },
  { path: '/expenses', title: '费用审批', icon: 'CreditCard', permission: 'expense:list' },
  { path: '/vehicles', title: '车辆管理', icon: 'Van', permission: 'vehicle:list' },
  { path: '/contracts', title: '合同管理', icon: 'Notebook', permission: 'contract:list' },
  { path: '/statistics', title: '统计分析', icon: 'TrendCharts', permission: 'statistics:view' },
  {
    path: '/system', title: '系统管理', icon: 'Setting',
    children: [
      { path: '/users', title: '用户管理', permission: 'user:list' },
      { path: '/roles', title: '角色管理', permission: 'role:list' },
      { path: '/audit-logs', title: '审计日志', permission: 'audit:list' },
      { path: '/monthly-close', title: '月结管理', permission: 'monthly_close:close' },
    ],
  },
]

const menuItems = computed(() => {
  function filterMenu(items: MenuItem[]): MenuItem[] {
    return items.filter(item => {
      if (item.children) {
        const filtered = filterMenu(item.children)
        if (filtered.length === 0) return false
        item.children = filtered
        return true
      }
      if (item.permission) return userStore.hasPermission(item.permission)
      return true
    })
  }
  return filterMenu(JSON.parse(JSON.stringify(allMenuItems)))
})

function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    userStore.logout()
  } else if (cmd === 'password') {
    pwdForm.value = { old_password: '', new_password: '' }
    pwdVisible.value = true
  }
}

async function changePassword() {
  if (!pwdForm.value.old_password || !pwdForm.value.new_password) {
    ElMessage.warning('请填写完整')
    return
  }
  await authApi.changePassword(pwdForm.value)
  ElMessage.success('密码修改成功')
  pwdVisible.value = false
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}
.sidebar {
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}
.logo {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  background-color: #263445;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 16px;
  height: 50px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.collapse-btn {
  font-size: 20px;
  cursor: pointer;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
}
.main-content {
  background-color: #f5f5f5;
  padding: 16px;
}
.el-menu {
  border-right: none;
}

@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    z-index: 999;
    height: 100vh;
  }
}
</style>
