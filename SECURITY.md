# 安全配置说明

## 必须配置的环境变量

### 后端 (.env)
```bash
# 数据库连接 - 必须修改密码
DATABASE_URL=postgresql+asyncpg://catering_user:YOUR_STRONG_PASSWORD@localhost/catering_db

# JWT密钥 - 必须使用强随机密钥
# 生成方法: openssl rand -hex 32
SECRET_KEY=YOUR_GENERATED_SECRET_KEY_HERE

# JWT配置
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 前端 (.env.production)
```bash
VITE_API_BASE_URL=http://YOUR_SERVER_IP:8000
```

## 部署安全检查清单

- [ ] 修改数据库密码
- [ ] 生成并配置强随机 SECRET_KEY
- [ ] 使用非 root 用户运行服务
- [ ] 配置 SSH 密钥认证，禁用密码登录
- [ ] 启用防火墙，只开放必要端口
- [ ] 定期更新系统和依赖包
- [ ] 配置 HTTPS (使用 Let's Encrypt)
- [ ] 定期备份数据库
- [ ] 监控审计日志

## 生成密钥命令

```bash
# 生成 SECRET_KEY
openssl rand -hex 32

# 生成数据库密码
openssl rand -base64 24
```
