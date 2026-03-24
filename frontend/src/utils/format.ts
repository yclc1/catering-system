import { PURCHASE_STATUS, SETTLEMENT_STATUS, EXPENSE_STATUS, CONTRACT_STATUS, ACCOUNT_TYPES, INVENTORY_TYPES } from './constants'

export function formatMoney(val: number | string | null | undefined): string {
  if (val == null) return '0.00'
  const num = Number(val)
  if (isNaN(num)) return '0.00'
  return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

export function formatDate(val: string | null | undefined): string {
  if (!val) return ''
  return val.substring(0, 10)
}

export function formatDateTime(val: string | null | undefined): string {
  if (!val) return ''
  return val.substring(0, 19).replace('T', ' ')
}

export function statusLabel(type: string, value: string): string {
  const maps: Record<string, Record<string, string>> = {
    purchase: PURCHASE_STATUS,
    settlement: SETTLEMENT_STATUS,
    expense: EXPENSE_STATUS,
    contract: CONTRACT_STATUS,
    account_type: ACCOUNT_TYPES,
    inventory: INVENTORY_TYPES,
  }
  return maps[type]?.[value] ?? value
}

export function statusType(type: string, value: string): string {
  const map: Record<string, Record<string, string>> = {
    purchase: { draft: 'info', confirmed: 'success', cancelled: 'danger' },
    settlement: { draft: 'info', confirmed: 'success', settled: 'warning' },
    expense: { pending: 'warning', approved: 'success', rejected: 'danger' },
    contract: { draft: 'info', active: 'success', expired: 'warning', terminated: 'danger' },
  }
  return map[type]?.[value] ?? 'info'
}
