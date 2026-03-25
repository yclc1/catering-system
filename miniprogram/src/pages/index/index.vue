<template>
  <view class="container">
    <view class="header">
      <text class="title">餐饮管理系统</text>
    </view>

    <view v-if="!token" class="login-box">
      <input v-model="username" placeholder="用户名" class="input" />
      <input v-model="password" type="password" placeholder="密码" class="input" />
      <button @click="handleLogin" class="btn">登录</button>
    </view>

    <view v-else class="menu-grid">
      <view class="menu-item" @click="navigateTo('/pages/meals/index')">
        <text class="icon">📝</text>
        <text>用餐登记</text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/approval/index')">
        <text class="icon">✅</text>
        <text>费用审批</text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/purchase/index')">
        <text class="icon">🛒</text>
        <text>采购管理</text>
      </view>
      <view class="menu-item" @click="navigateTo('/pages/inventory/index')">
        <text class="icon">📦</text>
        <text>库存查询</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { login } from '../../api/index'

const username = ref('')
const password = ref('')
const token = ref('')

onMounted(() => {
  token.value = uni.getStorageSync('token')
})

const handleLogin = async () => {
  try {
    const res = await login({
      username: username.value,
      password: password.value
    })
    uni.setStorageSync('token', res.access_token)
    token.value = res.access_token
    uni.showToast({ title: '登录成功', icon: 'success' })
  } catch (error: any) {
    uni.showToast({ title: error.message || '登录失败', icon: 'none' })
  }
}

const navigateTo = (url: string) => {
  uni.navigateTo({ url })
}
</script>

<style scoped>
.container {
  padding: 20px;
}

.header {
  text-align: center;
  padding: 40px 0;
}

.title {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
}

.login-box {
  margin-top: 40px;
}

.input {
  width: 100%;
  height: 44px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0 15px;
  margin-bottom: 15px;
  box-sizing: border-box;
}

.btn {
  width: 100%;
  height: 44px;
  background: #409EFF;
  color: white;
  border: none;
  border-radius: 4px;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-top: 20px;
}

.menu-item {
  background: white;
  padding: 30px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.icon {
  font-size: 40px;
  display: block;
  margin-bottom: 10px;
}
</style>
