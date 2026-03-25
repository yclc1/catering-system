<template>
  <view class="container">
    <button @click="showForm = true" class="add-btn">+ 新建采购</button>

    <view class="list">
      <view v-for="item in purchases" :key="item.id" class="item">
        <view class="item-header">
          <text class="supplier">{{ item.supplier_name }}</text>
          <text class="amount">¥{{ item.total_amount }}</text>
        </view>
        <text class="status">{{ item.status }}</text>
        <text class="time">{{ item.created_at }}</text>
      </view>
    </view>

    <view v-if="showForm" class="modal" @click="showForm = false">
      <view class="modal-content" @click.stop>
        <text class="modal-title">新建采购</text>
        <view class="form">
          <picker @change="onSupplierChange" :range="suppliers" range-key="name">
            <view class="picker">{{ suppliers[supplierIndex]?.name || '选择供应商' }}</view>
          </picker>
          <input v-model="form.amount" type="digit" placeholder="金额" class="input" />
          <textarea v-model="form.notes" placeholder="备注" class="textarea" />
        </view>
        <button @click="submit" class="btn">提交</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getPurchases, createPurchase, getSuppliers } from '../../api/index'

const purchases = ref<any[]>([])
const suppliers = ref<any[]>([])
const supplierIndex = ref(0)
const showForm = ref(false)
const form = ref({ supplier_id: 0, amount: '', notes: '' })

onMounted(async () => {
  purchases.value = await getPurchases()
  suppliers.value = await getSuppliers()
})

const onSupplierChange = (e: any) => {
  supplierIndex.value = e.detail.value
  form.value.supplier_id = suppliers.value[e.detail.value].id
}

const submit = async () => {
  try {
    await createPurchase({ ...form.value, amount: Number(form.value.amount) })
    uni.showToast({ title: '创建成功', icon: 'success' })
    showForm.value = false
    purchases.value = await getPurchases()
  } catch (error: any) {
    uni.showToast({ title: error.message, icon: 'none' })
  }
}
</script>

<style scoped>
.container { padding: 15px; }
.add-btn { width: 100%; height: 44px; background: #409EFF; color: white; border: none; border-radius: 4px; margin-bottom: 15px; }
.list { background: white; border-radius: 8px; }
.item { padding: 15px; border-bottom: 1px solid #f0f0f0; }
.item-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.supplier { font-weight: bold; }
.amount { color: #F56C6C; }
.status, .time { font-size: 12px; color: #999; display: block; margin-top: 5px; }
.modal { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; }
.modal-content { background: white; width: 80%; border-radius: 8px; padding: 20px; }
.modal-title { font-size: 18px; font-weight: bold; margin-bottom: 15px; display: block; }
.form { margin-bottom: 15px; }
.picker, .input, .textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px; box-sizing: border-box; }
.textarea { height: 80px; }
.btn { width: 100%; height: 40px; background: #409EFF; color: white; border: none; border-radius: 4px; }
</style>
