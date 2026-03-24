#!/bin/bash
# 自动部署脚本 - 本地执行

set -e

SERVER="43.153.196.14"
PASSWORD="dodse7-qopgeq-guwsEp"

echo "=== 开始自动部署 ==="

# 1. 提交并推送到 GitHub
echo "1. 推送代码到 GitHub..."
git add .
git commit -m "自动部署: $(date '+%Y-%m-%d %H:%M:%S')" || echo "没有新的更改"
git push origin main

# 2. 服务器拉取代码
echo "2. 服务器拉取最新代码..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER "cd /opt/catering-system && git pull origin main"

# 3. 更新后端
echo "3. 更新后端..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER "cd /opt/catering-system/backend && pip3 install -r requirements.txt && python3 -m alembic upgrade head && systemctl restart catering-backend"

# 4. 更新前端
echo "4. 更新前端..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER 'export NVM_DIR="$HOME/.nvm" && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && nvm use 20 && cd /opt/catering-system/frontend && npm install && npm run build && cp -r dist/* /var/www/catering/'

# 5. 重启服务
echo "5. 重启服务..."
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER "systemctl restart nginx"

echo "=== 部署完成 ==="
echo "访问地址: http://43.153.196.14"
echo "后端 API: http://43.153.196.14/docs"
