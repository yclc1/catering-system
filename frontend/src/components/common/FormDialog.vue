<template>
  <el-dialog
    v-model="visible"
    :title="title"
    :width="width"
    :close-on-click-modal="false"
    :fullscreen="isMobile"
    destroy-on-close
    @close="$emit('close')"
  >
    <el-form
      ref="formRef"
      :model="modelValue"
      :rules="rules"
      :label-width="labelWidth"
      :label-position="isMobile ? 'top' : 'right'"
    >
      <slot :form="modelValue" />
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">
        {{ submitText }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useWindowSize } from '@vueuse/core'
import type { FormInstance, FormRules } from 'element-plus'

const props = withDefaults(defineProps<{
  modelValue: Record<string, any>
  title?: string
  width?: string
  rules?: FormRules
  labelWidth?: string
  loading?: boolean
  submitText?: string
}>(), {
  title: '',
  width: '600px',
  labelWidth: '100px',
  submitText: '确定',
})

const emit = defineEmits<{
  'submit': [data: any]
  'close': []
}>()

const visible = defineModel<boolean>('visible', { default: false })
const formRef = ref<FormInstance>()
const { width: windowWidth } = useWindowSize()
const isMobile = computed(() => windowWidth.value < 768)

async function handleSubmit() {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  emit('submit', props.modelValue)
}
</script>
