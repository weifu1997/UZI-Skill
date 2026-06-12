#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Load environment variables from .env file

Usage:
1. Create .env file with your configuration
2. Import: from load_env import load_env
3. Call: load_env()
"""
import os
from pathlib import Path


def load_env(env_file: str = ".env") -> bool:
    """Load environment variables from .env file

    Args:
        env_file: Path to .env file, defaults to .env in project root

    Returns:
        bool: True if successfully loaded
    """
    # Find .env file
    env_path = Path(env_file)

    if not env_path.exists():
        # Try project root
        project_root = Path(__file__).parent
        env_path = project_root / ".env"

    if not env_path.exists():
        print(f"Warning: .env file not found: {env_path}")
        print(f"   Create .env file or use environment variables")
        return False

    # Read and parse .env file
    loaded_count = 0

    # P1-1 Fix: Multi-encoding support
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    content = None

    for encoding in encodings:
        try:
            with open(env_path, 'r', encoding=encoding) as f:
                content = f.readlines()
                if encoding != 'utf-8':
                    print(f"Warning: .env file uses {encoding} encoding (UTF-8 recommended)")
                break
        except (UnicodeDecodeError, LookupError):
            continue
        except (PermissionError, OSError, IOError) as e:
            # P1-3 Fix: I/O error handling
            print(f"Error: Cannot read .env file: {e}")
            print(f"   Please check file permissions")
            return False

    if content is None:
        print(f"Error: Cannot decode .env file encoding")
        return False

    for line_num, line in enumerate(content, 1):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue

        # Parse KEY=VALUE
        if '=' not in line:
            continue

        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()

        # P1-2 Fix: Handle inline comments (only for unquoted values)
        if '#' in value and not (value.startswith('"') or value.startswith("'")):
            value = value.split('#')[0].strip()

        # P1-4 Fix: Improved quote handling
        if len(value) >= 2:
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                # Check quote pairing
                if value[0] == value[-1]:
                    value = value[1:-1]
                    # Handle escape characters
                    value = value.replace('\\"', '"').replace("\\'", "'")
                else:
                    # Mismatched quotes warning
                    print(f"Warning: Line {line_num} has mismatched quotes: {line}")

        # Set environment variable (don't override existing)
        if key and not os.environ.get(key):
            os.environ[key] = value
            loaded_count += 1

    print(f"OK: Loaded {loaded_count} environment variables from .env")
    return True


if __name__ == "__main__":
    # Test
    load_env()

    # Show key configuration
    print("\nConfiguration check:")

    url = os.environ.get('TUSHARE_HTTP_URL')
    if url:
        print(f"  OK: TUSHARE_HTTP_URL = {url}")
    else:
        print(f"  Not configured: TUSHARE_HTTP_URL")

    token = os.environ.get('TUSHARE_HTTP_TOKEN')
    if token:
        print(f"  OK: TUSHARE_HTTP_TOKEN = {'*' * min(len(token), 10)}")
    else:
        print(f"  Optional: TUSHARE_HTTP_TOKEN not configured")
