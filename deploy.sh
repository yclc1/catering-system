#!/bin/bash
# 部署脚本 - 在服务器上运行

set -e

echo "=== 开始部署 ==="

# 拉取最新代码
git pull origin main

# 后端部署
echo "=== 部署后端 ==="
cd backend
pip3 install -r requirements.txt
python3 -m alembic upgrade head

# 重启后端服务
if systemctl is-active --quiet catering-backend; then
    sudo systemctl restart catering-backend
    echo "后端服务已重启"
else
    echo "后端服务未运行，请手动启动"
fi

# 前端部署
echo "=== 部署前端 ==="
cd ../frontend
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
npm install
npm run build

# 复制构建文件到 nginx 目录
if [ -d "/var/www/catering" ]; then
    sudo rm -rf /var/www/catering/*
    sudo cp -r dist/* /var/www/catering/
    echo "前端文件已更新"
fi

echo "=== 部署完成 ==="
