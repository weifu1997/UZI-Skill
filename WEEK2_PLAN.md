# Week 2 架构统一实施计划

**开始日期**: 2026-06-12  
**目标**: 迁移 22 个 fetcher 到统一的 BaseFetcher 架构  
**预计时间**: 5 天

---

## 🎯 Week 2 目标

### 核心目标
1. 创建 BaseFetcher 抽象基类
2. 迁移 10 个核心 fetcher（Week 2 重点）
3. 建立等价性测试框架
4. 确保输出完全一致

### 成功标准
- ✅ 所有迁移的 fetcher 通过等价性测试
- ✅ 代码重复率降低 40%
- ✅ 统一错误处理
- ✅ 性能无退化（±10%）

---

## 📅 5 天实施计划

### Day 1 (今天): BaseFetcher + 核心 2 个
**任务**:
1. 创建 `lib/pipeline/base_fetcher.py`
2. 创建 fetcher 注册表
3. 迁移 `fetch_basic` → `BasicFetcher`
4. 迁移 `fetch_financials` → `FinancialsFetcher`

**验证**:
- [ ] BasicFetcher 输出 = fetch_basic 输出
- [ ] FinancialsFetcher 输出 = fetch_financials 输出
- [ ] 单元测试通过

---

### Day 2: 行情与对比
**任务**:
1. 迁移 `fetch_kline` → `KlineFetcher`
2. 迁移 `fetch_peers` → `PeersFetcher`
3. 迁移 `fetch_macro` → `MacroFetcher`

**验证**:
- [ ] 3 个 fetcher 等价性测试通过

---

### Day 3: 估值与治理
**任务**:
1. 迁移 `fetch_valuation` → `ValuationFetcher`
2. 迁移 `fetch_governance` → `GovernanceFetcher`
3. 迁移 `fetch_research` → `ResearchFetcher`

**验证**:
- [ ] 3 个 fetcher 等价性测试通过

---

### Day 4: 分析维度
**任务**:
1. 迁移 `fetch_sentiment` → `SentimentFetcher`
2. 迁移 `fetch_lhb` → `LhbFetcher`
3. 迁移 `fetch_events` → `EventsFetcher`

**验证**:
- [ ] 10 个 fetcher 全部迁移完成
- [ ] 集成测试通过

---

### Day 5: 验收与文档
**任务**:
1. 完整回归测试
2. 性能基准测试
3. 更新文档
4. Week 2 总结报告

---

## 🏗️ 架构设计

### BaseFetcher 接口
```python
class BaseFetcher(ABC):
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.ti = parse_ticker(ticker)
    
    @abstractmethod
    def _fetch_impl(self) -> dict:
        """子类实现具体抓取逻辑"""
        pass
    
    def fetch(self) -> dict:
        """统一入口，包含错误处理、缓存、日志"""
        try:
            data = self._fetch_impl()
            return {
                "data": data,
                "source": self.source_name(),
                "fallback": False,
            }
        except Exception as e:
            return self._handle_error(e)
    
    def source_name(self) -> str:
        return self.__class__.__name__
    
    def _handle_error(self, e: Exception) -> dict:
        from .security import mask_secret
        return {
            "data": {},
            "error": mask_secret(str(e)),
            "fallback": True,
        }
```

### 目录结构
```
lib/pipeline/
├── __init__.py
├── base_fetcher.py          # 抽象基类
├── fetchers/
│   ├── __init__.py
│   ├── basic_fetcher.py     # Dimension 0
│   ├── financials_fetcher.py # Dimension 1
│   ├── kline_fetcher.py     # Dimension 2
│   └── ...
└── registry.py              # Fetcher 注册表
```

---

## 🧪 测试策略

### 等价性测试模板
```python
def test_basic_fetcher_equivalence():
    """验证 BasicFetcher 输出 = fetch_basic 输出"""
    ticker = "600519.SH"
    
    # Legacy
    from fetch_basic import main as legacy_main
    legacy_output = legacy_main(ticker)
    
    # Pipeline
    from lib.pipeline.fetchers import BasicFetcher
    pipeline_output = BasicFetcher(ticker).fetch()
    
    # 比较
    assert legacy_output["data"] == pipeline_output["data"]
    assert legacy_output["source"] == pipeline_output["source"]
```

---

## 📊 进度追踪

| Fetcher | 难度 | 状态 | 负责人 | 完成时间 |
|---------|------|------|--------|----------|
| basic | 简单 | 🔴 待开始 | - | - |
| financials | 中等 | 🔴 待开始 | - | - |
| kline | 简单 | 🔴 待开始 | - | - |
| peers | 中等 | 🔴 待开始 | - | - |
| macro | 中等 | 🔴 待开始 | - | - |
| valuation | 复杂 | 🔴 待开始 | - | - |
| governance | 中等 | 🔴 待开始 | - | - |
| research | 中等 | 🔴 待开始 | - | - |
| sentiment | 简单 | 🔴 待开始 | - | - |
| lhb | 中等 | 🔴 待开始 | - | - |

---

## 🎯 Day 1 具体任务

### 任务 1: 创建 BaseFetcher (30 分钟)
- [ ] 创建目录结构
- [ ] 实现 base_fetcher.py
- [ ] 编写单元测试

### 任务 2: 迁移 BasicFetcher (1 小时)
- [ ] 复制 fetch_basic.py 逻辑
- [ ] 适配 BaseFetcher 接口
- [ ] 等价性测试

### 任务 3: 迁移 FinancialsFetcher (1.5 小时)
- [ ] 复制 fetch_financials.py 逻辑
- [ ] 适配 BaseFetcher 接口
- [ ] 等价性测试

### 任务 4: 验收 (30 分钟)
- [ ] 运行全量测试
- [ ] 提交代码
- [ ] 更新进度

---

## 🚀 立即开始

准备好了吗？让我们从创建 BaseFetcher 开始！

输入 "开始" 继续...
