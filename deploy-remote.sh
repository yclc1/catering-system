#!/bin/bash
# 远程部署脚本 - 在本地运行，自动部署到云服务器

SERVER="root@43.153.196.14"
PROJECT_DIR="/opt/catering-system"

echo "🚀 开始远程部署..."

# 生成新的 SECRET_KEY
NEW_SECRET=$(openssl rand -hex 32)
echo "🔑 新密钥: $NEW_SECRET"

# 通过 SSH 执行部署命令
sshpass -p "dodse7-qopgeq-guwsEp" ssh -o StrictHostKeyChecking=no $SERVER << EOF
set -e

# 检查项目是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    echo "📦 首次部署，克隆项目..."
    cd /opt
    git clone https://github.com/yclc1/catering-system.git
    cd catering-system

    # 检查 PostgreSQL
    if ! command -v psql &> /dev/null; then
        echo "❌ 请先安装 PostgreSQL"
        exit 1
    fi

    echo "请手动创建数据库后继续..."
    exit 0
fi

cd $PROJECT_DIR

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 更新 .env 文件中的 SECRET_KEY
echo "🔑 更新密钥..."
sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$NEW_SECRET/" .env

# 更新数据库
echo "🗄️  更新数据库..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt -q
alembic upgrade head
deactivate
cd ..

# 重启 Docker 容器
echo "🐳 重启容器..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 等待启动
sleep 5

# 检查状态
echo "✅ 服务状态:"
docker-compose ps

echo "✨ 部署完成！"
EOF

echo ""
echo "🎉 远程部署完成！"
echo "🔗 访问: http://43.153.196.14"
