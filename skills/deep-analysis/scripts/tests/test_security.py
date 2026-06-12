"""Tests for lib/security.py"""
import pytest
from pathlib import Path
from lib.security import (
    mask_secret,
    safe_dict_repr,
    TickerValidator,
    validate_apikey,
)


class TestMaskSecret:
    def test_mask_apikey(self):
        text = "apikey: abc123def456ghi789"
        result = mask_secret(text)
        assert "abc123" not in result
        assert "***REDACTED***" in result

    def test_mask_mx_apikey(self):
        text = "MX_APIKEY=my_secret_key_12345"
        result = mask_secret(text)
        assert "my_secret" not in result
        assert "***REDACTED***" in result

    def test_mask_bearer_token(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = mask_secret(text)
        assert "eyJhbGci" not in result
        assert "***REDACTED***" in result

    def test_no_false_positives(self):
        text = "This is normal text with apikey mentioned"
        result = mask_secret(text)
        assert "apikey mentioned" in result  # 不应该 mask 纯文本


class TestSafeDictRepr:
    def test_mask_sensitive_keys(self):
        d = {"apikey": "secret123", "data": "ok", "token": "xyz"}
        result = safe_dict_repr(d)
        assert result["apikey"] == "***REDACTED***"
        assert result["token"] == "***REDACTED***"
        assert result["data"] == "ok"

    def test_nested_dict(self):
        d = {"outer": {"apikey": "secret"}, "safe": "data"}
        result = safe_dict_repr(d)
        assert result["outer"]["apikey"] == "***REDACTED***"
        assert result["safe"] == "data"


class TestTickerValidator:
    def test_valid_a_share(self):
        is_valid, result = TickerValidator.validate("600519.SH")
        assert is_valid
        assert result == "600519.SH"

    def test_valid_hk_stock(self):
        is_valid, result = TickerValidator.validate("00700.HK")
        assert is_valid
        assert result == "00700.HK"

    def test_valid_us_stock(self):
        is_valid, result = TickerValidator.validate("AAPL")
        assert is_valid
        assert result == "AAPL"

    def test_valid_chinese_name(self):
        is_valid, result = TickerValidator.validate("贵州茅台")
        assert is_valid
        assert result == "贵州茅台"

    def test_path_traversal_blocked(self):
        is_valid, msg = TickerValidator.validate("../etc/passwd")
        assert not is_valid
        assert "traversal" in msg.lower()

    def test_slash_blocked(self):
        is_valid, msg = TickerValidator.validate("600519/SH")
        assert not is_valid

    def test_empty_ticker(self):
        is_valid, msg = TickerValidator.validate("")
        assert not is_valid

    def test_safe_path(self, tmp_path):
        base = tmp_path / "cache"
        base.mkdir()

        result = TickerValidator.safe_path("600519.SH", base)
        assert result.is_relative_to(base)
        assert "600519.SH" in str(result)

    def test_safe_path_blocks_traversal(self, tmp_path):
        base = tmp_path / "cache"
        base.mkdir()

        with pytest.raises(ValueError, match="traversal"):
            TickerValidator.safe_path("../etc/passwd", base)


class TestValidateApikey:
    def test_no_key_is_valid(self, monkeypatch):
        monkeypatch.delenv("MX_APIKEY", raising=False)
        is_valid, msg = validate_apikey()
        assert is_valid

    def test_short_key_invalid(self):
        is_valid, msg = validate_apikey("short")
        assert not is_valid
        assert "too short" in msg.lower()

    def test_placeholder_key_invalid(self):
        is_valid, msg = validate_apikey("test_key_123456789")
        assert not is_valid
        assert "placeholder" in msg.lower()

    def test_valid_key(self):
        is_valid, msg = validate_apikey("a" * 32)
        assert is_valid
        assert msg == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
