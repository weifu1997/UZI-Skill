#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整流程测试 - 验证 Pipeline 默认启用后的表现"""
import sys
import os
import io
import time
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加路径
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# 确保 Pipeline 启用
os.environ.pop("UZI_LEGACY", None)

from lib.pipeline import is_pipeline_enabled, collect


def test_pipeline_default_enabled():
    """测试 Pipeline 默认启用"""
    print("🧪 测试 1: Pipeline 默认状态...")

    enabled = is_pipeline_enabled()

    if enabled:
        print(f"  ✅ Pipeline 默认启用")
        return True
    else:
        print(f"  ❌ Pipeline 未启用")
        return False


def test_legacy_flag():
    """测试 UZI_LEGACY=1 禁用 Pipeline"""
    print("\n🧪 测试 2: UZI_LEGACY=1 禁用...")

    os.environ["UZI_LEGACY"] = "1"

    # 重新导入
    import importlib
    import lib.pipeline.collect as c
    importlib.reload(c)

    enabled = c.is_pipeline_enabled()

    os.environ.pop("UZI_LEGACY", None)

    if not enabled:
        print(f"  ✅ UZI_LEGACY=1 正确禁用 Pipeline")
        return True
    else:
        print(f"  ❌ UZI_LEGACY=1 未能禁用")
        return False


def test_full_collect():
    """测试完整 collect 流程（轻量级）"""
    print("\n🧪 测试 3: 完整 Collect 流程...")

    try:
        t0 = time.time()

        # 运行 collect（贵州茅台）
        print("     正在采集 600519.SH 数据...")
        result = collect("600519.SH", max_workers=3)

        elapsed = time.time() - t0

        if not result:
            print("  ❌ Collect 返回空")
            return False

        print(f"  ✅ Collect 完成")
        print(f"     采集维度: {len(result)} 个")
        print(f"     耗时: {elapsed:.2f}s")

        # 检查关键维度
        key_dims = ["0_basic", "1_financials", "2_kline"]
        for dim in key_dims:
            if dim in result:
                data = result[dim].get("data", {})
                quality = result[dim].get("_pipeline", {}).get("quality", "unknown")
                print(f"     {dim}: {len(data)} 字段, quality={quality}")

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 60)
    print("🚀 Pipeline 默认启用 - 完整流程测试")
    print("=" * 60 + "\n")

    results = []

    # 测试 1: 默认启用
    results.append(("Pipeline 默认启用", test_pipeline_default_enabled()))

    # 测试 2: Legacy flag
    results.append(("UZI_LEGACY flag", test_legacy_flag()))

    # 测试 3: 完整流程（可选，耗时）
    if os.environ.get("SKIP_FULL_TEST") != "1":
        results.append(("完整 Collect", test_full_collect()))
    else:
        print("\n🧪 测试 3: 完整 Collect (跳过)")
        print("     ℹ️  运行完整测试: 移除 SKIP_FULL_TEST 环境变量")

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果:")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name:<25} {status}")

    print()
    print(f"  总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！Pipeline 已默认启用并正常工作。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
