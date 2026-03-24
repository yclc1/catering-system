# 数据库迁移说明

## 首次部署时生成迁移文件

由于本地环境与服务器环境不同，迁移文件需要在服务器上生成：

```bash
# 在服务器上执行
cd /opt/catering-system/backend

# 删除旧的空迁移文件
rm -f alembic/versions/*.py

# 生成新的迁移文件
python3 -m alembic revision --autogenerate -m "initial_migration"

# 应用迁移
python3 -m alembic upgrade head
```

## 后续更新

修改模型后，在服务器上运行：

```bash
python3 -m alembic revision --autogenerate -m "描述你的修改"
python3 -m alembic upgrade head
```
