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
