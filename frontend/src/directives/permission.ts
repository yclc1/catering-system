import type { Directive } from 'vue'
import { useUserStore } from '@/stores/user'

export const vPermission: Directive = {
  mounted(el, binding) {
    const userStore = useUserStore()
    const permission = binding.value
    if (permission && !userStore.hasPermission(permission)) {
      el.parentNode?.removeChild(el)
    }
  },
}
