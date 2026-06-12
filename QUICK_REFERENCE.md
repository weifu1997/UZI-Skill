# 🚀 UZI-Skill v4.0 重构 - 快速参考卡片

> 打印此卡片贴在工位，随时查看

---

## 📊 项目状态

| 项目 | 当前 v3.9 | 目标 v4.0 |
|------|-----------|-----------|
| 代码行数 | 44,413 | ~33,000 (-25%) |
| 架构路径 | 2 套（pipeline + legacy） | 1 套 |
| macOS 崩溃 | 存在（mini_racer） | 消除 |
| 安全评分 | ⭐⭐⭐☆☆ | ⭐⭐⭐⭐⭐ |
| 测试覆盖 | ~60% | >75% |

---

## 🎯 4 周目标

```
Week 1: P0 安全修复
  ├─ Day 1-2: 密钥脱敏 + 输入验证
  ├─ Day 3-4: mini_racer 替换
  └─ Day 5: 验收测试

Week 2: 核心 fetcher 迁移 (10个)
  ├─ fetch_basic, financials, kline
  ├─ peers, valuation, governance
  └─ research, sentiment, lhb

Week 3: 剩余 fetcher + 清理 (12个)
  ├─ 迁移所有 22 fetcher
  ├─ 移除 legacy 路径
  └─ 等价性测试

Week 4: 发布
  ├─ 文档更新
  ├─ 性能测试
  └─ v4.0.0 发布
```

---

## 🔴 P0 问题（本周必修）

| # | 问题 | 修复时间 | 工具 |
|---|------|----------|------|
| 1 | API密钥泄露 | 2天 | lib/security.py |
| 2 | mini_racer崩溃 | 2天 | 纯HTTP替代 |
| 3 | 输入验证缺失 | 1天 | TickerValidator |

---

## 💻 常用命令

### 测试
```bash
# 安全测试
cd skills/deep-analysis/scripts
pytest tests/test_security.py -v

# 全量测试
pytest tests/ -v --cov=lib

# 单个 fetcher
python fetch_basic.py 600519.SH
```

### 修复
```bash
# 预览修复
./scripts/week1_security_fixes.sh

# 应用修复
./scripts/week1_security_fixes.sh --apply

# 手动修复
python scripts/quick_fix_security.py --apply
```

### 分析
```bash
# 端到端测试
python run.py 600519.SH --no-browser  # A股
python run.py 00700.HK --no-browser   # 港股
python run.py AAPL --no-browser       # 美股
```

---

## 📁 关键文件位置

```
UZI-Skill/
├── SECURITY_AUDIT_REPORT.md      ← 深度分析
├── REFACTOR_ROADMAP.md            ← 路线图
├── IMPLEMENTATION_GUIDE.md        ← 实施指南
├── EXECUTIVE_SUMMARY.md           ← 执行摘要
├── scripts/
│   ├── week1_security_fixes.sh    ← Week 1 自动化
│   └── quick_fix_security.py      ← 快速修复
└── skills/deep-analysis/scripts/
    ├── lib/
    │   ├── security.py            ← 安全工具（新）
    │   ├── pipeline/              ← 新架构
    │   └── data_sources.py        ← 数据源
    ├── tests/
    │   └── test_security.py       ← 安全测试（新）
    ├── fetch_*.py (22个)          ← 数据采集器
    └── run_real_test.py           ← Legacy引擎
```

---

## 🧪 测试清单

### Week 1 验收
- [ ] 所有 pytest 通过 (60+ 测试)
- [ ] 安全模块覆盖率 >90%
- [ ] mini_racer 完全移除
- [ ] 3 个市场均正常
- [ ] 性能无退化 (±10%)

### Week 4 发布
- [ ] 测试覆盖率 >75%
- [ ] 类型检查 mypy 通过
- [ ] 代码质量 pylint >8.0
- [ ] 文档更新完成
- [ ] 版本号更新

---

## 🆘 常见问题

### Q: pytest 找不到模块？
```bash
cd skills/deep-analysis/scripts
export PYTHONPATH=$PWD:$PYTHONPATH
pytest tests/ -v
```

### Q: mini_racer 仍然崩溃？
```bash
export UZI_DISABLE_MINI_RACER=1
python run.py 600519.SH --no-browser
```

### Q: 如何回退到 v3.9？
```bash
git checkout v3.9.0
pip install -r requirements.txt
```

---

## 📞 获取帮助

- **文档**: 见上方关键文件
- **Issue**: GitHub Issues (标签 `refactor-v4`)
- **测试**: `pytest tests/ -v`
- **审查**: Code Review 需 2 人 approve

---

## ✅ 每日检查清单

### 开始工作
- [ ] `git pull origin refactor/v4.0.0`
- [ ] 查看当日任务 (REFACTOR_ROADMAP.md)
- [ ] 运行 `pytest tests/ -q` 确保起点健康

### 结束工作
- [ ] 提交代码 `git commit -m "refactor: [Week#-Day#] ..."`
- [ ] 运行全量测试
- [ ] 更新进度（如有）
- [ ] `git push origin refactor/v4.0.0`

---

## 🎖️ 成功指标

| 指标 | 当前 | 目标 | 进度 |
|------|------|------|------|
| 代码行数 | 44k | 33k | ⬜⬜⬜⬜⬜ |
| 测试覆盖 | 60% | 75% | ⬜⬜⬜⬜⬜ |
| 崩溃率 | 5% | 0% | ⬜⬜⬜⬜⬜ |
| 架构数 | 2 | 1 | ⬜⬜⬜⬜⬜ |
| 安全评分 | 3/5 | 5/5 | ⬜⬜⬜⬜⬜ |

---

## 🔖 快速链接

- [安全审计](SECURITY_AUDIT_REPORT.md)
- [路线图](REFACTOR_ROADMAP.md)
- [实施指南](IMPLEMENTATION_GUIDE.md)
- [测试套件](skills/deep-analysis/scripts/tests/)

---

**打印日期**: 2026-06-12  
**版本**: v4.0.0-refactor  
**状态**: 🟢 Ready to start

*贴在显示器旁，随时参考*
