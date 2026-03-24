<template>
  <div>
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>角色管理</span>
          <el-button v-permission="'role:create'" type="primary" @click="openCreate">新增角色</el-button>
        </div>
      </template>
      <el-table :data="roles" v-loading="loading" stripe border>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="code" label="编码" width="150" />
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="is_system" label="系统角色" width="100">
          <template #default="{ row }"><el-tag v-if="row.is_system" type="warning">系统</el-tag></template>
        </el-table-column>
        <el-table-column label="权限数">
          <template #default="{ row }">{{ row.permissions?.length || 0 }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="openPermissions(row)">配置权限</el-button>
            <el-button v-if="!row.is_system" v-permission="'role:delete'" type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="createVisible" title="新增角色" width="400px">
      <el-form :model="createForm" label-width="60px">
        <el-form-item label="编码" required><el-input v-model="createForm.code" /></el-form-item>
        <el-form-item label="名称" required><el-input v-model="createForm.name" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="permVisible" :title="`配置权限 - ${selectedRole?.name || ''}`" width="600px">
      <el-tree
        ref="treeRef"
        :data="permTree"
        :props="{ label: 'label', children: 'children' }"
        show-checkbox
        node-key="id"
        :default-checked-keys="checkedKeys"
      />
      <template #footer>
        <el-button @click="permVisible = false">取消</el-button>
        <el-button type="primary" @click="savePermissions">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ElTree } from 'element-plus'
import { roleApi } from '@/api'

const loading = ref(false)
const roles = ref<any[]>([])
const allPermissions = ref<any[]>([])

const createVisible = ref(false)
const createForm = ref({ code: '', name: '' })

const permVisible = ref(false)
const selectedRole = ref<any>(null)
const checkedKeys = ref<number[]>([])
const treeRef = ref<InstanceType<typeof ElTree>>()

onMounted(loadData)

async function loadData() {
  loading.value = true
  try {
    roles.value = (await roleApi.list()) as any
    allPermissions.value = (await roleApi.permissions()) as any
  } finally { loading.value = false }
}

const permTree = ref<any[]>([])
function buildTree() {
  const modules: Record<string, any[]> = {}
  for (const p of allPermissions.value) {
    if (!modules[p.module]) modules[p.module] = []
    modules[p.module].push({ id: p.id, label: p.name })
  }
  permTree.value = Object.entries(modules).map(([mod, perms]) => ({
    id: `mod_${mod}`, label: mod, children: perms,
  }))
}

function openCreate() { createForm.value = { code: '', name: '' }; createVisible.value = true }

async function handleCreate() {
  await roleApi.create(createForm.value)
  ElMessage.success('已创建'); createVisible.value = false; loadData()
}

function openPermissions(role: any) {
  selectedRole.value = role
  buildTree()
  checkedKeys.value = role.permissions?.map((p: any) => p.id) || []
  permVisible.value = true
}

async function savePermissions() {
  const checked = treeRef.value?.getCheckedKeys(true) as number[]
  const permissionIds = checked.filter((k) => typeof k === 'number')
  await roleApi.update(selectedRole.value.id, { permission_ids: permissionIds })
  ElMessage.success('权限已更新'); permVisible.value = false; loadData()
}

async function handleDelete(role: any) {
  await ElMessageBox.confirm('确定删除？', '确认')
  await roleApi.delete(role.id); ElMessage.success('已删除'); loadData()
}
</script>
