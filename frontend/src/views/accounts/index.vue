<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <SearchBar v-model:keyword="keyword" placeholder="搜索账户..." @search="loadData" @reset="resetSearch" />
        <el-button v-permission="'account:create'" type="primary" @click="openCreate">新增账户</el-button>
      </template>

      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="account_type" label="类型" width="100">
        <template #default="{ row }">{{ ACCOUNT_TYPES[row.account_type as keyof typeof ACCOUNT_TYPES] || row.account_type }}</template>
      </el-table-column>
      <el-table-column prop="bank_name" label="开户行" />
      <el-table-column prop="account_number" label="账号" />
      <el-table-column prop="current_balance" label="余额" width="130" align="right" :formatter="(r:any) => formatMoney(r.current_balance)" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="'account:update'" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-permission="'account:delete'" type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <FormDialog v-model:visible="dialogVisible" :model-value="form" :title="isEdit ? '编辑账户' : '新增账户'" :loading="saving" @submit="handleSave">
      <template #default>
        <el-form-item label="名称" required><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.account_type" style="width:100%">
            <el-option v-for="(label, key) in ACCOUNT_TYPES" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="开户行"><el-input v-model="form.bank_name" /></el-form-item>
        <el-form-item label="账号"><el-input v-model="form.account_number" /></el-form-item>
        <el-form-item v-if="!isEdit" label="初始余额"><el-input-number v-model="form.current_balance" :min="0" :precision="2" style="width:100%" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      </template>
    </FormDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import { accountApi } from '@/api'
import { formatMoney } from '@/utils/format'
import { ACCOUNT_TYPES } from '@/utils/constants'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const form = ref<any>({})

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const res: any = await accountApi.list()
    list.value = Array.isArray(res) ? res : (res.items || [])
    total.value = list.value.length
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }
function resetSearch() { keyword.value = ''; page.value = 1; loadData() }

function openCreate() { isEdit.value = false; form.value = { name: '', account_type: 'bank', bank_name: '', account_number: '', current_balance: 0, notes: '' }; dialogVisible.value = true }
function openEdit(row: any) { isEdit.value = true; editId.value = row.id; form.value = { ...row }; dialogVisible.value = true }

async function handleSave() {
  saving.value = true
  try {
    if (isEdit.value && editId.value) await accountApi.update(editId.value, form.value)
    else await accountApi.create(form.value)
    ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
  } finally { saving.value = false }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除？', '确认')
  await accountApi.delete(row.id); ElMessage.success('已删除'); loadData()
}
</script>
