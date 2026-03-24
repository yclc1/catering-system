# Docker 部署指南

## 快速开始

1. **创建环境变量文件**
```bash
cat > .env << EOF
DB_PASSWORD=$(openssl rand -base64 24)
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

2. **启动服务**
```bash
docker-compose up -d
```

3. **初始化数据库**
```bash
docker-compose exec backend alembic upgrade head
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
# 备份数据库
docker-compose exec db pg_dump -U catering_user catering_db > backup.sql

# 备份上传文件
docker-compose exec backend tar czf /tmp/uploads.tar.gz uploads
docker cp $(docker-compose ps -q backend):/tmp/uploads.tar.gz ./
```

### 更新部署

```bash
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

## 监控

```bash
# 查看日志
docker-compose logs -f backend

# 查看资源使用
docker stats
```
