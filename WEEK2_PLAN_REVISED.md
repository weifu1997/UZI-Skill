# Week 2 架构统一 - 调整后的实施计划

**开始日期**: 2026-06-12  
**状态**: 🔄 计划调整  
**原因**: 发现 pipeline 架构已完成 90%

---

## 🎊 重大发现

### Pipeline 架构已存在！
在 Week 1 代码审查过程中，我们发现项目**已经实施了 v3.0.0 pipeline 重构**：

✅ **已完成的工作**:
- `lib/pipeline/base_fetcher.py` - 完整的抽象基类
- `lib/pipeline/schema.py` - DimResult/FetcherSpec 数据模型
- `lib/pipeline/validators.py` - 数据验证框架
- `lib/pipeline/collect.py` - 并发数据收集
- `lib/pipeline/fetchers/registry.py` - **20/22 fetcher 已通过 adapter 迁移**
- `lib/pipeline/run.py` - Pipeline 运行入口

### 迁移进度: 20/22 (91%)

**已迁移** (通过 adapter 模式):
1. ✅ 0_basic - 基础信息
2. ✅ 1_financials - 财报三表
3. ✅ 2_kline - K线走势
4. ✅ 3_macro - 宏观经济
5. ✅ 4_peers - 同行对比
6. ✅ 5_chain - 产业链
7. ✅ 6_fund_holders - 基金持仓
8. ✅ 6_research - 研报评级
9. ✅ 7_industry - 行业景气
10. ✅ 8_materials - 原材料
11. ✅ 9_futures - 期货
12. ✅ 10_valuation - 估值
13. ✅ 11_governance - 治理
14. ✅ 12_capital_flow - 资金流
15. ✅ 13_policy - 政策
16. ✅ 14_moat - 护城河
17. ✅ 15_events - 事件驱动
18. ✅ 16_lhb - 龙虎榜
19. ✅ 17_sentiment - 舆情
20. ✅ 18_trap - 杀猪盘
21. ✅ 19_contests - 实盘大赛

**未迁移**:
- ❓ `fetch_similar_stocks.py` - 可能未包含在 20 个维度中

---

## 🎯 调整后的 Week 2 目标

### 原计划（已过时）
> 从零开始创建 BaseFetcher，逐个迁移 22 fetcher

### 新计划（适应现状）

#### 目标 1: 验证与测试 Pipeline 架构
- [ ] 测试 pipeline 是否正常工作
- [ ] 验证 20 个 adapter 的输出一致性
- [ ] 性能基准测试

#### 目标 2: 完成剩余迁移
- [ ] 分析 `fetch_similar_stocks.py` 是否需要迁移
- [ ] 检查是否有其他遗漏的 fetcher

#### 目标 3: 启用 Pipeline 为默认路径
- [ ] 查看 `is_pipeline_enabled()` 逻辑
- [ ] 移除 legacy 路径或标记为废弃
- [ ] 更新 run_real_test.py

#### 目标 4: 清理与文档
- [ ] 删除/废弃 22 个 legacy `fetch_*.py`
- [ ] 更新 AGENTS.md
- [ ] 更新 README.md
- [ ] 创建 v4.0.0 迁移指南

---

## 📅 修订后的 5 天计划

### Day 1 (今天): 验证 Pipeline 架构

**任务**:
1. 测试 pipeline.run_pipeline() 是否工作
2. 验证 adapter 输出 = legacy 输出
3. 性能对比测试

**验证脚本**:
```python
# test_pipeline.py
from lib.pipeline import run_pipeline

# 测试
result = run_pipeline("600519.SH")
print(f"Pipeline 返回了 {len(result)} 个维度")
```

**成功标准**:
- [ ] Pipeline 正常运行
- [ ] 输出格式正确
- [ ] 性能无显著退化

---

### Day 2: 完善与修复

**任务**:
1. 修复发现的问题
2. 添加集成测试
3. 性能优化

---

### Day 3: 清理 Legacy 代码

**任务**:
1. 标记 22 个 `fetch_*.py` 为废弃
2. 移除 `run_real_test.py` 中的 legacy 路径
3. 更新调用点

**影响分析**:
```bash
# 查找所有直接调用 fetch_*.py 的代码
grep -r "import fetch_" --include="*.py"
grep -r "from fetch_" --include="*.py"
```

---

### Day 4: 文档更新

**任务**:
1. 更新 AGENTS.md - 移除 legacy 路径描述
2. 更新 README.md - 说明 v4.0 架构
3. 创建 MIGRATION_V4.md - 迁移指南
4. 更新 REFACTOR_ROADMAP.md

---

### Day 5: 验收与发布

**任务**:
1. 完整回归测试
2. 创建 Week 2 完成报告
3. 提交所有变更
4. 发布 v4.0.0-beta

---

## 🚀 立即开始 Day 1

### 任务清单
- [ ] 创建 `test_pipeline_architecture.py`
- [ ] 运行 pipeline 测试
- [ ] 对比 adapter vs legacy 输出
- [ ] 记录发现的问题

---

**准备好开始测试了吗？** 🎯
