<template>
  <div>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="库存交易" name="transactions">
        <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
          <template #toolbar>
            <SearchBar v-model:keyword="keyword" placeholder="搜索..." @search="loadData" @reset="resetSearch">
              <el-select v-model="typeFilter" placeholder="类型" clearable style="width:120px" @change="loadData">
                <el-option v-for="(label, key) in INVENTORY_TYPES" :key="key" :label="label" :value="key" />
              </el-select>
            </SearchBar>
            <el-button v-permission="'inventory:create'" type="primary" @click="openCreate">新增交易</el-button>
          </template>

          <el-table-column prop="code" label="编码" width="160" />
          <el-table-column prop="transaction_type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag>{{ INVENTORY_TYPES[row.transaction_type as keyof typeof INVENTORY_TYPES] || row.transaction_type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="transaction_date" label="日期" width="120" :formatter="(r:any) => formatDate(r.transaction_date)" />
          <el-table-column prop="supplier_name" label="供应商" />
          <el-table-column prop="total_amount" label="金额" width="120" align="right" :formatter="(r:any) => formatMoney(r.total_amount)" />
          <el-table-column prop="notes" label="备注" />
        </DataTable>
      </el-tab-pane>

      <el-tab-pane label="库存台账" name="stock">
        <DataTable :data="stockList" :loading="stockLoading">
          <el-table-column prop="product_code" label="商品编码" width="120" />
          <el-table-column prop="product_name" label="商品名称" />
          <el-table-column prop="category_name" label="分类" width="100" />
          <el-table-column prop="product_unit" label="单位" width="80" />
          <el-table-column prop="current_qty" label="当前库存" width="120" align="right" />
          <el-table-column prop="avg_unit_cost" label="平均成本" width="120" align="right" :formatter="(r:any) => formatMoney(r.avg_unit_cost)" />
        </DataTable>
      </el-tab-pane>
    </el-tabs>

    <!-- Create Transaction Dialog -->
    <el-dialog v-model="dialogVisible" title="新增库存交易" width="800px" destroy-on-close>
      <el-form :model="form" label-width="100px">
        <el-form-item label="交易类型" required>
          <el-select v-model="form.transaction_type" style="width:100%">
            <el-option v-for="(label, key) in INVENTORY_TYPES" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
        <el-form-item label="交易日期" required>
          <el-date-picker v-model="form.transaction_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item v-if="['inbound','return'].includes(form.transaction_type)" label="供应商">
          <el-select v-model="form.supplier_id" placeholder="选择供应商" filterable clearable style="width:100%">
            <el-option v-for="s in supplierOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" />
        </el-form-item>

        <el-divider>明细</el-divider>
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
              <el-input :model-value="((item.quantity||0)*(item.unit_price||0)).toFixed(2)" disabled />
            </el-col>
            <el-col :span="4">
              <el-button type="danger" @click="form.items.splice(idx,1)">删除</el-button>
            </el-col>
          </el-row>
        </div>
        <el-button type="primary" plain @click="form.items.push({product_id:null,quantity:0,unit_price:0})">+ 添加明细</el-button>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import { inventoryApi, supplierApi, productApi } from '@/api'
import { formatDate, formatMoney } from '@/utils/format'
import { INVENTORY_TYPES } from '@/utils/constants'

const activeTab = ref('transactions')
const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const typeFilter = ref('')

const stockLoading = ref(false)
const stockList = ref<any[]>([])

const dialogVisible = ref(false)
const saving = ref(false)
const form = ref<any>({ transaction_type: 'outbound', transaction_date: '', supplier_id: null, notes: '', items: [] })

const supplierOptions = ref<any[]>([])
const productOptions = ref<any[]>([])

onMounted(() => {
  loadData()
  loadStock()
  loadDropdowns()
})

watch(activeTab, (val) => {
  if (val === 'stock') loadStock()
})

async function loadData() {
  loading.value = true
  try {
    const res: any = await inventoryApi.list({ page: page.value, page_size: pageSize.value, keyword: keyword.value, transaction_type: typeFilter.value || undefined })
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function loadStock() {
  stockLoading.value = true
  try {
    stockList.value = ((await inventoryApi.stock()) as any).items || []
  } finally {
    stockLoading.value = false
  }
}

async function loadDropdowns() {
  supplierOptions.value = (await supplierApi.dropdown()) as any
  productOptions.value = (await productApi.dropdown()) as any
}

function handlePageChange(p: number, ps: number) {
  page.value = p; pageSize.value = ps; loadData()
}
function resetSearch() {
  keyword.value = ''; typeFilter.value = ''; page.value = 1; loadData()
}

function openCreate() {
  form.value = { transaction_type: 'outbound', transaction_date: '', supplier_id: null, notes: '', items: [{ product_id: null, quantity: 0, unit_price: 0 }] }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.transaction_type || !form.value.transaction_date) { ElMessage.warning('请填写必填项'); return }
  saving.value = true
  try {
    await inventoryApi.create({
      ...form.value,
      items: form.value.items.map((i: any) => ({ product_id: i.product_id, quantity: Number(i.quantity), unit_price: Number(i.unit_price) })),
    })
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadData()
    loadStock()
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.item-row { margin-bottom: 8px; }
</style>
