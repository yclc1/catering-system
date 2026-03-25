# 餐饮管理系统 - 微信小程序

基于 uni-app 开发的餐饮管理系统移动端，支持微信小程序和支付宝小程序。

## 功能模块

### Phase 1 (已完成)
- ✅ 登录授权
- ✅ 首页导航
- ✅ 用餐登记（拍照上传）
- ✅ 费用审批
- ✅ 采购管理
- ✅ 库存查询
- ✅ 个人中心

## 技术栈

- uni-app (Vue 3 + TypeScript)
- Vite
- 后端API: FastAPI (http://43.153.196.14:8000)

## 开发

```bash
# 安装依赖
npm install

# 微信小程序开发
npm run dev:mp-weixin

# 支付宝小程序开发
npm run dev:mp-alipay

# H5开发
npm run dev:h5
```

## 构建

```bash
# 微信小程序
npm run build:mp-weixin

# 支付宝小程序
npm run build:mp-alipay
```

## 目录结构

```
src/
├── api/              # API接口
├── pages/            # 页面
│   ├── index/        # 首页
│   ├── meals/        # 用餐登记
│   ├── approval/     # 费用审批
│   ├── purchase/     # 采购管理
│   ├── inventory/    # 库存查询
│   └── profile/      # 个人中心
├── utils/            # 工具函数
├── App.vue           # 应用入口
├── main.ts           # 主入口
└── pages.json        # 页面配置
```

## 微信小程序配置

1. 下载[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 运行 `npm run dev:mp-weixin`
3. 用微信开发者工具打开 `dist/dev/mp-weixin` 目录
4. 配置 AppID（测试可用测试号）

## 后续计划

- 配送管理
- 财务查询
- 消息推送
- 统计报表
