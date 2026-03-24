<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <div class="toolbar-filters">
          <el-select v-model="customerId" placeholder="客户" filterable clearable style="width:180px" @change="loadData">
            <el-option v-for="c in customerOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-input v-model="monthFilter" placeholder="YYYY-MM" style="width:120px" @keyup.enter="loadData" />
          <el-button type="primary" @click="loadData">搜索</el-button>
        </div>
        <div class="toolbar-actions">
          <el-button v-permission="'settlement:create'" type="primary" @click="generateVisible = true">生成结算</el-button>
        </div>
      </template>

      <el-table-column prop="customer_name" label="客户" />
      <el-table-column prop="settlement_month" label="结算月份" width="110" />
      <el-table-column prop="total_breakfast_count" label="早餐(人次)" width="100" align="right" />
      <el-table-column prop="total_lunch_count" label="午餐(人次)" width="100" align="right" />
      <el-table-column prop="total_dinner_count" label="晚餐(人次)" width="100" align="right" />
      <el-table-column prop="total_supper_count" label="夜宵(人次)" width="100" align="right" />
      <el-table-column prop="total_amount" label="小计" width="110" align="right" :formatter="(r:any) => formatMoney(r.total_amount)" />
      <el-table-column prop="adjustment_amount" label="调整" width="100" align="right" :formatter="(r:any) => formatMoney(r.adjustment_amount)" />
      <el-table-column prop="final_amount" label="应收" width="110" align="right" :formatter="(r:any) => formatMoney(r.final_amount)" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType('settlement', row.status) as any">{{ statusLabel('settlement', row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status==='draft'" v-permission="'settlement:update'" size="small" @click="openEdit(row)">调整</el-button>
          <el-button v-if="row.status==='draft'" v-permission="'settlement:confirm'" type="success" size="small" @click="handleConfirm(row)">确认</el-button>
          <el-button v-permission="'settlement:export'" size="small" @click="handleExport(row)">导出</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <!-- Generate Dialog -->
    <el-dialog v-model="generateVisible" title="生成月度结算" width="400px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="客户" required>
          <el-select v-model="genForm.customer_id" placeholder="选择客户" filterable style="width:100%">
            <el-option v-for="c in customerOptions" :key="c.id" :label="c.name" :value="c.id" />
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

    <!-- Adjust Dialog -->
    <el-dialog v-model="editVisible" title="调整结算" width="400px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="调整金额">
          <el-input-number v-model="editForm.adjustment_amount" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.notes" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import { settlementApi, customerApi } from '@/api'
import { formatMoney, statusLabel, statusType } from '@/utils/format'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const customerId = ref<number | null>(null)
const monthFilter = ref('')
const customerOptions = ref<any[]>([])

const generateVisible = ref(false)
const generating = ref(false)
const genForm = ref({ customer_id: null as number | null, month: '' })

const editVisible = ref(false)
const saving = ref(false)
const editId = ref<number | null>(null)
const editForm = ref({ adjustment_amount: 0, notes: '' })

onMounted(() => { loadData(); loadCustomers() })
async function loadCustomers() { customerOptions.value = (await customerApi.dropdown()) as any }

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (customerId.value) params.customer_id = customerId.value
    if (monthFilter.value) params.month = monthFilter.value
    const res: any = await settlementApi.list(params)
    list.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }

async function handleGenerate() {
  if (!genForm.value.customer_id || !genForm.value.month) { ElMessage.warning('请填写完整'); return }
  generating.value = true
  try {
    await settlementApi.generate(genForm.value)
    ElMessage.success('结算已生成'); generateVisible.value = false; loadData()
  } finally { generating.value = false }
}

function openEdit(row: any) {
  editId.value = row.id; editForm.value = { adjustment_amount: row.adjustment_amount || 0, notes: row.notes || '' }
  editVisible.value = true
}

async function handleSaveEdit() {
  if (!editId.value) return
  saving.value = true
  try {
    await settlementApi.update(editId.value, editForm.value)
    ElMessage.success('已保存'); editVisible.value = false; loadData()
  } finally { saving.value = false }
}

async function handleConfirm(row: any) {
  await ElMessageBox.confirm('确认后不可修改，是否继续？', '确认结算')
  await settlementApi.confirm(row.id)
  ElMessage.success('结算已确认'); loadData()
}

async function handleExport(row: any) {
  const res = await settlementApi.export(row.id) as any
  const url = URL.createObjectURL(new Blob([res]))
  const a = document.createElement('a'); a.href = url
  a.download = `结算_${row.customer_name}_${row.settlement_month}.xlsx`
  a.click(); URL.revokeObjectURL(url)
}
</script>

<style scoped>
.toolbar-filters, .toolbar-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
</style>
