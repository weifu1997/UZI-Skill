#!/usr/bin/env python3
"""Tushare HTTP 代理配置测试脚本"""
import os
import sys

sys.path.insert(0, 'skills/deep-analysis/scripts')

def test_config():
    """测试配置"""
    print("\n" + "="*60)
    print("Tushare HTTP 代理配置测试")
    print("="*60 + "\n")

    # 1. 检查环境变量
    print("1. 环境变量检查:")
    url = os.environ.get('TUSHARE_HTTP_URL')
    token = os.environ.get('TUSHARE_HTTP_TOKEN')

    if url:
        print(f"   ✅ TUSHARE_HTTP_URL = {url}")
    else:
        print(f"   ❌ TUSHARE_HTTP_URL 未配置")
        print("\n配置方法:")
        print("   Windows CMD:  set TUSHARE_HTTP_URL=http://your-api.com")
        print("   PowerShell:   $env:TUSHARE_HTTP_URL = 'http://your-api.com'")
        print("   Linux/Mac:    export TUSHARE_HTTP_URL=http://your-api.com")
        return False

    if token:
        print(f"   ✅ TUSHARE_HTTP_TOKEN = {'*' * min(len(token), 10)}")
    else:
        print(f"   ⏸  TUSHARE_HTTP_TOKEN 未配置 (可选)")

    # 2. 检查 Provider 注册
    print("\n2. Provider 注册检查:")
    try:
        from lib.providers import get
        provider = get('tushare_http')

        if provider:
            print(f"   ✅ tushare_http 已注册")
            print(f"   市场: {provider.markets}")
            print(f"   需要 Key: {provider.requires_key}")
        else:
            print(f"   ❌ tushare_http 未注册")
            return False
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return False

    # 3. 检查可用性
    print("\n3. 可用性检查:")
    is_available = provider.is_available()
    if is_available:
        print(f"   ✅ Provider 可用")
    else:
        print(f"   ❌ Provider 不可用")
        print(f"   原因: TUSHARE_HTTP_URL 未配置")
        return False

    # 4. 检查方法
    print("\n4. 方法检查:")
    methods = [
        'fetch_basic_a',
        'fetch_financials_a',
        'fetch_kline_a',
        'fetch_valuation_a',
        'fetch_moneyflow_a',
        'fetch_research_reports_a',
    ]

    for method in methods:
        has_method = hasattr(provider, method)
        status = "✅" if has_method else "❌"
        print(f"   {status} {method}")

    # 5. 测试调用（可选）
    print("\n5. 测试调用 (可选):")
    test_call = input("   是否测试实际 API 调用？(y/N): ").strip().lower()

    if test_call == 'y':
        print("\n   测试 fetch_basic_a('600519')...")
        try:
            result = provider.fetch_basic_a('600519')
            print(f"   ✅ 调用成功！")
            print(f"   返回数据示例: {str(result)[:100]}...")
        except Exception as e:
            print(f"   ❌ 调用失败: {e}")
            print(f"\n   可能原因:")
            print(f"   1. API 地址不正确")
            print(f"   2. TOKEN 无效")
            print(f"   3. 网络连接问题")
            print(f"   4. API 响应格式不匹配")
            return False

    # 总结
    print("\n" + "="*60)
    print("✅ 配置测试完成！")
    print("="*60)
    print("\n下一步:")
    print("  1. 运行实际分析:")
    print("     python run.py 600519.SH")
    print("\n  2. 自定义优先级:")
    print("     export UZI_PROVIDERS_FINANCIALS=tushare_http,akshare")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
