#!/usr/bin/env python3
"""
加载 .env 文件中的环境变量

使用方法:
1. 创建 .env 文件，填入配置
2. 在 Python 脚本开头导入: from load_env import load_env
3. 调用: load_env()
"""
import os
from pathlib import Path


def load_env(env_file: str = ".env") -> bool:
    """从 .env 文件加载环境变量

    Args:
        env_file: .env 文件路径，默认为项目根目录的 .env

    Returns:
        bool: 是否成功加载
    """
    # 查找 .env 文件
    env_path = Path(env_file)

    if not env_path.exists():
        # 尝试在项目根目录查找
        project_root = Path(__file__).parent
        env_path = project_root / ".env"

    if not env_path.exists():
        print(f"⚠️  .env 文件未找到: {env_path}")
        print(f"   创建 .env 文件或使用环境变量配置")
        return False

    # 读取并解析 .env 文件
    loaded_count = 0
    with open(env_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue

            # 解析 KEY=VALUE
            if '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            # 移除引号
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]

            # 设置环境变量（不覆盖已存在的）
            if key and not os.environ.get(key):
                os.environ[key] = value
                loaded_count += 1

    print(f"✅ 已从 .env 加载 {loaded_count} 个环境变量")
    return True


if __name__ == "__main__":
    # 测试
    load_env()

    # 显示关键配置
    print("\n配置检查:")

    url = os.environ.get('TUSHARE_HTTP_URL')
    if url:
        print(f"  ✅ TUSHARE_HTTP_URL = {url}")
    else:
        print(f"  ❌ TUSHARE_HTTP_URL 未配置")

    token = os.environ.get('TUSHARE_HTTP_TOKEN')
    if token:
        print(f"  ✅ TUSHARE_HTTP_TOKEN = {'*' * min(len(token), 10)}")
    else:
        print(f"  ⏸️  TUSHARE_HTTP_TOKEN 未配置（可选）")
