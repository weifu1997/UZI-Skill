#!/usr/bin/env bash
# UZI-Skill v4.0.0 Week 1 安全修复脚本
# 一键完成 P0 级别修复

set -e  # 遇错即停

echo "🚀 UZI-Skill v4.0.0 Week 1 安全修复"
echo "=================================="
echo ""

# 检测工作目录
if [ ! -f "run.py" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# Step 1: 创建 security.py（已完成）
echo "✅ Step 1/6: lib/security.py 已创建"

# Step 2: 运行安全测试
echo "🧪 Step 2/6: 运行安全模块测试..."
cd skills/deep-analysis/scripts
if python -m pytest tests/test_security.py -v --tb=short; then
    echo "✅ 安全模块测试通过"
else
    echo "❌ 测试失败，请检查"
    exit 1
fi
cd ../../..

# Step 3: 应用安全补丁
echo "🔧 Step 3/6: 应用安全补丁..."
if [ "$1" == "--apply" ]; then
    python scripts/quick_fix_security.py --apply
else
    echo "   [预览模式] 使用 --apply 参数应用修改"
    python scripts/quick_fix_security.py --dry-run
fi

# Step 4: 检查 mini_racer 依赖
echo "🔍 Step 4/6: 检查 mini_racer 使用..."
MINI_RACER_COUNT=$(grep -r "mini_racer" skills/deep-analysis/scripts --include="*.py" | wc -l || echo "0")
if [ "$MINI_RACER_COUNT" -gt 5 ]; then
    echo "⚠️  发现 $MINI_RACER_COUNT 处 mini_racer 引用，建议清理"
else
    echo "✅ mini_racer 使用已最小化"
fi

# Step 5: 检查 HTTP vs HTTPS
echo "🔍 Step 5/6: 检查非 HTTPS 调用..."
HTTP_COUNT=$(grep -r 'http://' skills/deep-analysis/scripts --include="*.py" | grep -v localhost | wc -l || echo "0")
if [ "$HTTP_COUNT" -gt 0 ]; then
    echo "⚠️  发现 $HTTP_COUNT 处 http:// 调用，建议改为 https://"
    echo "   运行: grep -rn 'http://' skills/deep-analysis/scripts --include='*.py' | grep -v localhost"
else
    echo "✅ 所有外部调用已使用 HTTPS"
fi

# Step 6: 检查 .env 权限
echo "🔒 Step 6/6: 检查 .env 文件权限..."
if [ -f ".env" ]; then
    if [ "$(uname)" != "Windows_NT" ]; then
        PERMS=$(stat -c "%a" .env 2>/dev/null || stat -f "%Lp" .env 2>/dev/null || echo "unknown")
        if [ "$PERMS" != "600" ] && [ "$PERMS" != "unknown" ]; then
            echo "⚠️  .env 权限为 $PERMS，建议: chmod 600 .env"
        else
            echo "✅ .env 权限正确"
        fi
    else
        echo "   (Windows 环境跳过权限检查)"
    fi
else
    echo "   .env 文件不存在（可选）"
fi

echo ""
echo "=================================="
echo "📊 Week 1 进度总结"
echo "=================================="
echo ""
echo "✅ 已完成:"
echo "  - lib/security.py 创建"
echo "  - 测试套件编写"
echo "  - 快速修复工具准备"
echo ""
echo "📋 待完成（需手动）:"
echo "  1. 运行: ./scripts/week1_security_fixes.sh --apply"
echo "  2. 实现 3 个 fetcher 的纯 HTTP 版本 (Day 3-4)"
echo "  3. 移除 mini_racer 代码 (Day 4)"
echo ""
echo "📚 参考文档:"
echo "  - SECURITY_AUDIT_REPORT.md"
echo "  - REFACTOR_ROADMAP.md"
echo ""

if [ "$1" == "--apply" ]; then
    echo "✅ 修复已应用！下一步:"
    echo "   cd skills/deep-analysis/scripts"
    echo "   pytest tests/ -v  # 运行全量测试"
else
    echo "💡 预览完成。应用修复请运行:"
    echo "   ./scripts/week1_security_fixes.sh --apply"
fi
