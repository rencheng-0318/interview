# 临床记录语义搜索 — Docker 部署与访问指南

---

## 前置条件

- Docker Desktop 已安装并运行（含 Compose v2）
- 无需本地安装 Python / Node / pnpm，全部在容器内运行
- 首次构建需网络畅通（下载嵌入模型 ~90MB）

---

## 部署步骤

```bash
# 1. 进入项目目录
cd /Users/ld/home_work/interview

# 2. 创建环境文件
cp .env.example .env

# 3. 构建镜像 + 启动核心服务 + 应用迁移
make setup
# 等价于:
#   docker compose build
#   docker compose up -d db embedding api
#   docker compose run --rm api python -m app.scripts.wait_for_dependencies
#   docker compose exec -T api python -m app.scripts.migrate
#   docker compose exec -T api python -m app.scripts.migrate --database test

# 4. 加载种子数据
make seed

# 5. 构建语义索引
make index

# 6. 启动全部服务（含前端热重载）
make dev
```

---

## 服务访问

| 服务 | 地址 | 说明 |
|---|---|---|
| Web (Next.js) | http://localhost:3000 | 前端应用 |
| API (FastAPI) | http://localhost:8000 | 后端 API |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| Embedding | http://localhost:8080 | 嵌入服务（内部使用） |
| PostgreSQL | localhost:5432 | 数据库（用户: clinical） |

### 前端页面

| 路由 | 功能 |
|---|---|
| http://localhost:3000 | 首页 |
| http://localhost:3000/search | 语义搜索 |
| http://localhost:3000/patients/[id] | 患者详情 |

### 诊所切换

页面顶部 Header 有诊所切换下拉框，可切换不同 demo 用户身份：
- `user-northside-01` -> Northside 诊所
- `user-lakeshore-01` -> Lakeshore 诊所
- `user-summit-01` -> Summit 诊所

---

## 验证命令

```bash
# 检查所有服务健康状态
make smoke

# 运行后端 + 前端测试
make test

# 仅后端测试
make test-api

# 仅前端测试
make test-web

# 集成测试（需 embedding 容器运行）
make test-integration

# 代码检查
make lint

# TypeScript 类型检查
make typecheck
```

---

## 常用运维命令

```bash
# 查看服务状态
make ps

# 跟踪日志
make logs

# 进入数据库 shell
make psql

# 停止服务（保留数据）
make down

# 停止并删除数据卷（重置数据库）
make destroy

# 重新加载种子数据
make reseed

# 应用数据库迁移
make migrate

# 重新构建语义索引
make index
```

---

## 环境变量

通过 `.env` 文件配置（复制自 `.env.example`）：

| 变量 | 默认值 | 说明 |
|---|---|---|
| POSTGRES_USER | clinical | 数据库用户 |
| POSTGRES_PASSWORD | local_dev_only | 数据库密码 |
| POSTGRES_DB | clinical_search | 数据库名 |
| POSTGRES_PORT | 5432 | 数据库端口 |
| API_PORT | 8000 | API 端口 |
| WEB_PORT | 3000 | 前端端口 |
| EMBEDDING_PORT | 8080 | 嵌入服务端口 |
| EMBEDDING_FAILURE_RATE | 0.0 | 设为 1.0 可模拟嵌入服务故障 |
| SEARCH_DEFAULT_LIMIT | 10 | 搜索默认返回数 |
| SEARCH_MAX_LIMIT | 25 | 搜索最大返回数 |
| SEARCH_MAX_QUERY_LENGTH | 500 | 查询最大字符数 |

---

## 故障排除

| 问题 | 解决方案 |
|---|---|
| `make setup` 无法连接 Docker | 启动 Docker Desktop 后重试 |
| 数据库容器立即退出 | `make destroy` 后重新 `make setup` |
| `pgvector types are not available` | 运行 `make migrate` |
| 搜索返回 501 | 搜索端点尚未实现（开发中） |
| 集成测试跳过 | embedding 容器未启动，执行 `docker compose up -d embedding` |
| Web 显示 "API not reachable" | 检查 `docker compose logs api`，API 需要已迁移的数据库 |
| 首次构建很慢 | 正常，需下载嵌入模型 (~90MB)，后续构建有缓存 |
| `pnpm install` 警告 ignored build scripts | 再执行一次 `pnpm install` |

---

## 模拟故障（测试用）

```bash
# 模拟嵌入服务完全不可用
EMBEDDING_FAILURE_RATE=1.0 docker compose up -d embedding

# 恢复正常
EMBEDDING_FAILURE_RATE=0.0 docker compose up -d embedding
```

---

## 完整重置

如需从零开始：

```bash
make destroy          # 删除所有容器和数据卷
cp .env.example .env  # 重置环境变量
make setup            # 重建
make seed             # 重新播种
make index            # 重建索引
make dev              # 启动
```
