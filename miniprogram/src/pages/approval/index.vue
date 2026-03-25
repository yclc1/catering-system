<template>
  <view class="container">
    <view class="tabs">
      <text :class="['tab', status === 'pending' && 'active']" @click="status = 'pending'">待审批</text>
      <text :class="['tab', status === 'approved' && 'active']" @click="status = 'approved'">已通过</text>
      <text :class="['tab', status === 'rejected' && 'active']" @click="status = 'rejected'">已驳回</text>
    </view>

    <view class="list">
      <view v-for="item in expenses" :key="item.id" class="item" @click="showDetail(item)">
        <view class="item-header">
          <text class="title">{{ item.category }}</text>
          <text class="amount">¥{{ item.amount }}</text>
        </view>
        <text class="desc">{{ item.description }}</text>
        <view class="item-footer">
          <text class="user">{{ item.applicant }}</text>
          <text class="time">{{ item.created_at }}</text>
        </view>
      </view>
    </view>

    <view v-if="showModal" class="modal" @click="showModal = false">
      <view class="modal-content" @click.stop>
        <text class="modal-title">审批详情</text>
        <view class="detail">
          <text>类别：{{ currentItem.category }}</text>
          <text>金额：¥{{ currentItem.amount }}</text>
          <text>说明：{{ currentItem.description }}</text>
          <text>申请人：{{ currentItem.applicant }}</text>
        </view>
        <view class="modal-actions">
          <button @click="approve" class="btn-approve">通过</button>
          <button @click="reject" class="btn-reject">驳回</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { getExpenses, approveExpense } from '../../api/index'

const status = ref('pending')
const expenses = ref<any[]>([])
const showModal = ref(false)
const currentItem = ref<any>({})

onMounted(() => {
  loadExpenses()
})

watch(status, () => {
  loadExpenses()
})

const loadExpenses = async () => {
  expenses.value = await getExpenses({ status: status.value })
}

const showDetail = (item: any) => {
  if (status.value === 'pending') {
    currentItem.value = item
    showModal.value = true
  }
}

const approve = async () => {
  try {
    await approveExpense(currentItem.value.id, { status: 'approved' })
    uni.showToast({ title: '已通过', icon: 'success' })
    showModal.value = false
    loadExpenses()
  } catch (error: any) {
    uni.showToast({ title: error.message, icon: 'none' })
  }
}

const reject = async () => {
  try {
    await approveExpense(currentItem.value.id, { status: 'rejected' })
    uni.showToast({ title: '已驳回', icon: 'success' })
    showModal.value = false
    loadExpenses()
  } catch (error: any) {
    uni.showToast({ title: error.message, icon: 'none' })
  }
}
</script>

<style scoped>
.container { padding: 15px; }
.tabs { display: flex; background: white; border-radius: 8px; padding: 5px; margin-bottom: 15px; }
.tab { flex: 1; text-align: center; padding: 8px; border-radius: 4px; }
.tab.active { background: #409EFF; color: white; }
.list { background: white; border-radius: 8px; }
.item { padding: 15px; border-bottom: 1px solid #f0f0f0; }
.item-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.title { font-weight: bold; }
.amount { color: #F56C6C; font-weight: bold; }
.desc { color: #666; font-size: 14px; display: block; margin-bottom: 8px; }
.item-footer { display: flex; justify-content: space-between; font-size: 12px; color: #999; }
.modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
.modal-content { background: white; width: 80%; border-radius: 8px; padding: 20px; }
.modal-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; display: block; }
.detail text { display: block; margin-bottom: 10px; }
.modal-actions { display: flex; gap: 10px; margin-top: 20px; }
.btn-approve, .btn-reject { flex: 1; height: 40px; border: none; border-radius: 4px; color: white; }
.btn-approve { background: #67C23A; }
.btn-reject { background: #F56C6C; }
</style>
