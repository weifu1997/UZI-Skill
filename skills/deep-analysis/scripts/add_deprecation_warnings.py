#!/usr/bin/env python3
"""自动为 22 个 legacy fetcher 添加废弃警告"""
import sys
from pathlib import Path

# Legacy fetcher 列表
LEGACY_FETCHERS = [
    "fetch_basic.py",
    "fetch_capital_flow.py",
    "fetch_chain.py",
    "fetch_contests.py",
    "fetch_events.py",
    "fetch_financials.py",
    "fetch_fund_holders.py",
    "fetch_futures.py",
    "fetch_governance.py",
    "fetch_industry.py",
    "fetch_kline.py",
    "fetch_lhb.py",
    "fetch_macro.py",
    "fetch_materials.py",
    "fetch_moat.py",
    "fetch_peers.py",
    "fetch_policy.py",
    "fetch_research.py",
    "fetch_sentiment.py",
    "fetch_similar_stocks.py",
    "fetch_trap_signals.py",
    "fetch_valuation.py",
]

DEPRECATION_NOTICE = '''"""
⚠️  DEPRECATED (v4.0.0): This legacy fetcher is deprecated.
    Use the Pipeline architecture instead (lib/pipeline/fetchers/).

    Migration: The functionality is preserved via adapter pattern.
    Set UZI_LEGACY=1 to continue using legacy fetchers.

    See: MIGRATION_V4.md for details.
"""
'''


def add_deprecation_notice(file_path: Path, dry_run: bool = False):
    """在文件顶部添加废弃警告"""
    if not file_path.exists():
        print(f"  ⚠️  文件不存在: {file_path.name}")
        return False

    content = file_path.read_text(encoding='utf-8')

    # 检查是否已有废弃警告
    if "DEPRECATED (v4.0.0)" in content:
        print(f"  ⏭️  已存在废弃警告: {file_path.name}")
        return False

    # 找到第一个 docstring 后插入
    lines = content.split('\n')
    insert_pos = 0

    # 找到模块 docstring 结束位置
    in_docstring = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip().startswith('"""'):
            in_docstring = True
        elif in_docstring and '"""' in line[1:]:
            insert_pos = i + 1
            break

    if insert_pos == 0:
        insert_pos = 0  # 如果没有 docstring，插在最开头

    # 插入废弃警告
    new_lines = lines[:insert_pos] + [DEPRECATION_NOTICE] + lines[insert_pos:]
    new_content = '\n'.join(new_lines)

    if dry_run:
        print(f"  🔍 [DRY RUN] 将添加废弃警告: {file_path.name}")
        return True

    file_path.write_text(new_content, encoding='utf-8')
    print(f"  ✅ 已添加废弃警告: {file_path.name}")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description='为 legacy fetchers 添加废弃警告')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际修改')
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🔧 Legacy Fetchers 废弃警告添加工具")
    print("=" * 60 + "\n")

    scripts_dir = Path(__file__).parent
    modified = 0
    skipped = 0
    missing = 0

    for fetcher_name in LEGACY_FETCHERS:
        file_path = scripts_dir / fetcher_name
        if add_deprecation_notice(file_path, dry_run=args.dry_run):
            modified += 1
        elif not file_path.exists():
            missing += 1
        else:
            skipped += 1

    # 总结
    print("\n" + "=" * 60)
    print("📊 处理结果:")
    print("=" * 60)
    print(f"  待处理: {len(LEGACY_FETCHERS)} 个文件")
    print(f"  已修改: {modified} 个")
    print(f"  已跳过: {skipped} 个（已有警告）")
    print(f"  缺失: {missing} 个")

    if args.dry_run:
        print("\n  ℹ️  这是预览模式。运行时移除 --dry-run 实际修改文件。")
    else:
        print("\n  ✅ 废弃警告添加完成！")

    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
