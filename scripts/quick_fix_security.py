#!/usr/bin/env python3
"""Quick fix script for P0 security issues.

Usage:
    python scripts/quick_fix_security.py --dry-run  # 预览修改
    python scripts/quick_fix_security.py --apply    # 应用修改
"""
import argparse
import re
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent


def patch_mx_api():
    """Patch lib/mx_api.py to mask secrets in error messages."""
    file = REPO_ROOT / "skills/deep-analysis/scripts/lib/mx_api.py"
    content = file.read_text(encoding="utf-8")

    # 在 _post 函数中添加 mask_secret
    old_pattern = r'last_err = f"HTTP {r\.status_code}: {r\.text\[:200\]}"'
    new_code = '''from .security import mask_secret
                last_err = mask_secret(f"HTTP {r.status_code}: {r.text[:200]}")'''

    if "from .security import mask_secret" not in content:
        # 在 _post 函数内第一次使用前导入
        content = re.sub(
            r'(def _post\(.*?\):.*?last_err = None)',
            r'\1\n    from lib.security import mask_secret',
            content,
            flags=re.DOTALL,
            count=1
        )

        # 替换错误消息
        content = content.replace(
            'last_err = f"HTTP {r.status_code}: {r.text[:200]}"',
            'last_err = mask_secret(f"HTTP {r.status_code}: {r.text[:200]}")'
        )
        content = content.replace(
            'last_err = f"{type(e).__name__}: {str(e)[:200]}"',
            'last_err = mask_secret(f"{type(e).__name__}: {str(e)[:200]}")'
        )

    return file, content


def patch_run_py():
    """Patch run.py to add security checks."""
    file = REPO_ROOT / "run.py"
    content = file.read_text(encoding="utf-8")

    # 在 main 函数开头添加安全检查
    if "check_env_security" not in content:
        # 找到 main() 函数中 parser.parse_args() 后插入
        insert_code = '''
    # v3.10.0 · 安全检查
    try:
        sys.path.insert(0, str(SCRIPTS_DIR / "lib"))
        from security import check_env_security, TickerValidator
        issues = check_env_security()
        if issues:
            for issue in issues:
                print(issue, file=sys.stderr)

        # 输入验证
        is_valid, result = TickerValidator.validate(args.ticker)
        if not is_valid:
            print(f"❌ {result}", file=sys.stderr)
            sys.exit(2)
        args.ticker = result
    except Exception as e:
        print(f"⚠️  安全检查失败（继续）: {e}", file=sys.stderr)
'''

        content = content.replace(
            '    args = parser.parse_args()',
            f'    args = parser.parse_args(){insert_code}'
        )

    return file, content


def patch_cache_py():
    """Patch lib/cache.py for thread-safe operations."""
    file = REPO_ROOT / "skills/deep-analysis/scripts/lib/cache.py"
    content = file.read_text(encoding="utf-8")

    if "_CACHE_LOCKS" not in content:
        # 在文件顶部添加锁机制
        imports_section = '''from __future__ import annotations

import hashlib
import json
import os
import time
import threading
from pathlib import Path
from typing import Any, Callable
'''

        locks_code = '''
# Thread-safe cache locks
_CACHE_LOCKS: dict[str, threading.Lock] = {}
_CACHE_LOCKS_LOCK = threading.Lock()


def _get_lock(key: str) -> threading.Lock:
    """Get or create lock for cache key."""
    with _CACHE_LOCKS_LOCK:
        if key not in _CACHE_LOCKS:
            _CACHE_LOCKS[key] = threading.Lock()
        return _CACHE_LOCKS[key]
'''

        # 替换导入部分
        content = re.sub(
            r'from __future__ import annotations.*?from typing import Any, Callable',
            imports_section + locks_code,
            content,
            flags=re.DOTALL,
            count=1
        )

        # 修改 cached 函数添加锁
        old_func = r'def cached\(ticker: str, key: str, fetch_fn: Callable\[\[\], Any\], ttl: int = CACHE_TTL_SECONDS\) -> Any:.*?return data'

        new_func = '''def cached(ticker: str, key: str, fetch_fn: Callable[[], Any], ttl: int = CACHE_TTL_SECONDS) -> Any:
    """Return cached value if fresh, else call fetch_fn and store. Thread-safe."""
    path = _cache_path(ticker, key)
    now = time.time()
    cache_key = str(path)

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

        data = fetch_fn()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"_cached_at": now, "data": data, "_ttl": ttl}, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    return data'''

        content = re.sub(old_func, new_func, content, flags=re.DOTALL, count=1)

    return file, content


def apply_patches(dry_run=True):
    """Apply all patches."""
    patches = [
        ("mx_api.py", patch_mx_api),
        ("run.py", patch_run_py),
        ("cache.py", patch_cache_py),
    ]

    print("🔧 UZI-Skill P0 安全修复\n")

    for name, patch_fn in patches:
        print(f"{'[DRY RUN] ' if dry_run else '[APPLY] '}修复 {name}...", end=" ")
        try:
            file, new_content = patch_fn()

            if not dry_run:
                # 备份原文件
                backup = file.with_suffix(file.suffix + ".bak")
                file.rename(backup)

                # 写入新内容
                file.write_text(new_content, encoding="utf-8")
                print(f"✅ (备份: {backup.name})")
            else:
                # 计算变化行数
                old_lines = file.read_text(encoding="utf-8").count('\n')
                new_lines = new_content.count('\n')
                diff = abs(new_lines - old_lines)
                print(f"✅ (将修改 ~{diff} 行)")

        except Exception as e:
            print(f"❌ 失败: {e}")

    print("\n📋 修复摘要:")
    print("  - mx_api.py: API 密钥脱敏")
    print("  - run.py: 输入验证 + 安全检查")
    print("  - cache.py: 线程安全锁")

    if dry_run:
        print("\n💡 运行 'python scripts/quick_fix_security.py --apply' 应用修改")
    else:
        print("\n✅ 修复已应用！")
        print("\n🧪 运行测试:")
        print("  cd skills/deep-analysis/scripts")
        print("  pytest tests/test_security.py -v")


def main():
    parser = argparse.ArgumentParser(description="Quick fix P0 security issues")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview changes without applying (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply changes to files")
    args = parser.parse_args()

    dry_run = not args.apply
    apply_patches(dry_run=dry_run)


if __name__ == "__main__":
    main()
