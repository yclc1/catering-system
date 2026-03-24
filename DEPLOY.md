# 云服务器部署指南

## 首次部署

### 1. 服务器准备
```bash
# SSH 登录服务器
ssh root@your-server-ip

# 安装必要软件
apt update
apt install -y git docker.io docker-compose postgresql-15

# 启动 Docker
systemctl start docker
systemctl enable docker
```

### 2. 配置 PostgreSQL
```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE catering_db;
CREATE USER catering_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE catering_db TO catering_user;
\q

# 配置允许本地连接（编辑 /etc/postgresql/15/main/pg_hba.conf）
# 添加：local   all   catering_user   md5

# 重启 PostgreSQL
systemctl restart postgresql
```

### 3. 克隆项目
```bash
cd /opt
git clone https://github.com/yclc1/catering-system.git
cd catering-system
```

### 4. 配置环境变量
```bash
# 创建 .env 文件
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://catering_user:your_strong_password@localhost/catering_db
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
EOF
```

### 5. 初始化数据库
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
deactivate
cd ..
```

### 6. 启动服务
```bash
docker-compose up -d
```

### 7. 配置防火墙
```bash
# 开放 80 和 443 端口
ufw allow 80
ufw allow 443
ufw enable
```

## 日常更新

### 方法一：使用部署脚本（推荐）
```bash
cd /opt/catering-system
./deploy.sh
```

### 方法二：手动更新
```bash
cd /opt/catering-system

# 拉取代码
git pull origin main

# 更新数据库
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
deactivate
cd ..

# 重启容器
docker-compose down
docker-compose build
docker-compose up -d
```

## 监控和维护

### 查看日志
```bash
# 应用日志
docker-compose logs -f backend

# Nginx 日志
docker-compose logs -f nginx

# 实时日志（最近 100 行）
docker-compose logs --tail=100 -f
```

### 查看状态
```bash
# 容器状态
docker-compose ps

# 资源使用
docker stats

# 健康检查
curl http://localhost/health
```

### 数据库备份
```bash
# 创建备份目录
mkdir -p /opt/backups

# 备份脚本
cat > /opt/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
pg_dump -U catering_user catering_db > $BACKUP_DIR/db_$DATE.sql

# 备份上传文件
cd /opt/catering-system
docker-compose exec -T backend tar czf - uploads > $BACKUP_DIR/uploads_$DATE.tar.gz

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $DATE"
EOF

chmod +x /opt/backup.sh

# 添加定时任务（每天凌晨 2 点备份）
crontab -e
# 添加：0 2 * * * /opt/backup.sh >> /var/log/backup.log 2>&1
```

### 恢复备份
```bash
# 恢复数据库
psql -U catering_user catering_db < /opt/backups/db_20240324_020000.sql

# 恢复上传文件
cd /opt/catering-system
docker-compose exec -T backend tar xzf - -C / < /opt/backups/uploads_20240324_020000.tar.gz
```

## HTTPS 配置

### 使用 Let's Encrypt
```bash
# 安装 certbot
apt install -y certbot

# 停止 nginx
docker-compose stop nginx

# 获取证书
certbot certonly --standalone -d your-domain.com

# 复制证书
mkdir -p /opt/catering-system/ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/catering-system/ssl/
cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/catering-system/ssl/

# 更新 nginx.conf（添加 HTTPS 配置）
# 重启 nginx
docker-compose up -d nginx

# 自动续期（添加到 crontab）
# 0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /opt/catering-system/ssl/ && docker-compose restart nginx
```

## 故障排查

### 容器无法启动
```bash
# 查看详细日志
docker-compose logs backend

# 检查端口占用
netstat -tlnp | grep :80

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 数据库连接失败
```bash
# 检查 PostgreSQL 状态
systemctl status postgresql

# 测试连接
psql -U catering_user -d catering_db -h localhost

# 查看 PostgreSQL 日志
tail -f /var/log/postgresql/postgresql-15-main.log
```

### 磁盘空间不足
```bash
# 清理 Docker
docker system prune -a

# 清理日志
journalctl --vacuum-time=7d

# 清理旧备份
find /opt/backups -mtime +30 -delete
```

## 性能优化

### PostgreSQL 优化
```bash
# 编辑 /etc/postgresql/15/main/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
max_connections = 100

# 重启
systemctl restart postgresql
```

### Nginx 缓存
```bash
# 在 nginx.conf 添加缓存配置
# 静态文件缓存 30 天
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

## 安全建议

1. **定期更新系统**
   ```bash
   apt update && apt upgrade -y
   ```

2. **配置 SSH 密钥登录**
   ```bash
   # 禁用密码登录
   # 编辑 /etc/ssh/sshd_config
   PasswordAuthentication no
   ```

3. **安装 fail2ban**
   ```bash
   apt install -y fail2ban
   systemctl enable fail2ban
   ```

4. **定期检查日志**
   ```bash
   # 查看登录日志
   tail -f /var/log/auth.log

   # 查看应用日志
   docker-compose logs --tail=100
   ```
