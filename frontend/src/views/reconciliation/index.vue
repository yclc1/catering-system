<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <div class="toolbar-filters">
          <el-select v-model="supplierId" placeholder="供应商" filterable clearable style="width:200px" @change="loadData">
            <el-option v-for="s in supplierOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
          <el-input v-model="monthFilter" placeholder="YYYY-MM" style="width:120px" @keyup.enter="loadData" />
          <el-button type="primary" @click="loadData">搜索</el-button>
        </div>
        <el-button v-permission="'reconciliation:create'" type="primary" @click="generateVisible = true">生成对账</el-button>
      </template>

      <el-table-column prop="supplier_name" label="供应商" />
      <el-table-column prop="reconciliation_month" label="月份" width="100" />
      <el-table-column prop="total_inbound_amount" label="入库金额" width="120" align="right" :formatter="(r:any) => formatMoney(r.total_inbound_amount)" />
      <el-table-column prop="total_return_amount" label="退货金额" width="120" align="right" :formatter="(r:any) => formatMoney(r.total_return_amount)" />
      <el-table-column prop="net_amount" label="净额" width="120" align="right" :formatter="(r:any) => formatMoney(r.net_amount)" />
      <el-table-column prop="paid_amount" label="已付" width="120" align="right" :formatter="(r:any) => formatMoney(r.paid_amount)" />
      <el-table-column prop="outstanding_amount" label="未付" width="120" align="right" :formatter="(r:any) => formatMoney(r.outstanding_amount)" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 'confirmed' ? 'success' : 'info'">{{ row.status === 'confirmed' ? '已确认' : '草稿' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetails(row)">明细</el-button>
          <el-button v-if="row.status==='draft'" v-permission="'reconciliation:confirm'" type="success" size="small" @click="handleConfirm(row)">确认</el-button>
          <el-button v-permission="'reconciliation:export'" size="small" @click="handleExport(row)">导出</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <el-dialog v-model="generateVisible" title="生成供应商对账" width="400px">
      <el-form label-width="80px">
        <el-form-item label="供应商" required>
          <el-select v-model="genForm.supplier_id" filterable style="width:100%">
            <el-option v-for="s in supplierOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="月份" required>
          <el-date-picker v-model="genForm.month" type="month" value-format="YYYY-MM" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">生成</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="对账明细" width="800px">
      <el-table :data="details" stripe border>
        <el-table-column prop="type" label="类型" width="80" />
        <el-table-column prop="code" label="单号" width="160" />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="amount" label="金额" width="120" align="right" :formatter="(r:any) => formatMoney(r.amount)" />
        <el-table-column prop="notes" label="备注" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import { reconciliationApi, supplierApi } from '@/api'
import { formatMoney } from '@/utils/format'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const supplierId = ref<number | null>(null)
const monthFilter = ref('')
const supplierOptions = ref<any[]>([])

const generateVisible = ref(false)
const generating = ref(false)
const genForm = ref({ supplier_id: null as number | null, month: '' })

const detailVisible = ref(false)
const details = ref<any[]>([])

onMounted(async () => {
  loadData()
  supplierOptions.value = (await supplierApi.dropdown()) as any
})

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (supplierId.value) params.supplier_id = supplierId.value
    if (monthFilter.value) params.month = monthFilter.value
    const res: any = await reconciliationApi.list(params)
    list.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }

async function handleGenerate() {
  if (!genForm.value.supplier_id || !genForm.value.month) { ElMessage.warning('请填写完整'); return }
  generating.value = true
  try {
    await reconciliationApi.generate(genForm.value)
    ElMessage.success('对账已生成'); generateVisible.value = false; loadData()
  } finally { generating.value = false }
}

async function viewDetails(row: any) {
  details.value = (await reconciliationApi.details(row.id)) as any
  detailVisible.value = true
}

async function handleConfirm(row: any) {
  await ElMessageBox.confirm('确认对账？', '确认')
  await reconciliationApi.confirm(row.id)
  ElMessage.success('已确认'); loadData()
}

async function handleExport(row: any) {
  const res = await reconciliationApi.export(row.id) as any
  const url = URL.createObjectURL(new Blob([res]))
  const a = document.createElement('a'); a.href = url
  a.download = `对账_${row.supplier_name}_${row.reconciliation_month}.xlsx`
  a.click(); URL.revokeObjectURL(url)
}
</script>

<style scoped>
.toolbar-filters { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
</style>
