# UZI-Skill 重构路线图

**版本**: v3.10.0 → v4.0.0  
**时间**: 4 周（2026-06-12 至 2026-07-10）  
**目标**: 消除技术债务，提升安全性和稳定性

---

## 📅 时间表

```
Week 1 (Jun 12-18)  🔴 P0 安全修复
Week 2 (Jun 19-25)  🔴 P0 架构迁移 Phase 1
Week 3 (Jun 26-Jul 2) 🔴 P0 架构迁移 Phase 2  
Week 4 (Jul 3-10)   🟡 P1 加固 + 发布
```

---

## Week 1: P0 安全修复

### Day 1-2: 密钥安全加固

**任务**:
- [x] 创建 `lib/security.py`
- [ ] 实现 `mask_secret()` 函数
- [ ] 实现 `TickerValidator` 类
- [ ] 实现 `check_env_security()`
- [ ] 修改 `mx_api.py` 应用脱敏
- [ ] 修改 `run.py` 添加启动检查

**验证**:
```bash
# 测试密钥脱敏
python -c "from lib.security import mask_secret; print(mask_secret('apikey: abc123def456'))"
# 预期: apikey: ***REDACTED***

# 测试 ticker 验证
python -c "from lib.security import TickerValidator; print(TickerValidator.validate('../etc/passwd'))"
# 预期: (False, 'Path traversal detected')
```

**产出**:
- ✅ `skills/deep-analysis/scripts/lib/security.py`（新建）
- ✅ `mx_api.py` 修改
- ✅ `run.py` 修改

---

### Day 3-4: mini_racer 根除

**任务**:
- [ ] 实现 `fetch_capital_flow_pure_http()` in `data_sources.py`
- [ ] 实现 `fetch_industry_pure_http()`
- [ ] 实现 `fetch_valuation_pure_http()`
- [ ] 修改 3 个 fetcher 优先调用纯 HTTP
- [ ] 移除 sentinel 系统代码
- [ ] 移除 `_MINI_RACER_LOCK`

**验证**:
```bash
cd skills/deep-analysis/scripts

# 测试每个 fetcher
python fetch_capital_flow.py 600519.SH
python fetch_industry.py 金融
python fetch_valuation.py 600519.SH

# 确认无 mini_racer 调用
grep -r "mini_racer" . --include="*.py"  # 应无结果
```

**产出**:
- ✅ `lib/data_sources.py` 新增 3 个函数
- ✅ `fetch_capital_flow.py` 修改
- ✅ `fetch_industry.py` 修改
- ✅ `fetch_valuation.py` 修改
- ✅ `run_real_test.py` 删除 mini_racer 相关代码

---

### Day 5: 输入验证强化

**任务**:
- [ ] 在 `run.py` 应用 `TickerValidator`
- [ ] 修改 `cache.py` 使用 `TickerValidator.safe_path()`
- [ ] 修改 `write_task_output()` 防止路径遍历
- [ ] 审计所有 `Path()` 构造调用

**验证**:
```bash
# 测试路径遍历防护
python run.py "../etc/passwd"
# 预期: ❌ Path traversal detected

python run.py "600519.SH; rm -rf /"
# 预期: ❌ Invalid ticker format
```

**产出**:
- ✅ 所有文件路径操作已加固

---

## Week 2-3: 架构统一（22 Fetcher 迁移）

### 迁移优先级

**Phase 1 - 核心数据层** (Week 2):
```
Day 1-2: fetch_basic, fetch_financials, fetch_kline
Day 3:   fetch_valuation, fetch_peers  
Day 4:   fetch_governance, fetch_research
Day 5:   集成测试
```

**Phase 2 - 分析层** (Week 3):
```
Day 1: fetch_sentiment, fetch_lhb, fetch_events
Day 2: fetch_industry, fetch_capital_flow, fetch_macro
Day 3: fetch_chain, fetch_moat, fetch_policy
Day 4: 剩余 7 个
Day 5: 等价性测试 + 移除 legacy
```

### 迁移模板

每个 fetcher 改造步骤：

```python
# 1. 创建 lib/pipeline/fetchers/<name>_fetcher.py
from ..base_fetcher import BaseFetcher

class BasicFetcher(BaseFetcher):
    def _fetch_impl(self) -> dict:
        # 复制原 fetch_basic.py 的 main() 逻辑
        from lib.data_sources import fetch_basic
        return fetch_basic(self.ti)
    
    def source_name(self) -> str:
        return f"akshare:{self.ti.market}"

# 2. 注册到 lib/pipeline/fetchers/registry.py
FETCHER_REGISTRY["0_basic"] = BasicFetcher

# 3. 删除原 fetch_basic.py（或标记 deprecated）

# 4. 测试等价性
pytest tests/test_basic_fetcher.py -v
```

### 等价性测试

```python
# tests/test_fetcher_migration.py
import pytest

TICKERS = ["600519.SH", "00700.HK", "AAPL", "002273.SZ"]

@pytest.mark.parametrize("ticker", TICKERS)
def test_all_fetchers_migrated(ticker):
    """验证所有 22 个 fetcher 已迁移到 pipeline."""
    from lib.pipeline.fetchers.registry import FETCHER_REGISTRY
    
    expected_dims = [
        "0_basic", "1_financials", "2_kline", "3_macro", "4_peers",
        "5_chain", "6_research", "7_industry", "8_materials", "9_futures",
        "10_valuation", "11_governance", "12_capital_flow", "13_policy",
        "14_moat", "15_events", "16_lhb", "17_sentiment", "18_trap",
        "19_contests",
    ]
    
    for dim in expected_dims:
        assert dim in FETCHER_REGISTRY, f"{dim} not migrated"
        
        fetcher = FETCHER_REGISTRY[dim](ticker)
        result = fetcher.fetch()
        
        assert "data" in result
        assert "source" in result
        assert "fallback" in result
```

---

## Week 4: P1 加固 + 发布

### Day 1-2: 缓存加固

**任务**:
- [ ] 重写 `cache.py` 添加线程锁
- [ ] 添加文件锁（Unix fcntl / Windows msvcrt）
- [ ] 性能测试：并发 10 线程抓取同一 ticker

**验证**:
```python
# tests/test_cache_concurrency.py
def test_cache_no_thundering_herd():
    """10个线程同时请求，只触发1次 fetch_fn."""
    call_count = 0
    
    def expensive_fetch():
        nonlocal call_count
        call_count += 1
        time.sleep(0.1)
        return {"test": "data"}
    
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(cached, "TEST", "key", expensive_fetch) for _ in range(10)]
        results = [f.result() for f in futures]
    
    assert call_count == 1  # 只调用一次
    assert all(r == {"test": "data"} for r in results)
```

---

### Day 3: HTTPS 强制

**任务**:
- [ ] 审计所有 `http://` URL
- [ ] 改为 `https://`
- [ ] 添加 `verify=True`（证书验证）
- [ ] 处理证书错误（降级提示，不静默）

**审计命令**:
```bash
grep -rn "http://" skills/deep-analysis/scripts --include="*.py" | grep -v "localhost"
```

**修改示例**:
```python
# Before
r = requests.get("http://www.cninfo.com.cn/api", timeout=10)

# After
r = requests.get("https://www.cninfo.com.cn/api", timeout=10, verify=True)
```

---

### Day 4: 文档更新

**任务**:
- [ ] 更新 `AGENTS.md` 移除 legacy 路径说明
- [ ] 更新 `README.md` 安全最佳实践
- [ ] 创建 `ARCHITECTURE.md` 架构图
- [ ] 更新 `CLAUDE.md` 移除双路径指令
- [ ] 创建 `CHANGELOG-v4.0.0.md`

**ARCHITECTURE.md 内容**:
```markdown
# UZI-Skill 架构（v4.0）

## 数据流

```
用户输入 ticker
    ↓
[run.py] 入口 + 验证
    ↓
[pipeline.collect] 并发抓取 22 维
    ↓ (max_workers=6)
[22 BaseFetcher 子类]
    ↓
[pipeline.score] 评分 + 66 评委
    ↓
[pipeline.synthesize] 生成报告
    ↓
HTML 输出
```

## 模块职责

- `run.py`: CLI 入口，环境检测，参数解析
- `lib/pipeline/run.py`: 编排入口
- `lib/pipeline/collect.py`: 并发数据采集
- `lib/pipeline/score.py`: 评分逻辑
- `lib/pipeline/fetchers/`: 22 个数据源适配器
- `lib/security.py`: 输入验证、密钥脱敏
- `lib/cache.py`: 线程安全缓存
```

---

### Day 5: 发布 v4.0.0

**发布检查清单**:
```markdown
- [ ] 所有测试通过 (pytest -v)
- [ ] 安全审计通过（无密钥泄露）
- [ ] 性能回归测试（不慢于 v3.9）
- [ ] 文档更新完成
- [ ] CHANGELOG 完成
- [ ] 版本号更新（plugin.json, package.json）
- [ ] Git tag: v4.0.0
- [ ] 发布 GitHub Release
- [ ] 通知用户升级
```

**CHANGELOG-v4.0.0.md**:
```markdown
# v4.0.0 (2026-07-10)

## 🚨 Breaking Changes

- 移除 legacy stage1/stage2 路径
- 移除 `UZI_LEGACY=1` 环境变量支持
- mini_racer 依赖完全移除

## ✨ 新特性

- 全新 pipeline 架构（统一代码路径）
- 密钥安全加固（自动脱敏）
- 输入验证（防止路径遍历）
- 线程安全缓存（防止雪崩）

## 🐛 Bug 修复

- 修复 macOS Python 3.12+ mini_racer 崩溃
- 修复并发场景缓存竞态
- 修复 API 密钥可能泄露到日志

## 🔧 内部改进

- 22 个 fetcher 统一为 BaseFetcher 架构
- 所有 HTTP 调用强制 HTTPS
- 代码行数减少 30%（删除重复代码）
- 测试覆盖率提升到 75%

## 📦 升级指南

无需代码修改，直接升级：
\`\`\`bash
git pull origin main
pip install -r requirements.txt --upgrade
\`\`\`

已弃用功能：
- `UZI_LEGACY=1` → 无替代（pipeline 是唯一路径）
- Sentinel 文件系统 → 已移除（不再需要）
```

---

## 🎯 成功指标

**代码质量**:
- [ ] 代码行数减少 ≥25%（从 44k → 33k）
- [ ] 测试覆盖率 ≥75%
- [ ] Mypy 类型检查通过率 ≥90%

**安全性**:
- [ ] 0 个密钥泄露点
- [ ] 100% 输入验证覆盖
- [ ] 0 个路径遍历漏洞

**稳定性**:
- [ ] macOS mini_racer 崩溃率：100% → 0%
- [ ] 缓存竞态条件：存在 → 消除
- [ ] 并发测试通过率：100%

**性能**:
- [ ] 分析速度不低于 v3.9（容忍 ±10%）
- [ ] 缓存命中率 ≥80%
- [ ] 并发效率提升 ≥20%

**可维护性**:
- [ ] 新人 onboarding 时间：2周 → 2天
- [ ] Bug 修复平均工时：减半
- [ ] 代码审查耗时：减少 40%

---

## 🚀 快速开始（给工程师）

### 克隆并创建分支
```bash
git checkout -b refactor/v4.0.0
```

### Week 1 快速入门
```bash
# 创建安全模块
touch skills/deep-analysis/scripts/lib/security.py

# 复制模板代码（见 SECURITY_AUDIT_REPORT.md）
# 实现 mask_secret, TickerValidator, check_env_security

# 测试
pytest tests/test_security.py -v
```

### 每日提交规范
```bash
git commit -m "refactor(security): implement credential masking [Week1-Day1]"
git commit -m "fix(mini_racer): replace with pure HTTP [Week1-Day3]"
git commit -m "feat(pipeline): migrate fetch_basic to BaseFetcher [Week2-Day1]"
```

---

## ❓ FAQ

**Q: 为什么要花 4 周重构？**  
A: 技术债务已累积到影响开发速度。不重构的话，每个新功能都要实现两次，bug 修复也要两次。

**Q: v4.0 会丢失功能吗？**  
A: 不会。所有用户可见功能保持不变，只是内部实现统一。

**Q: 如何回退到 v3.9？**  
A: `git checkout v3.9.0 && pip install -r requirements.txt`

**Q: 测试策略是什么？**  
A: 每个 fetcher 迁移后都有等价性测试（pipeline 输出 = legacy 输出）。

---

## 📞 联系

**技术问题**: 提 GitHub Issue  
**进度跟踪**: 项目看板 → https://github.com/yourorg/UZI-Skill/projects/4  
**Code Review**: 每个 PR 需 2 人 approve  

---

**Last Updated**: 2026-06-12  
**Status**: 🟢 Ready to start
