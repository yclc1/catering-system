<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <div class="toolbar-filters">
          <el-select v-model="customerId" placeholder="选择客户" filterable clearable style="width:200px" @change="loadData">
            <el-option v-for="c in customerOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-date-picker v-model="dateRange" type="daterange" value-format="YYYY-MM-DD" start-placeholder="开始日期" end-placeholder="结束日期" style="width:260px" @change="loadData" />
          <el-button type="primary" @click="loadData">搜索</el-button>
        </div>
        <el-button v-permission="'meal:create'" type="primary" @click="openCreate">新增登记</el-button>
      </template>

      <el-table-column prop="customer_name" label="客户" />
      <el-table-column prop="meal_date" label="日期" width="120" />
      <el-table-column label="早餐" width="80" align="right"><template #default="{row}">{{ row.breakfast_count }}</template></el-table-column>
      <el-table-column label="午餐" width="80" align="right"><template #default="{row}">{{ row.lunch_count }}</template></el-table-column>
      <el-table-column label="晚餐" width="80" align="right"><template #default="{row}">{{ row.dinner_count }}</template></el-table-column>
      <el-table-column label="夜宵" width="80" align="right"><template #default="{row}">{{ row.supper_count }}</template></el-table-column>
      <el-table-column prop="daily_total" label="日合计(元)" width="120" align="right" :formatter="(r:any) => formatMoney(r.daily_total)" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="'meal:update'" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-permission="'meal:delete'" type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用餐登记' : '新增用餐登记'" width="500px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="客户" required>
          <el-select v-model="form.customer_id" placeholder="选择客户" filterable style="width:100%">
            <el-option v-for="c in customerOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker v-model="form.meal_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="早餐人数">
          <el-input-number v-model="form.breakfast_count" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="午餐人数">
          <el-input-number v-model="form.lunch_count" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="晚餐人数">
          <el-input-number v-model="form.dinner_count" :min="0" style="width:100%" />
        </el-form-item>
        <el-form-item label="夜宵人数">
          <el-input-number v-model="form.supper_count" :min="0" style="width:100%" />
        </el-form-item>
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
import { mealApi, customerApi } from '@/api'
import { formatMoney } from '@/utils/format'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const customerId = ref<number | null>(null)
const dateRange = ref<string[] | null>(null)
const customerOptions = ref<any[]>([])

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref<number | null>(null)
const saving = ref(false)
const form = ref<any>({ customer_id: null, meal_date: '', breakfast_count: 0, lunch_count: 0, dinner_count: 0, supper_count: 0 })

onMounted(() => { loadData(); loadCustomers() })

async function loadCustomers() { customerOptions.value = (await customerApi.dropdown()) as any }

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (customerId.value) params.customer_id = customerId.value
    if (dateRange.value?.[0]) { params.start_date = dateRange.value[0]; params.end_date = dateRange.value[1] }
    const res: any = await mealApi.list(params)
    list.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }

function openCreate() {
  isEdit.value = false; editId.value = null
  form.value = { customer_id: null, meal_date: '', breakfast_count: 0, lunch_count: 0, dinner_count: 0, supper_count: 0 }
  dialogVisible.value = true
}
function openEdit(row: any) {
  isEdit.value = true; editId.value = row.id
  form.value = { customer_id: row.customer_id, meal_date: row.meal_date, breakfast_count: row.breakfast_count, lunch_count: row.lunch_count, dinner_count: row.dinner_count, supper_count: row.supper_count }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.customer_id || !form.value.meal_date) { ElMessage.warning('请填写必填项'); return }
  saving.value = true
  try {
    if (isEdit.value && editId.value) { await mealApi.update(editId.value, form.value) }
    else { await mealApi.create(form.value) }
    ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
  } finally { saving.value = false }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除？', '确认')
  await mealApi.delete(row.id); ElMessage.success('已删除'); loadData()
}
</script>

<style scoped>
.toolbar-filters { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
</style>
