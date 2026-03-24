<template>
  <div>
    <DataTable :data="list" :loading="loading" :total="total" :page="page" :page-size="pageSize" @page-change="handlePageChange">
      <template #toolbar>
        <div class="toolbar-filters">
          <el-select v-model="statusFilter" placeholder="状态" clearable style="width:120px" @change="loadData">
            <el-option label="待审批" value="pending" />
            <el-option label="已通过" value="approved" />
            <el-option label="已驳回" value="rejected" />
          </el-select>
        </div>
        <el-button v-permission="'expense:create'" type="primary" @click="openCreate">新增费用</el-button>
      </template>

      <el-table-column prop="code" label="编码" width="160" />
      <el-table-column prop="title" label="标题" />
      <el-table-column prop="category_name" label="类别" width="100" />
      <el-table-column prop="applicant_name" label="申请人" width="100" />
      <el-table-column prop="approver_name" label="审核人" width="100" />
      <el-table-column prop="total_amount" label="金额" width="120" align="right" :formatter="(r:any) => formatMoney(r.total_amount)" />
      <el-table-column prop="expense_date" label="日期" width="120" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="statusType('expense', row.status) as any">{{ statusLabel('expense', row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">查看</el-button>
          <el-button v-if="row.status==='pending'" v-permission="'expense:approve'" type="success" size="small" @click="handleApprove(row)">通过</el-button>
          <el-button v-if="row.status==='pending'" v-permission="'expense:reject'" type="danger" size="small" @click="openReject(row)">驳回</el-button>
        </template>
      </el-table-column>
    </DataTable>

    <!-- Create Dialog -->
    <el-dialog v-model="createVisible" title="新增费用审批" width="700px" destroy-on-close>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required><el-input v-model="form.title" /></el-form-item>
        <el-form-item label="类别" required>
          <SelectWithAdd v-model="form.category_id" :options="categoryOptions" label="费用类别" :create-api="expenseCategoryApi.create" @created="loadCategories">
            <template #form="{ form: addForm }">
              <el-form-item label="名称"><el-input v-model="addForm.name" /></el-form-item>
            </template>
          </SelectWithAdd>
        </el-form-item>
        <el-form-item label="审核人" required>
          <el-select v-model="form.approver_id" filterable style="width:100%">
            <el-option v-for="u in userOptions" :key="u.id" :label="u.name" :value="u.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="日期" required>
          <el-date-picker v-model="form.expense_date" type="date" value-format="YYYY-MM-DD" style="width:100%" />
        </el-form-item>
        <el-form-item label="总金额" required>
          <el-input-number v-model="form.total_amount" :min="0" :precision="2" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="照片">
          <el-upload
            v-model:file-list="fileList"
            action="#"
            list-type="picture-card"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>
        <el-divider>费用明细</el-divider>
        <div v-for="(item, idx) in form.items" :key="idx" style="margin-bottom:8px">
          <el-row :gutter="8">
            <el-col :span="10"><el-input v-model="item.description" placeholder="描述" /></el-col>
            <el-col :span="6"><el-input-number v-model="item.amount" :min="0" :precision="2" placeholder="金额" style="width:100%" /></el-col>
            <el-col :span="4"><el-button type="danger" @click="form.items.splice(idx,1)">删除</el-button></el-col>
          </el-row>
        </div>
        <el-button type="primary" plain @click="form.items.push({description:'',amount:0})">+ 添加明细</el-button>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreate">提交</el-button>
      </template>
    </el-dialog>

    <!-- Detail Dialog -->
    <el-dialog v-model="detailVisible" title="费用详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="编码">{{ detailData.code }}</el-descriptions-item>
        <el-descriptions-item label="标题">{{ detailData.title }}</el-descriptions-item>
        <el-descriptions-item label="类别">{{ detailData.category_name }}</el-descriptions-item>
        <el-descriptions-item label="金额">{{ formatMoney(detailData.total_amount) }}</el-descriptions-item>
        <el-descriptions-item label="申请人">{{ detailData.applicant_name }}</el-descriptions-item>
        <el-descriptions-item label="审核人">{{ detailData.approver_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ statusLabel('expense', detailData.status) }}</el-descriptions-item>
        <el-descriptions-item label="日期">{{ detailData.expense_date }}</el-descriptions-item>
        <el-descriptions-item v-if="detailData.reject_reason" label="驳回原因" :span="2">{{ detailData.reject_reason }}</el-descriptions-item>
        <el-descriptions-item v-if="detailData.notes" label="备注" :span="2">{{ detailData.notes }}</el-descriptions-item>
        <el-descriptions-item label="照片" :span="2" v-if="detailData.photos?.length">
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <el-image v-for="(url, i) in detailData.photos" :key="i" :src="url" :preview-src-list="detailData.photos" style="width:100px;height:100px" fit="cover" />
          </div>
        </el-descriptions-item>
      </el-descriptions>
      <el-table v-if="detailData.items?.length" :data="detailData.items" style="margin-top:12px" stripe border>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="amount" label="金额" width="120" align="right" :formatter="(r:any) => formatMoney(r.amount)" />
      </el-table>
    </el-dialog>

    <!-- Reject Dialog -->
    <el-dialog v-model="rejectVisible" title="驳回原因" width="400px">
      <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请输入驳回原因" />
      <template #footer>
        <el-button @click="rejectVisible = false">取消</el-button>
        <el-button type="danger" @click="handleReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { UploadFile } from 'element-plus'
import DataTable from '@/components/common/DataTable.vue'
import SelectWithAdd from '@/components/common/SelectWithAdd.vue'
import { expenseApi, expenseCategoryApi, userApi } from '@/api'
import { formatMoney, statusLabel, statusType } from '@/utils/format'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const statusFilter = ref('')

const createVisible = ref(false)
const saving = ref(false)
const form = ref<any>({})

const categoryOptions = ref<any[]>([])
const userOptions = ref<any[]>([])
const fileList = ref<UploadFile[]>([])

const detailVisible = ref(false)
const detailData = ref<any>({})

const rejectVisible = ref(false)
const rejectId = ref<number | null>(null)
const rejectReason = ref('')

onMounted(async () => {
  loadData()
  loadCategories()
  userOptions.value = (await userApi.dropdown()) as any
})

async function loadCategories() { categoryOptions.value = (await expenseCategoryApi.dropdown()) as any }

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (statusFilter.value) params.status = statusFilter.value
    const res: any = await expenseApi.list(params)
    list.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

function handlePageChange(p: number, ps: number) { page.value = p; pageSize.value = ps; loadData() }

function openCreate() {
  form.value = { title: '', category_id: null, approver_id: null, expense_date: '', total_amount: 0, notes: '', photos: [], items: [{ description: '', amount: 0 }] }
  fileList.value = []
  createVisible.value = true
}

function handleFileChange(file: UploadFile) {
  const reader = new FileReader()
  reader.onload = (e) => {
    form.value.photos.push(e.target?.result as string)
  }
  reader.readAsDataURL(file.raw!)
}

function handleFileRemove(file: UploadFile) {
  const idx = fileList.value.findIndex(f => f.uid === file.uid)
  if (idx > -1) form.value.photos.splice(idx, 1)
}

async function handleCreate() {
  saving.value = true
  try {
    await expenseApi.create(form.value)
    ElMessage.success('已提交'); createVisible.value = false; loadData()
  } finally { saving.value = false }
}

async function viewDetail(row: any) {
  detailData.value = (await expenseApi.get(row.id)) as any
  detailVisible.value = true
}

async function handleApprove(row: any) {
  await ElMessageBox.confirm('确认通过？', '审批')
  await expenseApi.approve(row.id)
  ElMessage.success('已通过'); loadData()
}

function openReject(row: any) { rejectId.value = row.id; rejectReason.value = ''; rejectVisible.value = true }

async function handleReject() {
  if (!rejectReason.value) { ElMessage.warning('请输入原因'); return }
  await expenseApi.reject(rejectId.value!, { reason: rejectReason.value })
  ElMessage.success('已驳回'); rejectVisible.value = false; loadData()
}
</script>

<style scoped>
.toolbar-filters { display: flex; gap: 8px; align-items: center; }
</style>
