"""Security utilities for UZI-Skill v4.0.0.

Provides:
- Credential masking for logs/errors
- Input validation (ticker format, path traversal)
- Startup security checks
"""
import os
import re
import sys
from pathlib import Path
from typing import Any


def mask_secret(text: str, patterns: list[str] = None) -> str:
    """Mask secrets in text output.

    Args:
        text: Input text that may contain secrets
        patterns: Custom regex patterns (default: common API key formats)

    Returns:
        Text with secrets replaced by '***REDACTED***'

    Example:
        >>> mask_secret('apikey: abc123def456')
        'apikey: ***REDACTED***'
    """
    if patterns is None:
        patterns = [
            r'(apikey["\s:=]+)([a-zA-Z0-9_\-]{16,})',
            r'(MX_APIKEY["\s:=]+)([a-zA-Z0-9_\-]{16,})',
            r'(Authorization["\s:]+Bearer\s+)([a-zA-Z0-9_\-\.]+)',
            r'(token["\s:=]+)([a-zA-Z0-9_\-]{20,})',
            r'(password["\s:=]+)([^\s"\']{6,})',
        ]

    result = text
    for pattern in patterns:
        result = re.sub(pattern, r'\1***REDACTED***', result, flags=re.IGNORECASE)

    return result


def safe_dict_repr(d: dict, sensitive_keys: set[str] = None) -> dict:
    """Return dict copy with sensitive keys masked.

    Args:
        d: Input dictionary
        sensitive_keys: Keys to mask (default: common secret keys)

    Returns:
        New dict with sensitive values replaced

    Example:
        >>> safe_dict_repr({'apikey': 'secret', 'data': 'ok'})
        {'apikey': '***REDACTED***', 'data': 'ok'}
    """
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


class TickerValidator:
    """Validate and sanitize ticker input to prevent attacks."""

    PATTERNS = {
        "A": re.compile(r'^[0-9]{6}\.(SH|SZ|BJ)$'),
        "H": re.compile(r'^[0-9]{5}\.HK$'),
        "U": re.compile(r'^[A-Z]{1,5}$'),
        "name": re.compile(r'^[一-龥]{2,10}$'),
    }

    @classmethod
    def validate(cls, ticker: str) -> tuple[bool, str]:
        """Validate ticker format and security.

        Args:
            ticker: User input ticker

        Returns:
            (is_valid, sanitized_ticker_or_error_message)

        Example:
            >>> TickerValidator.validate('600519.SH')
            (True, '600519.SH')
            >>> TickerValidator.validate('../etc/passwd')
            (False, 'Path traversal detected')
        """
        if not ticker or not isinstance(ticker, str):
            return False, "Empty or invalid ticker"

        ticker = ticker.strip().upper()

        if ".." in ticker or "/" in ticker or "\\" in ticker:
            return False, "Path traversal detected"

        for market, pattern in cls.PATTERNS.items():
            if pattern.match(ticker):
                return True, ticker

        if cls.PATTERNS["name"].match(ticker):
            return True, ticker

        return False, f"Invalid ticker format: {ticker}"

    @classmethod
    def safe_path(cls, ticker: str, base_dir: Path) -> Path:
        """Generate safe file path for ticker.

        Args:
            ticker: Validated ticker
            base_dir: Base directory (must be absolute)

        Returns:
            Safe path within base_dir

        Raises:
            ValueError: If ticker invalid or path traversal detected
        """
        is_valid, result = cls.validate(ticker)
        if not is_valid:
            raise ValueError(result)

        path = (base_dir / result).resolve()
        if not path.is_relative_to(base_dir.resolve()):
            raise ValueError(f"Path traversal blocked: {ticker}")

        return path


def validate_apikey(key: str = None) -> tuple[bool, str]:
    """Validate MX_APIKEY format.

    Args:
        key: API key to validate (default: from env)

    Returns:
        (is_valid, error_message)
    """
    key = key or os.getenv("MX_APIKEY")
    if not key:
        return True, ""

    if len(key) < 16:
        return False, "MX_APIKEY too short (minimum 16 chars)"

    weak_patterns = ['test', '123456', 'demo', 'example']
    if any(p in key.lower() for p in weak_patterns):
        return False, "MX_APIKEY appears to be a placeholder"

    return True, ""


def check_env_security() -> list[str]:
    """Startup security checks.

    Returns:
        List of warning messages (empty if all OK)
    """
    issues = []

    env_file = Path(__file__).parent.parent.parent.parent / ".env"
    if env_file.exists() and sys.platform != "win32":
        stat = env_file.stat()
        if stat.st_mode & 0o077:
            issues.append(
                f"⚠️  .env 文件权限过宽（当前 {oct(stat.st_mode)[-3:]}），"
                f"建议: chmod 600 {env_file}"
            )

    is_valid, msg = validate_apikey()
    if not is_valid:
        issues.append(f"⚠️  {msg}")

    return issues
