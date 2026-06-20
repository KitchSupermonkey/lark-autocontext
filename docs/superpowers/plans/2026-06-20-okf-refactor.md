# OKF-Based Lark AutoContext Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor lark-autocontext from Feishu Bitable storage to OKF-compliant Markdown Bundle, with Scanner/Agent/OKF Writer/Query Engine pipeline.

**Architecture:** Pipeline architecture — Feishu docs → Scanner extracts → Agent classifies → OKF Writer generates .md → Bundle (Git) → Query Engine → Agent. Feishu Bitable downgraded to optional.

**Tech Stack:** Python 3 (stdlib only), lark-cli (Feishu API), YAML frontmatter in Markdown files, Git for version control.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/config.json.example` | Modify | New config structure with bundle_path + feishu |
| `scripts/scan_config.json.example` | Create | Scan source configuration (wiki/folder/bitable tokens) |
| `scripts/init_bundle.py` | Create | Initialize OKF Bundle directory structure |
| `scripts/cli.py` | Modify | Add `fetch_wiki_tree()`, `fetch_folder_files()` methods |
| `scripts/scanner.py` | Create | Batch scan + single doc extraction from Feishu |
| `scripts/okf_writer.py` | Create | Generate OKF Markdown files from classified JSON |
| `scripts/query.py` | Create | Query OKF Bundle by project/keyword/type |
| `scripts/onboarding.py` | Modify | Adapt status check for new architecture |
| `SKILL.md` | Modify | New architecture skill definition with classification guide |
| `README.md` | Modify | New architecture description |
| `.gitignore` | Modify | Ensure config.json ignored |
| `scripts/extract_data.py` | Delete | Replaced by scanner.py |
| `scripts/write_context.py` | Delete | Replaced by okf_writer.py |
| `scripts/search_context.py` | Delete | Replaced by query.py |
| `scripts/global_search.py` | Delete | Replaced by query.py |
| `scripts/get_or_create_table.py` | Delete | No longer needed |
| `scripts/create_doc.py` | Delete | No longer needed |
| `scripts/create_dashboard.py` | Delete | No longer needed |
| `scripts/init_base.py` | Delete | Replaced by init_bundle.py |
| `scripts/test_project_entity_split.py` | Delete | Deprecated |

---

## Task 1: Update Configuration Structure

**Files:**
- Modify: `scripts/config.json.example`
- Create: `scripts/scan_config.json.example`

- [ ] **Step 1: Write new config.json.example**

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

- [ ] **Step 2: Write scan_config.json.example**

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

- [ ] **Step 3: Commit**

```bash
git add scripts/config.json.example scripts/scan_config.json.example
git commit -m "feat: update config structure for OKF architecture"
```

---

## Task 2: Create init_bundle.py

**Files:**
- Create: `scripts/init_bundle.py`

- [ ] **Step 1: Write init_bundle.py**

```python
"""
Initialize the OKF Bundle directory structure.
Creates: bundle/index.md, bundle/log.md, bundle/projects/index.md
"""
import os
import sys
import json
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def init_bundle(bundle_path=None):
    """Create the OKF Bundle directory structure."""
    if bundle_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        bundle_path = "./bundle"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            bundle_path = config.get("bundle_path", "./bundle")

    # Resolve relative to project root (parent of scripts/)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isabs(bundle_path):
        bundle_path = os.path.join(project_root, bundle_path)

    dirs_to_create = [
        bundle_path,
        os.path.join(bundle_path, "projects"),
        os.path.join(bundle_path, "concepts"),
        os.path.join(bundle_path, "people"),
    ]

    for d in dirs_to_create:
        os.makedirs(d, exist_ok=True)

    # Create index.md files
    index_files = {
        os.path.join(bundle_path, "index.md"): "# Lark AutoContext OKF Bundle\n\n## Projects\n\n* [View all projects](projects/index.md)\n\n## Concepts\n\n* [View concepts](concepts/index.md)\n",
        os.path.join(bundle_path, "projects", "index.md"): "# Projects\n\nNo projects yet. Run a scan or save a document to create one.\n",
        os.path.join(bundle_path, "concepts", "index.md"): "# Concepts\n\nNo concepts yet.\n",
        os.path.join(bundle_path, "people", "index.md"): "# People\n\nNo people yet.\n",
    }

    for filepath, content in index_files.items():
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

    # Create log.md
    log_path = os.path.join(bundle_path, "log.md")
    if not os.path.exists(log_path):
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"# Change Log\n\n## {datetime.now().strftime('%Y-%m-%d')}\n\n* **Initialization**: Bundle created\n")

    print(f"✅ OKF Bundle initialized at: {bundle_path}")
    print(f"   - index.md, log.md created")
    print(f"   - projects/, concepts/, people/ directories created")
    return bundle_path


if __name__ == "__main__":
    init_bundle()
```

- [ ] **Step 2: Test init_bundle.py**

Run: `python scripts/init_bundle.py`
Expected output:
```
✅ OKF Bundle initialized at: D:\AI\Lark-AutoContext\context-wizard\bundle
   - index.md, log.md created
   - projects/, concepts/, people/ directories created
```

- [ ] **Step 3: Verify directory structure**

Run: `dir /s /b bundle\*.md`
Expected: Shows index.md, log.md, projects/index.md, concepts/index.md, people/index.md

- [ ] **Step 4: Commit**

```bash
git add scripts/init_bundle.py bundle/
git commit -m "feat: add init_bundle.py for OKF Bundle initialization"
```

---

## Task 3: Update cli.py with Wiki/Folder Scan Methods

**Files:**
- Modify: `scripts/cli.py`

- [ ] **Step 1: Add fetch_wiki_tree method to cli.py**

Add this method to the `LarkCLI` class in `cli.py`, after the existing `fetch_sheet` method:

```python
    def fetch_wiki_tree(self, space_id):
        """Fetch all nodes in a wiki space. Returns list of node dicts."""
        output = self.run(["wiki", "+node-list", "--space-id", space_id, "--page-all"], as_json=False)
        try:
            data = json.loads(output)
            return data.get("data", {}).get("nodes", [])
        except:
            return []

    def fetch_folder_files(self, folder_token):
        """Search files in a Feishu folder. Returns list of file dicts."""
        output = self.run(["drive", "+search", "--folder-tokens", folder_token], as_json=False)
        try:
            data = json.loads(output)
            return data.get("data", {}).get("files", [])
        except:
            return []

    def fetch_doc_title(self, doc_token):
        """Fetch just the title of a doc. Returns title string."""
        output = self.run(["docs", "+fetch", "--doc", doc_token, "--doc-format", "markdown"], as_json=False)
        try:
            data = json.loads(output)
            return data.get("data", {}).get("document", {}).get("title", doc_token)
        except:
            return doc_token
```

- [ ] **Step 2: Verify cli.py syntax**

Run: `python -c "import sys; sys.path.insert(0, 'scripts'); from cli import LarkCLI; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add scripts/cli.py
git commit -m "feat: add wiki/folder scan methods to cli.py"
```

---

## Task 4: Create scanner.py

**Files:**
- Create: `scripts/scanner.py`

- [ ] **Step 1: Write scanner.py**

```python
"""
Scanner: Extract content from Feishu documents.
Two modes:
  1. Batch scan: python scanner.py (reads scan_config.json)
  2. Single doc: python scanner.py --doc "https://feishu.cn/docx/xxx"

Output: JSON with document content for Agent classification.
"""
import sys
import json
import os
import re
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from cli import LarkCLI


def is_feishu_doc(url):
    return "feishu.cn/docx/" in url or "larksuite.com/docx/" in url

def is_feishu_sheet(url):
    return "feishu.cn/sheet/" in url or "larksuite.cn/sheet/" in url

def extract_doc_token(url):
    match = re.search(r'docx/([a-zA-Z0-9]+)', url)
    return match.group(1) if match else "N/A"

def extract_sheet_token(url):
    match = re.search(r'sheet/([a-zA-Z0-9]+)', url)
    return match.group(1) if match else "N/A"


def scan_single_doc(url, cli=None):
    """Extract content from a single Feishu document URL."""
    if cli is None:
        cli = LarkCLI()

    try:
        if is_feishu_doc(url):
            doc_token = extract_doc_token(url)
            content = cli.fetch_doc(doc_token)
            title = cli.fetch_doc_title(doc_token)
            return {
                "source_type": "doc",
                "doc_token": doc_token,
                "title": title,
                "url": url,
                "content": content,
                "fetched_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
        elif is_feishu_sheet(url):
            sheet_token = extract_sheet_token(url)
            content = cli.fetch_sheet(sheet_token, "0")
            return {
                "source_type": "sheet",
                "doc_token": sheet_token,
                "title": sheet_token,
                "url": url,
                "content": content,
                "fetched_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
        else:
            return {
                "source_type": "text",
                "doc_token": "N/A",
                "title": "Raw Text",
                "url": url,
                "content": url,
                "fetched_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "error": str(e),
            "hint": "If extraction failed, treat input as raw text."
        }


def scan_batch(config_path=None, cli=None):
    """Scan all sources defined in scan_config.json."""
    if cli is None:
        cli = LarkCLI()

    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "scan_config.json")

    if not os.path.exists(config_path):
        return {"error": "scan_config.json not found. Create it from scan_config.json.example"}

    with open(config_path, 'r', encoding='utf-8') as f:
        scan_config = json.load(f)

    sources = scan_config.get("sources", [])
    documents = []
    errors = []

    for source in sources:
        source_type = source.get("type")
        token = source.get("token")
        name = source.get("name", "Unknown")

        try:
            if source_type == "wiki":
                nodes = cli.fetch_wiki_tree(token)
                for node in nodes:
                    node_type = node.get("obj_type", "")
                    node_token = node.get("obj_token", "")
                    node_title = node.get("title", node_token)

                    if node_type == "docx" and node_token:
                        try:
                            content = cli.fetch_doc(node_token)
                            documents.append({
                                "source_type": "doc",
                                "doc_token": node_token,
                                "title": node_title,
                                "url": f"https://feishu.cn/docx/{node_token}",
                                "content": content,
                                "source_name": name,
                                "fetched_at": datetime.now().isoformat(),
                                "last_modified": node.get("obj_edit_time", "")
                            })
                        except Exception as e:
                            errors.append({"token": node_token, "error": str(e)})

            elif source_type == "folder":
                files = cli.fetch_folder_files(token)
                for f_info in files:
                    file_type = f_info.get("type", "")
                    file_token = f_info.get("token", "")
                    file_name = f_info.get("name", file_token)

                    if file_type == "docx" and file_token:
                        try:
                            content = cli.fetch_doc(file_token)
                            documents.append({
                                "source_type": "doc",
                                "doc_token": file_token,
                                "title": file_name,
                                "url": f"https://feishu.cn/docx/{file_token}",
                                "content": content,
                                "source_name": name,
                                "fetched_at": datetime.now().isoformat(),
                                "last_modified": f_info.get("modified_time", "")
                            })
                        except Exception as e:
                            errors.append({"token": file_token, "error": str(e)})

            elif source_type == "bitable":
                tables_output = cli.run(["base", "+table-list", "--base-token", token])
                tables_data = json.loads(tables_output)
                tables = tables_data.get("data", {}).get("tables", [])

                for table in tables:
                    table_id = table.get("id")
                    table_name = table.get("name", "Unknown")

                    records_output = cli.run([
                        "base", "+record-list",
                        "--base-token", token,
                        "--table-id", table_id
                    ])
                    records_data = json.loads(records_output)

                    fields = records_data.get("data", {}).get("fields", [])
                    rows = records_data.get("data", {}).get("data", [])

                    for row in rows:
                        record = {}
                        for i, field_name in enumerate(fields):
                            if i < len(row):
                                val = row[i]
                                if isinstance(val, list):
                                    val = ", ".join(str(v) for v in val)
                                record[field_name] = val

                        content = json.dumps(record, ensure_ascii=False, indent=2)
                        documents.append({
                            "source_type": "bitable_record",
                            "doc_token": f"{table_id}_{record.get('id', '')}",
                            "title": record.get("实体名称", table_name),
                            "url": f"https://feishu.cn/base/{token}?table={table_id}",
                            "content": content,
                            "source_name": name,
                            "fetched_at": datetime.now().isoformat(),
                            "last_modified": record.get("最后更新", "")
                        })

        except Exception as e:
            errors.append({"source": name, "error": str(e)})

    return {
        "scanned_at": datetime.now().isoformat(),
        "total_documents": len(documents),
        "documents": documents,
        "errors": errors
    }


def main():
    if len(sys.argv) < 2:
        # Batch mode
        result = scan_batch()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif sys.argv[1] == "--doc":
        if len(sys.argv) < 3:
            print("Usage: python scanner.py --doc <feishu_url>")
            sys.exit(1)
        result = scan_single_doc(sys.argv[2])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Usage:")
        print("  python scanner.py              # Batch scan from scan_config.json")
        print("  python scanner.py --doc <url>  # Single document extraction")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify scanner.py syntax**

Run: `python -c "import sys; sys.path.insert(0, 'scripts'); from scanner import scan_single_doc, scan_batch; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Test single doc mode (without real Feishu connection)**

Run: `python scripts/scanner.py --doc "https://example.com/test"`
Expected: JSON output with `source_type: "text"` (falls back to text mode)

- [ ] **Step 4: Commit**

```bash
git add scripts/scanner.py
git commit -m "feat: add scanner.py for Feishu document scanning"
```

---

## Task 5: Create okf_writer.py

**Files:**
- Create: `scripts/okf_writer.py`

- [ ] **Step 1: Write okf_writer.py**

```python
"""
OKF Writer: Generate OKF-compliant Markdown files from classified JSON.

Input: JSON with classification fields (from Agent) + raw content (from Scanner)
Output: .md file in bundle/projects/{project}/{category}/{filename}

Usage:
  python okf_writer.py '<classified_json>' '<raw_content>'
  
  classified_json example:
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
    "filename": "2026-06-20-重构讨论.md",
    "resource": "https://feishu.cn/docx/abc123"
  }
"""
import sys
import json
import os
import re
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# Type to category directory mapping
TYPE_TO_CATEGORY = {
    "Meeting Minutes": "meetings",
    "Requirement Doc": "requirements",
    "Review Report": "reviews",
    "Operation Plan": "plans",
    "Data Analysis": "analysis",
    "Competitor Research": "research",
    "Contract": "contracts",
    "Reference": "references",
    "Metric": "metrics",
    "Other": "misc"
}


def get_bundle_path():
    """Get bundle path from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    bundle_path = "./bundle"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        bundle_path = config.get("bundle_path", "./bundle")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isabs(bundle_path):
        bundle_path = os.path.join(project_root, bundle_path)
    return bundle_path


def sanitize_filename(name):
    """Remove characters unsafe for filenames."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


def generate_frontmatter(data):
    """Generate YAML frontmatter from classified data."""
    lines = ["---"]
    lines.append(f"type: {data.get('type', 'Other')}")

    title = data.get('title', 'Untitled')
    lines.append(f'title: "{title}"')

    if data.get('description'):
        lines.append(f"description: {data['description']}")
    if data.get('resource'):
        lines.append(f"resource: {data['resource']}")
    if data.get('tags'):
        tags_str = ", ".join(data['tags'])
        lines.append(f"tags: [{tags_str}]")

    lines.append(f"timestamp: {datetime.now().isoformat()}")

    if data.get('project'):
        lines.append(f"project: {data['project']}")
    if data.get('people'):
        people_str = ", ".join(data['people'])
        lines.append(f"people: [{people_str}]")

    lines.append("---")
    return "\n".join(lines)


def generate_body(data, raw_content=""):
    """Generate Markdown body from classified data."""
    sections = []

    if data.get('core_conclusion'):
        sections.append("# 核心结论\n\n" + data['core_conclusion'])

    if data.get('key_dates'):
        dates_lines = ["# 关键时间", ""]
        for kd in data['key_dates']:
            if isinstance(kd, dict):
                dates_lines.append(f"- {kd.get('date', '')}: {kd.get('event', '')}")
            else:
                dates_lines.append(f"- {kd}")
        sections.append("\n".join(dates_lines))

    if data.get('people'):
        people_lines = ["# 涉及人员", ""]
        for person in data['people']:
            people_lines.append(f"- {person}")
        sections.append("\n".join(people_lines))

    if raw_content and raw_content.strip():
        sections.append("# 原始内容\n\n" + raw_content)

    if data.get('resource'):
        sections.append("# Citations\n\n[1] [飞书原文文档](" + data['resource'] + ")")

    return "\n\n".join(sections)


def find_existing_file(bundle_path, resource):
    """Find existing file by resource (doc_token) in frontmatter."""
    if not resource:
        return None

    projects_dir = os.path.join(bundle_path, "projects")
    if not os.path.exists(projects_dir):
        return None

    for root, dirs, files in os.walk(projects_dir):
        for fname in files:
            if not fname.endswith('.md') or fname == 'index.md':
                continue
            filepath = os.path.join(root, fname)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if f"resource: {resource}" in content:
                    return filepath
            except:
                continue
    return None


def update_index_md(dir_path, title, filename, description):
    """Update or create index.md in a directory."""
    index_path = os.path.join(dir_path, "index.md")
    entry = f"* [{title}]({filename}) - {description}\n"

    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if entry already exists
        if f"]({filename})" in content:
            # Update existing entry
            lines = content.split('\n')
            updated_lines = []
            for line in lines:
                if f"]({filename})" in line:
                    updated_lines.append(entry.strip())
                else:
                    updated_lines.append(line)
            content = '\n'.join(updated_lines)
        else:
            # Append new entry
            content = content.rstrip() + '\n' + entry

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        # Create new index.md
        category_name = os.path.basename(dir_path)
        header = f"# {category_name.title()}\n\n"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(header + entry)


def update_log_md(bundle_path, action, file_path, title):
    """Append entry to log.md."""
    log_path = os.path.join(bundle_path, "log.md")
    today = datetime.now().strftime('%Y-%m-%d')
    relative_path = os.path.relpath(file_path, bundle_path)
    entry = f"* **{action}**: {title} ([{relative_path}]({relative_path}))\n"

    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if today's section exists
        if f"## {today}" in content:
            # Insert entry after today's header
            content = content.replace(f"## {today}\n", f"## {today}\n{entry}")
        else:
            # Add new day section
            content = content.rstrip() + f"\n\n## {today}\n\n{entry}"

        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"# Change Log\n\n## {today}\n\n{entry}")


def write_okf_document(classified_data, raw_content=""):
    """
    Write an OKF-compliant Markdown file to the Bundle.

    Args:
        classified_data: Dict with project, type, title, tags, etc.
        raw_content: Original document content from Scanner

    Returns:
        Dict with file_path and action (created/updated)
    """
    bundle_path = get_bundle_path()

    # Ensure bundle exists
    if not os.path.exists(bundle_path):
        return {"error": "Bundle not initialized. Run: python scripts/init_bundle.py"}

    project = classified_data.get('project', 'misc')
    doc_type = classified_data.get('type', 'Other')
    category = classified_data.get('category') or TYPE_TO_CATEGORY.get(doc_type, 'misc')
    title = classified_data.get('title', 'Untitled')
    filename = sanitize_filename(classified_data.get('filename', f"{title}.md"))
    description = classified_data.get('description', '')
    resource = classified_data.get('resource', '')

    # Check for existing file (deduplication)
    existing_file = find_existing_file(bundle_path, resource)
    action = "Update" if existing_file else "Creation"

    # Determine target path
    if existing_file:
        target_path = existing_file
    else:
        project_dir = os.path.join(bundle_path, "projects", project, category)
        os.makedirs(project_dir, exist_ok=True)
        target_path = os.path.join(project_dir, filename)

    # Generate file content
    frontmatter = generate_frontmatter(classified_data)
    body = generate_body(classified_data, raw_content)
    file_content = frontmatter + "\n\n" + body + "\n"

    # Write file
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(file_content)

    # Update index.md in the category directory
    target_dir = os.path.dirname(target_path)
    update_index_md(target_dir, title, filename, description)

    # Update project index.md if it's a new project
    project_index = os.path.join(bundle_path, "projects", project, "index.md")
    if not os.path.exists(project_index):
        with open(project_index, 'w', encoding='utf-8') as f:
            f.write(f"# {project}\n\n* [{title}]({category}/{filename}) - {description}\n")
    else:
        # Check if project is listed in projects/index.md
        projects_index = os.path.join(bundle_path, "projects", "index.md")
        if os.path.exists(projects_index):
            with open(projects_index, 'r', encoding='utf-8') as f:
                content = f.read()
            if f"]({project}/index.md)" not in content and f"]({project}/)" not in content:
                with open(projects_index, 'a', encoding='utf-8') as f:
                    f.write(f"\n* [{project}]({project}/index.md)\n")

    # Update log.md
    update_log_md(bundle_path, action, target_path, title)

    return {
        "action": action,
        "file_path": os.path.relpath(target_path, bundle_path),
        "absolute_path": target_path,
        "title": title
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python okf_writer.py '<classified_json>' [raw_content]")
        print("")
        print("classified_json example:")
        print('  {"project":"my-project","type":"Meeting Minutes","title":"周会","tags":["会议"]}')
        sys.exit(1)

    classified_data = json.loads(sys.argv[1])
    raw_content = sys.argv[2] if len(sys.argv) > 2 else ""

    result = write_okf_document(classified_data, raw_content)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify okf_writer.py syntax**

Run: `python -c "import sys; sys.path.insert(0, 'scripts'); from okf_writer import write_okf_document, generate_frontmatter; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Test okf_writer with sample data**

Run:
```bash
python scripts/okf_writer.py "{\"project\":\"test-project\",\"type\":\"Meeting Minutes\",\"title\":\"测试会议\",\"description\":\"测试描述\",\"tags\":[\"测试\"],\"people\":[\"张三\"],\"core_conclusion\":\"测试结论\",\"resource\":\"https://feishu.cn/docx/test123\",\"filename\":\"test-meeting.md\"}" "这是原始内容"
```
Expected: JSON output with `action: "Creation"` and file path

- [ ] **Step 4: Verify file was created**

Run: `dir /s /b bundle\projects\test-project\meetings\test-meeting.md`
Expected: Shows the created file

- [ ] **Step 5: Test deduplication (run same command again)**

Run the same command from Step 3 again.
Expected: JSON output with `action: "Update"`

- [ ] **Step 6: Clean up test data**

Delete: `bundle/projects/test-project/` directory

- [ ] **Step 7: Commit**

```bash
git add scripts/okf_writer.py
git commit -m "feat: add okf_writer.py for OKF Markdown generation"
```

---

## Task 6: Create query.py

**Files:**
- Create: `scripts/query.py`

- [ ] **Step 1: Write query.py**

```python
"""
Query Engine: Search the OKF Bundle for context.

Three modes:
  1. Project-scoped: python query.py --project <name> --keyword <keyword>
  2. Global search:  python query.py --keyword <keyword>
  3. Type filter:    python query.py --type <type>

Output: JSON with matching concept documents.
"""
import sys
import json
import os
import re

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def get_bundle_path():
    """Get bundle path from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    bundle_path = "./bundle"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        bundle_path = config.get("bundle_path", "./bundle")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.isabs(bundle_path):
        bundle_path = os.path.join(project_root, bundle_path)
    return bundle_path


def parse_frontmatter(content):
    """Parse YAML frontmatter from Markdown content. Returns dict."""
    if not content.startswith("---"):
        return {}

    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}

    frontmatter_str = content[3:end_idx].strip()
    result = {}

    for line in frontmatter_str.split('\n'):
        line = line.strip()
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()

            # Parse list values: [item1, item2]
            if value.startswith('[') and value.endswith(']'):
                items = [item.strip().strip('"').strip("'") for item in value[1:-1].split(',')]
                result[key] = [item for item in items if item]
            # Parse quoted strings
            elif value.startswith('"') and value.endswith('"'):
                result[key] = value[1:-1]
            else:
                result[key] = value

    return result


def extract_body_preview(content, max_chars=200):
    """Extract body text (after frontmatter) for preview."""
    if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
            body = content[end_idx + 3:].strip()
        else:
            body = content
    else:
        body = content

    # Remove markdown headers for cleaner preview
    body = re.sub(r'^#+\s+', '', body, flags=re.MULTILINE)
    body = body.replace('\n', ' ').strip()

    if len(body) > max_chars:
        body = body[:max_chars] + "..."
    return body


def scan_bundle(bundle_path, project_filter=None, type_filter=None, keyword=None):
    """Scan the OKF Bundle and return matching documents."""
    results = []
    projects_dir = os.path.join(bundle_path, "projects")

    if not os.path.exists(projects_dir):
        return results

    # Determine search root
    if project_filter:
        search_root = os.path.join(projects_dir, project_filter)
        if not os.path.exists(search_root):
            return results
    else:
        search_root = projects_dir

    # Walk through all .md files (excluding index.md)
    for root, dirs, files in os.walk(search_root):
        for fname in files:
            if not fname.endswith('.md') or fname == 'index.md':
                continue

            filepath = os.path.join(root, fname)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                continue

            frontmatter = parse_frontmatter(content)

            # Apply type filter
            if type_filter and frontmatter.get('type', '') != type_filter:
                continue

            # Apply keyword filter
            if keyword:
                keyword_lower = keyword.lower()
                searchable_text = (
                    frontmatter.get('title', '') + ' ' +
                    frontmatter.get('description', '') + ' ' +
                    ' '.join(frontmatter.get('tags', [])) + ' ' +
                    ' '.join(frontmatter.get('people', [])) + ' ' +
                    content
                ).lower()

                if keyword_lower not in searchable_text:
                    continue

            # Build result entry
            relative_path = os.path.relpath(filepath, bundle_path)
            concept_id = relative_path.replace('\\', '/').replace('.md', '')

            result = {
                "concept_id": concept_id,
                "title": frontmatter.get('title', fname),
                "type": frontmatter.get('type', 'Unknown'),
                "description": frontmatter.get('description', ''),
                "tags": frontmatter.get('tags', []),
                "timestamp": frontmatter.get('timestamp', ''),
                "resource": frontmatter.get('resource', ''),
                "project": frontmatter.get('project', ''),
                "people": frontmatter.get('people', []),
                "body_preview": extract_body_preview(content),
                "file_path": relative_path.replace('\\', '/')
            }
            results.append(result)

    # Sort by timestamp descending
    results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Query OKF Bundle")
    parser.add_argument('--project', help='Filter by project name')
    parser.add_argument('--keyword', help='Search keyword')
    parser.add_argument('--type', help='Filter by document type')
    args = parser.parse_args()

    bundle_path = get_bundle_path()

    if not os.path.exists(bundle_path):
        print(json.dumps({
            "error": "Bundle not initialized. Run: python scripts/init_bundle.py"
        }, ensure_ascii=False))
        sys.exit(1)

    results = scan_bundle(
        bundle_path,
        project_filter=args.project,
        type_filter=args.type,
        keyword=args.keyword
    )

    # Determine mode
    if args.project:
        mode = "project"
    elif args.type:
        mode = "type"
    else:
        mode = "global"

    output = {
        "query": args.keyword or args.type or args.project or "",
        "mode": mode,
        "count": len(results),
        "results": results
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify query.py syntax**

Run: `python -c "import sys; sys.path.insert(0, 'scripts'); from query import scan_bundle, parse_frontmatter; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Test query with no results**

Run: `python scripts/query.py --keyword "nonexistent"`
Expected: JSON with `count: 0` and empty `results`

- [ ] **Step 4: Test with sample data**

First create a test document:
```bash
python scripts/okf_writer.py "{\"project\":\"test-project\",\"type\":\"Meeting Minutes\",\"title\":\"测试会议\",\"description\":\"测试描述\",\"tags\":[\"测试\"],\"people\":[\"张三\"],\"core_conclusion\":\"测试结论\",\"resource\":\"https://feishu.cn/docx/test123\",\"filename\":\"test-meeting.md\"}" "这是原始内容"
```

Then query:
```bash
python scripts/query.py --keyword "测试"
```
Expected: JSON with `count: 1` and the test document in results

- [ ] **Step 5: Test project filter**

Run: `python scripts/query.py --project test-project`
Expected: JSON with `count: 1`

- [ ] **Step 6: Test type filter**

Run: `python scripts/query.py --type "Meeting Minutes"`
Expected: JSON with `count: 1`

- [ ] **Step 7: Clean up test data**

Delete: `bundle/projects/test-project/` directory

- [ ] **Step 8: Commit**

```bash
git add scripts/query.py
git commit -m "feat: add query.py for OKF Bundle search"
```

---

## Task 7: Update onboarding.py

**Files:**
- Modify: `scripts/onboarding.py`

- [ ] **Step 1: Rewrite onboarding.py for new architecture**

```python
"""
Quick status check and guided setup for Lark AutoContext (OKF architecture).
Run: python scripts/onboarding.py
"""
import json
import os
import sys

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from cli import LarkCLI


def check_status():
    """Check current setup status and guide the user."""
    cli = LarkCLI()
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    scan_config_path = os.path.join(os.path.dirname(__file__), "scan_config.json")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bundle_path = os.path.join(project_root, "bundle")

    print("🧙 Lark AutoContext — 状态检查 (OKF 架构)")
    print("=" * 50)

    # Check 1: config.json
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ 配置文件: 存在")
        bundle_path_config = config.get("bundle_path", "./bundle")
        print(f"✅ Bundle 路径: {bundle_path_config}")
    else:
        print("❌ 配置文件: 不存在")
        print("   → 运行 init_bundle.py 自动创建")
        return

    # Check 2: Bundle directory
    if os.path.exists(bundle_path):
        print("✅ OKF Bundle: 已初始化")
        # Count projects
        projects_dir = os.path.join(bundle_path, "projects")
        if os.path.exists(projects_dir):
            projects = [d for d in os.listdir(projects_dir) if os.path.isdir(os.path.join(projects_dir, d))]
            print(f"   已有 {len(projects)} 个项目: {', '.join(projects) if projects else '(空)'}")
    else:
        print("❌ OKF Bundle: 未初始化")
        print("   → 运行: python scripts/init_bundle.py")
        return

    # Check 3: scan_config.json
    if os.path.exists(scan_config_path):
        with open(scan_config_path, 'r', encoding='utf-8') as f:
            scan_config = json.load(f)
        sources = scan_config.get("sources", [])
        print(f"✅ 扫描配置: {len(sources)} 个数据源")
    else:
        print("⚠️  扫描配置: 不存在 (单文档保存仍可用，批量扫描需要配置)")
        print("   → 从 scan_config.json.example 复制并填写飞书 token")

    # Check 4: lark-cli auth
    try:
        auth_output = cli.run(["auth", "status"], as_json=False)
        auth_data = json.loads(auth_output)
        note = auth_data.get("note", "")
        if "not logged in" in note.lower():
            print("⚠️  lark-cli: 未登录用户，仅可使用 bot 身份")
            print("   → 如需用户身份，运行: lark-cli auth login --recommend --no-wait")
        else:
            print("✅ lark-cli: 已认证")
    except Exception as e:
        print(f"⚠️  lark-cli: 检查失败 ({e})")

    print()
    print("📌 **使用方式:**")
    print("  1. '保存这个文档 <链接>' → 单文档提取 → AI分类 → OKF入库")
    print("  2. '扫描飞书文档' → 批量扫描 → AI分类 → OKF入库")
    print("  3. 'XX项目里关于XX的信息？' → 查询OKF Bundle")


if __name__ == "__main__":
    check_status()
```

- [ ] **Step 2: Test onboarding.py**

Run: `python scripts/onboarding.py`
Expected: Shows status check with OKF architecture info

- [ ] **Step 3: Commit**

```bash
git add scripts/onboarding.py
git commit -m "feat: update onboarding.py for OKF architecture"
```

---

## Task 8: Update SKILL.md

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: Rewrite SKILL.md for new architecture**

```markdown
---
name: lark-autocontext
description: |
  Trigger when user mentions ANY of: 保存上下文 / 存入上下文 / 业务记忆 / 项目知识 / 存入知识库 / lark-autocontext / /lark-autocontext / 保存到业务上下文 / 扫描飞书 / 同步飞书知识.
  Also trigger when: user sends a Feishu doc/sheet link with intent to store or remember.
  Supports: save single document, batch scan Feishu sources, retrieve project history, ask cross-project questions.
  If config.json is missing, guide first-time setup automatically.
---

# Lark AutoContext (OKF Architecture)

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
   - tags: 2-5 relevant keywords (as array)
   - people: Names mentioned as participants/authors (as array)
   - key_dates: Important dates mentioned (as array of {"date": "...", "event": "..."})
   - core_conclusion: Main takeaway or conclusion
   - filename: Generate from title, e.g., "2026-06-20 重构讨论" → "2026-06-20-重构讨论.md"
   - resource: The original Feishu document URL (for traceability and deduplication)

4. **category**: Auto-derived from type:
   | type | category |
   |------|----------|
   | Meeting Minutes | meetings |
   | Requirement Doc | requirements |
   | Review Report | reviews |
   | Operation Plan | plans |
   | Data Analysis | analysis |
   | Competitor Research | research |
   | Contract | contracts |
   | Reference | references |
   | Metric | metrics |
   | Other | misc |

### Classified JSON Example

```json
{
  "project": "lark-autocontext",
  "type": "Meeting Minutes",
  "category": "meetings",
  "title": "2026-06-20 重构讨论",
  "description": "讨论 OKF 重构方案",
  "tags": ["重构", "OKF"],
  "people": ["张三", "李四"],
  "key_dates": [{"date": "2026-06-20", "event": "方案确定"}],
  "core_conclusion": "采用 Pipeline 架构，OKF 为主存储",
  "filename": "2026-06-20-重构讨论.md",
  "resource": "https://feishu.cn/docx/abc123"
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
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "feat: rewrite SKILL.md for OKF architecture"
```

---

## Task 9: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Read current README.md**

Run: Read `README.md`

- [ ] **Step 2: Rewrite README.md for new architecture**

```markdown
# Lark AutoContext

> 基于 OKF 标准的飞书业务上下文引擎 — Agent-agnostic business context management tool

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

## 📁 Project Structure

```
lark-autocontext/
├── scripts/
│   ├── cli.py            # Feishu API wrapper
│   ├── scanner.py        # Document scanner
│   ├── okf_writer.py     # OKF Markdown generator
│   ├── query.py          # Query engine
│   ├── init_bundle.py    # Bundle initialization
│   └── onboarding.py     # Status check
├── bundle/               # OKF Bundle (knowledge storage)
├── SKILL.md              # Agent skill definition
└── README.md
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for OKF architecture"
```

---

## Task 10: Delete Old Files

**Files:**
- Delete: `scripts/extract_data.py`
- Delete: `scripts/write_context.py`
- Delete: `scripts/search_context.py`
- Delete: `scripts/global_search.py`
- Delete: `scripts/get_or_create_table.py`
- Delete: `scripts/create_doc.py`
- Delete: `scripts/create_dashboard.py`
- Delete: `scripts/init_base.py`
- Delete: `scripts/test_project_entity_split.py`

- [ ] **Step 1: Delete old script files**

Delete all 9 files listed above.

- [ ] **Step 2: Verify no imports reference deleted files**

Run: `python -c "import sys; sys.path.insert(0, 'scripts'); from cli import LarkCLI; from scanner import scan_single_doc; from okf_writer import write_okf_document; from query import scan_bundle; from init_bundle import init_bundle; from onboarding import check_status; print('All imports OK')"`
Expected: `All imports OK`

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor: remove old Feishu Bitable scripts, replaced by OKF architecture"
```

---

## Task 11: Final Integration Test

- [ ] **Step 1: Run onboarding check**

Run: `python scripts/onboarding.py`
Expected: All checks pass (config exists, Bundle initialized, lark-cli authenticated)

- [ ] **Step 2: Test single doc save with text input**

Run:
```bash
python scripts/scanner.py --doc "这是一段测试文本"
```
Expected: JSON output with `source_type: "text"` and content

- [ ] **Step 3: Test OKF writer with classified data**

Run:
```bash
python scripts/okf_writer.py "{\"project\":\"integration-test\",\"type\":\"Reference\",\"title\":\"集成测试文档\",\"description\":\"测试完整流程\",\"tags\":[\"测试\",\"集成\"],\"people\":[\"开发者\"],\"core_conclusion\":\"所有模块正常工作\",\"resource\":\"https://example.com/test\",\"filename\":\"integration-test.md\"}" "这是测试内容"
```
Expected: JSON output with `action: "Creation"`

- [ ] **Step 4: Test query**

Run: `python scripts/query.py --keyword "测试"`
Expected: JSON with `count >= 1` and the test document in results

- [ ] **Step 5: Test deduplication**

Run the same okf_writer command from Step 3 again.
Expected: JSON output with `action: "Update"`

- [ ] **Step 6: Clean up test data**

Delete: `bundle/projects/integration-test/` directory

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "test: integration test passed, clean up test data"
git push
```

---

## Self-Review Notes

**Spec coverage check:**
- ✅ OKF Bundle structure (Section 3) → Task 2 (init_bundle.py)
- ✅ Scanner Module (Section 4) → Task 4 (scanner.py)
- ✅ Agent Classification (Section 5) → Task 8 (SKILL.md)
- ✅ OKF Writer Module (Section 6) → Task 5 (okf_writer.py)
- ✅ Query Engine Module (Section 7) → Task 6 (query.py)
- ✅ File Structure (Section 8) → Task 10 (delete old files)
- ✅ Configuration (Section 9) → Task 1 (config files)
- ✅ SKILL.md Workflow (Section 10) → Task 8 (SKILL.md)
- ✅ Error Handling (Section 11) → Implemented in each script
- ✅ Single Document Save Workflow → Task 8 (SKILL.md Workflow A)
- ✅ Batch Scan Workflow → Task 8 (SKILL.md Workflow B)
- ✅ Query Workflow → Task 8 (SKILL.md Workflow C)

**Type consistency check:**
- `scan_single_doc()` in scanner.py returns dict with `source_type`, `doc_token`, `title`, `url`, `content` — matches SKILL.md description
- `write_okf_document()` in okf_writer.py takes `classified_data` dict — matches SKILL.md Classification Guide
- `scan_bundle()` in query.py returns list of dicts with `concept_id`, `title`, `type`, etc. — matches SKILL.md return format
- TYPE_TO_CATEGORY mapping in okf_writer.py matches SKILL.md category table
