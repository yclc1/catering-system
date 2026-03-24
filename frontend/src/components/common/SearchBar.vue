<template>
  <div class="search-bar">
    <el-input
      v-if="showKeyword"
      v-model="keyword"
      :placeholder="placeholder"
      clearable
      style="width: 240px"
      @keyup.enter="$emit('search')"
    >
      <template #prefix>
        <el-icon><Search /></el-icon>
      </template>
    </el-input>
    <slot />
    <el-button type="primary" @click="$emit('search')">搜索</el-button>
    <el-button @click="handleReset">重置</el-button>
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'

withDefaults(defineProps<{
  placeholder?: string
  showKeyword?: boolean
}>(), {
  placeholder: '搜索...',
  showKeyword: true,
})

const keyword = defineModel<string>('keyword', { default: '' })

const emit = defineEmits<{
  'search': []
  'reset': []
}>()

function handleReset() {
  keyword.value = ''
  emit('reset')
}
</script>

<style scoped>
.search-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
