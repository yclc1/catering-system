<template>
  <view class="container">
    <view class="search">
      <input v-model="keyword" placeholder="搜索商品" class="search-input" @input="search" />
    </view>

    <view class="list">
      <view v-for="item in inventory" :key="item.id" class="item">
        <view class="item-header">
          <text class="name">{{ item.product_name }}</text>
          <text :class="['stock', item.quantity < item.min_stock && 'warning']">
            {{ item.quantity }} {{ item.unit }}
          </text>
        </view>
        <view class="item-footer">
          <text class="category">{{ item.category }}</text>
          <text v-if="item.quantity < item.min_stock" class="alert">库存不足</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getInventory } from '../../api/index'

const keyword = ref('')
const inventory = ref<any[]>([])
const allInventory = ref<any[]>([])

onMounted(async () => {
  allInventory.value = await getInventory()
  inventory.value = allInventory.value
})

const search = () => {
  if (!keyword.value) {
    inventory.value = allInventory.value
  } else {
    inventory.value = allInventory.value.filter(item =>
      item.product_name.includes(keyword.value)
    )
  }
}
</script>

<style scoped>
.container { padding: 15px; }
.search { margin-bottom: 15px; }
.search-input { width: 100%; height: 40px; padding: 0 15px; border: 1px solid #ddd; border-radius: 20px; box-sizing: border-box; }
.list { background: white; border-radius: 8px; }
.item { padding: 15px; border-bottom: 1px solid #f0f0f0; }
.item-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.name { font-weight: bold; }
.stock { color: #67C23A; font-weight: bold; }
.stock.warning { color: #F56C6C; }
.item-footer { display: flex; justify-content: space-between; font-size: 12px; color: #999; }
.alert { color: #F56C6C; }
</style>
