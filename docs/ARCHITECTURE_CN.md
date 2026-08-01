# 临床记录语义搜索 — 架构设计

---

## 一、系统整体架构

```
+------------------+       +------------------+       +--------------------+
|   Next.js Web    |------>|  FastAPI (API)   |------>|  Embedding Service |
|  (Port 3000)     | HTTP  |  (Port 8000)     | HTTP  |  (Port 8080)       |
|  React 19 / SSR  |       |  asyncpg pool    |       |  ONNX + all-MiniLM |
+------------------+       +--------+---------+       +--------------------+
                                    |
                                    | asyncpg
                                    v
                           +------------------+
                           |  PostgreSQL 18   |
                           |  + pgvector 0.8.5|
                           |  + HNSW index    |
                           +------------------+
```

四个容器通过 Docker Compose 编排，依赖链: `web -> api -> db + embedding`。

### 数据流总览

```
源文档 (clinical_documents)
    |
    v
[索引工作流] -- Recursive Character 分块 --> chunks -- 嵌入服务 --> vectors
    |
    v
PostgreSQL (document_chunks 表 + pgvector + HNSW 索引)
    |
    v
[搜索 API] <-- 查询向量化 <-- 嵌入服务 (LRU 缓存 + 熔断器)
    |
    v
向量相似度检索 + 诊所隔离 + 患者聚合
    |
    v
Next.js 前端渲染
```

---

## 二、完整数据库设计

数据库: PostgreSQL 18 + pgvector 扩展
数据库实例: `clinical_search`（主库）、`clinical_search_test`（测试库）

### 2.1 已有表（0001_base_schema.sql，不可修改）

#### practices（诊所）

| 字段 | 类型 | 约束 |
|---|---|---|
| id | text | PRIMARY KEY |
| name | text | NOT NULL, CHECK (非空白) |
| slug | text | NOT NULL, UNIQUE |
| city | text | NOT NULL |
| region | text | NOT NULL |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

数据量: 3 条

#### users（用户/医护人员）

| 字段 | 类型 | 约束 |
|---|---|---|
| id | text | PRIMARY KEY |
| practice_id | text | NOT NULL, FK -> practices(id) ON DELETE CASCADE |
| display_name | text | NOT NULL |
| email | text | NOT NULL, UNIQUE (lower) |
| role | text | NOT NULL, CHECK IN ('clinician','nurse','admin') |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

索引: `users_email_key` (UNIQUE, lower(email)), `users_practice_id_idx`

#### patients（患者）

| 字段 | 类型 | 约束 |
|---|---|---|
| id | text | PRIMARY KEY |
| practice_id | text | NOT NULL, FK -> practices(id) ON DELETE CASCADE |
| mrn | text | NOT NULL |
| first_name | text | NOT NULL |
| last_name | text | NOT NULL |
| date_of_birth | date | NOT NULL |
| sex | text | NOT NULL, CHECK IN ('female','male','other','unknown') |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

索引: `patients_practice_mrn_key` (UNIQUE, practice_id + mrn), `patients_practice_id_idx`
数据量: 715 条

#### clinical_documents（临床文档 - 源数据）

| 字段 | 类型 | 约束 |
|---|---|---|
| id | text | PRIMARY KEY |
| practice_id | text | NOT NULL, FK -> practices(id) ON DELETE CASCADE |
| patient_id | text | NOT NULL, FK -> patients(id) ON DELETE CASCADE |
| document_type | document_type (ENUM) | NOT NULL |
| title | text | NOT NULL |
| document_date | date | NOT NULL |
| author_name | text | NOT NULL |
| body | text | NOT NULL |
| source_updated_at | timestamptz | NOT NULL, DEFAULT now() |
| created_at | timestamptz | NOT NULL, DEFAULT now() |

索引: `clinical_documents_practice_type_idx`, `clinical_documents_patient_idx`, `clinical_documents_practice_date_idx`
触发器: body/title 变更时自动更新 `source_updated_at`; 插入/更新时校验 practice_id 与 patient 一致
数据量: 2,400 条

#### ENUM 类型

```sql
document_type: 'diagnostic_note' | 'specialist_note' | 'radiology_report' | 'lab_report'
```

### 2.2 新增表（0002_document_chunks.sql）

#### document_chunks（文档分块 + 向量）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | bigint | PK, GENERATED ALWAYS AS IDENTITY | 自增主键 |
| document_id | text | NOT NULL, FK -> clinical_documents(id) ON DELETE CASCADE | 源文档 |
| practice_id | text | NOT NULL, FK -> practices(id) ON DELETE CASCADE | 冗余，隔离过滤 |
| patient_id | text | NOT NULL, FK -> patients(id) ON DELETE CASCADE | 冗余，患者聚合 |
| document_type | document_type | NOT NULL | 冗余，类型过滤 |
| chunk_index | smallint | NOT NULL | 块序号 |
| content | text | NOT NULL | 块文本 |
| embedding | vector(384) | NOT NULL | 嵌入向量 |
| source_updated_at | timestamptz | NOT NULL | 变更检测 |
| created_at | timestamptz | NOT NULL, DEFAULT now() | 创建时间 |

约束: `UNIQUE (document_id, chunk_index)` -- 支持幂等 upsert

索引:
- `document_chunks_embedding_idx`: HNSW (embedding vector_cosine_ops), m=16, ef_construction=64
- `document_chunks_practice_type_idx`: (practice_id, document_type)
- `document_chunks_patient_idx`: (patient_id)

设计要点:
- ON DELETE CASCADE: 源文档删除时自动清理 chunks
- 冗余字段避免搜索热路径上的 JOIN
- HNSW 索引: 稳定 recall，无需手动调参，对增量数据友好

### 2.3 ER 关系图

```
practices (1) ──< users (N)
practices (1) ──< patients (N)
practices (1) ──< clinical_documents (N)
patients  (1) ──< clinical_documents (N)
clinical_documents (1) ──< document_chunks (N)  [新增]
```

---

## 三、Session 身份与多租户隔离

### 3.1 Session 身份建立

```
浏览器 Cookie (demo_user_id)
  -> Next.js Server Component 读取 cookie -> getSessionToken() -> "demo_<user_id>"
  -> API 请求携带 Authorization: Bearer demo_<user_id>
  -> FastAPI context.py 解析 token -> 查库获取 user + practice 信息
  -> RequestContext(user_id, practice_id, display_name, role, practice_name)
```

- 关键文件: `apps/web/lib/session.ts`, `services/api/app/context.py`
- practice_id 在服务端确定，客户端无法伪造，保证多租户隔离

### 3.2 多租户隔离策略

| 维度 | 说明 |
|---|---|
| 隔离粒度 | practice_id (诊所级别) |
| 实现方式 | SQL WHERE 子句强制 practice_id = context.practice_id |
| 来源 | practice_id 从服务端 session 解析, 非请求体传入 |
| 冗余设计 | document_chunks 表冗余存储 practice_id, 避免搜索热路径 JOIN |

---

## 四、索引工作流设计

文件: `services/api/app/features/indexing/__init__.py`
入口: `services/api/app/scripts/index_clinical_documents.py`
命令: `make index`

### 分块策略: Recursive Character Splitting

- 按分隔符层级递归切分: `\n\n` (段落) -> `. ` (句子) -> ` ` (词) -> `` (字符)
- 每块目标 ~800 字符
- 块间重叠 ~50 字符，避免语义断裂
- 单块不超过 8000 字符（嵌入服务硬限制）
- 空白或过短文档跳过并记录
- 相比 Fixed-Size splitting，能更好地保持语义完整性

### 变更检测

- 比对 `clinical_documents.source_updated_at` 与已索引 chunks 的 `source_updated_at`
- 仅处理新增或变更的文档
- 变更文档: 先 DELETE 旧 chunks，再 INSERT 新 chunks（事务内）

### 执行流程

1. 查询所有需索引文档 (新增 + 变更)
2. 对每份文档执行 Recursive Character 分块
3. 按 64 条/批调用嵌入服务
4. 事务内: DELETE 旧 chunks + INSERT 新 chunks (per document)
5. 单文档失败: 记录错误，跳过，继续下一份
6. 输出汇总: total / indexed / skipped / failed

### 幂等保证

使用 `INSERT ... ON CONFLICT (document_id, chunk_index) DO UPDATE`

---

## 五、搜索 API 设计

端点: `POST /api/clinical-search`
文件: `services/api/app/features/search/router.py`, `service.py`

### 处理流程

```
用户输入 "recurring headaches with nausea"
  |
  v
[FastAPI search router]
  |-- 校验: query 非空且 <= 500 字符, limit <= 25
  |-- 查 EmbeddingCache -> 命中则跳过嵌入调用
  |-- 未命中 -> 调用 Embedding Service 获取 query 向量
  |
  v
[search_patients service] -- 向量检索 (主策略) --
  |
  |-- 向量检索: HNSW 索引, cosine distance, WHERE practice_id = ?
  |-- 降级: 若嵌入服务不可用, 退回 BM25-only, degraded=true
  |
  v
[患者聚合] GROUP BY patient_id
  |-- 每位患者取最高分 chunk 作为 best_match
  |-- 计算 additional_matching_documents
  |-- 按最高分降序排列, 截取 limit 条
  |
  v
[响应] ClinicalSearchResponse { query, results[], meta{result_count, took_ms, degraded} }
```

### 向量检索策略

| 维度 | 说明 |
|---|---|
| 主策略 | pgvector cosine distance + HNSW 索引 |
| 擅长场景 | 语义匹配 ("头痛" 匹配 "偏头痛") |
| 评分方式 | 1 - cosine_distance, 值越大越相关 |
| 候选扩大 | candidate_limit = limit * 5, 保证聚合后有足够的结果 |

### 降级策略: BM25-only 兜底

| 维度 | 说明 |
|---|---|
| 触发条件 | EmbeddingClient 抛出 CircuitOpenError 或 EmbeddingServiceError |
| 降级行为 | 跳过向量检索, 仅使用 BM25 全文检索, 响应 meta.degraded = true |
| 前端感知 | 前端可据此展示降级提示 |
| 设计理由 | 保证搜索功能在嵌入服务故障时仍可用 (虽然质量下降), 而非直接返回 503 |

### 诊所隔离

在 SQL WHERE 子句中强制 `practice_id = context.practice_id`。practice_id 来源于服务端 session 解析（`RequestContext`），请求体中无此字段，无法被客户端覆盖。

### 错误处理

- 嵌入服务不可用 -> 503 `embedding_service_unavailable`
- 请求验证失败 -> 422 `validation_error`
- 数据库异常 -> 500 `internal_error`（不暴露细节）

---

## 六、嵌入服务容错体系

### 6.1 熔断器 (Circuit Breaker)

文件: `services/api/app/clients/circuit_breaker.py`

三态模型: CLOSED -> OPEN -> HALF_OPEN

| 状态 | 行为 |
|---|---|
| CLOSED | 正常放行; 记录连续失败次数 |
| OPEN | 立即拒绝 (CircuitOpenError); 不发起实际请求 |
| HALF_OPEN | 允许有限探测请求 (half_open_max); 成功则回到 CLOSED, 失败则回到 OPEN |

参数: failure_threshold=5, recovery_timeout=30s, half_open_max=2

### 6.2 指数退避重试

文件: `services/api/app/clients/embedding.py`

- 失败后重试, delay 指数增长: base_delay * 2^(attempt-1)
- 加入随机 jitter 避免雷群效应
- CircuitOpenError 和 EmbeddingInputRejected 不重试, 立即抛出
- 参数: max_attempts=3, base_delay=1s

### 6.3 LRU 嵌入缓存

文件: `services/api/app/clients/embedding_cache.py`

- 查询文本 -> 向量映射, 避免重复调用嵌入服务
- 基于 OrderedDict 实现, max_size=1000
- 无 TTL (嵌入是确定性的, 相同文本永远产生相同向量)
- asyncio 单线程模型下无需显式锁

---

## 七、嵌入模型

文件: `services/embedding/app/encoder.py`

| 维度 | 说明 |
|---|---|
| 模型 | sentence-transformers/all-MiniLM (384维) |
| 推理框架 | ONNX Runtime (CPU) |
| 后处理 | Mean pooling + L2 normalization |
| 选型理由 | 384维向量在存储和查询性能上平衡良好; ONNX 推理无需 GPU, 适合容器化部署; L2 归一化后 cosine distance 等价于欧氏距离排序 |

---

## 八、前端搜索体验

文件: `apps/web/app/search/page.tsx` + `apps/web/features/search/`

### 方案

Server Action + useActionState (React 19)

```
搜索表单 (query input + document type select + submit)
    |
    v  Server Action (searchAction)
features/search/actions.ts -> 前端校验 -> features/search/api.ts -> searchClinicalRecords()
    |
    v  渲染
结果列表 / 空状态 / 错误状态
```

### 状态管理

- idle: 初始，显示提示文字
- loading: 使用 useFormStatus 的 pending 状态显示 Spinner
- results: 渲染患者卡片列表
- no-results: EmptyState 组件
- validation_error: 前端校验 + 后端 422 回显
- service_error: Alert 组件显示 503 错误

### 结果卡片内容

- 患者姓名 (链接到 `/patients/[id]`)
- 文档类型 Badge
- 文档标题 + 日期
- 匹配摘录 (snippet)
- 额外匹配文档数 ("+N more documents")

### 前端架构要点

| 维度 | 说明 |
|---|---|
| 模式 | Server Action + useActionState (React 19) |
| 状态管理 | 无客户端状态库, 通过 useActionState 管理搜索状态机 |
| 数据校验 | Zod schema 前后端共享, 服务端 apiRequest 统一解析+校验 |
| Session | Cookie (demo_user_id) -> Server Component 读取 -> Bearer token 传给 API |

---

## 九、评估看板

文件: `services/api/app/features/evaluation/router.py` + `apps/web/features/evaluation/`

### 流程

```
前端点击 "Run evaluation"
  -> Server Action -> POST /api/evaluation/run
  -> 后端遍历 curated_cases.json (6组 ground truth)
  -> 每组调用 search_patients() 执行搜索
  -> 计算指标: Hit Rate, MRR, NDCG@10, 延迟分位数, decoy 泄漏数
  -> 返回 EvaluationReport
  -> 前端 IndexedDB 持久化历史报告, 支持对比查看
```

### 评估指标

| 指标 | 说明 |
|---|---|
| Hit Rate | 期望患者出现在 top-10 中的比例 |
| MRR | Mean Reciprocal Rank, 命中排名的倒数均值 |
| NDCG@10 | 考虑排名位置的检索质量指标 |
| 延迟分位数 | P50 / P95 / P99 |
| Decoy 泄漏 | 跨诊所 decoy 患者出现在结果中的次数 (应为 0) |

---

## 十、API 端点汇总

| 方法 | 路径 | 功能 |
|---|---|---|
| GET | `/health` | 健康检查 (含依赖状态) |
| GET | `/api/session` | 当前会话信息 |
| GET | `/api/session/identities` | Demo 用户列表 |
| POST | `/api/clinical-search` | 语义搜索 (核心) |
| GET | `/api/patients/{id}` | 患者详情 |
| POST | `/api/evaluation/run` | 运行评估 |

---

## 十一、验收测试

入口: `services/api/tests/acceptance/test_acceptance_checklist.py`
数据: `database/seed/data/curated_cases.json`（6 组 ground truth）

### 11.1 基础功能验收

使用 StubEmbeddingClient（确定性，无需真实嵌入服务）:

| 测试项 | 验证内容 |
|---|---|
| 索引幂等性 | 跑两次索引，chunk 总数不变 |
| 增量更新 | 改文档 body 后重跑，旧 chunk 消失、新 chunk 出现 |
| 容错性 | 6 篇病理文档失败不阻塞整体，其余正常索引 |
| 诊所隔离 | 对每个 curated case，crossPracticeDecoyPatientId 不出现在结果中 |
| 患者去重 | 同一患者多篇匹配文档，结果中只出现一次，additionalMatchingDocuments 正确 |
| 请求验证 | 空查询/超长/非法类型/limit 过大 -> 422，且不触发嵌入调用 |
| 嵌入服务故障 | 返回 503，body 无堆栈信息 |
| 单次嵌入调用 | 一次搜索请求只调用嵌入服务一次 |

### 11.2 向量检索质量验收

使用 real_embedding_client（需 embedding 容器，标记 `@pytest.mark.integration`）:

| 指标 | 目标 | 验证方式 |
|---|---|---|
| Recall@10 | 6/6 curated case 的 expectedPatientId 在 top-10 内 | 集成测试 |
| 隔离正确性 | crossPracticeDecoy 出现次数 = 0 | 集成测试 |
| 排名质量 | expectedPatientId 排名尽量靠前（理想 top-3） | 手动/日志 |
| 证据准确性 | bestMatch.documentId == expectedDocumentId | 集成测试 |
| snippet 可读性 | 摘录包含与 query 相关的完整临床描述 | 手动验证 |

### 11.3 前端状态验收

至少覆盖: 加载中状态、结果渲染、无结果空状态、后端故障提示

---

## 十二、核心设计决策一览

| 决策点 | 选择 | 核心理由 |
|---|---|---|
| 向量索引 | HNSW (m=16, ef_construction=64) | 稳定 recall, 无需手动调参, 增量友好 |
| 检索策略 | 向量检索为主, BM25 仅作降级兜底 | 语义匹配优先, 避免混合融合排序优先级难判定 |
| 降级方案 | BM25-only 兜底 | 保证可用性, degraded 标记透明告知 |
| 嵌入容错 | 熔断器 + 指数退避重试 + LRU 缓存 | 多层防护, 快速失败, 减少冗余调用 |
| 分块策略 | Recursive Character (~800字符, 50字符重叠) | 保持语义完整性, 减少语义断裂 |
| 嵌入模型 | all-MiniLM 384维 ONNX | 轻量, 无需 GPU, 性能够用 |
| 多租户隔离 | SQL WHERE practice_id, 服务端确定 | 安全隔离, 无法客户端伪造 |
| 前端模式 | Server Action + useActionState | SSR 友好, 无客户端状态库依赖 |
