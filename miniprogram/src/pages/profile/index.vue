<template>
  <view class="container">
    <view class="header">
      <view class="avatar">👤</view>
      <text class="username">{{ userInfo.username || '未登录' }}</text>
    </view>

    <view class="menu">
      <view class="menu-item">
        <text>个人信息</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item">
        <text>消息通知</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item">
        <text>设置</text>
        <text class="arrow">›</text>
      </view>
    </view>

    <button v-if="token" @click="logout" class="logout-btn">退出登录</button>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const token = ref('')
const userInfo = ref<any>({})

onMounted(() => {
  token.value = uni.getStorageSync('token')
  userInfo.value = uni.getStorageSync('userInfo') || {}
})

const logout = () => {
  uni.showModal({
    title: '提示',
    content: '确定退出登录？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('token')
        uni.removeStorageSync('userInfo')
        uni.reLaunch({ url: '/pages/index/index' })
      }
    }
  })
}
</script>

<style scoped>
.container { padding: 15px; }
.header { background: white; padding: 30px; text-align: center; border-radius: 8px; margin-bottom: 15px; }
.avatar { font-size: 60px; margin-bottom: 10px; }
.username { font-size: 18px; font-weight: bold; display: block; }
.menu { background: white; border-radius: 8px; margin-bottom: 15px; }
.menu-item { padding: 15px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; }
.menu-item:last-child { border-bottom: none; }
.arrow { font-size: 20px; color: #999; }
.logout-btn { width: 100%; height: 44px; background: #F56C6C; color: white; border: none; border-radius: 4px; }
</style>
