<template>
  <div class="dashboard" v-loading="loading">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #409eff">
            <el-icon :size="28"><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">本月销售额</div>
            <div class="stat-value">¥{{ formatMoney(dashboardData.monthly_sales) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #e6a23c">
            <el-icon :size="28"><ShoppingCart /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">本月采购额</div>
            <div class="stat-value">¥{{ formatMoney(dashboardData.monthly_purchases) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #67c23a">
            <el-icon :size="28"><Wallet /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">本月收入</div>
            <div class="stat-value">¥{{ formatMoney(dashboardData.monthly_income) }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon" style="background: #f56c6c">
            <el-icon :size="28"><Money /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-label">本月支出</div>
            <div class="stat-value">¥{{ formatMoney(dashboardData.monthly_expenses) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 今日用餐统计 -->
    <el-row :gutter="16" class="section-row">
      <el-col :xs="24" :md="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>今日用餐人数</span>
            </div>
          </template>
          <el-row :gutter="16" class="meal-counts">
            <el-col :xs="12" :sm="4" v-for="item in mealItems" :key="item.key">
              <div class="meal-item">
                <div class="meal-count">{{ dashboardData.today_meals?.[item.key] ?? 0 }}</div>
                <div class="meal-label">{{ item.label }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 合同提醒 + 车辆提醒 -->
    <el-row :gutter="16" class="section-row">
      <el-col :xs="24" :md="12">
        <el-card shadow="hover" class="reminder-card" v-loading="contractLoading">
          <template #header>
            <div class="card-header">
              <span>合同到期提醒</span>
              <el-tag type="danger" v-if="contractReminders.length" size="small">
                {{ contractReminders.length }}
              </el-tag>
            </div>
          </template>
          <div v-if="contractReminders.length === 0" class="empty-tip">
            暂无到期提醒
          </div>
          <div v-else class="reminder-list">
            <div
              v-for="item in contractReminders"
              :key="item.contract_id"
              class="reminder-item"
              :class="{ urgent: item.urgent }"
            >
              <div class="reminder-title">
                <el-icon v-if="item.urgent" color="#f56c6c"><WarningFilled /></el-icon>
                <span>{{ item.code }} - {{ item.title }}</span>
              </div>
              <div class="reminder-meta">
                <span>到期日期：{{ formatDate(item.end_date) }}</span>
                <el-tag
                  :type="item.urgent ? 'danger' : 'warning'"
                  size="small"
                >
                  {{ item.days_left <= 0 ? '已过期' : `剩余${item.days_left}天` }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="hover" class="reminder-card" v-loading="vehicleLoading">
          <template #header>
            <div class="card-header">
              <span>车辆到期提醒</span>
              <el-tag type="danger" v-if="vehicleReminders.length" size="small">
                {{ vehicleReminders.length }}
              </el-tag>
            </div>
          </template>
          <div v-if="vehicleReminders.length === 0" class="empty-tip">
            暂无到期提醒
          </div>
          <div v-else class="reminder-list">
            <div
              v-for="(item, index) in vehicleReminders"
              :key="index"
              class="reminder-item"
              :class="{ urgent: item.urgent }"
            >
              <div class="reminder-title">
                <el-icon v-if="item.urgent" color="#f56c6c"><WarningFilled /></el-icon>
                <span>{{ item.plate_number }} - {{ item.type === 'insurance' ? '保险到期' : '保养到期' }}</span>
              </div>
              <div class="reminder-meta">
                <span>到期日期：{{ formatDate(item.date) }}</span>
                <el-tag
                  :type="item.urgent ? 'danger' : 'warning'"
                  size="small"
                >
                  {{ item.days_left <= 0 ? '已过期' : `剩余${item.days_left}天` }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { statisticsApi, contractApi, vehicleApi } from '@/api'
import { formatMoney, formatDate } from '@/utils/format'

const loading = ref(false)
const contractLoading = ref(false)
const vehicleLoading = ref(false)

const dashboardData = ref<Record<string, any>>({
  monthly_sales: 0,
  monthly_purchases: 0,
  monthly_income: 0,
  monthly_expenses: 0,
  today_meals: {
    breakfast: 0,
    lunch: 0,
    dinner: 0,
    supper: 0,
    total: 0,
  },
})

const contractReminders = ref<any[]>([])
const vehicleReminders = ref<any[]>([])

const mealItems = [
  { key: 'breakfast', label: '早餐' },
  { key: 'lunch', label: '午餐' },
  { key: 'dinner', label: '晚餐' },
  { key: 'supper', label: '夜宵' },
  { key: 'total', label: '合计' },
]

async function fetchDashboard() {
  loading.value = true
  try {
    dashboardData.value = await statisticsApi.dashboard() as any
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

async function fetchContractReminders() {
  contractLoading.value = true
  try {
    contractReminders.value = (await contractApi.reminders() as any) ?? []
  } catch {
    // error handled by interceptor
  } finally {
    contractLoading.value = false
  }
}

async function fetchVehicleReminders() {
  vehicleLoading.value = true
  try {
    vehicleReminders.value = (await vehicleApi.reminders() as any) ?? []
  } catch {
    // error handled by interceptor
  } finally {
    vehicleLoading.value = false
  }
}

onMounted(() => {
  fetchDashboard()
  fetchContractReminders()
  fetchVehicleReminders()
})
</script>

<style scoped>
.dashboard {
  padding: 16px;
}

.stat-row {
  margin-bottom: 16px;
}

.section-row {
  margin-bottom: 16px;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.meal-counts {
  text-align: center;
}

.meal-item {
  padding: 12px 0;
}

.meal-count {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.meal-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.reminder-card :deep(.el-card__body) {
  padding: 0;
  max-height: 360px;
  overflow-y: auto;
}

.reminder-list {
  padding: 0;
}

.reminder-item {
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.reminder-item:last-child {
  border-bottom: none;
}

.reminder-item:hover {
  background: #fafafa;
}

.reminder-item.urgent {
  background: #fef0f0;
}

.reminder-item.urgent:hover {
  background: #fde2e2;
}

.reminder-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #303133;
  margin-bottom: 6px;
  font-weight: 500;
}

.reminder-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #909399;
}

.empty-tip {
  padding: 40px 0;
  text-align: center;
  color: #c0c4cc;
  font-size: 14px;
}

@media (max-width: 768px) {
  .stat-card :deep(.el-card__body) {
    padding: 16px;
  }

  .stat-value {
    font-size: 18px;
  }

  .stat-row .el-col {
    margin-bottom: 8px;
  }

  .section-row .el-col {
    margin-bottom: 8px;
  }
}
</style>
