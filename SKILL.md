---
name: lark-autocontext
description: |
  Trigger when user mentions ANY of: 保存上下文 / 存入上下文 / 业务记忆 / 项目知识 / 存入知识库 / lark-autocontext / /lark-autocontext / 保存到业务上下文 / 扫描飞书 / 同步飞书知识.
  Also trigger when: user sends a Feishu doc/sheet link with intent to store or remember.
  Supports: save single document, batch scan Feishu sources, retrieve project history, ask cross-project questions.
  If config.json is missing, guide first-time setup automatically.
---

# Lark AutoContext (OKF Architecture)

## Pre-flight Check (每次执行前必检)

**Before running ANY workflow (A/B/C/D), always check lark-cli availability first:**

1. **Check lark-cli installed:** Run `lark-cli --version` in terminal.
   - If command not found → Tell user: "需要先安装 lark-cli：`npm install -g @larksuiteoapi/lark-cli`"
   - Do NOT proceed until installed.

2. **Check lark-cli logged in:** Run `lark-cli auth status`.
   - If not logged in → Tell user: "需要先登录飞书：`lark-cli auth login --recommend --no-wait`，然后在浏览器完成授权"
   - Do NOT proceed until authenticated.

3. **Check config.json exists:** Verify `scripts/config.json` exists.
   - If missing → Guide user to copy from `config.json.example` and fill in tokens.

4. **Check bundle initialized:** Verify `bundle/index.md` exists.
   - If missing → Run `python scripts/init_bundle.py` first.

Only after ALL 4 checks pass, proceed to the requested workflow.

## 🎯 Quick Start (首次使用引导)

**When this skill is triggered for the first time** (config.json missing or bundle not initialized):

Show the user this onboarding card **before any other action**:

```
🧙 **Lark AutoContext** — 你的业务记忆库 (OKF 架构)

让业务知识永不丢失。把飞书文档、会议纪要、复盘报告自动转化为 OKF 标准知识。

━━━━━━━━━━━━━━━━━━━━━━

📌 **如何使用？**

方式 1️⃣  保存单文档
  直接发文档链接 + "帮我存一下" / "保存到上下文"
  → 自动提取 → AI分类 → 生成OKF Markdown → 入库

方式 2️⃣  批量扫描
  "扫描飞书文档" / "同步飞书知识"
  → 批量提取 → AI分类 → 生成OKF Markdown → 入库

方式 3️⃣  查询上下文
  "XX 项目里关于优惠券做了什么决策？"
  → 查询OKF Bundle → 返回结果

━━━━━━━━━━━━━━━━━━━━━━

⚡ **首次使用：需要初始化**

我将为你自动创建 OKF Bundle 目录来存储知识。
确认后输入 ✅ 或 "开始"，我会自动完成。
```

**After user confirms**, run `python scripts/init_bundle.py` automatically and show:
```
✅ OKF Bundle 已初始化！
📝 现在可以开始保存上下文了。
```

Then **wait for the user's next message**.

---

This skill guides the agent to extract, classify, and store business context from Feishu documents into an OKF-compliant Markdown Bundle.

## 🔧 Configuration

Scripts automatically load `scripts/config.json` for bundle path and optional Feishu config.
Batch scanning requires `scripts/scan_config.json` (copy from `scan_config.json.example`).

**First-time Setup (Auto-detected):**
- If `config.json` is missing → trigger the **Quick Start** onboarding flow above.
- If Bundle directory doesn't exist → run `python scripts/init_bundle.py`.
- **NEVER** show raw Python tracebacks to the user. Always catch errors and provide friendly guidance.

## Mandatory Workflows

### Step 0: First-Time Check (ALWAYS run first)
- Run `python scripts/onboarding.py` to check setup status.
- If it shows ❌ or ⚠️ → trigger the **Quick Start** onboarding flow above.
- If all ✅ → proceed to appropriate workflow.

---

## Workflow A: Single Document Save

**Trigger:** User sends a Feishu doc/sheet link with save intent, or says "保存这个文档 <link>".

### Step A1: Extract Document Content
- Run `python scripts/scanner.py --doc "<url>"`.
- The script extracts content from Feishu and returns JSON with `source_type`, `doc_token`, `title`, `url`, `content`.

### Step A2: Classify Document (AI Classification)
Read the document content and apply the **Classification Guide** below to extract structured fields.

### Step A3: Generate OKF Markdown
- Construct the classified JSON (see Classification Guide for fields).
- Run `python scripts/okf_writer.py '<classified_json>' '<raw_content>'`.
- The script writes the .md file to the Bundle and updates index.md/log.md.

### Step A4: Show Save Summary
```
✅ 已保存到 OKF Bundle
📄 文件: projects/{project}/{category}/{filename}
🏷️ 类型: {type}
📝 描述: {description}
🔗 来源: {resource}
```

### Step A5: Commit to Git
- Run `git add bundle/` and `git commit -m "docs: save {title} to OKF Bundle"`.

---

## Workflow B: Batch Scan

**Trigger:** User says "扫描飞书文档" / "同步飞书知识" / "批量导入".

### Step B1: Run Scanner
- Run `python scripts/scanner.py` (reads scan_config.json automatically).
- The script scans all configured Feishu sources and returns JSON with `documents` array.

### Step B2: Classify Each Document
For each document in the scan result, apply the **Classification Guide** to extract structured fields.

### Step B3: Generate OKF Markdown for Each
- For each classified document, run `python scripts/okf_writer.py '<classified_json>' '<raw_content>'`.
- Process documents one by one.

### Step B4: Show Scan Summary
```
✅ 扫描完成
📊 总计: {total} 个文档
🆕 新增: {created} 个
🔄 更新: {updated} 个
⚠️ 失败: {failed} 个
```

### Step B5: Commit to Git
- Run `git add bundle/` and `git commit -m "docs: batch scan {total} documents to OKF Bundle"`.

### ⚡ 批量处理优化（文档量大时使用 Subagent）

**当扫描结果超过 10 篇文档时**，为避免阻塞主对话，使用 Task tool 启动 subagent 执行批量处理：

```
Task(subagent_type="general_purpose", query="批量处理飞书文档", description="Batch scan Feishu docs", response_language="Chinese", 
     task_description="在 lark-autocontext 项目下执行 Workflow B（批量扫描飞书文档）：
     1. 运行 python scripts/scanner.py 获取文档列表
     2. 对每篇文档执行 Classification Guide 分类
     3. 对每篇文档运行 python scripts/okf_writer.py 生成 OKF Markdown
     4. 运行 git add bundle/ && git commit -m 'docs: batch scan'
     5. 返回扫描结果摘要：总计/新增/更新/失败数量")
```

**主对话可以继续响应用户**，subagent 完成后返回结果摘要。

---

## Workflow C: Query Context

**Trigger:** User asks a question about stored context.

### Mode 1: Project-Scoped Query
When user mentions a specific project (e.g., "lark-autocontext项目里关于 XX 的信息"):
- Run `python scripts/query.py --project "<project_name>" --keyword "<keyword>"`.
- Parse the JSON results and answer the user's question.
- Include `resource` links for traceability.

### Mode 2: Global Search
When user asks an open-ended question (e.g., "最近有什么关于 OKF 的讨论？"):
- Run `python scripts/query.py --keyword "<keyword>"`.
- Results are sorted by timestamp descending.
- Synthesize a coherent answer from multiple sources.

### Mode 3: Type Filter
When user asks for a specific type (e.g., "给我所有会议纪要"):
- Run `python scripts/query.py --type "Meeting Minutes"`.
- Return the list of matching documents.

### Getting Full Content
- Query results include `body_preview` (first 200 chars) and `file_path`.
- When full content is needed, Read the .md file at `bundle/{file_path}`.

---

## Workflow D: Auto-Sync (自动同步)

**Trigger:** Agent 定时任务调用 / 用户说"扫一遍飞书" / "同步飞书知识".

### Step D1: List Changed Documents
- Run `python scripts/auto_sync.py list-only --config config.json`.
- This produces `.auto_sync/pending_changes.json` with all changed docs since last sync.

### Step D2: Classify & Write Each Change
Read `.auto_sync/pending_changes.json`. For each entry in `changes`:
1. Fetch full content: `python scripts/scanner.py --doc "<url>"` (content is auto-cleaned).
2. Apply the **Classification Guide** to determine `type`, `project`, `category`, etc.
3. Run `python scripts/okf_writer.py '<classified_json>' '<raw_content>'`.
   - People/Concept entities are auto-upserted with preserved `# Profile` / `# Definition` regions.

### Step D3: Finalize
- Run `python scripts/auto_sync.py finalize --commit`.
- This updates `.auto_sync/state.json` watermarks and commits to git.

### Step D4: Summary
```
✅ 同步完成
📊 本次: {N} 篇文档
📁 路径: bundle/projects/...
⏭️  下次自动跳过未变更文档
```

**幂等保证:** 同一 `resource`（doc_token）重跑不会产生重复条目；人工编辑过的 `# Profile` / `# Definition` 区段不会被覆盖。

### ⚡ 批量同步优化（文档量大时使用 Subagent）

**当 pending_changes 超过 10 篇文档时**，为避免阻塞主对话，使用 Task tool 启动 subagent 执行批量同步：

```
Task(subagent_type="general_purpose", query="批量同步飞书文档", description="Auto-sync Feishu docs", response_language="Chinese",
     task_description="在 lark-autocontext 项目下执行 Workflow D（自动同步飞书到 bundle）：
     1. 运行 python scripts/auto_sync.py list-only --config config.json 获取变更列表
     2. 对每篇变更文档执行 Classification Guide 分类
     3. 对每篇文档运行 python scripts/okf_writer.py 生成 OKF Markdown
     4. 运行 python scripts/auto_sync.py finalize --commit
     5. 返回同步结果摘要：本次同步数量、路径、下次自动跳过未变更文档")
```

**主对话可以继续响应用户**，subagent 完成后返回结果摘要。

---

## Agent Cron Setup

本项目不内置守护进程，定时由 Agent 侧承担。

### TRAE Schedule
使用 Schedule 工具，cron `0 9 * * *`，message：
> 在 lark-autocontext 项目下执行 Workflow D（自动同步飞书到 bundle）。完成后只输出一句"同步 N 篇"或"无变化"。

### Cursor Tasks
在项目根 `.cursor/tasks.json` 里登记同样的命令序列。

### Claude Code cron
通过用户自己的 crontab：
```
0 9 * * * cd ~/projects/lark-autocontext && claude --workflow=auto-sync
```

---

## Classification Guide

> **设计哲学**：本项目对齐 [OKF SPEC §1 Non-goals](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) —— **不预设固定的 type 词表**。
> 飞书用户来自各行各业（产品、运营、法务、研究、教育……），任何硬编码的分类都会逼用户把内容塞进不合身的格子。
> Agent 的职责是 **基于实际内容判断**，并通过"bundle 内复用约束 + consumer 兜底"保持图谱一致。

When you receive document content from the Scanner, analyze it and produce a JSON with the fields below.

### 1. project
Which project does this belong to? Infer from:
- Document title (e.g., "Lark AutoContext 周会" → `lark-autocontext`)
- Content context (mentions of specific project names)
- Folder / wiki space structure if available
- If unclear, ask the user before writing

### 2. type — **open vocabulary, soft-constrained**

`type` 是 OKF SPEC 唯一必填的 frontmatter 字段。它的值应该：

- **2–4 个词的英文 Title Case 或 PascalCase 名词短语**（例如：`Meeting Minutes`、`Design Doc`、`ADR`、`Postmortem`、`Runbook`、`Policy`、`Research Note`、`Contract Clause`）
- 描述"**这是什么**"，不描述"它属于哪个项目"（项目用 `project` 字段表达）
- **跨文档可复用**：同一类内容必须给同一个 `type` 值

#### 优先复用已有 type（强约束）

写入前**先读取** `bundle/index.md` 的 frontmatter，里面有 `types_seen: [...]` 列表（由 okf_writer 自动维护）。

- 如果当前文档**完全可以匹配**已有 type，**必须复用**——不要用同义词造新值（不要今天写 `Meeting Minutes`、明天写 `Meeting Note` 或 `会议纪要`）。
- 只有当文档**确实属于一个新类别**，且这个类别**预计未来还会重复出现**时，才创造新 type。

#### 何时该创造新 type

- 法务用户首次导入合同条款 → 可以创造 `Contract Clause` / `Legal Opinion`
- 研究用户首次导入实验记录 → 可以创造 `Experiment Log` / `Dataset Card` / `Finding`
- 教育用户首次导入教案 → 可以创造 `Lesson Plan` / `Rubric`

#### 常见 type 参考（**非穷举、非强制**，仅作为命名风格参考）

| 场景 | 常见 type 候选 |
|------|---------------|
| 通用协作 | `Meeting Minutes`, `Requirement Doc`, `Design Doc`, `Review Report`, `Operation Plan` |
| 工程研发 | `ADR`, `Runbook`, `Postmortem`, `API Reference`, `Tech Spec` |
| 数据/分析 | `Data Analysis`, `Metric`, `Dataset Card`, `Dashboard Note` |
| 法务/合规 | `Contract`, `Contract Clause`, `Policy`, `Legal Opinion` |
| 研究 | `Research Note`, `Experiment Log`, `Hypothesis`, `Finding`, `Reference` |
| 实体节点（跨文档） | `Person`, `Concept`, `Project`, `Product`, `Feature` |

不要**强行**把内容塞进上表。表里没有的，按上面的命名规则自己起。

### 3. Structured fields (extract from content)

| 字段 | 说明 |
|------|------|
| `title` | 文档标题 |
| `description` | 一句话摘要，必须有实质信息，不能是 `"{type} - {title}"` 这种机械模板 |
| `tags` | 2–5 个关键词（array），用于过滤和搜索 |
| `people` | 文中出现的真实人名（array） |
| `concepts` | 反复出现的术语 / 缩写 / 代号（array） |
| `summary` | 1–3 句正文摘要 |
| `key_points` | 主要要点（array of string） |
| `decisions` | 仅当文档包含明确决议时填，结构 `{decision, owner, deadline}` |
| `action_items` | 仅当文档包含可追踪行动项时填，结构 `{task, owner, due}` |
| `filename` | 从 title 派生，例如 `"2026-06-20 重构讨论"` → `"2026-06-20-重构讨论.md"` |
| `resource` | 原飞书文档 URL（用于去重和回溯） |
| `edited_time` | 飞书原始编辑时间（写入 frontmatter 的 `timestamp`） |

### 4. category — auto-derived (不需要 LLM 决定)

`category` 由 okf_writer 根据 `type` 自动 slugify：
- `Meeting Minutes` → `meeting-minutes`
- `ADR` → `adr`
- `Contract Clause` → `contract-clause`

写出到 `bundle/projects/{project}/{category}/{filename}`。Agent **不需要**显式输出 `category`，传了也会被覆盖。

### 5. Atomic Entities — second-pass extraction (核心增强)

> 这一步是让图谱"活起来"的关键。**不要只把文档本身当节点**，要把文档里出现的**跨文档复用实体**也升格为独立的 OKF 文件。

扫描文档正文，识别出**值得独立成节点**的原子实体。判断标准（三条全部满足）：

1. **跨文档复用可能性高**——这个实体**很可能**在其他文档里被再次提到
2. **有自己的属性**——不只是一个标签词，而是有定义/描述/关系的东西
3. **独立于当前文档存在**——脱离当前文档后仍然有意义

**type 由你自己定**（同样遵循"开放 + 复用"原则）。一些示例（**非穷举**）：

| 用户类型 | 可能抽取出的实体 type |
|---------|---------------------|
| 产品/运营 | `Person`, `Concept`, `Project`, `Product`, `Feature`, `Metric` |
| 法务 | `Person`, `Party`, `Contract`, `Clause` |
| 研究 | `Person`, `Concept`, `Dataset`, `Hypothesis`, `Finding`, `Reference` |
| 工程 | `Person`, `Service`, `API`, `Library`, `Incident` |

对每个抽取出的实体，在最终 JSON 里**直接用对应字段表达**：
- `people: [...]` 会被自动 upsert 为 `bundle/people/{name}.md`
- `concepts: [...]` 会被自动 upsert 为 `bundle/concepts/{name}.md`
- 其他自定义实体类型，写入 `entities` 字段（见下方扩展示例），okf_writer 会自动 upsert 到 `bundle/{slug(type)}/{name}.md`

```json
"entities": [
  {"type": "Metric", "name": "GMV", "brief": "总成交额，运营核心指标"},
  {"type": "Feature", "name": "智能推荐 v2", "brief": "..."},
  {"type": "Project", "name": "618 大促", "brief": "..."}
]
```

**重要**：实体抽取宁缺勿滥。每篇文档的 `entities` 应保持在 0–8 个之间，只挑**真正会被复用**的。把所有名词都升格为节点 = 退化成另一种"灰球海"。

### OKF Body Structure (7 Sections)

All documents follow this body structure (sections are omitted when empty):

1. `# Summary` — 1-3 sentence summary
2. `# Key Points` — Bullet list of main takeaways
3. `# Decisions` — (Meeting Minutes / Review Report only) Decisions with owner + deadline
4. `# Action Items` — (Meeting Minutes / Requirement Doc only) Tasks with owner + due
5. `# Source Content` — Original document content (auto-cleaned)
6. `# Related` — Cross-links to people/concepts/projects (auto-generated)
7. `# Citations` — Link to original Feishu document

### Classified JSON Example

```json
{
  "project": "lark-autocontext",
  "type": "Meeting Minutes",
  "title": "2026-06-20 重构讨论",
  "description": "讨论 OKF taxonomy 开放化与 Agent 自决实体抽取方案",
  "tags": ["重构", "OKF", "taxonomy"],
  "people": ["张三", "李四"],
  "concepts": ["OKF", "taxonomy"],
  "entities": [
    {"type": "Project", "name": "Lark AutoContext", "brief": "飞书知识库自动归档项目"},
    {"type": "Metric", "name": "节点图谱密度", "brief": "可视化质量指标"}
  ],
  "summary": "团队决定放弃硬编码 type 词表，改为 Agent 基于内容自决",
  "key_points": ["对齐 OKF SPEC 开放性原则", "bundle 自描述 types_seen 列表"],
  "decisions": [
    {"decision": "采用开放 type + 软约束方案", "owner": "张三", "deadline": "2026-06-25"}
  ],
  "action_items": [
    {"task": "重写 SKILL.md Classification Guide", "owner": "李四", "due": "2026-06-22"}
  ],
  "filename": "2026-06-20-重构讨论.md",
  "resource": "https://feishu.cn/docx/abc123",
  "edited_time": "2026-06-20T15:00:00+08:00"
}
```

---

## OKF Bundle Structure

```
bundle/
├── index.md              # Root navigation
├── log.md                # Change history
├── projects/             # Organized by project
│   ├── index.md
│   └── {project}/        # One directory per project
│       ├── index.md
│       ├── meetings/
│       ├── requirements/
│       └── ...
├── concepts/             # Cross-project concepts
└── people/               # People info
```

## Pitfalls & Lessons Learned

1. **Preview Card Rendering**: Use plain text list format, NOT markdown tables. Tables fail to render in Feishu mobile.
2. **Deduplication**: OKF Writer uses `resource` field (Feishu doc_token) to detect duplicates. Same doc scanned twice = update, not duplicate.
3. **Filename Safety**: Filenames are sanitized (no `<>:"/\|?*` characters).
4. **Index Updates**: Every write updates the category's index.md and root log.md automatically.
5. **Incremental Scan**: Scanner tracks `last_modified` to skip unchanged documents on subsequent scans.
6. **Windows Encoding**: All scripts force UTF-8 output on Windows to handle Chinese characters and emoji.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| 首次使用 / 没有 config.json | 运行 `python scripts/init_bundle.py` 自动创建 Bundle |
| Bundle 未初始化 | 运行 `python scripts/init_bundle.py` |
| Token 过期 / 认证失败 | 运行 `lark-cli auth login --recommend --no-wait` 重新登录 |
| 扫描配置缺失 | 从 `scan_config.json.example` 复制并填写飞书 token |
| 查询无结果 | 先保存文档或运行批量扫描 |
| 提取失败 | 检查文档链接格式是否正确（应为 feishu.cn/docx/xxx） |

### ⚠️ Windows 用户注意

| 问题 | 说明 |
|------|------|
| **PowerShell `&&` 不支持** | Windows PowerShell 不支持 `&&` 连接符，请用分号 `;` 或直接分开运行命令 |
| **PowerShell JSON 引号转义** | 在 PowerShell 中直接传递 `--json "{...}"` 时引号会被转义，**建议使用 Python 脚本调用** |

**错误处理铁律**：
- ❌ **禁止** 向用户展示 Python traceback 或 raw JSON 错误
- ✅ **必须** 捕获异常，转换为中文友好提示
- ✅ **必须** 告诉用户下一步该做什么
