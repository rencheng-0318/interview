# 临床记录语义搜索 — 架构设计

---

## 一、整体数据流

```
源文档 (clinical_documents)
    |
    v
[索引工作流] -- 分块 --> chunks -- 嵌入服务 --> vectors
    |
    v
PostgreSQL (document_chunks 表 + pgvector)
    |
    v
[搜索 API] <-- 查询向量化 <-- 嵌入服务
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
- `document_chunks_embedding_idx`: IVFFlat (embedding vector_cosine_ops), lists=100
- `document_chunks_practice_type_idx`: (practice_id, document_type)
- `document_chunks_patient_idx`: (patient_id)

设计要点:
- ON DELETE CASCADE: 源文档删除时自动清理 chunks
- 冗余字段避免搜索热路径上的 JOIN
- IVFFlat 适合当前数据量；<10k 行时精确搜索亦可

### 2.3 ER 关系图

```
practices (1) ──< users (N)
practices (1) ──< patients (N)
practices (1) ──< clinical_documents (N)
patients  (1) ──< clinical_documents (N)
clinical_documents (1) ──< document_chunks (N)  [新增]
```

---

## 三、索引工作流设计

文件: `services/api/app/features/indexing/__init__.py`
入口: `services/api/app/scripts/index_clinical_documents.py`
命令: `make index`

### 分块策略

- 按段落/句子边界分块，每块目标 ~800 字符
- 块间重叠 ~50 字符，避免语义断裂
- 单块不超过 8000 字符（嵌入服务硬限制）
- 空白或过短文档跳过并记录

### 变更检测

- 比对 `clinical_documents.source_updated_at` 与已索引 chunks 的 `source_updated_at`
- 仅处理新增或变更的文档
- 变更文档: 先 DELETE 旧 chunks，再 INSERT 新 chunks（事务内）

### 执行流程

1. 查询所有需索引文档 (新增 + 变更)
2. 对每份文档执行分块
3. 按 64 条/批调用嵌入服务
4. 事务内: DELETE 旧 chunks + INSERT 新 chunks (per document)
5. 单文档失败: 记录错误，跳过，继续下一份
6. 输出汇总: total / indexed / skipped / failed

### 幂等保证

使用 `INSERT ... ON CONFLICT (document_id, chunk_index) DO UPDATE`

---

## 四、搜索 API 设计

端点: `POST /api/clinical-search`
文件: `services/api/app/features/search/router.py`

### 处理流程

1. 验证请求 (query 非空且 <= 500 字符, limit <= 25)
2. 调用嵌入服务将 query 向量化
3. 执行向量检索 SQL:
   - WHERE practice_id = context.practice_id (诊所隔离)
   - 可选: AND document_type = ANY($types)
   - ORDER BY embedding <=> $query_vector
   - LIMIT 扩大 (如 limit * 5) 以获取足够候选
4. 患者聚合:
   - GROUP BY patient_id
   - 每位患者取最高分 chunk 作为 best_match
   - 计算 additional_matching_documents
5. 按最高分排序，截取 limit 条
6. 组装响应

### 诊所隔离

在 SQL WHERE 子句中强制 `practice_id = context.practice_id`。practice_id 来源于服务端 session 解析（`RequestContext`），请求体中无此字段，无法被客户端覆盖。

### 错误处理

- 嵌入服务不可用 -> 503 `embedding_service_unavailable`
- 请求验证失败 -> 422 `validation_error`
- 数据库异常 -> 500 `internal_error`（不暴露细节）

---

## 五、前端搜索体验

文件: `apps/web/app/search/page.tsx` + `apps/web/features/search/`

### 方案

Server Action + useActionState (React 19)

```
搜索表单 (query input + document type select + submit)
    |
    v  Server Action
features/search/api.ts -> searchClinicalRecords()
    |
    v  渲染
结果列表 / 空状态 / 错误状态
```

### 状态管理

- idle: 初始，显示提示文字
- loading: 使用 useFormStatus 的 pending 状态显示 Spinner
- results: 渲染患者卡片列表
- no-results: EmptyState 组件
- invalid-input: 前端校验 + 后端 422 回显
- dependency-failure: Alert 组件显示 503 错误

### 结果卡片内容

- 患者姓名 (链接到 `/patients/[id]`)
- 文档类型 Badge
- 文档标题 + 日期
- 匹配摘录 (snippet)
- 额外匹配文档数 ("+N more documents")

---

## 六、验收测试

入口: `services/api/tests/acceptance/test_acceptance_checklist.py`
数据: `database/seed/data/curated_cases.json`（6 组 ground truth）

### 6.1 基础功能验收

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

### 6.2 向量检索质量验收

使用 real_embedding_client（需 embedding 容器，标记 `@pytest.mark.integration`）:

| 指标 | 目标 | 验证方式 |
|---|---|---|
| Recall@10 | 6/6 curated case 的 expectedPatientId 在 top-10 内 | 集成测试 |
| 隔离正确性 | crossPracticeDecoy 出现次数 = 0 | 集成测试 |
| 排名质量 | expectedPatientId 排名尽量靠前（理想 top-3） | 手动/日志 |
| 证据准确性 | bestMatch.documentId == expectedDocumentId | 集成测试 |
| snippet 可读性 | 摘录包含与 query 相关的完整临床描述 | 手动验证 |

### 6.3 前端状态验收

至少覆盖: 加载中状态、结果渲染、无结果空状态、后端故障提示
