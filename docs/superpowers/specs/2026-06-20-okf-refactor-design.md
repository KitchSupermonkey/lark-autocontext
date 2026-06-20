# OKF-Based Lark AutoContext Refactor Design

**Date:** 2026-06-20
**Status:** Approved (spec review complete)
**Author:** KitchXia + TRAE

---

## 1. Motivation

The current lark-autocontext stores business context in Feishu Bitable (one table per project). While functional, this approach has limitations:

- **No version control**: Context changes are not diffable or rollbackable.
- **Agent lock-in**: Only agents with Feishu API access can consume the context.
- **No semantic structure**: Records are flat rows in a table, not navigable knowledge graphs.
- **Search latency**: Every query requires real-time Feishu API calls traversing all tables.

Google's Open Knowledge Format (OKF) v0.1 solves these problems by defining a standard for knowledge representation using Markdown + YAML Frontmatter. This refactor rebuilds lark-autocontext as an **OKF producer and consumer**: scanning Feishu documents, auto-classifying them with AI, and generating an OKF Bundle that any agent can read.

### Goals

1. **OKF-first storage**: Knowledge stored as OKF Markdown files in a Git-versioned Bundle.
2. **Automated scanning**: Scan specified Feishu sources (wiki, folder, bitable) and extract content.
3. **AI classification**: Automatically classify documents into OKF concept types.
4. **Fast retrieval**: Agents query the local OKF Bundle via Skill scripts, no Feishu API calls needed.
5. **Incremental sync**: Only process changed documents on subsequent scans.

### Non-goals

- Replacing all Feishu functionality (Feishu remains the source of truth for raw documents).
- Building a web UI (the OKF Bundle is consumed by agents, not humans directly).
- Vector search / semantic retrieval (keyword matching is sufficient for v1).
- MCP Server integration (can be added later as a thin wrapper over Query Engine).
- Migrating existing Bitable data (existing data stays in Bitable, new data goes to OKF).

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────┐
│                   lark-autocontext                   │
│                                                      │
│  ┌──────────┐   ┌───────────┐   ┌────────────┐      │
│  │ Scanner  │→→│   Agent   │→→│ OKF Writer │      │
│  │ (飞书扫描)│   │ (AI分类)   │   │ (生成MD)   │      │
│  └──────────┘   └───────────┘   └────────────┘      │
│       ↑                              ↓               │
│  lark-cli                      ┌──────────┐         │
│  (保留现有封装)                 │ OKF Bundle│         │
│                                │ (本地Git) │         │
│                                └──────────┘         │
│                                      ↓               │
│                                ┌──────────┐         │
│                                │  Query   │         │
│                                │ Engine   │         │
│                                │ (Skill)  │         │
│                                └──────────┘         │
│                                      ↓               │
│                                ┌──────────┐         │
│                                │  Agent   │         │
│                                └──────────┘         │
└─────────────────────────────────────────────────────┘
```

### Data Flow

**Batch Scan Flow:**
```
Feishu wiki/folder/bitable → Scanner extracts content → Agent classifies (AI)
→ OKF Writer generates .md files → Bundle directory (Git)
```

**Single Document Flow:**
```
User provides link → Scanner extracts single doc → Agent classifies (AI)
→ OKF Writer generates .md file → Bundle directory (Git)
```

### Core Modules

1. **Scanner** — Scans specified Feishu sources OR extracts single document. Reuses existing `cli.py` API wrappers.
2. **Agent Classification** — Agent uses LLM to auto-classify documents (meeting minutes, requirements, reviews, etc.) and extract structured fields. Defined in SKILL.md as agent guidance.
3. **OKF Writer** — Generates OKF-compliant Markdown files (YAML Frontmatter + Body) into the Bundle directory.
4. **Query Engine** — Skill script that agents call to retrieve context from the OKF Bundle.

### Feishu Bitable Role

Downgraded to optional visualization. The primary storage is the OKF Bundle. A "sync to Feishu" step can be added later if dashboard visualization is still needed.

---

## 3. OKF Bundle Structure

```
lark-autocontext-bundle/
├── index.md                          # Root navigation: lists all projects
├── log.md                            # Change history: records each scan/update
│
├── projects/                         # Organized by project (one directory per project)
│   ├── index.md                      # Project list navigation
│   │
│   ├── lark-autocontext/             # Single project directory
│   │   ├── index.md                  # In-project document list
│   │   ├── meetings/                 # Meeting minutes
│   │   │   ├── index.md
│   │   │   └── 2026-06-20-周会.md
│   │   ├── requirements/             # Requirement docs
│   │   │   ├── index.md
│   │   │   └── v2-重构需求.md
│   │   ├── reviews/                  # Review reports
│   │   │   └── q2-复盘.md
│   │   └── metrics/                  # Business metrics
│   │       └── 用户活跃度.md
│   │
│   └── okf-project/                  # Another project
│       ├── index.md
│       └── ...
│
├── concepts/                         # Cross-project general concepts
│   ├── index.md
│   └── glossary.md                   # Glossary
│
└── people/                           # People info (optional)
    └── index.md
```

### Concept Document Format

```markdown
---
type: Meeting Minutes
title: "2026-06-20 Lark AutoContext 重构讨论"
description: 讨论基于 OKF 标准重构 lark-autocontext 的方案
resource: https://your-tenant.feishu.cn/docx/abc123
tags: [重构, OKF, 架构设计]
timestamp: 2026-06-20T14:00:00Z
project: lark-autocontext
people: [张三, 李四]
---

# 会议要点

## 核心结论
确定采用 Pipeline 架构，OKF 为主存储...

## 关键时间
- 2026-06-20: 方案确定
- 2026-06-25: 开始实现

## 涉及人员
- 张三: 架构设计
- 李四: 飞书 API 对接

# Citations
[1] [飞书原文文档](https://your-tenant.feishu.cn/docx/abc123)
```

### OKF Conformance

- `type` is the only required field (OKF v0.1 spec).
- `project`, `people` are extension fields for Query Engine filtering.
- `resource` points to the original Feishu document for traceability.
- `index.md` provides progressive disclosure navigation.
- `log.md` records all changes in ISO 8601 date format.

---

## 4. Scanner Module

The Scanner supports two modes: **batch scan** and **single document extraction**.

### Mode 1: Batch Scan

#### Input

`scan_config.json` specifying Feishu resources to scan:

```json
{
  "sources": [
    {
      "type": "wiki",
      "token": "wiki_token_xxx",
      "name": "产品知识库"
    },
    {
      "type": "folder",
      "token": "folder_token_xxx",
      "name": "项目文档"
    },
    {
      "type": "bitable",
      "token": "app_token_xxx",
      "name": "业务数据"
    }
  ],
  "scan_interval": "manual"
}
```

#### Scan Flow

```
1. Read scan_config.json → get Feishu resource list
2. For each resource:
   ├─ Wiki → lark-cli wiki +node-list --space-id <id> --page-all (traverse node tree)
   ├─ Folder → lark-cli drive +search --folder-tokens <token> (search files in folder)
   └─ Bitable → lark-cli base +table-list + record-list
3. For each document:
   ├─ Doc → cli.fetch_doc() → extract Markdown content
   ├─ Sheet → cli.fetch_sheet() → extract table content
   └─ Bitable → record-list → extract records
4. Output scan result JSON:
   {
     "scanned_at": "2026-06-20T14:00:00Z",
     "documents": [
       {
         "source_type": "doc",
         "doc_token": "abc123",
         "title": "周会纪要",
         "url": "https://...",
         "content": "...",
         "fetched_at": "...",
         "last_modified": "..."
       }
     ]
   }
```

### Mode 2: Single Document Extraction

#### Input

User provides a Feishu document URL directly.

#### Flow

```
1. User: "保存这个文档 https://feishu.cn/docx/abc123"
2. scanner.py --doc "https://feishu.cn/docx/abc123"
3. Extract content using cli.fetch_doc()
4. Output single document JSON:
   {
     "source_type": "doc",
     "doc_token": "abc123",
     "title": "文档标题",
     "url": "https://feishu.cn/docx/abc123",
     "content": "...",
     "fetched_at": "...",
     "last_modified": "..."
   }
5. Agent classifies → OKF Writer generates single .md file
```

### Incremental Scan

- Track each document's `doc_token` + `last_modified` timestamp.
- On subsequent scans, only process documents with changes.
- State stored in Bundle's `log.md` and a `.scan_state.json` file.
- Alternative: Use `lark-cli drive +search --edited-since <timestamp>` for native incremental support.

### Reused Code

- `cli.py`: `fetch_doc()`, `fetch_sheet()`, `check_auth()` — directly reused.
- New methods added to `cli.py`: `fetch_wiki_tree()`, `fetch_folder_files()`.

### lark-cli Commands (Verified)

| Command | Function | Status |
|---------|----------|--------|
| `wiki +space-list` | List wiki spaces | ✅ |
| `wiki +node-list --page-all` | List all nodes in a space | ✅ |
| `drive +search --folder-tokens` | Search files in folder | ✅ |
| `drive +search --edited-since` | Search recently edited docs | ✅ |
| `docs +fetch --doc-format markdown` | Fetch doc as markdown | ✅ |
| `sheets +cells-get` | Read spreadsheet cells | ✅ |
| `base +table-list` | List tables in bitable | ✅ |
| `base +record-list` | List records in table | ✅ |

---

## 5. Agent Classification (SKILL.md Guidance)

Classification is performed by the Agent using its LLM capabilities, guided by instructions in SKILL.md. This is NOT a separate script — it's agent intelligence directed by the skill definition.

### Input

Scanner output JSON (document content).

### SKILL.md Classification Instructions

The SKILL.md will include a section like:

```markdown
## Classification Guide

When you receive document content from the Scanner, analyze it and extract:

1. **project**: Which project does this belong to? Infer from:
   - Document title (e.g., "Lark AutoContext 周会" → project: "lark-autocontext")
   - Content context (e.g., mentions of specific project names)
   - Folder/wiki space structure if available
   - If unclear, ask the user

2. **type**: What kind of document is this? Choose from:
   | type | Use when |
   |------|----------|
   | `Meeting Minutes` | Contains meeting notes, attendees, action items |
   | `Requirement Doc` | Describes features, user stories, acceptance criteria |
   | `Review Report` | Post-mortem analysis, lessons learned |
   | `Operation Plan` | Strategy, roadmap, operational procedures |
   | `Data Analysis` | Charts, metrics analysis, data insights |
   | `Competitor Research` | Market analysis, competitor comparison |
   | `Contract` | Agreements, terms, legal documents |
   | `Reference` | Documentation, guides, how-tos |
   | `Metric` | Business metrics definitions, KPIs |
   | `Other` | Doesn't fit above categories |

3. **Structured fields**: Extract from content:
   - title: Document title
   - description: One-sentence summary
   - tags: 2-5 relevant keywords
   - people: Names mentioned as participants/authors
   - key_dates: Important dates mentioned
   - core_conclusion: Main takeaway or conclusion

4. **filename**: Generate from title, e.g., "2026-06-20 重构讨论" → "2026-06-20-重构讨论.md"
```

### Agent Workflow

```
1. Scanner outputs document JSON with content
2. Agent reads content and applies classification guide from SKILL.md
3. Agent constructs structured JSON:
   {
     "project": "lark-autocontext",
     "type": "Meeting Minutes",
     "category": "meetings",
     "title": "2026-06-20 重构讨论",
     "description": "讨论 OKF 重构方案",
     "tags": ["重构", "OKF"],
     "people": ["张三", "李四"],
     "key_dates": [{"date": "2026-06-20", "event": "方案确定"}],
     "core_conclusion": "采用 Pipeline 架构...",
     "filename": "2026-06-20-重构讨论.md"
   }
4. Agent passes this JSON to okf_writer.py
```

### Why Agent-Based, Not Script-Based

- **Flexibility**: Agent can handle ambiguous cases, ask user for clarification
- **Context awareness**: Agent can use conversation history to better classify
- **No separate LLM call**: Agent already has LLM capabilities
- **Simpler architecture**: No need for classifier.py script and LLM API integration

---

## 6. OKF Writer Module

### Input

Classifier output JSON + Scanner output raw content.

### Write Flow

```
For each classified document:
1. Determine target path: bundle/projects/{project}/{category}/{filename}
2. Generate YAML Frontmatter (type required + optional fields)
3. Generate Markdown Body (structured content + citations)
4. Write file
5. Update corresponding directory's index.md (append entry)
6. Update root log.md (record change)
```

### Generated File Example

```markdown
---
type: Meeting Minutes
title: "2026-06-20 重构讨论"
description: 讨论基于 OKF 标准重构 lark-autocontext 的方案
resource: https://your-tenant.feishu.cn/docx/abc123
tags: [重构, OKF]
timestamp: 2026-06-20T14:00:00Z
project: lark-autocontext
people: [张三, 李四]
---

# 核心结论

确定采用 Pipeline 架构，OKF 为主存储...

# 关键时间

- 2026-06-20: 方案确定
- 2026-06-25: 开始实现

# 涉及人员

- 张三: 架构设计
- 李四: 飞书 API 对接

# Citations

[1] [飞书原文文档](https://your-tenant.feishu.cn/docx/abc123)
```

### index.md Auto-Generation

```markdown
# Meetings

* [2026-06-20 重构讨论](2026-06-20-重构讨论.md) - 讨论基于 OKF 标准重构方案
* [2026-06-13 周会](2026-06-13-周会.md) - 周度同步会议
```

### log.md Auto-Append

```markdown
## 2026-06-20
* **Creation**: 新增 [2026-06-20 重构讨论](/projects/lark-autocontext/meetings/2026-06-20-重构讨论.md)
* **Update**: 更新 [Q2 复盘](/projects/lark-autocontext/reviews/q2-复盘.md)
```

### Deduplication and Update

- Use `resource` field (Feishu doc_token) to determine if document already exists.
- If exists: update file content + log.md records "Update".
- If not exists: create new file + log.md records "Creation".

---

## 7. Query Engine Module

Replaces existing `search_context.py` and `global_search.py`.

### Three Query Modes

#### Mode 1: Project-Scoped Query

```
Agent: "lark-autocontext 项目里关于重构的上下文"
→ query.py --project lark-autocontext --keyword "重构"
→ Traverse projects/lark-autocontext/ all .md files
→ Match keyword against title/description/tags/body
→ Return matching concept document list + content summary
```

#### Mode 2: Global Search

```
Agent: "最近有什么关于 OKF 的讨论？"
→ query.py --keyword "OKF"
→ Traverse entire Bundle all .md files
→ Return matches, sorted by timestamp descending
```

#### Mode 3: Type/Tag Filter

```
Agent: "给我所有会议纪要"
→ query.py --type "Meeting Minutes"
→ Traverse all type=Meeting Minutes files
→ Return list
```

### Return Format

```json
{
  "query": "重构",
  "mode": "project",
  "project": "lark-autocontext",
  "count": 3,
  "results": [
    {
      "concept_id": "projects/lark-autocontext/meetings/2026-06-20-重构讨论",
      "title": "2026-06-20 重构讨论",
      "type": "Meeting Minutes",
      "description": "讨论基于 OKF 标准重构方案",
      "tags": ["重构", "OKF"],
      "timestamp": "2026-06-20T14:00:00Z",
      "resource": "https://your-tenant.feishu.cn/docx/abc123",
      "body_preview": "确定采用 Pipeline 架构...",
      "file_path": "projects/lark-autocontext/meetings/2026-06-20-重构讨论.md"
    }
  ]
}
```

### Agent Full Content Access

- First use `query.py` to get summary list.
- When full content is needed, Agent directly Reads the `.md` file via `file_path`.

### Performance

- Bottom layer changes from Feishu API calls to local file reads.
- Significant speed improvement (no network latency, no QPS limits).

---

## 8. File Structure and Module Mapping

### New Project Structure

```
lark-autocontext/
├── scripts/
│   ├── cli.py                    # Kept: Feishu API wrapper (add wiki/folder scan methods)
│   ├── scanner.py                # New: Feishu document scanner (batch + single doc)
│   ├── okf_writer.py             # New: OKF Markdown generator
│   ├── query.py                  # New: OKF Bundle query engine
│   ├── onboarding.py             # Kept: Status check (adapted for new architecture)
│   ├── init_bundle.py            # New: OKF Bundle initialization
│   ├── config.json.example       # Updated: Add scan_config example
│   └── scan_config.json.example  # New: Scan source config example
│
├── bundle/                       # New: OKF Bundle (knowledge storage)
│   ├── index.md
│   ├── log.md
│   └── projects/
│       └── index.md
│
├── SKILL.md                      # Updated: New architecture skill definition
├── README.md                     # Updated: New architecture description
├── .gitignore                    # Updated: Ignore config.json
└── LICENSE
```

### Deleted Files (Replaced by New Modules)

| Old File | New File | Notes |
|----------|----------|-------|
| `extract_data.py` | `scanner.py` | Extraction logic merged into Scanner |
| `write_context.py` | `okf_writer.py` | Write logic changed to generate OKF MD |
| `search_context.py` | `query.py` | Search logic changed to read local files |
| `global_search.py` | `query.py` | Merged into Query Engine |
| `get_or_create_table.py` | - | No longer need Feishu table management |
| `create_doc.py` | - | No longer need to create Feishu Docs |
| `create_dashboard.py` | - | Feishu dashboard downgraded to optional |
| `init_base.py` | `init_bundle.py` | Init changed to create Bundle directory |
| `test_project_entity_split.py` | - | Old test deprecated |

### Kept Files

- `cli.py` — Core Feishu API wrapper, new scan methods added.
- `onboarding.py` — Adapted for new architecture status check.

### Removed: classifier.py

Classification is NOT a separate script. It's performed by the Agent using its LLM capabilities, guided by instructions in SKILL.md. See Section 5 for details.

---

## 9. Configuration

### config.json (Feishu Auth + Bundle Path)

```json
{
  "feishu": {
    "base_token": "YOUR_BASE_TOKEN_HERE",
    "description": "Optional: Feishu Bitable for visualization"
  },
  "bundle_path": "./bundle",
  "description": "Lark AutoContext - OKF Bundle path and optional Feishu config"
}
```

### scan_config.json (Scan Sources)

```json
{
  "sources": [
    {
      "type": "wiki",
      "token": "wiki_token_xxx",
      "name": "产品知识库"
    },
    {
      "type": "folder",
      "token": "folder_token_xxx",
      "name": "项目文档"
    },
    {
      "type": "bitable",
      "token": "app_token_xxx",
      "name": "业务数据"
    }
  ],
  "scan_interval": "manual"
}
```

---

## 10. SKILL.md Workflow (Updated)

### Single Document Save Workflow

```
User: "保存这个文档 https://feishu.cn/docx/abc123"
  → Step 0: onboarding.py (check config + auth)
  → Step 1: scanner.py --doc "https://feishu.cn/docx/abc123" (extract single doc)
  → Step 2: Agent reads content, applies classification guide from SKILL.md
  → Step 3: Agent constructs structured JSON (project, type, title, tags, etc.)
  → Step 4: okf_writer.py (generate single OKF Markdown file)
  → Step 5: Show save summary (file created, location)
  → Step 6: User confirms → commit to Git
```

### Batch Scan Workflow

```
User: "扫描飞书文档" / "同步飞书知识"
  → Step 0: onboarding.py (check config + auth)
  → Step 1: scanner.py (scan Feishu sources, extract content)
  → Step 2: Agent reads each document, applies classification guide from SKILL.md
  → Step 3: Agent constructs structured JSON for each document
  → Step 4: okf_writer.py (generate OKF Markdown files)
  → Step 5: Show scan summary (new/updated/skipped counts)
  → Step 6: User confirms → commit to Git
```

### Query Workflow (Updated)

```
User: "lark-autocontext 项目里关于 X 的信息"
  → Step 1: query.py --project lark-autocontext --keyword "X"
  → Step 2: Return matching results
  → Step 3: If full content needed, Read the .md file
  → Step 4: Agent answers with context + source links
```

### Global Search Workflow (Updated)

```
User: "最近有什么关于 X 的讨论？"
  → Step 1: query.py --keyword "X"
  → Step 2: Return all matches across projects, sorted by time
  → Step 3: Agent synthesizes answer from multiple sources
```

---

## 11. Error Handling

- **Feishu API failures**: Scanner catches per-document errors, continues scanning other documents, reports failed items at end.
- **LLM classification failures**: Classifier falls back to `type: Other`, `category: misc/`, preserves raw content in body.
- **File write failures**: OKF Writer reports errors, does not crash entire batch.
- **Query empty results**: Query Engine returns empty list with suggestion to scan first.
- **Config missing**: onboarding.py guides user through setup.

---

## 12. Testing Strategy

- **Scanner**: Test with mock Feishu API responses (doc, sheet, bitable).
- **Classifier**: Test prompt generation and JSON parsing with sample documents.
- **OKF Writer**: Test file generation, index.md/log.md updates, deduplication.
- **Query Engine**: Test all three modes, empty results, large result sets.
- **Integration**: End-to-end test from scan → classify → write → query.

---

## 13. Implementation Path

1. **Phase 1**: Implement new modules alongside existing code (no deletion).
2. **Phase 2**: Run first scan or single doc save, generate OKF Bundle, verify data correctness.
3. **Phase 3**: Update SKILL.md to use new workflow.
4. **Phase 4**: Delete old files, clean up.
5. **Phase 5**: Commit everything to Git.

Note: Existing Bitable data is NOT migrated. Users can keep their old data in Bitable while new data goes to OKF.

---

## References

- [OKF v0.1 Spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)
- [OKF Repository](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
- [Google Cloud OKF Blog Post](https://cloud.google.com/blog/products/data-analytics/introducing-the-open-knowledge-format)
- [Karpathy LLM Wiki Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
