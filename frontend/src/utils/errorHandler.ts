// 全局错误处理包装器
export function wrapConfirm(fn: () => Promise<void>) {
  return async () => {
    try {
      await fn()
    } catch (error) {
      if (error !== 'cancel') {
        console.error('操作失败:', error)
      }
    }
  }
}
