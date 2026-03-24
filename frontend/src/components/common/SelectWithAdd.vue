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

    <el-dialog v-model="addVisible" :title="`新增${label}`" width="500px" append-to-body>
      <slot name="form" :form="addForm" />
      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
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

function handleChange(val: any) {
  if (val === '__add__') {
    addForm.value = {}
    addVisible.value = true
    emit('update:modelValue', null)
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
  } catch {
    // handled by interceptor
  } finally {
    addLoading.value = false
  }
}
</script>

<style scoped>
.add-option {
  color: #409eff;
  font-weight: bold;
}
</style>
