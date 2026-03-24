<template>
  <div>
    <el-select
      :model-value="modelValue"
      :placeholder="placeholder"
      filterable
      :clearable="clearable"
      style="width: 100%"
      @change="handleChange"
    >
      <el-option value="__add__" :label="`-- 新增${label} --`" class="add-option" />
      <el-option
        v-for="item in options"
        :key="item.id"
        :label="item.name"
        :value="item.id"
      />
    </el-select>

    <el-dialog v-model="addVisible" :title="`新增${label}`" :width="isMobile ? '90%' : '500px'" :fullscreen="isMobile" append-to-body>
      <slot name="form" :form="addForm" />
      <template #footer>
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

interface DropdownItem {
  id: number
  name: string
}

const props = defineProps<{
  modelValue: number | null | undefined
  options: DropdownItem[]
  label: string
  placeholder?: string
  clearable?: boolean
  createApi: (data: any) => Promise<any>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: number | null]
  'created': [item: any]
  'change': [value: number | null]
}>()

const addVisible = ref(false)
const addLoading = ref(false)
const addForm = ref<Record<string, any>>({})
const previousValue = ref<number | null>(null)

const isMobile = computed(() => window.innerWidth <= 768)

function handleChange(val: any) {
  if (val === '__add__') {
    previousValue.value = props.modelValue || null
    addForm.value = {}
    addVisible.value = true
    // Don't emit null, keep the previous value
    emit('update:modelValue', previousValue.value)
    return
  }
  emit('update:modelValue', val)
  emit('change', val)
}

async function handleAdd() {
  addLoading.value = true
  try {
    const result = await props.createApi(addForm.value)
    ElMessage.success('创建成功')
    addVisible.value = false
    emit('created', result)
    emit('update:modelValue', result.id)
    previousValue.value = null
  } catch {
    // handled by interceptor
  } finally {
    addLoading.value = false
  }
}

function handleCancel() {
  addVisible.value = false
  previousValue.value = null
}
</script>

<style scoped>
.add-option {
  color: #409eff;
  font-weight: bold;
}
</style>
