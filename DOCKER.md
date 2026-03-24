# Docker 部署指南

## 前置条件

**PostgreSQL 数据库**（独立部署，不在 Docker 中）
```bash
# 安装 PostgreSQL
# macOS: brew install postgresql@15
# Ubuntu: sudo apt install postgresql-15

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE catering_db;
CREATE USER catering_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE catering_db TO catering_user;
\q
```

## 快速开始

1. **创建环境变量文件**
```bash
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://catering_user:your_password@localhost/catering_db
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

2. **初始化数据库**
```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 运行迁移
alembic upgrade head
cd ..
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问系统**
- 前端: http://localhost
- API文档: http://localhost/docs (仅开发环境)

## 生产部署

### 配置 HTTPS

1. 获取 SSL 证书
```bash
certbot certonly --standalone -d your-domain.com
```

2. 复制证书
```bash
mkdir ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
```

3. 更新 nginx.conf 添加 HTTPS 配置

### 备份数据

```bash
# 备份数据库（本地 PostgreSQL）
pg_dump -U catering_user catering_db > backup_$(date +%Y%m%d).sql

# 备份上传文件
docker-compose exec backend tar czf /tmp/uploads.tar.gz uploads
docker cp $(docker-compose ps -q backend):/tmp/uploads.tar.gz ./
```

### 更新部署

```bash
git pull origin main

# 更新数据库
cd backend
alembic upgrade head
cd ..

# 重新构建并启动容器
docker-compose down
docker-compose build
docker-compose up -d
```

## 监控

```bash
# 查看日志
docker-compose logs -f backend

# 查看资源使用
docker stats
```
