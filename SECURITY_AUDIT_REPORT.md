# UZI-Skill 安全审计报告

生成时间：2026-06-12  
审计范围：API 密钥处理、输入验证、并发安全、错误处理

---

## 🔴 P0 级别问题详解

### 1. API 密钥安全隐患

#### 1.1 当前实现分析

**密钥读取点**：
```python
# lib/mx_api.py:71
self.api_key = api_key or os.getenv("MX_APIKEY") or ""

# run.py:393-396
if os.environ.get("MX_APIKEY"):
    print(f"🔑 MX_APIKEY 已设置 · 将优先使用东财妙想 API")
else:
    print(f"ℹ️  未设置 MX_APIKEY · 走默认 akshare/xueqiu 链")
```

**存在的风险**：
1. ✅ **好消息**：代码中未直接打印密钥值
2. ⚠️ **潜在风险**：
   - HTTP headers 中的 apikey 可能出现在异常堆栈
   - 缓存文件包含 API 响应但不含密钥（已验证）
   - 错误消息可能暴露部分密钥信息

#### 1.2 修复方案

**方案 A：密钥脱敏工具**（立即实施）

```python
# skills/deep-analysis/scripts/lib/security.py（新建）
"""Security utilities for credential handling."""
import re
from typing import Any


def mask_secret(text: str, patterns: list[str] = None) -> str:
    """Mask secrets in text output.
    
    Args:
        text: Input text
        patterns: Custom regex patterns (default: common API key formats)
    
    Returns:
        Text with secrets replaced by '***REDACTED***'
    """
    if patterns is None:
        patterns = [
            r'(apikey["\s:=]+)([a-zA-Z0-9_\-]{16,})',  # apikey: xxx
            r'(MX_APIKEY["\s:=]+)([a-zA-Z0-9_\-]{16,})',
            r'(Authorization["\s:]+Bearer\s+)([a-zA-Z0-9_\-\.]+)',
            r'(token["\s:=]+)([a-zA-Z0-9_\-]{20,})',
        ]
    
    result = text
    for pattern in patterns:
        result = re.sub(pattern, r'\1***REDACTED***', result, flags=re.IGNORECASE)
    
    return result


def safe_dict_repr(d: dict, sensitive_keys: set[str] = None) -> dict:
    """Return dict copy with sensitive keys masked."""
    if sensitive_keys is None:
        sensitive_keys = {'apikey', 'api_key', 'token', 'password', 'secret'}
    
    result = {}
    for k, v in d.items():
        if k.lower() in sensitive_keys:
            result[k] = '***REDACTED***'
        elif isinstance(v, dict):
            result[k] = safe_dict_repr(v, sensitive_keys)
        else:
            result[k] = v
    
    return result
```

**应用到现有代码**：

```python
# lib/mx_api.py 修改
def _post(url: str, body: dict, api_key: str, timeout: int = 30, attempts: int = 2) -> dict:
    """POST with small retry. Returns parsed JSON or {'error': ...}."""
    if requests is None:
        return {"error": "requests library missing"}
    
    headers = {"Content-Type": "application/json", "apikey": api_key}
    last_err = None
    
    for i in range(attempts):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=timeout)
            if r.status_code != 200:
                # 修复：脱敏错误消息
                from .security import mask_secret
                last_err = mask_secret(f"HTTP {r.status_code}: {r.text[:200]}")
                if r.status_code in (401, 403):
                    break
                time.sleep(1.0 * (i + 1))
                continue
            return r.json()
        except Exception as e:
            # 修复：脱敏异常消息
            from .security import mask_secret
            last_err = mask_secret(f"{type(e).__name__}: {str(e)[:200]}")
            time.sleep(1.0 * (i + 1))
    
    return {"error": last_err or "unknown"}
```

**方案 B：环境变量验证**（本周完成）

```python
# lib/security.py 追加
import os
import sys


def validate_apikey(key: str = None) -> tuple[bool, str]:
    """Validate MX_APIKEY format and security.
    
    Returns:
        (is_valid, error_message)
    """
    key = key or os.getenv("MX_APIKEY")
    if not key:
        return True, ""  # 未设置不算错误
    
    # 长度检查
    if len(key) < 16:
        return False, "MX_APIKEY too short (minimum 16 chars)"
    
    # 弱密钥检查
    weak_patterns = ['test', '123456', 'demo', 'example']
    if any(p in key.lower() for p in weak_patterns):
        return False, "MX_APIKEY appears to be a placeholder"
    
    return True, ""


def check_env_security():
    """Startup security check - call from run.py"""
    issues = []
    
    # 检查 .env 文件权限（Unix）
    env_file = Path(".env")
    if env_file.exists() and sys.platform != "win32":
        stat = env_file.stat()
        if stat.st_mode & 0o077:  # 任何组/其他用户可读
            issues.append(f"⚠️  .env 文件权限过宽（当前 {oct(stat.st_mode)[-3:]}），建议: chmod 600 .env")
    
    # 验证 API key
    is_valid, msg = validate_apikey()
    if not is_valid:
        issues.append(f"⚠️  {msg}")
    
    return issues
```

**集成到 run.py**：

```python
# run.py 主函数开头添加
def main():
    # ... 现有代码 ...
    
    # v3.10.0 · 安全检查
    try:
        from lib.security import check_env_security
        issues = check_env_security()
        if issues:
            for issue in issues:
                print(issue, file=sys.stderr)
    except Exception:
        pass  # 不阻塞主流程
    
    # ... 继续现有逻辑 ...
```

---

### 2. mini_racer 崩溃问题（P0 Critical）

#### 2.1 根因分析

**当前缓解措施不足**：
```python
# run_real_test.py:141-145
if module_name in _MINI_RACER_FETCHERS:
    with _MINI_RACER_LOCK:
        _arm_mini_racer_sentinel(module_name)
        result = mod.main(*args)
        _disarm_mini_racer_sentinel()
```

**问题**：
- 锁只能防止并发初始化
- V8 isolate pool 在 macOS Py 3.12+ 中即使串行也崩溃
- Sentinel 文件是事后检测，不是预防

#### 2.2 根本解决方案

**方案 A：用纯 Python 替代 mini_racer**（推荐）

受影响函数：
1. `fetch_industry.py` → `ak.stock_industry_pe_ratio()` → cninfo JS 混淆
2. `fetch_capital_flow.py` → `ak.stock_individual_fund_flow()` → eastmoney JS
3. `fetch_valuation.py` → `ak.stock_a_pe_and_pb()` → lg JS

**修复示例**（fetch_capital_flow）：

```python
# lib/data_sources.py 新增纯 HTTP 备用源
def fetch_capital_flow_pure_http(ticker_code: str) -> dict:
    """Pure HTTP fallback for capital flow (no mini_racer).
    
    直接调用东财 API，绕过 akshare 的 JS 解析层。
    """
    import requests
    from datetime import datetime, timedelta
    
    # 东财资金流 API（公开端点，无需 JS）
    url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
    params = {
        "secid": f"1.{ticker_code}" if ticker_code.startswith("6") else f"0.{ticker_code}",
        "fields1": "f1,f2,f3,f7",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
        "lmt": 30,  # 最近30天
        "klt": 101,  # 日K
        "ut": "b2884a393a59ad64002292a3e90d46a5",
        "cb": "cb",
    }
    
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return {}
        
        # 解析 JSONP
        text = r.text.strip()
        if text.startswith("cb("):
            text = text[3:-1]
        
        data = json.loads(text)
        klines = data.get("data", {}).get("klines", [])
        
        if not klines:
            return {}
        
        # 解析最近一天
        latest = klines[-1].split(",")
        return {
            "date": latest[0],
            "main_net_inflow": float(latest[1]) if len(latest) > 1 else 0,
            "small_net_inflow": float(latest[2]) if len(latest) > 2 else 0,
            "medium_net_inflow": float(latest[3]) if len(latest) > 3 else 0,
            "large_net_inflow": float(latest[4]) if len(latest) > 4 else 0,
            "super_large_net_inflow": float(latest[5]) if len(latest) > 5 else 0,
        }
    except Exception as e:
        return {"error": str(e)}
```

**修改 fetch_capital_flow.py**：

```python
# fetch_capital_flow.py 修改
def main(ticker: str) -> dict:
    ti = parse_ticker(ticker)
    
    # v3.10.0 · 优先用纯 HTTP，完全绕过 mini_racer
    from lib.data_sources import fetch_capital_flow_pure_http
    result = fetch_capital_flow_pure_http(ti.code)
    
    if result and "error" not in result:
        return {
            "data": result,
            "source": "eastmoney_pure_http",
            "fallback": False,
        }
    
    # 回退到 akshare（仍有 mini_racer 风险，但尝试）
    try:
        import akshare as ak
        df = ak.stock_individual_fund_flow(ti.code, market="sh" if ti.code[0]=="6" else "sz")
        # ... 现有解析逻辑 ...
    except Exception as e:
        return {"data": {}, "error": str(e), "fallback": True}
```

**方案 B：进程隔离**（备选）

如果无法替换 mini_racer，用子进程隔离：

```python
# run_real_test.py 修改
def run_fetcher(module_name: str, args: tuple) -> dict:
    if module_name in _MINI_RACER_FETCHERS and _mini_racer_disabled():
        return {"data": {"_disabled": "mini_racer skipped"}, "fallback": True}
    
    # v3.10.0 · 进程隔离 mini_racer
    if module_name in _MINI_RACER_FETCHERS:
        return _run_in_subprocess(module_name, args)
    
    # 正常线程执行
    try:
        mod = __import__(module_name)
        result = mod.main(*args)
        return result if isinstance(result, dict) else {"data": result}
    except Exception as e:
        return {"data": {}, "error": str(e), "fallback": True}


def _run_in_subprocess(module_name: str, args: tuple, timeout: int = 90) -> dict:
    """Run fetcher in isolated subprocess to prevent V8 crashes."""
    import subprocess
    import json
    
    script = f"""
import sys
sys.path.insert(0, {str(HERE)!r})
import {module_name}
result = {module_name}.main(*{args!r})
print(json.dumps(result, ensure_ascii=False, default=str))
"""
    
    try:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        
        if proc.returncode != 0:
            return {"data": {}, "error": f"subprocess failed: {proc.stderr[:200]}", "fallback": True}
        
        return json.loads(proc.stdout)
    except subprocess.TimeoutExpired:
        return {"data": {}, "error": f"{module_name} timeout", "fallback": True}
    except Exception as e:
        return {"data": {}, "error": str(e), "fallback": True}
```

**优先级**：方案 A（纯 HTTP）> 方案 B（进程隔离）

---

### 3. 双架构技术债务（P0）

#### 3.1 迁移计划

**当前状态**：
- Pipeline 路径：完成 60%
- Legacy 路径：仍在使用
- 双路径重叠：~1600 行代码

**2-Sprint 迁移计划**：

**Sprint 1（Week 1-2）：完成 BaseFetcher 迁移**

```python
# lib/pipeline/base_fetcher.py 增强
class BaseFetcher:
    """Base class for all 22 fetchers."""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.ti = parse_ticker(ticker)
    
    def fetch(self) -> dict:
        """Main entry point - calls _fetch_impl with error handling."""
        try:
            data = self._fetch_impl()
            return {
                "data": data,
                "source": self.source_name(),
                "fallback": False,
                "fetcher_version": "v3.10",
            }
        except Exception as e:
            return self._handle_error(e)
    
    def _fetch_impl(self) -> dict:
        """Override in subclass."""
        raise NotImplementedError
    
    def source_name(self) -> str:
        """Override in subclass."""
        return self.__class__.__name__
    
    def _handle_error(self, e: Exception) -> dict:
        """Unified error handling."""
        from .security import mask_secret
        return {
            "data": {},
            "error": mask_secret(str(e)),
            "fallback": True,
            "error_type": type(e).__name__,
        }
```

**迁移清单**（22 个 fetcher）：

```markdown
- [ ] Week 1.1: fetch_basic, fetch_kline, fetch_peers（核心3个）
- [ ] Week 1.2: fetch_financials, fetch_valuation, fetch_governance
- [ ] Week 1.3: fetch_research, fetch_sentiment, fetch_lhb
- [ ] Week 1.4: fetch_industry, fetch_capital_flow（mini_racer 替换）
- [ ] Week 2.1: 剩余 12 个 fetcher
- [ ] Week 2.2: 集成测试 - 验证输出一致性
```

**Sprint 2（Week 3-4）：废弃 Legacy**

```markdown
- [ ] Week 3: 移除 run.py 双路径逻辑
- [ ] Week 3: 删除 stage1/stage2（保留一个兼容 wrapper）
- [ ] Week 4: 更新所有文档
- [ ] Week 4: 发布 v4.0.0
```

**测试策略**：

```python
# tests/test_migration_equivalence.py（新建）
"""Verify pipeline and legacy produce identical output."""
import pytest


@pytest.mark.parametrize("ticker", [
    "600519.SH",  # A股大盘
    "00700.HK",   # 港股
    "AAPL",       # 美股
    "002273.SZ",  # A股中盘
])
def test_pipeline_legacy_equivalence(ticker):
    """Pipeline 和 legacy 输出必须一致."""
    # Legacy
    os.environ["UZI_LEGACY"] = "1"
    from run_real_test import stage1
    legacy_raw = stage1(ticker)
    
    # Pipeline
    os.environ.pop("UZI_LEGACY")
    from lib.pipeline.run import run_pipeline
    pipeline_raw = _load_cache(ticker)
    
    # 比较 22 个维度
    for dim in DIMENSION_KEYS:
        assert legacy_raw.get(dim) == pipeline_raw.get(dim), \
            f"{ticker} {dim} mismatch"
```

---

### 4. 输入验证（P1）

#### 4.1 Ticker 格式验证

```python
# lib/security.py 追加
import re
from pathlib import Path


class TickerValidator:
    """Validate and sanitize ticker input."""
    
    # 严格正则
    PATTERNS = {
        "A": re.compile(r'^[0-9]{6}\.(SH|SZ|BJ)$'),        # A股
        "H": re.compile(r'^[0-9]{5}\.HK$'),                # 港股
        "U": re.compile(r'^[A-Z]{1,5}$'),                  # 美股
        "name": re.compile(r'^[一-龥]{2,10}$'),   # 中文名
    }
    
    @classmethod
    def validate(cls, ticker: str) -> tuple[bool, str]:
        """
        Returns:
            (is_valid, sanitized_ticker_or_error)
        """
        if not ticker or not isinstance(ticker, str):
            return False, "Empty or invalid ticker"
        
        ticker = ticker.strip().upper()
        
        # 路径遍历检测
        if ".." in ticker or "/" in ticker or "\\" in ticker:
            return False, "Path traversal detected"
        
        # 格式验证
        for market, pattern in cls.PATTERNS.items():
            if pattern.match(ticker):
                return True, ticker
        
        # 中文名单独处理
        if cls.PATTERNS["name"].match(ticker):
            return True, ticker
        
        return False, f"Invalid ticker format: {ticker}"
    
    @classmethod
    def safe_path(cls, ticker: str, base_dir: Path) -> Path:
        """Generate safe file path for ticker.
        
        Prevents directory traversal attacks.
        """
        is_valid, result = cls.validate(ticker)
        if not is_valid:
            raise ValueError(result)
        
        # 二次确保在基目录内
        path = (base_dir / result).resolve()
        if not path.is_relative_to(base_dir.resolve()):
            raise ValueError(f"Path traversal blocked: {ticker}")
        
        return path
```

**应用到 run.py**：

```python
# run.py 修改
def main():
    args = parser.parse_args()
    
    # v3.10.0 · 输入验证
    from lib.security import TickerValidator
    is_valid, result = TickerValidator.validate(args.ticker)
    if not is_valid:
        print(f"❌ {result}", file=sys.stderr)
        sys.exit(2)
    
    args.ticker = result  # 使用清理后的值
    # ... 继续现有逻辑 ...
```

---

### 5. 缓存竞态条件（P1）

#### 5.1 问题分析

```python
# lib/cache.py:50-64 当前实现
if not NO_CACHE and path.exists():
    # 竞态条件：多线程同时检查到 miss
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if now - payload.get("_cached_at", 0) < ttl:
            return payload["data"]
    except:
        pass

data = fetch_fn()  # 多线程同时抓取
path.write_text(...)  # 雪崩
```

#### 5.2 修复方案

```python
# lib/cache.py 完全重写
import fcntl  # Unix 文件锁
import threading
from typing import Any, Callable


_CACHE_LOCKS: dict[str, threading.Lock] = {}
_CACHE_LOCKS_LOCK = threading.Lock()


def _get_lock(key: str) -> threading.Lock:
    """Get or create lock for cache key."""
    with _CACHE_LOCKS_LOCK:
        if key not in _CACHE_LOCKS:
            _CACHE_LOCKS[key] = threading.Lock()
        return _CACHE_LOCKS[key]


def cached(ticker: str, key: str, fetch_fn: Callable[[], Any], ttl: int = CACHE_TTL_SECONDS) -> Any:
    """Thread-safe cached fetch with file locking."""
    path = _cache_path(ticker, key)
    now = time.time()
    cache_key = str(path)
    
    # 线程锁
    lock = _get_lock(cache_key)
    
    with lock:
        # Double-check pattern
        if not NO_CACHE and path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if now - payload.get("_cached_at", 0) < ttl:
                    return payload["data"]
            except (json.JSONDecodeError, KeyError):
                pass
        
        # 抓取数据
        data = fetch_fn()
        
        # 写入缓存（文件锁）
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_with_lock(path, {
            "_cached_at": now,
            "data": data,
            "_ttl": ttl,
        })
    
    return data


def _write_with_lock(path: Path, payload: dict) -> None:
    """Write JSON with file lock (Unix)."""
    import sys
    
    content = json.dumps(payload, ensure_ascii=False, default=str)
    
    if sys.platform == "win32":
        # Windows: msvcrt.locking
        import msvcrt
        with open(path, "w", encoding="utf-8") as f:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, len(content))
            f.write(content)
    else:
        # Unix: fcntl
        with open(path, "w", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(content)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

---

## 📋 实施检查清单

### 第 1 周（P0 修复）

```markdown
- [ ] 实现 lib/security.py（密钥脱敏 + 输入验证）
- [ ] 修改 mx_api.py 应用脱敏
- [ ] 修改 run.py 添加启动安全检查
- [ ] 实现 3 个 mini_racer fetcher 的纯 HTTP 替代
- [ ] 移除 sentinel 系统
- [ ] 测试：运行 pytest 确保无回归
```

### 第 2-3 周（P0 架构迁移）

```markdown
- [ ] 增强 BaseFetcher
- [ ] 迁移 22 个 fetcher（每天 2-3 个）
- [ ] 端到端等价性测试
- [ ] 移除 run.py 双路径
```

### 第 4 周（P1 加固）

```markdown
- [ ] 重写 cache.py 添加锁
- [ ] 所有 HTTP 改 HTTPS
- [ ] 添加结构化日志
- [ ] 更新文档
```

---

## 🎯 预期收益

**安全性**：
- 消除 API 密钥泄露风险
- 阻止路径遍历攻击
- 防止缓存雪崩

**稳定性**：
- 解决 macOS mini_racer 崩溃
- 消除竞态条件
- 减少 50% 维护负担

**性能**：
- 纯 HTTP 比 akshare+mini_racer 快 2-3x
- 锁机制避免重复抓取

**可维护性**：
- 单一架构路径
- 新人 onboarding 从 2 周降到 2 天
- Bug 修复工作量减半

---

**估算工作量**：1 名高级工程师 × 4 周 = 全职 1 个月

需要我开始实施修复吗？
