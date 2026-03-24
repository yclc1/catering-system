<template>
  <div class="supplier-page">
    <SearchBar
      v-model:keyword="queryParams.keyword"
      placeholder="搜索供应商名称/编码..."
      @search="handleSearch"
      @reset="handleReset"
    />

    <DataTable
      :data="tableData"
      :loading="loading"
      :total="total"
      :page="queryParams.page"
      :page-size="queryParams.page_size"
      @update:page="queryParams.page = $event"
      @update:page-size="queryParams.page_size = $event"
      @page-change="handlePageChange"
    >
      <template #toolbar>
        <el-button
          v-permission="'supplier:create'"
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          新增供应商
        </el-button>
      </template>

      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="name" label="名称" min-width="150" />
      <el-table-column prop="contact_person" label="联系人" width="120" />
      <el-table-column prop="phone" label="电话" width="140" />
      <el-table-column prop="address" label="地址" min-width="180" show-overflow-tooltip />
      <el-table-column prop="bank_name" label="开户行" min-width="150" show-overflow-tooltip />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button
            v-permission="'supplier:update'"
            type="primary"
            link
            @click="handleEdit(row)"
          >
            编辑
          </el-button>
          <el-button
            v-permission="'supplier:delete'"
            type="danger"
            link
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </DataTable>

    <FormDialog
      v-model:visible="dialogVisible"
      :model-value="formData"
      :title="isEdit ? '编辑供应商' : '新增供应商'"
      :rules="formRules"
      :loading="submitting"
      label-width="100px"
      @submit="handleSubmit"
      @close="handleDialogClose"
    >
      <template #default>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入供应商名称" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact_person">
          <el-input v-model="formData.contact_person" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入电话" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="formData.address" placeholder="请输入地址" />
        </el-form-item>
        <el-form-item label="开户行" prop="bank_name">
          <el-input v-model="formData.bank_name" placeholder="请输入开户行" />
        </el-form-item>
        <el-form-item label="银行账号" prop="bank_account">
          <el-input v-model="formData.bank_account" placeholder="请输入银行账号" />
        </el-form-item>
        <el-form-item label="税号" prop="tax_id">
          <el-input v-model="formData.tax_id" placeholder="请输入税号" />
        </el-form-item>
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="formData.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注"
          />
        </el-form-item>
      </template>
    </FormDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormRules } from 'element-plus'
import { supplierApi } from '@/api'
import SearchBar from '@/components/common/SearchBar.vue'
import DataTable from '@/components/common/DataTable.vue'
import FormDialog from '@/components/common/FormDialog.vue'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const tableData = ref<any[]>([])
const total = ref(0)

const queryParams = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
})

const defaultForm = () => ({
  name: '',
  contact_person: '',
  phone: '',
  address: '',
  bank_name: '',
  bank_account: '',
  tax_id: '',
  notes: '',
})

const formData = reactive(defaultForm())

const formRules: FormRules = {
  name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
}

async function fetchData() {
  loading.value = true
  try {
    const res: any = await supplierApi.list({
      page: queryParams.page,
      page_size: queryParams.page_size,
      keyword: queryParams.keyword || undefined,
    })
    tableData.value = res.items
    total.value = res.total
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryParams.page = 1
  fetchData()
}

function handleReset() {
  queryParams.page = 1
  queryParams.keyword = ''
  fetchData()
}

function handlePageChange(page: number, pageSize: number) {
  queryParams.page = page
  queryParams.page_size = pageSize
  fetchData()
}

function handleCreate() {
  isEdit.value = false
  editingId.value = null
  Object.assign(formData, defaultForm())
  dialogVisible.value = true
}

function handleEdit(row: any) {
  isEdit.value = true
  editingId.value = row.id
  Object.assign(formData, {
    name: row.name,
    contact_person: row.contact_person,
    phone: row.phone,
    address: row.address,
    bank_name: row.bank_name,
    bank_account: row.bank_account,
    tax_id: row.tax_id,
    notes: row.notes,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (isEdit.value && editingId.value !== null) {
      await supplierApi.update(editingId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await supplierApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchData()
  } catch {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
}

function handleDialogClose() {
  Object.assign(formData, defaultForm())
}

async function handleDelete(row: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除供应商「${row.name}」吗？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' },
    )
    await supplierApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // cancelled or error handled by interceptor
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.supplier-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
