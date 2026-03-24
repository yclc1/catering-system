<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <SearchBar v-model:keyword="keyword" placeholder="搜索客户..." @search="loadData" @reset="resetSearch" />
        <el-button v-permission="'customer:create'" type="primary" @click="openCreate">新增客户</el-button>
      </template>

      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="contact_person" label="联系人" width="100" />
      <el-table-column prop="phone" label="电话" width="130" />
      <el-table-column prop="billing_type" label="计费方式" width="100" />
      <el-table-column label="餐标(元)" width="240">
        <template #default="{ row }">
          早{{ row.breakfast_price }} / 午{{ row.lunch_price }} / 晚{{ row.dinner_price }} / 夜{{ row.supper_price }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button v-permission="'customer:update'" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-permission="'customer:delete'" type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <FormDialog
      v-model:visible="dialogVisible"
      :model-value="form"
      :title="isEdit ? '编辑客户' : '新增客户'"
      :loading="saving"
      label-width="100px"
      @submit="handleSave"
    >
      <template #default>
        <el-form-item label="名称" prop="name" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="form.contact_person" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item label="计费方式">
          <el-select v-model="form.billing_type" style="width:100%">
            <el-option label="按人头" value="per_head" />
            <el-option label="包餐" value="fixed" />
          </el-select>
        </el-form-item>
        <el-divider>餐标设置(元/人)</el-divider>
        <el-row :gutter="12">
          <el-col :span="6"><el-form-item label="早餐"><el-input-number v-model="form.breakfast_price" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="午餐"><el-input-number v-model="form.lunch_price" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="晚餐"><el-input-number v-model="form.dinner_price" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
          <el-col :span="6"><el-form-item label="夜宵"><el-input-number v-model="form.supper_price" :min="0" :precision="2" style="width:100%" /></el-form-item></el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" />
        </el-form-item>
      </template>
    </FormDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import SearchBar from '@/components/common/SearchBar.vue'
import FormDialog from '@/components/common/FormDialog.vue'
import { customerApi } from '@/api'

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

const defaultForm = () => ({
  name: '', contact_person: '', phone: '', address: '',
  billing_type: 'per_head',
  breakfast_price: 0, lunch_price: 0, dinner_price: 0, supper_price: 0,
  notes: '',
})

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    const res: any = await customerApi.list({ page: page.value, page_size: pageSize.value, keyword: keyword.value })
    list.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }
function resetSearch() { keyword.value = ''; page.value = 1; loadData() }

function openCreate() { isEdit.value = false; editId.value = null; form.value = defaultForm(); dialogVisible.value = true }
function openEdit(row: any) {
  isEdit.value = true; editId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (isEdit.value && editId.value) {
      await customerApi.update(editId.value, form.value)
    } else {
      await customerApi.create(form.value)
    }
    ElMessage.success('保存成功'); dialogVisible.value = false; loadData()
  } finally { saving.value = false }
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm('确定删除该客户？', '确认')
  await customerApi.delete(row.id)
  ElMessage.success('已删除'); loadData()
}
</script>
