<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <div class="toolbar-filters">
          <el-select v-model="directionFilter" placeholder="方向" clearable style="width:120px" @change="loadData">
            <el-option label="收入" value="inbound" />
            <el-option label="支出" value="outbound" />
          </el-select>
          <el-button type="primary" @click="loadData">搜索</el-button>
        </div>
        <el-button v-permission="'payment:create'" type="primary" @click="openCreate">新增记录</el-button>
      </template>

      <el-table-column prop="code" label="编码" width="160" />
      <el-table-column prop="direction" label="方向" width="80">
        <template #default="{ row }">
          <el-tag :type="row.direction === 'inbound' ? 'success' : 'danger'">{{ row.direction === 'inbound' ? '收入' : '支出' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="account_name" label="账户" />
      <el-table-column prop="amount" label="金额" width="120" align="right" :formatter="(r:any) => formatMoney(r.amount)" />
      <el-table-column prop="payment_date" label="日期" width="120" />
      <el-table-column label="对方">
        <template #default="{ row }">{{ row.customer_name || row.supplier_name || '-' }}</template>
      </el-table-column>
      <el-table-column prop="notes" label="备注" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="'payment:update'" size="small" @click="openEdit(row)">编辑</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑收付款' : '新增收付款'" width="500px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="方向" required>
          <el-radio-group v-model="form.direction">
            <el-radio value="inbound">收入</el-radio>
            <el-radio value="outbound">支出</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="账户" required>
          <el-select v-model="form.account_id" style="width:100%" filterable>
            <el-option v-for="a in accountOptions" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额" required>
          <el-input-number v-model="form.amount" :min="0.01" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker v-model="form.payment_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="对方类型">
          <el-radio-group v-model="form.counterparty_type" @change="form.customer_id = null; form.supplier_id = null">
            <el-radio value="customer">客户</el-radio>
            <el-radio value="supplier">供应商</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.counterparty_type === 'customer'" label="客户">
          <el-select v-model="form.customer_id" filterable style="width:100%">
            <el-option v-for="c in customerOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.counterparty_type === 'supplier'" label="供应商">
          <el-select v-model="form.supplier_id" filterable style="width:100%">
            <el-option v-for="s in supplierOptions" :key="s.id" :label="s.name" :value="s.id" />
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
import { ElMessage } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import { paymentApi, accountApi, customerApi, supplierApi } from '@/api'
import { formatMoney } from '@/utils/format'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const directionFilter = ref('')

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const form = ref<any>({})

const accountOptions = ref<any[]>([])
const customerOptions = ref<any[]>([])
const supplierOptions = ref<any[]>([])

onMounted(async () => {
  loadData()
  accountOptions.value = (await accountApi.dropdown()) as any
  customerOptions.value = (await customerApi.dropdown()) as any
  supplierOptions.value = (await supplierApi.dropdown()) as any
})

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (directionFilter.value) params.direction = directionFilter.value
    const res: any = await paymentApi.list(params)
    list.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }

function openCreate() {
  isEdit.value = false; editId.value = null
  form.value = { direction: 'inbound', account_id: null, amount: 0, payment_date: '', counterparty_type: 'customer', customer_id: null, supplier_id: null, notes: '' }
  dialogVisible.value = true
}

function openEdit(row: any) {
  isEdit.value = true; editId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.account_id || !form.value.amount || !form.value.payment_date) { ElMessage.warning('请填写必填项'); return }
  saving.value = true
  try {
    if (isEdit.value && editId.value) await paymentApi.update(editId.value, form.value)
    else await paymentApi.create(form.value)
    ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
  } finally { saving.value = false }
}
</script>

<style scoped>
.toolbar-filters { display: flex; gap: 8px; align-items: center; }
</style>
