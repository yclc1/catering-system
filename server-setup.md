# 服务器部署指南

## 1. 服务器环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.11+
sudo apt install python3 python3-pip python3-venv -y

# 安装 Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# 安装 Nginx
sudo apt install nginx -y

# 安装 Git
sudo apt install git -y
```

## 2. 数据库配置

```bash
# 切换到 postgres 用户
sudo -u postgres psql

# 在 psql 中执行
CREATE DATABASE catering_db;
CREATE USER catering_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE catering_db TO catering_user;
\q
```

## 3. 克隆代码

```bash
cd /opt
sudo git clone https://github.com/your-username/catering-system.git
sudo chown -R $USER:$USER catering-system
cd catering-system
```

## 4. 后端配置

```bash
cd backend

# 创建 .env 文件
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://catering_user:your_password@localhost/catering_db
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF

# 安装依赖
pip3 install -r requirements.txt

# 运行迁移
python3 -m alembic upgrade head

# 创建初始管理员（可选）
python3 -c "
from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
db = SessionLocal()
admin = User(username='admin', password_hash=get_password_hash('admin123'), real_name='管理员', is_active=True)
db.add(admin)
db.commit()
print('管理员创建成功: admin/admin123')
"
```

## 5. 创建后端 systemd 服务

```bash
sudo tee /etc/systemd/system/catering-backend.service > /dev/null << EOF
[Unit]
Description=Catering Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/catering-system/backend
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable catering-backend
sudo systemctl start catering-backend
sudo systemctl status catering-backend
```

## 6. 前端配置

```bash
cd /opt/catering-system/frontend

# 创建 .env.production 文件
cat > .env.production << EOF
VITE_API_BASE_URL=http://your-server-ip:8000
EOF

# 安装依赖并构建
npm install
npm run build

# 创建 nginx 目录
sudo mkdir -p /var/www/catering
sudo cp -r dist/* /var/www/catering/
sudo chown -R www-data:www-data /var/www/catering
```

## 7. Nginx 配置

```bash
sudo tee /etc/nginx/sites-available/catering > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # 改成你的域名或IP

    # 前端
    location / {
        root /var/www/catering;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF

# 启用站点
sudo ln -s /etc/nginx/sites-available/catering /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 8. 防火墙配置

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 9. 后续更新部署

```bash
cd /opt/catering-system
chmod +x deploy.sh
./deploy.sh
```

## 10. 查看日志

```bash
# 后端日志
sudo journalctl -u catering-backend -f

# Nginx 日志
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## 11. SSL 证书（可选）

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```
