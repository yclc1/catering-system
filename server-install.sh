#!/bin/bash
# 服务器环境安装脚本

set -e

echo "=== 开始安装环境 ==="

# 更新系统
echo "更新系统..."
yum update -y

# 安装基础工具
echo "安装基础工具..."
yum install -y git curl wget vim

# 安装 Python 依赖
echo "安装 Python 依赖..."
yum install -y python3-pip python3-devel gcc

# 安装 Node.js 18
echo "安装 Node.js..."
curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
yum install -y nodejs

# 安装 PostgreSQL 15
echo "安装 PostgreSQL..."
yum install -y postgresql15-server postgresql15-contrib
postgresql-setup --initdb
systemctl enable postgresql
systemctl start postgresql

# 配置 PostgreSQL
echo "配置 PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE catering_db;"
sudo -u postgres psql -c "CREATE USER catering_user WITH PASSWORD 'Catering@2026';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE catering_db TO catering_user;"
sudo -u postgres psql -d catering_db -c "GRANT ALL ON SCHEMA public TO catering_user;"

# 修改 PostgreSQL 认证方式
sed -i 's/ident/md5/g' /var/lib/pgsql/data/pg_hba.conf
systemctl restart postgresql

# 安装 Nginx
echo "安装 Nginx..."
yum install -y nginx
systemctl enable nginx

echo "=== 环境安装完成 ==="
