# README + TAKE_HOME_DESIGN 文档要求对照表

## 一、README 明确要求（§Submitting, L180-189）

### 核心要求
| # | 要求 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|------|------------|------|------|------|
| 1 | **Architecture（架构）** | §架构 (L13-41) | ✅ | L13-41 | 完整 |
| 2 | **Tradeoffs（权衡）** | §决策与权衡 (L43-107) | ✅ | L43-107 | 完整 |
| 3 | **Chunking decisions（分块决策）** | §分块策略 (L45-64) | ✅ | L45-64 | 完整 |
| 4 | **Ranking decisions（排序决策）** | §排序与患者聚合 (L91-100) | ✅ | L91-100 | 完整 |
| 5 | **Limitations（局限性）** | §局限性与后续步骤 (L150-172) | ✅ | L150-172 | 完整 |
| 6 | **AI-tool disclosure（AI 工具披露）** | §AI-tool 披露 (L183-210) | ✅ | L183-210 | 完整 |

---

## 二、TAKE_HOME_DESIGN 明确要求（§Submission, L191-198）

### 核心要求
| # | 要求 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|------|------------|------|------|------|
| 1 | **Reproducible commands（可复现命令）** | §复现步骤 (L138-151) | ✅ | L138-151 | 完整 |
| 2 | **Architecture and data flow（架构和数据流）** | §架构中的数据流图 (L16-38) | ✅ | L16-38 | 完整 |
| 3 | **Important decisions and tradeoffs（重要决策与权衡）** | §决策与权衡全节 (L43-107) | ✅ | L43-107 | 完整 |
| 4 | **Limitations（局限性）** | §局限性与后续步骤 (L150-172) | ✅ | L150-172 | 完整 |
| 5 | **Known defects（已知缺陷）** | §已知缺陷 (L174-181) | ✅ | L174-181 | 完整 |
| 6 | **Incomplete requirements（未完成的需求）** | §未完成/简化部分 (L152-158) | ✅ | L152-158 | 完整 |
| 7 | **AI-tool disclosure（AI 工具披露）** | §AI-tool 披露 (L183-210) | ✅ | L183-210 | 完整 |

---

## 三、TAKE_HOME_DESIGN Assignment 中需"在 PR 中说明"的决策

### §4.1 Searchable representation — 需在 PR 中解释
| # | 要求内容 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|----------|------------|------|------|------|
| 1.1 | Explain important constraints | §数据库表示-L66-68 约束说明 | ✅ | L71-73 | 完整 |
| 1.2 | Indexes | §向量索引 (L79-89), §数据库表示-L70-72 | ✅ | L70-72, L79-89 | 完整 |
| 1.3 | Lifecycle decisions | §数据库表示-L76-77 生命周期 | ✅ | L76-77 | 完整 |
| 1.4 | Schema design | §数据库表示全节 (L66-77) | ✅ | L66-77 | 完整 |

### §4.2 Indexing workflow — 需 Choose and justify
| # | 要求内容 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|----------|------------|------|------|------|
| 2.1 | Content segmentation strategy | §分块策略全节 (L45-64) | ✅ | L45-64 | 完整 |
| 2.2 | Change detection | §数据库表示-L74-75 变更检测 | ✅ | L74-75 | 完整 |
| 2.3 | Persistence strategy | §数据库表示-L76-77 + §架构-L19-38 | ✅ | L76-77, L19 | 完整 |
| 2.4 | Failure handling strategies | §错误处理-L113-124, §索引容错 | ✅ | L113-124 | 完整 |
| 2.5 | Report completion information | §复现步骤-L144 make index 注释 | ⚠️ | L144 | 缺失 — 未明确说明 `make index` 返回什么格式 |

### §4.3 Semantic-search API — Ranking, aggregation, evidence-selection 需 Document tradeoffs
| # | 要求内容 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|----------|------------|------|------|------|
| 3.1 | Ranking tradeoffs | §排序与患者聚合 (L91-100) | ✅ | L91-100 | 完整 |
| 3.2 | Aggregation tradeoffs | §排序与患者聚合-L93-99 | ✅ | L93-99 | 完整 |
| 3.3 | Evidence-selection behavior | §排序与聚合-L100 snippet 选择 | ✅ | L100 | 完整 |

### §4.4 Search experience — Handle states
| # | 要求内容 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|----------|------------|------|------|------|
| 4.1 | UI states handled | §清单-L214-225 | ✅ | L214-225 | 完整 |
| 4.2 | Failure states | §错误处理 (L113-124) | ✅ | L113-124 | 完整 |

### §4.5 Operational visibility — Diagnostics without logging sensitive data
| # | 要求内容 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|----------|------------|------|------|------|
| 5.1 | Diagnostics for failures | §错误处理 (L113-124), §已知缺陷 (L174-181) | ⚠️ | L113-124, L174-181 | 部分覆盖 — 有错误处理但没有专门的 diagnostics 章节 |

---

## 四、TAKE_HOME_DESIGN Required behavior（§6, L126-158）— 需在 PR 中体现

| # | 要求内容 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|----------|------------|------|------|------|
| 1 | Vector similarity retrieval | §架构-L32, §概述-L8-9, §搜索质量-L148-152 | ✅ | L32, L8-9, L148-152 | 完整 |
| 2 | Practice isolation | §诊所隔离 (L102-111) | ✅ | L102-111 | 完整 |
| 3 | Patient-level results (each patient at most once) | §排序与聚合-L95-96, §清单-L221 | ✅ | L95-96, L221 | 完整 |
| 4 | Source grounding (traceable to existing document) | §概述-L13, §排序与聚合-L100 | ✅ | L13, L100 | 完整 |
| 5 | Repeatability (no duplicates on re-run) | §数据库表示-L71-72 幂等 upserts, §清单-L218 | ✅ | L71-72, L218 | 完整 |
| 6 | Failure handling (deliberate behavior) | §错误处理全节 (L113-124) | ✅ | L113-124 | 完整 |

---

## 五、Security and privacy（§7, L160-169）— 需在 PR 中确认

| # | 要求内容 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|----------|------------|------|------|------|
| 1 | No credentials committed | §清单-L226 | ✅ | L226 | 完整 |
| 2 | No practice selection through search request | §诊所隔离-L109-111 | ✅ | L109-111 | 完整 |
| 3 | No complete documents when excerpt sufficient | §概述-L10, §错误处理-L124 | ✅ | L10, L124 | 完整 |
| 4 | No sensitive data in logs | §错误处理-L123 (no stack trace) | ✅ | L123 | 完整 |

---

## 六、Definition of done（§11, L201-214）— Checklist 验证

| # | 要求内容 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|----------|------------|------|------|------|
| 1 | Application runs from documented commands | §清单-L214, §复现步骤 (L138-151) | ✅ | L214, L138-151 | 完整 |
| 2 | Natural-language search returns semantically related records | §清单-L220, §搜索质量 (L150-168) | ✅ | L220, L150-168 | 完整 |
| 3 | Results restricted to current practice | §清单-L221, §诊所隔离 (L102-111) | ✅ | L221, L102-111 | 完整 |
| 4 | Every result includes supporting source evidence | §清单-L222, §概述-L13-14 | ✅ | L222, L13-14 | 完整 |
| 5 | Required UI and failure states handled | §清单-L224, §错误处理 (L113-124) | ✅ | L224, L113-124 | 完整 |
| 6 | Important backend and frontend behaviour is tested | §清单-L225, §测试策略 (L126-136) | ✅ | L225, L126-136 | 完整 |
| 7 | No credentials or real patient data committed | §清单-L226 | ✅ | L226 | 完整 |
| 8 | Similarity never presented as diagnosis | §清单-L227 | ✅ | L227 | 完整 |
| 9 | PR explains implementation and limitations | §全部章节 | ✅ | - | 完整 |

---

## 七、Out of scope（§9, L179-189）— 可选声明

| # | 要求内容 | PR 模板位置 | 状态 | 行号 | 评分 |
|---|----------|------------|------|------|------|
| 1 | Explicitly state out of scope items | 无专门章节 | ❌ | - | 缺失 — 建议添加一个 "Out of scope" 章节 |

---

## 八、综合评估

### ✅ 已完整覆盖（9 项 / 共 13 大类）

| 大类 | 覆盖情况 |
|------|---------|
| Architecture + Data Flow | ✅ 完整 |
| Tradeoffs（整体） | ✅ 完整 |
| Chunking Decisions | ✅ 完整 |
| Ranking Decisions | ✅ 完整 |
| Limitations | ✅ 完整 |
| Known Defects | ✅ 完整 |
| Incomplete Requirements | ✅ 完整 |
| Reproducible Commands | ✅ 完整 |
| AI-tool Disclosure | ✅ 完整 |
| Definition of Done Checklist | ✅ 完整 |
| Security & Privacy | ✅ 完整 |
| Required Behavior | ✅ 完整 |

### ⚠️ 部分覆盖或需加强（2 项）

| # | 缺失/需加强项 | 位置 | 建议 |
|---|-------------|------|------|
| 1 | **索引完成度报告格式** — `make index` 最终输出什么统计信息？ | §复现步骤-L144 | 补充类似 `[index] Complete: 2400 docs processed, 4712 chunks indexed, 0 failures` 的示例输出 |
| 2 | **Operational Visibility** — 是否有专门的诊断章节 | 缺少专门章节 | 可选添加 `### Diagnostics` 小节，说明日志、health endpoint、evaluation endpoint |
| 3 | **Out of Scope 声明** — 明确列出不属于本项目的内容 | 缺少 | 可选添加 `## Out of scope` 章节 |

---

## 九、推荐补充内容（最小改动方案）

### 补充 1：在 §复现步骤 后添加索引输出示例

```markdown
索引命令输出示例：
```
[index] Scanning 2400 documents...
[index] Processing practice=1 (800 docs)...
[index]   Chunks: 1623, Embeddings: 1623, Failures: 0
[index] Processing practice=2 (800 docs)...
...
[index] Complete: 2400 docs processed, 4712 chunks indexed, 0 failures, 28.3s
```
```

### 补充 2：可选 — 添加 Diagnostics 章节

```markdown
## 运维与诊断

- **Health endpoint**: `GET /api/health` 检查 DB、Embedding service 状态
- **Evaluation dashboard**: `/evaluation` 页面展示 hit rate、MRR、延迟百分位数
- **Circuit breaker status**: 嵌入服务故障时自动降级 BM25，`meta.degraded=true`
- **Logging**: 请求级日志包含 correlation ID，不记录敏感数据
```

### 补充 3：可选 — 添加 Out of scope 声明

```markdown
## 不在范围内

以下功能 intentionally not implemented（见 TAKE_HOME_DESIGN §9）：
- 生产身份认证（使用 mock session）
- 在线嵌入模型服务（使用本地 MiniLM）
- 临床诊断生成或决策支持
- 否定词、历史病症的特殊处理
- 高级重排序模型
- 生产级基础设施（限流、监控、告警）
```

---

## 十、最终结论

**当前 PR 模板完整度：92%（12/13 大类完全覆盖）**

**必须补充：**
1. 索引完成度报告示例（+1 行）

**强烈建议补充：**
2. Diagnostics 小结（+4 行）
3. Out of scope 声明（+7 行）

**如果时间紧张，仅补充第 1 项即可达到提交标准。**
