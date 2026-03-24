<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <SearchBar v-model:keyword="keyword" placeholder="搜索合同..." @search="loadData" @reset="resetSearch">
          <el-select v-model="statusFilter" placeholder="状态" clearable style="width:120px" @change="loadData">
            <el-option label="草稿" value="draft" />
            <el-option label="生效中" value="active" />
            <el-option label="已到期" value="expired" />
            <el-option label="已终止" value="terminated" />
          </el-select>
        </SearchBar>
        <el-button v-permission="'contract:create'" type="primary" @click="openCreate">新增合同</el-button>
      </template>

      <el-table-column prop="code" label="编码" width="140" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="contract_type" label="类型" width="100" />
      <el-table-column label="对方" width="120">
        <template #default="{ row }">{{ row.customer_name || row.supplier_name || '-' }}</template>
      </el-table-column>
      <el-table-column prop="start_date" label="开始" width="110" />
      <el-table-column prop="end_date" label="结束" width="110" />
      <el-table-column prop="amount" label="金额" width="120" align="right" :formatter="(r:any) => formatMoney(r.amount)" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType('contract', row.status) as any">{{ statusLabel('contract', row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="'contract:update'" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-permission="'contract:delete'" type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑合同' : '新增合同'" width="600px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="标题" required><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="合同类型">
          <el-select v-model="form.contract_type" style="width:100%">
            <el-option label="客户合同" value="customer" />
            <el-option label="供应商合同" value="supplier" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="对方类型">
          <el-radio-group v-model="form.counterparty_type">
            <el-radio value="customer">客户</el-radio>
            <el-radio value="supplier">供应商</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.counterparty_type==='customer'" label="客户">
          <el-select v-model="form.customer_id" filterable clearable style="width:100%">
            <el-option v-for="c in customerOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.counterparty_type==='supplier'" label="供应商">
          <el-select v-model="form.supplier_id" filterable clearable style="width:100%">
            <el-option v-for="s in supplierOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12"><el-form-item label="开始日期" required><el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item></el-col>
          <el-col :span="12"><el-form-item label="结束日期" required><el-date-picker v-model="form.end_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="金额"><el-input-number v-model="form.amount" :min="0" :precision="2" style="width:100%" /></el-form-item>
        <el-form-item label="提醒天数"><el-input-number v-model="form.reminder_days_before" :min="1" :max="365" style="width:100%" /></el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width:100%">
            <el-option label="草稿" value="draft" />
            <el-option label="生效中" value="active" />
            <el-option label="已到期" value="expired" />
            <el-option label="已终止" value="terminated" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import { contractApi, customerApi, supplierApi } from '@/api'
import { formatMoney, statusLabel, statusType } from '@/utils/format'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const statusFilter = ref('')

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const form = ref<any>({})

const customerOptions = ref<any[]>([])
const supplierOptions = ref<any[]>([])

onMounted(async () => {
  loadData()
  customerOptions.value = (await customerApi.dropdown()) as any
  supplierOptions.value = (await supplierApi.dropdown()) as any
})

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value, keyword: keyword.value }
    if (statusFilter.value) params.status = statusFilter.value
    const res: any = await contractApi.list(params)
    list.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }
function resetSearch() { keyword.value = ''; statusFilter.value = ''; page.value = 1; loadData() }

function openCreate() {
  isEdit.value = false; editId.value = null
  form.value = { title: '', contract_type: 'customer', counterparty_type: 'customer', customer_id: null, supplier_id: null, start_date: '', end_date: '', amount: 0, reminder_days_before: 30, status: 'draft', notes: '' }
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEdit.value = true; editId.value = row.id; form.value = { ...row }; dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (isEdit.value && editId.value) await contractApi.update(editId.value, form.value)
    else await contractApi.create(form.value)
    ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
  } finally { saving.value = false }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除？', '确认')
  await contractApi.delete(row.id); ElMessage.success('已删除'); loadData()
}
</script>
