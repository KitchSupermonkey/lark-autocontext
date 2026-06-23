"""
One-command setup for Lark AutoContext.

Usage:
  python scripts/setup.py                  # interactive (human)
  python scripts/setup.py --auto           # non-interactive (agent-driven)

This script handles everything:
  1. Check lark-cli installed + logged in
  2. Create config.json from example (no tokens needed — auth is via lark-cli)
  3. Create scan_config.json (interactive: user pastes Feishu folder/wiki URLs,
     script extracts tokens automatically)
  4. Initialize OKF Bundle directory

The user NEVER needs to manually edit JSON files.
"""
import json
import os
import re
import sys
import shutil
import subprocess
import argparse

if sys.platform == "win32" and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)


def step(msg):
    print(f"\n{'='*50}")
    print(f"  {msg}")
    print(f"{'='*50}")


def ok(msg):
    print(f"  ✅ {msg}")


def warn(msg):
    print(f"  ⚠️  {msg}")


def fail(msg):
    print(f"  ❌ {msg}")


def check_lark_cli():
    """Check lark-cli is installed and logged in."""
    step("Step 1: 检查 lark-cli")
    try:
        r = subprocess.run(["lark-cli", "--version"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            raise FileNotFoundError()
        ok(f"lark-cli 已安装 ({r.stdout.strip()})")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        fail("lark-cli 未安装")
        print("  请运行: npm install -g @larksuiteoapi/lark-cli")
        print("  安装后重新运行 setup.py")
        return False

    # Check auth
    try:
        r = subprocess.run(["lark-cli", "auth", "status"],
                           capture_output=True, text=True, timeout=10)
        output = (r.stdout + r.stderr).lower()
        if "not logged in" in output or "未登录" in output:
            warn("lark-cli 未登录")
            print("  请运行: lark-cli auth login --recommend --no-wait")
            print("  在浏览器中完成飞书授权后，重新运行 setup.py")
            return False
        ok("lark-cli 已认证")
        return True
    except Exception as e:
        warn(f"无法检查认证状态 ({e})")
        print("  假设已认证，继续...")
        return True


def create_config():
    """Create config.json from example. No user input needed."""
    step("Step 2: 创建配置文件")
    config_path = os.path.join(SCRIPTS_DIR, "config.json")
    example_path = os.path.join(SCRIPTS_DIR, "config.json.example")

    if os.path.exists(config_path):
        ok("config.json 已存在，跳过")
        return True

    if not os.path.exists(example_path):
        # Create a minimal config directly
        config = {
            "bundle_path": "./bundle",
            "identity": "user",
        }
    else:
        with open(example_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        # Strip comment fields
        config = {k: v for k, v in config.items() if not k.startswith("_")}

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    ok("config.json 已创建（使用默认配置，无需手动填写）")
    return True


def extract_token_from_url(url):
    """Extract folder/wiki/bitable token from a Feishu URL.

    Examples:
      https://xxx.feishu.cn/drive/folder/ABC123  → ("folder", "ABC123")
      https://xxx.feishu.cn/wiki/DEF456          → ("wiki", "DEF456")
      https://xxx.feishu.cn/base/GHI789          → ("bitable", "GHI789")
    """
    url = url.strip()

    # folder
    m = re.search(r'/drive/folder/([A-Za-z0-9]+)', url)
    if m:
        return ("folder", m.group(1))

    # wiki
    m = re.search(r'/wiki/([A-Za-z0-9]+)', url)
    if m:
        return ("wiki", m.group(1))

    # bitable / base
    m = re.search(r'/base/([A-Za-z0-9]+)', url)
    if m:
        return ("bitable", m.group(1))

    # Bare token (heuristic: alphanumeric string, 10+ chars)
    if re.match(r'^[A-Za-z0-9]{10,}$', url):
        return ("folder", url)

    return (None, None)


def create_scan_config(auto=False, sources=None):
    """Create scan_config.json. In interactive mode, ask user for Feishu URLs."""
    step("Step 3: 配置扫描源")
    scan_config_path = os.path.join(SCRIPTS_DIR, "scan_config.json")

    if os.path.exists(scan_config_path):
        ok("scan_config.json 已存在，跳过")
        return True

    if auto and sources is None:
        # Non-interactive, no sources provided → create empty config
        config = {"sources": []}
        with open(scan_config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        ok("scan_config.json 已创建（暂无扫描源，后续可添加）")
        print("  提示: 之后发飞书文件夹/wiki 链接给 agent，会自动添加扫描源")
        return True

    if sources is None:
        sources = []
        print("  现在可以添加要扫描的飞书文件夹/Wiki。")
        print("  直接粘贴飞书 URL（例如 https://xxx.feishu.cn/drive/folder/XXX）")
        print("  输入空行结束添加\n")

        while True:
            url = input("  飞书 URL (空行结束): ").strip()
            if not url:
                break
            src_type, token = extract_token_from_url(url)
            if not token:
                warn(f"无法识别 URL 中的 token，跳过: {url}")
                continue
            name = input(f"  给这个源起个名字 (默认: {src_type}): ").strip()
            if not name:
                name = src_type
            sources.append({"type": src_type, "token": token, "name": name})
            ok(f"已添加: {name} ({src_type}, token={token[:8]}...)")

    config = {"sources": sources}
    with open(scan_config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    ok(f"scan_config.json 已创建（{len(sources)} 个扫描源）")
    return True


def init_bundle():
    """Initialize the OKF Bundle directory."""
    step("Step 4: 初始化 OKF Bundle")

    from init_bundle import init_bundle as _init
    _init()
    ok("OKF Bundle 已就绪")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="One-command setup for Lark AutoContext")
    parser.add_argument("--auto", action="store_true",
                        help="Non-interactive mode (for agent automation)")
    parser.add_argument("--sources", nargs="*", default=None,
                        help="Feishu URLs to add as scan sources (with --auto)")
    args = parser.parse_args()

    print("\n🧙 Lark AutoContext — 一键初始化")
    print("  Agent 会自动完成所有配置，你不需要手动编辑任何 JSON 文件。")

    # Step 1: lark-cli
    if not check_lark_cli():
        print("\n❌ 初始化未完成。请解决上述问题后重新运行 setup.py")
        sys.exit(1)

    # Step 2: config.json
    create_config()

    # Step 3: scan_config.json
    sources = None
    if args.auto and args.sources:
        # Parse URLs provided via CLI
        sources = []
        for url in args.sources:
            src_type, token = extract_token_from_url(url)
            if token:
                sources.append({"type": src_type, "token": token, "name": src_type})
    create_scan_config(auto=args.auto, sources=sources)

    # Step 4: bundle
    init_bundle()

    # Summary
    step("初始化完成！")
    print("  📦 OKF Bundle 已就绪")
    print("  📊 可视化: bundle/viz.html (每次写入自动更新)")
    print("  📝 现在可以开始保存上下文了")
    print("\n  使用方式:")
    print("    1. 发飞书文档链接 + '保存' → 自动提取分类入库")
    print("    2. '扫描飞书文档' → 批量扫描导入")
    print("    3. 'XX项目里关于XX的信息？' → 查询已存上下文")
    print("    4. 打开 bundle/viz.html → 查看知识图谱")


if __name__ == "__main__":
    main()
