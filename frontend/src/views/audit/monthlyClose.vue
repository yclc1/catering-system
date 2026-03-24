<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>月结管理</span>
          <el-button v-permission="'monthly_close:close'" type="primary" @click="closeVisible = true">关闭月份</el-button>
        </div>
      </template>
      <el-table :data="list" v-loading="loading" stripe border>
        <el-table-column prop="close_month" label="月份" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'closed' ? 'danger' : 'success'">{{ row.status === 'closed' ? '已关闭' : '已重开' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="closed_at" label="关闭时间" width="180" />
        <el-table-column prop="reopened_at" label="重开时间" width="180" />
        <el-table-column prop="notes" label="备注" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button v-if="row.status==='closed'" v-permission="'monthly_close:reopen'" size="small" @click="openReopen(row)">重新打开</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="closeVisible" title="关闭月份" width="400px">
      <el-form label-width="60px">
        <el-form-item label="月份">
          <el-date-picker v-model="closeMonth" type="month" value-format="YYYY-MM" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeVisible = false">取消</el-button>
        <el-button type="danger" @click="handleClose">确认关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="reopenVisible" title="重新打开月份" width="400px">
      <el-form label-width="60px">
        <el-form-item label="原因">
          <el-input v-model="reopenReason" type="textarea" :rows="3" placeholder="请输入重新打开的原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reopenVisible = false">取消</el-button>
        <el-button type="primary" @click="handleReopen">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { monthlyCloseApi } from '@/api'

const loading = ref(false)
const list = ref<any[]>([])

const closeVisible = ref(false)
const closeMonth = ref('')

const reopenVisible = ref(false)
const reopenId = ref<number | null>(null)
const reopenReason = ref('')

onMounted(loadData)

async function loadData() {
  loading.value = true
  try { list.value = (await monthlyCloseApi.list()) as any } finally { loading.value = false }
}

async function handleClose() {
  if (!closeMonth.value) { ElMessage.warning('请选择月份'); return }
  await ElMessageBox.confirm(`确定关闭 ${closeMonth.value}？关闭后该月数据将无法修改。`, '确认关闭')
  await monthlyCloseApi.close({ month: closeMonth.value })
  ElMessage.success('月份已关闭'); closeVisible.value = false; loadData()
}

function openReopen(row: any) { reopenId.value = row.id; reopenReason.value = ''; reopenVisible.value = true }

async function handleReopen() {
  if (!reopenReason.value) { ElMessage.warning('请输入原因'); return }
  await monthlyCloseApi.reopen(reopenId.value!, { reason: reopenReason.value })
  ElMessage.success('月份已重新打开'); reopenVisible.value = false; loadData()
}
</script>
