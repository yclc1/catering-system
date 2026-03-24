#!/bin/bash
set -e

echo "🚀 开始部署到云服务器..."

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 更新数据库
echo "🗄️  更新数据库..."
cd backend
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -q
alembic upgrade head
deactivate
cd ..

# 重新构建并启动容器
echo "🐳 重启 Docker 容器..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo "✅ 检查服务状态..."
docker-compose ps

# 健康检查
echo "🏥 健康检查..."
curl -f http://localhost/health || echo "⚠️  健康检查失败"

echo "✨ 部署完成！"
