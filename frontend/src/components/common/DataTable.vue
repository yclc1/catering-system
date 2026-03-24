<template>
  <div class="data-table">
    <div v-if="$slots.toolbar" class="table-toolbar">
      <slot name="toolbar" />
    </div>

    <el-table
      :data="data"
      v-loading="loading"
      stripe
      border
      :max-height="maxHeight"
      style="width: 100%"
      @sort-change="$emit('sort-change', $event)"
    >
      <slot />
    </el-table>

    <div v-if="(total ?? 0) > 0" class="table-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="currentPageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  data: any[]
  loading?: boolean
  total?: number
  page?: number
  pageSize?: number
  maxHeight?: number | string
}>()

const emit = defineEmits<{
  'update:page': [value: number]
  'update:pageSize': [value: number]
  'page-change': [page: number, pageSize: number]
  'sort-change': [value: any]
}>()

const currentPage = computed({
  get: () => props.page || 1,
  set: (val) => emit('update:page', val),
})

const currentPageSize = computed({
  get: () => props.pageSize || 20,
  set: (val) => emit('update:pageSize', val),
})

function handlePageChange(page: number) {
  emit('page-change', page, currentPageSize.value)
}

function handleSizeChange(size: number) {
  emit('page-change', 1, size)
}
</script>

<style scoped>
.data-table {
  background: #fff;
  border-radius: 4px;
  padding: 16px;
}
.table-toolbar {
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.table-pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
