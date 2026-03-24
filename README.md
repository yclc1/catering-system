# 团膳公司管理系统

团体餐饮/食堂承包公司的在线管理系统，支持采购、库存、客户、财务、费用审批、车辆、合同等全流程管理。

## 技术栈

- **前端**: Vue 3 + TypeScript + Element Plus + Vite + Pinia
- **后端**: Python FastAPI + SQLAlchemy 2.0 + Alembic
- **数据库**: PostgreSQL
- **认证**: JWT + RBAC

## 功能模块

- 用户权限管理
- 供应商管理
- 商品管理
- 采购管理
- 库存管理
- 客户管理
- 用餐登记
- 客户结算
- 收付款管理
- 费用审批
- 车辆管理
- 合同管理
- 统计报表

## 本地开发

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 配置数据库连接
alembic upgrade head
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 服务器部署

详见 [server-setup.md](./server-setup.md)

## License

Private
