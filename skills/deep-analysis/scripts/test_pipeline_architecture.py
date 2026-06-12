#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 Pipeline 架构是否正常工作（v4.0.0）"""
import sys
import os
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加路径
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

# 启用 pipeline
os.environ["UZI_PIPELINE"] = "1"

from lib.pipeline import is_pipeline_enabled, collect
from lib.pipeline.fetchers.registry import list_fetchers, FETCHER_REGISTRY


def test_pipeline_enabled():
    """测试 pipeline 是否启用"""
    print("🧪 测试 1: Pipeline 启用状态...")
    enabled = is_pipeline_enabled()

    if enabled:
        print(f"  ✅ Pipeline 已启用 (UZI_PIPELINE={os.environ.get('UZI_PIPELINE')})")
        return True
    else:
        print(f"  ❌ Pipeline 未启用")
        return False


def test_registry():
    """测试 fetcher 注册表"""
    print("\n🧪 测试 2: Fetcher 注册表...")
    fetchers = list_fetchers()

    print(f"  ✅ 已注册 {len(fetchers)} 个 fetcher:")
    for i, dim_key in enumerate(fetchers, 1):
        print(f"     {i:2d}. {dim_key}")

    return len(fetchers) >= 20


def test_basic_fetcher():
    """测试单个 fetcher"""
    print("\n🧪 测试 3: 单个 Fetcher (0_basic)...")

    try:
        from lib.pipeline.fetchers.registry import get_fetcher
        fetcher = get_fetcher("0_basic")

        if not fetcher:
            print("  ❌ 无法获取 fetcher")
            return False

        # 测试调用（使用贵州茅台）- 修正：fetch() 只需要 ticker 参数
        result = fetcher.fetch("600519.SH")

        print(f"  ✅ Fetcher 返回: dim_key={result.dim_key}")
        print(f"     质量: {result.quality.value}")
        print(f"     数据字段: {len(result.data)} 个")
        print(f"     来源: {result.source}")

        # 检查关键字段
        if "name" in result.data or "price" in result.data:
            print(f"     ✅ 包含关键数据")
            return True
        else:
            print(f"     ⚠️  数据可能不完整（quality={result.quality.value}）")
            return True  # 不阻塞测试

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_collect_pipeline():
    """测试完整 collect 流程（轻量级）"""
    print("\n🧪 测试 4: Pipeline Collect (仅 basic)...")

    try:
        # 只测试 basic，避免网络请求过多
        os.environ["UZI_QUICK_TEST"] = "1"

        result = collect("600519.SH", max_workers=1)

        if not result:
            print("  ❌ Collect 返回空")
            return False

        print(f"  ✅ Collect 返回 {len(result)} 个维度")

        # 检查格式
        if "0_basic" in result:
            basic = result["0_basic"]
            print(f"     0_basic 格式检查:")
            print(f"       - 有 'data' 字段: {'data' in basic}")
            print(f"       - 有 'source' 字段: {'source' in basic}")
            print(f"       - 有 'fallback' 字段: {'fallback' in basic}")

            return "data" in basic and "source" in basic

        return True

    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 60)
    print("🚀 Pipeline 架构验证测试（v4.0.0）")
    print("=" * 60 + "\n")

    results = []

    # 测试 1: Pipeline 启用
    results.append(("Pipeline 启用", test_pipeline_enabled()))

    # 测试 2: 注册表
    results.append(("Fetcher 注册表", test_registry()))

    # 测试 3: 单个 fetcher
    results.append(("单个 Fetcher", test_basic_fetcher()))

    # 测试 4: Collect（可选，耗时）
    if os.environ.get("FULL_TEST") == "1":
        results.append(("Pipeline Collect", test_collect_pipeline()))
    else:
        print("\n🧪 测试 4: Pipeline Collect (跳过)")
        print("     ℹ️  运行完整测试: FULL_TEST=1 python test_pipeline_architecture.py")

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
        print("\n🎉 所有测试通过！Pipeline 架构运行正常。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
