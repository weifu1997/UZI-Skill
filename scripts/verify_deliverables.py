#!/usr/bin/env python3
"""验证代码审查交付物的完整性和正确性."""
import sys
from pathlib import Path


def main():
    print("🔍 UZI-Skill v4.0 代码审查交付验证\n")
    print("=" * 60)

    repo_root = Path(__file__).parent.parent

    # 检查文档
    docs = [
        "CODE_REVIEW_REPORT.md",
        "SECURITY_AUDIT_REPORT.md",
        "REFACTOR_ROADMAP.md",
        "IMPLEMENTATION_GUIDE.md",
        "EXECUTIVE_SUMMARY.md",
        "QUICK_REFERENCE.md",
    ]

    print("\n📚 文档检查:")
    doc_ok = 0
    for doc in docs:
        path = repo_root / doc
        if path.exists():
            size = path.stat().st_size // 1024
            print(f"  ✅ {doc:<35} ({size:>4} KB)")
            doc_ok += 1
        else:
            print(f"  ❌ {doc:<35} (缺失)")

    # 检查代码
    code_files = [
        "skills/deep-analysis/scripts/lib/security.py",
        "skills/deep-analysis/scripts/tests/test_security.py",
        "scripts/quick_fix_security.py",
        "scripts/week1_security_fixes.sh",
    ]

    print("\n💻 代码检查:")
    code_ok = 0
    for code in code_files:
        path = repo_root / code
        if path.exists():
            lines = len(path.read_text(encoding="utf-8").splitlines())
            print(f"  ✅ {code:<55} ({lines:>4} 行)")
            code_ok += 1
        else:
            print(f"  ❌ {code:<55} (缺失)")

    # 运行测试
    print("\n🧪 测试验证:")
    test_path = repo_root / "skills/deep-analysis/scripts/tests/test_security.py"
    if test_path.exists():
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=repo_root / "skills/deep-analysis/scripts",
        )

        if result.returncode == 0:
            # 解析通过的测试数
            passed = result.stdout.count(" PASSED")
            print(f"  ✅ 测试套件通过 ({passed} 个测试)")
        else:
            print(f"  ⚠️  测试失败")
            print(result.stdout[-500:])
    else:
        print("  ❌ 测试文件不存在")

    # 总结
    print("\n" + "=" * 60)
    print("📊 交付摘要:\n")
    print(f"  文档: {doc_ok}/{len(docs)} ✅")
    print(f"  代码: {code_ok}/{len(code_files)} ✅")
    print(f"  测试: {'✅ 通过' if result.returncode == 0 else '⚠️  失败'}")

    total_ok = doc_ok + code_ok + (1 if result.returncode == 0 else 0)
    total = len(docs) + len(code_files) + 1

    print(f"\n  总计: {total_ok}/{total} 项完成")

    if total_ok == total:
        print("\n✅ 所有交付物已就绪！")
        print("\n📋 下一步:")
        print("  1. 阅读 EXECUTIVE_SUMMARY.md（5分钟）")
        print("  2. 运行 ./scripts/week1_security_fixes.sh --dry-run")
        print("  3. 开始 Week 1 实施")
        return 0
    else:
        print(f"\n⚠️  {total - total_ok} 项缺失或失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
