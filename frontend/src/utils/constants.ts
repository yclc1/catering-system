export const APP_NAME = '团膳管理系统'

export const TOKEN_KEY = 'access_token'
export const REFRESH_TOKEN_KEY = 'refresh_token'

export const MEAL_TYPES = [
  { key: 'breakfast', label: '早餐' },
  { key: 'lunch', label: '午餐' },
  { key: 'dinner', label: '晚餐' },
  { key: 'supper', label: '夜宵' },
]

export const PURCHASE_STATUS = {
  draft: '草稿',
  confirmed: '已确认',
  cancelled: '已取消',
}

export const SETTLEMENT_STATUS = {
  draft: '草稿',
  confirmed: '已确认',
  settled: '已结清',
}

export const EXPENSE_STATUS = {
  pending: '待审批',
  approved: '已通过',
  rejected: '已驳回',
}

export const CONTRACT_STATUS = {
  draft: '草稿',
  active: '生效中',
  expired: '已到期',
  terminated: '已终止',
}

export const ACCOUNT_TYPES = {
  bank: '银行账户',
  wechat: '微信',
  alipay: '支付宝',
  cash: '现金',
}

export const INVENTORY_TYPES = {
  inbound: '入库',
  outbound: '出库',
  return: '退货',
  damage: '报损',
  loss: '报失',
  stocktake_adjust: '盘点调整',
}
