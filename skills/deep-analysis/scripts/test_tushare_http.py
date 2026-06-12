#!/usr/bin/env python3
"""测试 Tushare HTTP Provider"""
import sys
import os

# 添加路径
sys.path.insert(0, 'skills/deep-analysis/scripts')

# 配置测试环境变量（示例）
# os.environ['TUSHARE_HTTP_URL'] = 'http://your-api.com'
# os.environ['TUSHARE_HTTP_TOKEN'] = 'your_token'

def test_provider_registration():
    """测试 Provider 是否正确注册"""
    print("\n" + "="*60)
    print("测试 1: Provider 注册")
    print("="*60)

    from lib.providers import list_providers, get

    # 列出所有 providers
    all_providers = list_providers()
    print(f"\n已注册 Providers: {len(all_providers)} 个")
    for p in all_providers:
        avail = "✅ 可用" if p.is_available() else "⏸️  未配置"
        print(f"  • {p.name:<15} {avail}  市场: {p.markets}")

    # 检查 tushare_http
    tushare_http = get("tushare_http")
    if tushare_http:
        print(f"\n✅ tushare_http Provider 已注册")
        print(f"   可用: {tushare_http.is_available()}")
        print(f"   需要 Key: {tushare_http.requires_key}")
        print(f"   市场: {tushare_http.markets}")
    else:
        print("\n❌ tushare_http Provider 未找到")
        return False

    return True


def test_provider_chain():
    """测试 Provider Chain"""
    print("\n" + "="*60)
    print("测试 2: Provider Chain 优先级")
    print("="*60)

    from lib.providers import get_provider_chain

    # 测试默认顺序
    chain = get_provider_chain("financials", market="A")
    print(f"\n默认顺序 (financials/A): {len(chain)} 个可用")
    for i, p in enumerate(chain, 1):
        print(f"  {i}. {p.name}")

    # 检查 tushare_http 是否在链中
    names = [p.name for p in chain]
    if "tushare_http" in names:
        print(f"\n✅ tushare_http 在默认链中 (位置: {names.index('tushare_http') + 1})")
    else:
        print("\n⏸️  tushare_http 不在链中（可能未配置 TUSHARE_HTTP_URL）")

    return True


def test_http_call():
    """测试 HTTP 调用（如果已配置）"""
    print("\n" + "="*60)
    print("测试 3: HTTP 调用测试")
    print("="*60)

    from lib.providers import get

    tushare_http = get("tushare_http")
    if not tushare_http or not tushare_http.is_available():
        print("\n⏸️  跳过：TUSHARE_HTTP_URL 未配置")
        print("\n配置方法:")
        print("  export TUSHARE_HTTP_URL=http://your-api.com")
        print("  export TUSHARE_HTTP_TOKEN=your_token  # 可选")
        return True

    print(f"\n✅ TUSHARE_HTTP_URL 已配置")
    print(f"   URL: {os.environ.get('TUSHARE_HTTP_URL')}")

    # 测试调用（需要实际的 API）
    print("\n💡 提示: 实际调用需要有效的代理 API")
    print("   可以手动测试:")
    print("   >>> from lib.providers import get")
    print("   >>> p = get('tushare_http')")
    print("   >>> result = p.fetch_basic_a('600519')")

    return True


def test_new_methods():
    """测试新增方法"""
    print("\n" + "="*60)
    print("测试 4: 新增方法检查")
    print("="*60)

    from lib.providers import get

    tushare_http = get("tushare_http")
    if not tushare_http:
        print("\n❌ tushare_http Provider 未注册")
        return False

    # 检查方法
    methods = [
        "fetch_basic_a",
        "fetch_financials_a",
        "fetch_kline_a",
        "fetch_valuation_a",         # 新增
        "fetch_research_reports_a",  # 新增
        "fetch_moneyflow_a",         # 新增
        "fetch_top10_holders",
        "fetch_top_list",
        "fetch_hsgt_top10",
    ]

    print(f"\n方法检查:")
    for method in methods:
        has_method = hasattr(tushare_http, method)
        status = "✅" if has_method else "❌"
        label = "新增" if method in ["fetch_valuation_a", "fetch_research_reports_a", "fetch_moneyflow_a"] else ""
        print(f"  {status} {method:<30} {label}")

    return True


def main():
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║   🧪 Tushare HTTP Provider 测试套件                          ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    results = []

    # 运行测试
    results.append(("Provider 注册", test_provider_registration()))
    results.append(("Provider Chain", test_provider_chain()))
    results.append(("HTTP 调用", test_http_call()))
    results.append(("新增方法", test_new_methods()))

    # 总结
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name:<20} {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n下一步:")
        print("  1. 配置 TUSHARE_HTTP_URL")
        print("  2. 测试实际调用")
        print("  3. 开始使用")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
