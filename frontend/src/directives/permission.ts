import type { Directive } from 'vue'
import { useUserStore } from '@/stores/user'
import { watch } from 'vue'

export const vPermission: Directive = {
  mounted(el, binding) {
    const userStore = useUserStore()
    const checkPermission = () => {
      const permission = binding.value
      if (permission && !userStore.hasPermission(permission)) {
        el.style.display = 'none'
      } else {
        el.style.display = ''
      }
    }
    checkPermission()

    // Watch for permission changes
    const unwatch = watch(() => userStore.permissions, checkPermission)
    el._permissionUnwatch = unwatch
  },
  unmounted(el) {
    if (el._permissionUnwatch) {
      el._permissionUnwatch()
    }
  },
}
