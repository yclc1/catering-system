<template>
  <div class="product-page">
    <SearchBar
      v-model:keyword="queryParams.keyword"
      placeholder="搜索产品编码/名称..."
      @search="handleSearch"
      @reset="handleReset"
    >
      <el-select
        v-model="queryParams.category_id"
        placeholder="全部分类"
        clearable
        style="width: 160px"
      >
        <el-option
          v-for="item in categoryOptions"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        />
      </el-select>
    </SearchBar>

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
          v-permission="'product:create'"
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          新增产品
        </el-button>
      </template>

      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="name" label="名称" min-width="150" />
      <el-table-column prop="category_name" label="分类" width="120" />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column prop="spec" label="规格" width="120" />
      <el-table-column prop="default_supplier_name" label="默认供应商" width="150" />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button
            v-permission="'product:update'"
            type="primary"
            link
            @click="handleEdit(row)"
          >
            编辑
          </el-button>
          <el-button
            v-permission="'product:delete'"
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
      :title="isEdit ? '编辑产品' : '新增产品'"
      :rules="formRules"
      :loading="submitting"
      label-width="100px"
      @submit="handleSubmit"
      @close="handleDialogClose"
    >
      <template #default>
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入产品名称" />
        </el-form-item>
        <el-form-item label="分类" prop="category_id">
          <SelectWithAdd
            v-model="formData.category_id"
            :options="categoryOptions"
            label="分类"
            placeholder="请选择分类"
            :create-api="productCategoryApi.create"
            @created="loadCategoryOptions"
          >
            <template #form="{ form: addForm }">
              <el-form-item label="分类名称">
                <el-input v-model="addForm.name" placeholder="请输入分类名称" />
              </el-form-item>
            </template>
          </SelectWithAdd>
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-input v-model="formData.unit" placeholder="请输入单位（如：斤、个、箱）" />
        </el-form-item>
        <el-form-item label="规格" prop="spec">
          <el-input v-model="formData.spec" placeholder="请输入规格" />
        </el-form-item>
        <el-form-item label="默认供应商" prop="default_supplier_id">
          <el-select
            v-model="formData.default_supplier_id"
            placeholder="请选择默认供应商"
            filterable
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="item in supplierOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
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
import { productApi, productCategoryApi, supplierApi } from '@/api'
import SearchBar from '@/components/common/SearchBar.vue'
import DataTable from '@/components/common/DataTable.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import SelectWithAdd from '@/components/common/SelectWithAdd.vue'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const tableData = ref<any[]>([])
const total = ref(0)

const categoryOptions = ref<{ id: number; name: string }[]>([])
const supplierOptions = ref<{ id: number; name: string }[]>([])

const queryParams = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  category_id: null as number | null,
})

const defaultForm = () => ({
  name: '',
  category_id: null as number | null,
  unit: '',
  spec: '',
  default_supplier_id: null as number | null,
  notes: '',
})

const formData = reactive(defaultForm())

const formRules: FormRules = {
  name: [{ required: true, message: '请输入产品名称', trigger: 'blur' }],
  category_id: [{ required: true, message: '请选择分类', trigger: 'change' }],
  unit: [{ required: true, message: '请输入单位', trigger: 'blur' }],
}

async function fetchData() {
  loading.value = true
  try {
    const res: any = await productApi.list({
      page: queryParams.page,
      page_size: queryParams.page_size,
      keyword: queryParams.keyword || undefined,
      category_id: queryParams.category_id || undefined,
    })
    tableData.value = res.items
    total.value = res.total
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

async function loadCategoryOptions() {
  try {
    const data: any = await productCategoryApi.dropdown()
    categoryOptions.value = data
  } catch {
    // error handled by interceptor
  }
}

async function loadSupplierOptions() {
  try {
    const data: any = await supplierApi.dropdown()
    supplierOptions.value = data
  } catch {
    // error handled by interceptor
  }
}

function handleSearch() {
  queryParams.page = 1
  fetchData()
}

function handleReset() {
  queryParams.page = 1
  queryParams.keyword = ''
  queryParams.category_id = null
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
    category_id: row.category_id,
    unit: row.unit,
    spec: row.spec,
    default_supplier_id: row.default_supplier_id,
    notes: row.notes,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (isEdit.value && editingId.value !== null) {
      await productApi.update(editingId.value, formData)
      ElMessage.success('更新成功')
    } else {
      await productApi.create(formData)
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
      `确定要删除产品「${row.name}」吗？`,
      '删除确认',
      { type: 'warning', confirmButtonText: '确定', cancelButtonText: '取消' },
    )
    await productApi.delete(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {
    // cancelled or error handled by interceptor
  }
}

onMounted(() => {
  fetchData()
  loadCategoryOptions()
  loadSupplierOptions()
})
</script>

<style scoped>
.product-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
