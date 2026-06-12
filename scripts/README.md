# UZI-Skill 脚本目录

本目录包含配置工具和测试脚本。

## 📜 脚本列表

### 配置工具

1. **config_tushare.ps1** - Tushare HTTP 代理配置工具 (PowerShell)
   - 交互式配置向导
   - 支持临时/永久配置
   - 自动测试验证

2. **test_tushare_config.py** - Tushare 配置测试脚本
   - 环境变量检查
   - Provider 验证
   - API 调用测试

### 安装脚本

3. **install-hermes.sh** - Hermes 依赖安装脚本
   - 自动安装依赖
   - 平台检测

4. **setup.sh** - 项目初始化脚本
   - 环境设置
   - 依赖检查

## 📝 使用方法

### 配置 Tushare HTTP

**Windows (PowerShell)**:
```powershell
.\scripts\config_tushare.ps1
```

**测试配置**:
```bash
python scripts/test_tushare_config.py
```

## 🔙 返回

- [项目主页](../README.md)
