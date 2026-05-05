"""
Auto-create a universal dashboard for any project table.
Components: statistics, entity type pie, status column, text info.
Must be executed serially (not parallel).
"""
import sys
import json
import time

# Cross-platform: Windows console defaults to GBK, force UTF-8 for emoji output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from cli import LarkCLI

def create_dashboard(app_token, table_name):
    cli = LarkCLI()
    dashboard_name = f"{table_name} 数据看板"
    
    # Step 1: Check if dashboard already exists
    dashboard_id = None
    try:
        list_output = cli.run(["base", "+dashboard-list", "--base-token", app_token])
        list_data = json.loads(list_output)
        dashboards = list_data.get("data", {}).get("dashboards", [])
        for d in dashboards:
            if d.get("name") == dashboard_name:
                dashboard_id = d.get("id") or d.get("dashboard_id")
                break
    except Exception:
        pass  # If list fails, proceed to create
    
    if dashboard_id:
        print(f"✅ Dashboard already exists: {dashboard_name} (ID: {dashboard_id})")
    else:
        # Create new dashboard
        print(f"📊 Creating dashboard for table: {table_name}...")
        dashboard_output = cli.run(["base", "+dashboard-create", "--base-token", app_token, "--name", dashboard_name])
        dashboard_data = json.loads(dashboard_output)
        dashboard_id = dashboard_data.get("data", {}).get("dashboard", {}).get("dashboard_id")
        if not dashboard_id:
            dashboard_id = dashboard_data.get("data", {}).get("dashboard_id")
        if not dashboard_id:
            raise Exception(f"Failed to get dashboard_id. Output: {dashboard_output}")
        print(f"✅ Dashboard created: {dashboard_id}")
    
    # Step 2: Create blocks serially (must wait between each)
    blocks = [
        {
            "name": "📋 上下文总数",
            "type": "statistics",
            "data_config": {
                "table_name": table_name,
                "count_all": True
            }
        },
        {
            "name": "📊 文档类型分布",
            "type": "pie",
            "data_config": {
                "table_name": table_name,
                "count_all": True,
                "group_by": [{"field_name": "文档类型", "mode": "integrated"}]
            }
        },
        {
            "name": "📈 近期更新",
            "type": "column",
            "data_config": {
                "table_name": table_name,
                "count_all": True,
                "group_by": [{"field_name": "最后更新", "mode": "integrated"}]
            }
        },
        {
            "name": "📝 项目说明",
            "type": "text",
            "data_config": {
                "text": f"## {table_name}\\n\\n此看板展示该项目的上下文积累情况。\\n\\n- **上下文总数**: 已录入的文档/记录数量\\n- **文档类型**: 会议纪要/需求/复盘等分布\\n- **近期更新**: 最近录入时间线\\n\\n每条记录代表一次上下文来源（文档、会议、沟通等）。"
            }
        }
    ]
    
    for i, block in enumerate(blocks):
        print(f"   Creating block {i+1}/{len(blocks)}: {block['name']}...")
        try:
            cli.run(["base", "+dashboard-block-create",
                     "--base-token", app_token,
                     "--dashboard-id", dashboard_id,
                     "--name", block["name"],
                     "--type", block["type"],
                     "--data-config", json.dumps(block["data_config"], ensure_ascii=False)])
            time.sleep(1.5)  # Rate limit protection
        except Exception as e:
            print(f"   ⚠️  Block '{block['name']}' failed (non-critical): {e}")
            continue
    
    # Step 3: Auto-arrange layout
    print("🎨 Auto-arranging dashboard layout...")
    try:
        cli.run(["base", "+dashboard-arrange", "--base-token", app_token, "--dashboard-id", dashboard_id])
        print("✅ Layout arranged!")
    except Exception as e:
        print(f"⚠️  Auto-arrange skipped (non-critical): {e}")
    
    return dashboard_id

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_dashboard.py <app_token> <table_name>")
        sys.exit(1)
    
    app_token = sys.argv[1]
    table_name = sys.argv[2]
    
    try:
        did = create_dashboard(app_token, table_name)
        print(f"\n🎉 Dashboard ready! ID: {did}")
    except Exception as e:
        print(f"Error: {e}")
