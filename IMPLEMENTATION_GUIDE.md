# UZI-Skill 实施指南（v4.0.0 重构）

> 从审查报告到实际代码修复的完整指南

---

## 🎯 立即开始

### 前置检查

```bash
# 1. 确认在项目根目录
ls run.py AGENTS.md  # 应该看到这两个文件

# 2. 确认 Python 环境
python --version  # 需要 3.10+

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行现有测试（确保起点健康）
cd skills/deep-analysis/scripts
pytest tests/ -q
cd ../../..
```

---

## Week 1: P0 安全修复（预计 5 天）

### Day 1: 安全模块实现

**已完成**:
- ✅ `lib/security.py` 已创建
- ✅ `tests/test_security.py` 已创建
- ✅ `scripts/quick_fix_security.py` 已创建

**执行**:

```bash
# 1. 运行安全测试
cd skills/deep-analysis/scripts
pytest tests/test_security.py -v

# 预期输出:
# test_security.py::TestMaskSecret::test_mask_apikey PASSED
# test_security.py::TestTickerValidator::test_valid_a_share PASSED
# ... 共 20+ 个测试全部 PASSED

# 2. 预览修复（不修改文件）
cd ../../..
python scripts/quick_fix_security.py --dry-run

# 3. 应用修复（实际修改文件）
python scripts/quick_fix_security.py --apply

# 4. 验证修复
cd skills/deep-analysis/scripts
pytest tests/ -v  # 全量测试应该仍然通过
```

**验证清单**:
- [ ] 所有测试通过
- [ ] run.py 添加了输入验证
- [ ] mx_api.py 添加了密钥脱敏
- [ ] cache.py 添加了线程锁

---

### Day 2: 集成测试

**创建端到端安全测试**:

```bash
cd skills/deep-analysis/scripts/tests
```

创建 `test_security_integration.py`:

```python
"""Integration tests for security fixes."""
import os
import pytest
from pathlib import Path


def test_run_py_rejects_path_traversal():
    """run.py 应该拒绝路径遍历攻击."""
    import subprocess
    result = subprocess.run(
        ["python", "run.py", "../etc/passwd", "--no-browser"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "traversal" in result.stderr.lower() or "invalid" in result.stderr.lower()


def test_cache_does_not_leak_secrets(tmp_path):
    """缓存文件不应包含 API 密钥."""
    os.environ["MX_APIKEY"] = "test_secret_key_12345678"
    
    from lib.cache import cached
    
    def fetch():
        return {"data": "ok"}
    
    # 写入缓存
    result = cached("TEST", "test_key", fetch, ttl=60)
    
    # 检查缓存文件
    cache_files = list(Path(".cache/TEST").rglob("*.json"))
    for f in cache_files:
        content = f.read_text()
        assert "test_secret_key" not in content


def test_error_messages_masked():
    """错误消息应该脱敏."""
    from lib.mx_api import _post
    
    # 模拟失败请求（无需实际调用）
    result = _post(
        "https://example.com/api",
        {"query": "test"},
        api_key="secret_key_abc123",
        timeout=1,
        attempts=1,
    )
    
    # 错误消息不应包含密钥
    if "error" in result:
        assert "secret_key" not in result["error"]
        assert "abc123" not in result["error"]
```

运行:
```bash
pytest tests/test_security_integration.py -v
```

---

### Day 3-4: mini_racer 根除

**目标**: 替换 3 个使用 mini_racer 的 fetcher

#### 3.1 实现纯 HTTP 版本

编辑 `lib/data_sources.py`，添加:

```python
def fetch_capital_flow_pure_http(code: str) -> dict:
    """资金流（纯 HTTP，无 mini_racer）.
    
    直接调用东财 API，绕过 akshare 的 JS 解析。
    """
    import requests
    
    # 判断市场
    secid = f"1.{code}" if code.startswith("6") else f"0.{code}"
    
    url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
        "lmt": 30,
        "klt": 101,
        "ut": "b2884a393a59ad64002292a3e90d46a5",
    }
    
    try:
        r = requests.get(url, params=params, timeout=10, verify=True)
        if r.status_code != 200:
            return {}
        
        data = r.json()
        klines = data.get("data", {}).get("klines", [])
        
        if not klines:
            return {}
        
        # 解析最新一天
        latest = klines[-1].split(",")
        return {
            "date": latest[0],
            "main_net_inflow": float(latest[1] or 0),
            "small_net_inflow": float(latest[2] or 0),
            "medium_net_inflow": float(latest[3] or 0),
            "large_net_inflow": float(latest[4] or 0),
            "super_large_net_inflow": float(latest[5] or 0),
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_industry_pe_pure_http(industry: str) -> dict:
    """行业 PE（纯 HTTP）.
    
    使用东财聚源 API 替代 cninfo。
    """
    import requests
    
    # 东财行业 API（公开）
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "reportName": "RPT_INDUSTRY_INDEX",
        "columns": "ALL",
        "filter": f"(INDUSTRY_NAME=\"{industry}\")",
        "pageNumber": "1",
        "pageSize": "10",
        "sortColumns": "TRADE_DATE",
        "sortTypes": "-1",
    }
    
    try:
        r = requests.get(url, params=params, timeout=10, verify=True)
        if r.status_code != 200:
            return {}
        
        data = r.json()
        rows = data.get("result", {}).get("data", [])
        
        if not rows:
            return {}
        
        latest = rows[0]
        return {
            "industry": industry,
            "pe_ttm": latest.get("PE_TTM"),
            "pb": latest.get("PB"),
            "trade_date": latest.get("TRADE_DATE"),
        }
    except Exception as e:
        return {"error": str(e)}
```

#### 3.2 修改 fetcher

编辑 `fetch_capital_flow.py`:

```python
def main(ticker: str) -> dict:
    ti = parse_ticker(ticker)
    
    # v4.0.0 · 优先纯 HTTP（无 mini_racer）
    from lib.data_sources import fetch_capital_flow_pure_http
    result = fetch_capital_flow_pure_http(ti.code)
    
    if result and "error" not in result:
        return {
            "data": result,
            "source": "eastmoney_pure_http",
            "fallback": False,
        }
    
    # 降级到 akshare（仍有风险，但尝试）
    try:
        import akshare as ak
        df = ak.stock_individual_fund_flow(ti.code, market="sh" if ti.code[0]=="6" else "sz")
        # ... 现有代码 ...
    except Exception as e:
        return {"data": {}, "error": str(e), "fallback": True}
```

类似修改 `fetch_industry.py` 和 `fetch_valuation.py`。

#### 3.3 移除 mini_racer 代码

编辑 `run_real_test.py`:

```python
# 删除以下代码块（行 74-127）:
# _MINI_RACER_FETCHERS = ...
# _MINI_RACER_LOCK = ...
# _MINI_RACER_SENTINEL = ...
# def _mini_racer_disabled(): ...
# def _arm_mini_racer_sentinel(): ...
# def _disarm_mini_racer_sentinel(): ...

# 简化 run_fetcher 函数:
def run_fetcher(module_name: str, args: tuple) -> dict:
    try:
        mod = __import__(module_name)
        result = mod.main(*args)
        return result if isinstance(result, dict) else {"data": result}
    except Exception as e:
        return {"data": {}, "error": str(e), "fallback": True}
```

#### 3.4 测试

```bash
# 测试每个修改的 fetcher
cd skills/deep-analysis/scripts

python fetch_capital_flow.py 600519.SH
python fetch_industry.py 金融
python fetch_valuation.py 600519.SH

# 全量测试
pytest tests/ -v

# 运行实际分析（端到端）
cd ../../..
python run.py 600519.SH --no-browser
```

**验证清单**:
- [ ] 3 个 fetcher 输出正常
- [ ] 无 mini_racer 错误
- [ ] macOS 测试不崩溃
- [ ] pytest 全部通过

---

### Day 5: Week 1 验收

**运行完整测试套件**:

```bash
cd skills/deep-analysis/scripts

# 1. 单元测试
pytest tests/ -v --cov=lib --cov-report=term

# 2. 安全测试
pytest tests/test_security*.py -v

# 3. 端到端测试（3 个市场）
cd ../../..
python run.py 600519.SH --no-browser  # A股
python run.py 00700.HK --no-browser   # 港股
python run.py AAPL --no-browser       # 美股

# 4. 性能测试（确保无退化）
time python run.py 002273.SZ --no-browser
# 预期: 2-4 分钟（与 v3.9 相当）
```

**Week 1 验收清单**:
- [ ] 所有 pytest 通过（60+ 测试）
- [ ] 安全模块覆盖率 >90%
- [ ] mini_racer 完全移除
- [ ] 3 个市场均能正常分析
- [ ] 性能无显著退化（±10%）

**提交代码**:
```bash
git add .
git commit -m "refactor(security): Week 1 P0 fixes - credential masking, input validation, mini_racer removal [v4.0.0]"
git push origin refactor/v4.0.0
```

---

## Week 2-3: 架构统一（见 REFACTOR_ROADMAP.md）

**快速启动**:

```bash
# Week 2: 核心 fetcher 迁移
cd skills/deep-analysis/scripts/lib/pipeline/fetchers

# 创建第一个新 fetcher
cat > basic_fetcher.py << 'EOF'
from ..base_fetcher import BaseFetcher

class BasicFetcher(BaseFetcher):
    def _fetch_impl(self) -> dict:
        from lib.data_sources import fetch_basic
        return fetch_basic(self.ti)
    
    def source_name(self) -> str:
        return f"akshare:{self.ti.market}"
EOF

# 测试
python -c "from lib.pipeline.fetchers.basic_fetcher import BasicFetcher; print(BasicFetcher('600519.SH').fetch())"
```

详细迁移步骤见 `REFACTOR_ROADMAP.md` Week 2-3 部分。

---

## Week 4: 发布准备

**最终检查清单**:

```bash
# 1. 运行全量测试
cd skills/deep-analysis/scripts
pytest tests/ -v --cov=lib --cov-report=html
# 打开 htmlcov/index.html 查看覆盖率（目标 >75%）

# 2. 代码质量检查
cd ../../..
python -m pylint skills/deep-analysis/scripts/lib --disable=C0114,C0115,C0116
# 修复所有 E 级错误，W 级警告可选

# 3. 类型检查
python -m mypy skills/deep-analysis/scripts/lib --ignore-missing-imports
# 修复所有类型错误

# 4. 性能基准测试
./scripts/benchmark_v4.sh
# 对比 v3.9 vs v4.0 性能

# 5. 文档检查
ls -la *. md | wc -l  # 应该有完整文档

# 6. 更新版本号
# 编辑 .claude-plugin/plugin.json
# 编辑 package.json
# 编辑 skills/deep-analysis/SKILL.md
```

**发布**:
```bash
git tag v4.0.0
git push origin v4.0.0
gh release create v4.0.0 --notes-file CHANGELOG-v4.0.0.md
```

---

## 🆘 故障排查

### 问题 1: pytest 找不到模块

```bash
# 确保在正确目录
cd skills/deep-analysis/scripts

# 设置 PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH

# 重新运行
pytest tests/ -v
```

### 问题 2: mini_racer 仍然崩溃

```bash
# 临时禁用（测试用）
export UZI_DISABLE_MINI_RACER=1
python run.py 600519.SH --no-browser

# 永久解决：确认 Day 3-4 修改已应用
grep -r "mini_racer" skills/deep-analysis/scripts --include="*.py"
# 应该只在旧的 .bak 备份文件中出现
```

### 问题 3: 测试失败

```bash
# 查看详细错误
pytest tests/test_security.py -vv --tb=long

# 单独运行失败的测试
pytest tests/test_security.py::TestTickerValidator::test_valid_a_share -vv

# 检查依赖
pip list | grep -E "pytest|requests"
```

---

## 📞 获取帮助

- **文档**: `SECURITY_AUDIT_REPORT.md`, `REFACTOR_ROADMAP.md`
- **测试**: `pytest tests/ -v`
- **问题**: 提 GitHub Issue，标签 `refactor-v4`

---

**最后更新**: 2026-06-12  
**状态**: ✅ Week 1 工具就绪，可开始实施
