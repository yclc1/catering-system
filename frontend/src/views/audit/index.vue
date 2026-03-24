<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <div class="toolbar-filters">
          <el-select v-model="actionFilter" placeholder="操作" clearable style="width:120px" @change="loadData">
            <el-option label="创建" value="create" />
            <el-option label="更新" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="审批" value="approve" />
            <el-option label="驳回" value="reject" />
            <el-option label="确认" value="confirm" />
          </el-select>
          <el-select v-model="resourceFilter" placeholder="资源类型" clearable style="width:140px" @change="loadData">
            <el-option label="采购单" value="purchase" />
            <el-option label="库存" value="inventory" />
            <el-option label="费用" value="expense" />
            <el-option label="合同" value="contract" />
            <el-option label="车辆" value="vehicle" />
          </el-select>
        </div>
      </template>

      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户" width="100" />
      <el-table-column prop="action" label="操作" width="80" />
      <el-table-column prop="resource_type" label="资源类型" width="100" />
      <el-table-column prop="resource_code" label="资源编码" width="160" />
      <el-table-column prop="detail" label="详情">
        <template #default="{ row }">{{ row.detail ? JSON.stringify(row.detail).substring(0, 100) : '-' }}</template>
      </el-table-column>
      <el-table-column prop="ip_address" label="IP" width="130" />
      <el-table-column prop="created_at" label="时间" width="170" />
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import DataTable from '@/components/common/DataTable.vue'
import { auditApi } from '@/api'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const actionFilter = ref('')
const resourceFilter = ref('')

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (actionFilter.value) params.action = actionFilter.value
    if (resourceFilter.value) params.resource_type = resourceFilter.value
    const res: any = await auditApi.list(params)
    list.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }
</script>

<style scoped>
.toolbar-filters { display: flex; gap: 8px; align-items: center; }
</style>
