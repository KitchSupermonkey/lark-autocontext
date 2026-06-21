# Lark AutoContext

> **lark-autocontext** —— 把飞书（Lark）文档自动转成 OKF 标准的项目知识 bundle，供 AI Agent 长期上下文使用。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 What is this?

Lark AutoContext 把飞书文档、会议纪要、复盘报告自动转化为 [OKF (Open Knowledge Format)](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf) 标准的 Markdown 知识库，让任何 Agent 都能快速准确地获取业务上下文。

**核心方程：** AI 的产出 = 模型能力 × Agent 框架 × 上下文质量

## 🏗️ Architecture

```
飞书文档 → Scanner 提取 → Agent AI分类 → OKF Writer 生成 .md → Bundle (Git)
                                                              ↓
                                                        Query Engine
                                                              ↓
                                                           Agent
```

- **OKF-first**: 知识以 OKF Markdown 存储，Git 版本控制
- **Agent-agnostic**: 任何 Agent 都能通过 Skill 脚本读取
- **飞书为辅**: 飞书是数据源，不是存储引擎

## 📦 Installation

### Prerequisites
- Python 3.8+
- [lark-cli](https://www.npmjs.com/package/lark-cli) (`npm install -g @larksuiteoapi/lark-cli`)
- Feishu account with API access

### Setup
```bash
git clone https://github.com/KitchSupermonkey/lark-autocontext.git
cd lark-autocontext
cp scripts/config.json.example scripts/config.json
cp scripts/scan_config.json.example scripts/scan_config.json
# Edit config.json and scan_config.json with your tokens
python scripts/init_bundle.py
python scripts/onboarding.py
```

## 🚀 Usage

### Save Single Document
```
保存这个文档 https://feishu.cn/docx/xxx
```

### Batch Scan
```
扫描飞书文档
```

### Query Context
```
lark-autocontext 项目里关于重构的信息？
```

## 🔄 Auto-Sync 工作流

```bash
# 首次（让 Agent 跑）
python scripts/onboarding.py --quiet

# 之后每次扫描（或交给 Agent 定时任务）
python scripts/auto_sync.py list-only
# Agent 会按 SKILL.md Workflow D 分类并写入 bundle
python scripts/auto_sync.py finalize --commit
```

详见 [SKILL.md](./SKILL.md) Workflow D 与 Agent Cron Setup。

## 📊 可视化

```bash
python scripts/visualize.py --bundle bundle/ --out viz.html
# 浏览器打开 viz.html
```

生成单文件 HTML（Cytoscape.js 力导向图 + marked.js 渲染），节点颜色按 OKF `type` 区分，支持搜索过滤。

## 📁 Project Structure

```
lark-autocontext/
├── scripts/
│   ├── cli.py            # Feishu API wrapper
│   ├── scanner.py        # Document scanner (--list-changed for incremental)
│   ├── okf_writer.py     # OKF Markdown generator (cross-links, upsert)
│   ├── auto_sync.py      # Auto-Sync coordinator (list-only + finalize)
│   ├── visualize.py      # Single-file HTML visualizer
│   ├── query.py          # Query engine
│   ├── init_bundle.py    # Bundle initialization
│   └── onboarding.py     # Status check (--quiet for automation)
├── bundle/               # OKF Bundle (knowledge storage)
├── tests/                # pytest test suite
├── SKILL.md              # Agent skill definition
└── README.md
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
