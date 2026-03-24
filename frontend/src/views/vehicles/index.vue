<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <SearchBar v-model:keyword="keyword" placeholder="搜索车牌号..." @search="loadData" @reset="resetSearch" />
        <el-button v-permission="'vehicle:create'" type="primary" @click="openCreate">新增车辆</el-button>
      </template>

      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="plate_number" label="车牌号" width="120" />
      <el-table-column prop="brand" label="品牌" />
      <el-table-column prop="model" label="型号" />
      <el-table-column prop="current_mileage" label="里程(km)" width="110" align="right" />
      <el-table-column prop="insurance_expiry_date" label="保险到期" width="120" />
      <el-table-column prop="next_maintenance_date" label="下次保养" width="120" />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" @click="openMaintenance(row)">保养</el-button>
          <el-button size="small" @click="openInsurance(row)">保险</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <!-- Vehicle Create/Edit -->
    <FormDialog v-model:visible="dialogVisible" :model-value="form" :title="isEdit ? '编辑车辆' : '新增车辆'" :loading="saving" @submit="handleSave">
      <template #default>
        <el-form-item label="车牌号" required><el-input v-model="form.plate_number" /></el-form-item>
        <el-form-item label="品牌"><el-input v-model="form.brand" /></el-form-item>
        <el-form-item label="型号"><el-input v-model="form.model" /></el-form-item>
        <el-form-item label="当前里程"><el-input-number v-model="form.current_mileage" :min="0" style="width:100%" /></el-form-item>
        <el-form-item label="保险到期"><el-date-picker v-model="form.insurance_expiry_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="下次保养"><el-date-picker v-model="form.next_maintenance_date" type="date" value-format="YYYY-MM-DD" style="width:100%" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" /></el-form-item>
      </template>
    </FormDialog>

    <!-- Maintenance Dialog -->
    <el-dialog v-model="maintenanceVisible" :title="`保养记录 - ${selectedVehicle?.plate_number || ''}`" width="700px" destroy-on-close>
      <el-table :data="maintenanceList" stripe border>
        <el-table-column prop="maintenance_date" label="日期" width="120" />
        <el-table-column prop="maintenance_type" label="类型" width="100" />
        <el-table-column prop="cost" label="费用" width="100" align="right" :formatter="(r:any) => formatMoney(r.cost)" />
        <el-table-column prop="mileage_at_maintenance" label="里程" width="100" />
        <el-table-column prop="description" label="描述" />
      </el-table>
      <el-divider>添加保养记录</el-divider>
      <el-form :model="maintenanceForm" label-width="100px" inline>
        <el-form-item label="日期"><el-date-picker v-model="maintenanceForm.maintenance_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="类型"><el-input v-model="maintenanceForm.maintenance_type" style="width:100px" /></el-form-item>
        <el-form-item label="费用"><el-input-number v-model="maintenanceForm.cost" :min="0" :precision="2" /></el-form-item>
        <el-form-item label="里程"><el-input-number v-model="maintenanceForm.mileage_at_maintenance" :min="0" /></el-form-item>
        <el-form-item label="下次保养"><el-date-picker v-model="maintenanceForm.next_maintenance_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="maintenanceForm.description" /></el-form-item>
        <el-button type="primary" @click="addMaintenance">添加</el-button>
      </el-form>
    </el-dialog>

    <!-- Insurance Dialog -->
    <el-dialog v-model="insuranceVisible" :title="`保险记录 - ${selectedVehicle?.plate_number || ''}`" width="700px" destroy-on-close>
      <el-table :data="insuranceList" stripe border>
        <el-table-column prop="company" label="保险公司" />
        <el-table-column prop="policy_no" label="保单号" width="160" />
        <el-table-column prop="start_date" label="开始日期" width="120" />
        <el-table-column prop="end_date" label="结束日期" width="120" />
        <el-table-column prop="premium" label="保费" width="100" align="right" :formatter="(r:any) => formatMoney(r.premium)" />
      </el-table>
      <el-divider>添加保险记录</el-divider>
      <el-form :model="insuranceForm" label-width="80px" inline>
        <el-form-item label="类型" required>
          <el-select v-model="insuranceForm.insurance_type" style="width:120px">
            <el-option label="交强险" value="交强险" />
            <el-option label="商业险" value="商业险" />
            <el-option label="综合险" value="综合险" />
          </el-select>
        </el-form-item>
        <el-form-item label="公司"><el-input v-model="insuranceForm.company" /></el-form-item>
        <el-form-item label="保单号"><el-input v-model="insuranceForm.policy_no" /></el-form-item>
        <el-form-item label="开始"><el-date-picker v-model="insuranceForm.start_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="结束"><el-date-picker v-model="insuranceForm.end_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
        <el-form-item label="保费"><el-input-number v-model="insuranceForm.premium" :min="0" :precision="2" /></el-form-item>
        <el-button type="primary" @click="addInsurance">添加</el-button>
      </el-form>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import { vehicleApi } from '@/api'
import { formatMoney } from '@/utils/format'

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

const selectedVehicle = ref<any>(null)
const maintenanceVisible = ref(false)
const maintenanceList = ref<any[]>([])
const maintenanceForm = ref<any>({})

const insuranceVisible = ref(false)
const insuranceList = ref<any[]>([])
const insuranceForm = ref<any>({})

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const res: any = await vehicleApi.list({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    list.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }
function resetSearch() { keyword.value = ''; page.value = 1; loadData() }

function openCreate() { isEdit.value = false; form.value = { plate_number: '', brand: '', model: '', current_mileage: 0, insurance_expiry_date: '', next_maintenance_date: '', notes: '' }; dialogVisible.value = true }
function openEdit(row: any) { isEdit.value = true; editId.value = row.id; form.value = { ...row }; dialogVisible.value = true }

async function handleSave() {
  saving.value = true
  try {
    if (isEdit.value && editId.value) await vehicleApi.update(editId.value, form.value)
    else await vehicleApi.create(form.value)
    ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
  } finally { saving.value = false }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除？', '确认')
  await vehicleApi.delete(row.id); ElMessage.success('已删除'); loadData()
}

async function openMaintenance(row: any) {
  selectedVehicle.value = row
  maintenanceList.value = (await vehicleApi.maintenanceList(row.id)) as any
  maintenanceForm.value = { maintenance_date: '', maintenance_type: '常规保养', cost: 0, mileage_at_maintenance: row.current_mileage, next_maintenance_date: '', description: '' }
  maintenanceVisible.value = true
}

async function addMaintenance() {
  await vehicleApi.createMaintenance(selectedVehicle.value.id, maintenanceForm.value)
  ElMessage.success('已添加')
  maintenanceList.value = (await vehicleApi.maintenanceList(selectedVehicle.value.id)) as any
  loadData()
}

async function openInsurance(row: any) {
  selectedVehicle.value = row
  insuranceList.value = (await vehicleApi.insuranceList(row.id)) as any
  insuranceForm.value = { insurance_type: '商业险', company: '', policy_no: '', start_date: '', end_date: '', premium: 0 }
  insuranceVisible.value = true
}

async function addInsurance() {
  await vehicleApi.createInsurance(selectedVehicle.value.id, insuranceForm.value)
  ElMessage.success('已添加')
  insuranceList.value = (await vehicleApi.insuranceList(selectedVehicle.value.id)) as any
  loadData()
}
</script>
