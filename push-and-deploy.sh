#!/bin/bash
set -e

echo "=== 推送代码到 GitHub ==="
git add .
git commit -m "${1:-更新代码}"
git push origin main

echo "=== 部署到服务器 ==="
ssh root@43.153.196.14 "cd /opt/catering-system && ./deploy.sh"

echo "=== 完成 ==="
