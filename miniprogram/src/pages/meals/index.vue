<template>
  <view class="container">
    <view class="form">
      <view class="form-item">
        <text class="label">客户</text>
        <picker @change="onCustomerChange" :value="customerIndex" :range="customers" range-key="name">
          <view class="picker">{{ customers[customerIndex]?.name || '请选择客户' }}</view>
        </picker>
      </view>

      <view class="form-item">
        <text class="label">用餐人数</text>
        <input v-model="form.count" type="number" placeholder="请输入人数" class="input" />
      </view>

      <view class="form-item">
        <text class="label">备注</text>
        <textarea v-model="form.notes" placeholder="备注信息" class="textarea" />
      </view>

      <view class="form-item">
        <text class="label">拍照</text>
        <view class="image-list">
          <view v-for="(img, index) in images" :key="index" class="image-item">
            <image :src="img" mode="aspectFill" />
            <text @click="removeImage(index)" class="remove">×</text>
          </view>
          <view v-if="images.length < 3" @click="chooseImage" class="add-image">+</view>
        </view>
      </view>

      <button @click="submit" class="btn">提交</button>
    </view>

    <view class="list">
      <text class="list-title">今日登记</text>
      <view v-for="item in meals" :key="item.id" class="list-item">
        <view class="item-row">
          <text class="customer">{{ item.customer_name }}</text>
          <text class="count">{{ item.count }}人</text>
        </view>
        <text class="time">{{ item.created_at }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getCustomers, createMeal, getMeals } from '../../api/index'

const customers = ref<any[]>([])
const customerIndex = ref(0)
const form = ref({ customer_id: 0, count: '', notes: '' })
const images = ref<string[]>([])
const meals = ref<any[]>([])

onMounted(async () => {
  customers.value = await getCustomers()
  loadMeals()
})

const onCustomerChange = (e: any) => {
  customerIndex.value = e.detail.value
  form.value.customer_id = customers.value[e.detail.value].id
}

const chooseImage = () => {
  uni.chooseImage({
    count: 3 - images.value.length,
    success: (res) => {
      images.value.push(...res.tempFilePaths)
    }
  })
}

const removeImage = (index: number) => {
  images.value.splice(index, 1)
}

const submit = async () => {
  if (!form.value.customer_id || !form.value.count) {
    uni.showToast({ title: '请填写完整信息', icon: 'none' })
    return
  }
  try {
    await createMeal({ ...form.value, count: Number(form.value.count) })
    uni.showToast({ title: '登记成功', icon: 'success' })
    form.value = { customer_id: 0, count: '', notes: '' }
    images.value = []
    loadMeals()
  } catch (error: any) {
    uni.showToast({ title: error.message, icon: 'none' })
  }
}

const loadMeals = async () => {
  meals.value = await getMeals()
}
</script>

<style scoped>
.container { padding: 15px; }
.form { background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
.form-item { margin-bottom: 15px; }
.label { display: block; margin-bottom: 8px; font-weight: bold; }
.picker, .input, .textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
.textarea { height: 80px; }
.image-list { display: flex; gap: 10px; }
.image-item { position: relative; width: 80px; height: 80px; }
.image-item image { width: 100%; height: 100%; border-radius: 4px; }
.remove { position: absolute; top: -5px; right: -5px; width: 20px; height: 20px; background: red; color: white; border-radius: 50%; text-align: center; line-height: 20px; }
.add-image { width: 80px; height: 80px; border: 1px dashed #ddd; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 30px; color: #999; }
.btn { width: 100%; height: 44px; background: #409EFF; color: white; border: none; border-radius: 4px; margin-top: 10px; }
.list { background: white; padding: 15px; border-radius: 8px; }
.list-title { font-weight: bold; margin-bottom: 10px; display: block; }
.list-item { padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.item-row { display: flex; justify-content: space-between; margin-bottom: 5px; }
.customer { font-weight: bold; }
.count { color: #409EFF; }
.time { font-size: 12px; color: #999; }
</style>
