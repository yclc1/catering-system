#!/bin/bash
# 完整部署脚本

set -e

echo "=== 开始部署 ==="

# 配置后端环境变量
cd /opt/catering-system/backend
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://catering_user:Catering@2026@localhost/catering_db
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF

# 安装 Python 依赖
pip3 install -r requirements.txt

# 运行数据库迁移
python3 -m alembic upgrade head

# 创建 systemd 服务
cat > /etc/systemd/system/catering-backend.service << 'EOF'
[Unit]
Description=Catering Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/catering-system/backend
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable catering-backend
systemctl start catering-backend

# 配置前端
cd /opt/catering-system/frontend
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

cat > .env.production << 'EOF'
VITE_API_BASE_URL=http://43.153.196.14:8000
EOF

npm install
npm run build

# 部署前端到 nginx
mkdir -p /var/www/catering
cp -r dist/* /var/www/catering/

# 配置 Nginx
cat > /etc/nginx/conf.d/catering.conf << 'EOF'
server {
    listen 80;
    server_name 43.153.196.14;

    location / {
        root /var/www/catering;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }
}
EOF

nginx -t
systemctl restart nginx

echo "=== 部署完成 ==="
echo "访问地址: http://43.153.196.14"
