<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <SearchBar v-model:keyword="keyword" placeholder="搜索采购单..." @search="loadData" @reset="resetSearch">
          <el-select v-model="statusFilter" placeholder="状态" clearable style="width:120px" @change="loadData">
            <el-option label="草稿" value="draft" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </SearchBar>
        <el-button v-permission="'purchase:create'" type="primary" @click="openCreate">新增采购单</el-button>
      </template>

      <el-table-column prop="code" label="编码" width="160" />
      <el-table-column prop="supplier_name" label="供应商" />
      <el-table-column prop="order_date" label="采购日期" width="120" :formatter="(r:any) => formatDate(r.order_date)" />
      <el-table-column prop="total_amount" label="总金额" width="120" align="right" :formatter="(r:any) => formatMoney(r.total_amount)" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType('purchase', row.status) as any">{{ statusLabel('purchase', row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'draft'" v-permission="'purchase:confirm'" type="success" size="small" @click="handleConfirm(row)">确认</el-button>
          <el-button v-if="row.status === 'draft'" v-permission="'purchase:update'" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="row.status === 'draft'" v-permission="'purchase:delete'" type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑采购单' : '新增采购单'" width="800px" :fullscreen="isMobile" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="供应商" required>
          <SelectWithAdd
            v-model="form.supplier_id"
            :options="supplierOptions"
            label="供应商"
            placeholder="选择供应商"
            :create-api="supplierApi.create"
            @created="loadSuppliers"
          >
            <template #form="{ form: addForm }">
              <el-form-item label="名称"><el-input v-model="addForm.name" /></el-form-item>
              <el-form-item label="联系人"><el-input v-model="addForm.contact_person" /></el-form-item>
              <el-form-item label="电话"><el-input v-model="addForm.phone" /></el-form-item>
            </template>
          </SelectWithAdd>
        </el-form-item>
        <el-form-item label="采购日期" required>
          <el-date-picker v-model="form.order_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" />
        </el-form-item>

        <el-divider>采购明细</el-divider>
        <div v-for="(item, idx) in form.items" :key="idx" class="item-row">
          <el-row :gutter="8">
            <el-col :span="8">
              <el-select v-model="item.product_id" placeholder="商品" filterable style="width:100%">
                <el-option v-for="p in productOptions" :key="p.id" :label="p.name" :value="p.id" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-input-number v-model="item.quantity" :min="0" :precision="3" placeholder="数量" controls-position="right" style="width:100%" />
            </el-col>
            <el-col :span="4">
              <el-input-number v-model="item.unit_price" :min="0" :precision="4" placeholder="单价" controls-position="right" style="width:100%" />
            </el-col>
            <el-col :span="4">
              <el-input :model-value="((item.quantity || 0) * (item.unit_price || 0)).toFixed(2)" disabled placeholder="金额" />
            </el-col>
            <el-col :span="4">
              <el-button type="danger" @click="form.items.splice(idx, 1)">删除</el-button>
            </el-col>
          </el-row>
        </div>
        <el-button type="primary" plain @click="form.items.push({ product_id: null, quantity: 0, unit_price: 0 })">
          + 添加明细
        </el-button>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useWindowSize } from '@vueuse/core'
import { ElMessage, ElMessageBox } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import SelectWithAdd from '@/components/common/SelectWithAdd.vue'
import { purchaseApi, supplierApi, productApi } from '@/api'
import { formatDate, formatMoney, statusLabel, statusType } from '@/utils/format'

const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)

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
const form = ref<any>({ supplier_id: null, order_date: '', notes: '', items: [] })

const supplierOptions = ref<any[]>([])
const productOptions = ref<any[]>([])

onMounted(() => {
  loadData()
  loadSuppliers()
  loadProducts()
})

async function loadData() {
  loading.value = true
  try {
    const res: any = await purchaseApi.list({ page: page.value, page_size: pageSize.value, keyword: keyword.value, status: statusFilter.value || undefined })
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function loadSuppliers() {
  supplierOptions.value = (await supplierApi.dropdown()) as any
}
async function loadProducts() {
  productOptions.value = (await productApi.dropdown()) as any
}

function handlePageChange(p: number, ps: number) {
  page.value = p
  pageSize.value = ps
  loadData()
}

function resetSearch() {
  keyword.value = ''
  statusFilter.value = ''
  page.value = 1
  loadData()
}

function openCreate() {
  isEdit.value = false
  editId.value = null
  form.value = { supplier_id: null, order_date: '', notes: '', items: [{ product_id: null, quantity: 0, unit_price: 0 }] }
  dialogVisible.value = true
}

async function openEdit(row: any) {
  isEdit.value = true
  editId.value = row.id
  const detail: any = await purchaseApi.get(row.id)
  form.value = {
    supplier_id: detail.supplier_id,
    order_date: detail.order_date,
    notes: detail.notes,
    items: detail.items?.map((i: any) => ({ product_id: i.product_id, quantity: i.quantity, unit_price: i.unit_price })) || [],
  }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.supplier_id || !form.value.order_date) {
    ElMessage.warning('请填写必填项')
    return
  }
  saving.value = true
  try {
    const data = {
      ...form.value,
      items: form.value.items.map((i: any) => ({
        product_id: i.product_id,
        quantity: Number(i.quantity),
        unit_price: Number(i.unit_price),
      })),
    }
    if (isEdit.value && editId.value) {
      await purchaseApi.update(editId.value, data)
    } else {
      await purchaseApi.create(data)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

async function handleConfirm(row: any) {
  await ElMessageBox.confirm('确认此采购单将自动生成入库记录，是否继续？', '确认采购单')
  await purchaseApi.confirm(row.id)
  ElMessage.success('采购单已确认')
  loadData()
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除该采购单？', '确认删除')
  await purchaseApi.delete(row.id)
  ElMessage.success('已删除')
  loadData()
}
</script>

<style scoped>
.item-row { margin-bottom: 8px; }
</style>
