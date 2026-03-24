<template>
  <div>
    <el-row :gutter="16" style="margin-bottom:16px">
      <el-col :span="12">
        <el-card>
          <template #header>月度销售额趋势</template>
          <div style="display:flex;gap:8px;margin-bottom:8px">
            <el-date-picker v-model="salesRange[0]" type="month" value-format="YYYY-MM" placeholder="开始" />
            <el-date-picker v-model="salesRange[1]" type="month" value-format="YYYY-MM" placeholder="结束" />
            <el-button type="primary" @click="loadSales">查询</el-button>
          </div>
          <v-chart :option="salesOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span>货物分类占比</span>
              <el-date-picker v-model="categoryMonth" type="month" value-format="YYYY-MM" @change="loadCategory" />
            </div>
          </template>
          <v-chart :option="categoryOption" style="height:300px" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>客户营收排名</span>
          <el-date-picker v-model="revenueMonth" type="month" value-format="YYYY-MM" @change="loadRevenue" />
        </div>
      </template>
      <v-chart :option="revenueOption" style="height:300px" autoresize />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { statisticsApi } from '@/api'

use([BarChart, LineChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const now = new Date()
const currentMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
const sixMonthsAgo = (() => { const d = new Date(now); d.setMonth(d.getMonth() - 5); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}` })()

const salesRange = ref([sixMonthsAgo, currentMonth])
const salesData = ref<any[]>([])

const categoryMonth = ref(currentMonth)
const categoryData = ref<any[]>([])

const revenueMonth = ref(currentMonth)
const revenueData = ref<any[]>([])

onMounted(() => { loadSales(); loadCategory(); loadRevenue() })

async function loadSales() {
  salesData.value = (await statisticsApi.monthlySales({ start_month: salesRange.value[0], end_month: salesRange.value[1] })) as any
}
async function loadCategory() {
  categoryData.value = (await statisticsApi.categoryUsage({ month: categoryMonth.value })) as any
}
async function loadRevenue() {
  revenueData.value = (await statisticsApi.customerRevenue({ month: revenueMonth.value })) as any
}

const salesOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: salesData.value.map((d: any) => d.month) },
  yAxis: { type: 'value' },
  series: [{ type: 'line', data: salesData.value.map((d: any) => d.amount), smooth: true, areaStyle: {} }],
}))

const categoryOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{
    type: 'pie', radius: ['40%', '70%'],
    data: categoryData.value.map((d: any) => ({ name: d.category, value: d.amount })),
  }],
}))

const revenueOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: revenueData.value.map((d: any) => d.customer), axisLabel: { rotate: 30 } },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: revenueData.value.map((d: any) => d.amount) }],
}))
</script>
