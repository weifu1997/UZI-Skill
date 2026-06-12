"""Tushare HTTP 代理 Provider · 适配第三方 HTTP 接口.

适用场景：
  · 使用第三方 Tushare 代理服务（HTTP API）
  · 不依赖官方 tushare SDK
  · 纯 HTTP 请求，轻量级

配置：
  1. export TUSHARE_HTTP_URL=http://your-proxy-api.com
  2. export TUSHARE_HTTP_TOKEN=your_token  (可选)
  3. 无需安装 tushare SDK

API 格式要求：
  标准 Tushare HTTP API 格式：
  POST {base_url}/api
  Body: {
    "api_name": "stock_basic",
    "token": "your_token",
    "params": {"ts_code": "600519.SH"},
    "fields": "ts_code,symbol,name,industry"
  }
"""
from __future__ import annotations

import os
import json
from typing import Any

from . import Provider, register, ProviderError

try:
    import requests
    _REQUESTS_OK = True
except ImportError:
    requests = None
    _REQUESTS_OK = False


class _TushareHttpProvider:
    """Tushare HTTP 代理 Provider（纯 HTTP，无需 SDK）"""

    name = "tushare_http"
    requires_key = True
    markets = ("A",)  # A股

    def __init__(self):
        self._base_url = None
        self._token = None

    def is_available(self) -> bool:
        """检查是否配置了 HTTP 代理地址"""
        if not _REQUESTS_OK:
            return False
        url = os.environ.get("TUSHARE_HTTP_URL", "").strip()
        return bool(url)

    def _get_config(self):
        """获取配置"""
        if self._base_url is None:
            self._base_url = os.environ.get("TUSHARE_HTTP_URL", "").strip()
            self._token = os.environ.get("TUSHARE_HTTP_TOKEN", "").strip()

            if not self._base_url:
                raise ProviderError("TUSHARE_HTTP_URL 未配置")

        return self._base_url, self._token

    def _call_api(self, api_name: str, params: dict = None, fields: str = None) -> Any:
        """调用 Tushare HTTP API

        Args:
            api_name: API 名称，如 "stock_basic"
            params: 参数字典
            fields: 返回字段，逗号分隔

        Returns:
            响应数据（通常是 list[dict]）
        """
        base_url, token = self._get_config()

        # 构造请求体
        payload = {
            "api_name": api_name,
            "params": params or {},
        }

        if token:
            payload["token"] = token

        if fields:
            payload["fields"] = fields

        # 发送请求
        try:
            # 支持两种常见格式
            # 格式1: POST /api
            # 格式2: POST / 或其他路径
            url = base_url.rstrip('/') + '/api' if not base_url.endswith('/api') else base_url

            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()

            # 标准 Tushare 响应格式
            if "code" in data:
                if data["code"] != 0:
                    raise ProviderError(f"Tushare API error: {data.get('msg', 'unknown')}")

                # 返回数据
                if "data" in data:
                    items = data["data"].get("items", [])
                    fields_list = data["data"].get("fields", [])

                    # 转换为 dict 列表
                    result = []
                    for item in items:
                        result.append(dict(zip(fields_list, item)))
                    return result

            # 其他格式：直接返回 data
            return data.get("data", [])

        except requests.RequestException as e:
            raise ProviderError(f"Tushare HTTP 请求失败: {e}")
        except Exception as e:
            raise ProviderError(f"Tushare HTTP 调用异常: {e}")

    def _ts_code(self, code: str) -> str:
        """A 股 6 位码 → Tushare 格式 (600519 → 600519.SH)"""
        code6 = code.split(".")[0].zfill(6)
        if code6.startswith(("60", "68", "90", "50", "51", "52", "56", "58", "10", "11")):
            return f"{code6}.SH"
        if code6.startswith(("83", "87", "88", "92")):
            return f"{code6}.BJ"
        return f"{code6}.SZ"

    # ═══════════════════════════════════════════════════════════
    # Provider 接口实现
    # ═══════════════════════════════════════════════════════════

    def fetch_basic_a(self, code: str) -> dict:
        """stock_basic · 基础信息"""
        try:
            ts_code = self._ts_code(code)
            result = self._call_api(
                "stock_basic",
                params={"ts_code": ts_code},
                fields="ts_code,symbol,name,industry,market,list_date"
            )

            if not result:
                raise ProviderError("stock_basic 返回空")

            return {"ok": True, "raw": result[0]}

        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"fetch_basic_a: {e}")

    def fetch_financials_a(self, code: str, years: int = 5) -> dict:
        """利润表 + 资产负债表 + 现金流表"""
        try:
            ts_code = self._ts_code(code)
            limit = years * 4  # 每年4个季度

            # 利润表
            income = self._call_api(
                "income",
                params={"ts_code": ts_code, "limit": limit}
            )

            # 资产负债表
            balance = self._call_api(
                "balancesheet",
                params={"ts_code": ts_code, "limit": limit}
            )

            # 现金流表
            cashflow = self._call_api(
                "cashflow",
                params={"ts_code": ts_code, "limit": limit}
            )

            return {
                "ok": True,
                "income": income or [],
                "balance": balance or [],
                "cashflow": cashflow or [],
            }

        except Exception as e:
            raise ProviderError(f"fetch_financials_a: {e}")

    def fetch_kline_a(self, code: str, period: str = "daily", start: str = "20200101", adjust: str = "qfq") -> list[dict]:
        """K线数据"""
        try:
            ts_code = self._ts_code(code)

            # 获取日线数据
            df_data = self._call_api(
                "daily",
                params={"ts_code": ts_code, "start_date": start}
            )

            if not df_data:
                raise ProviderError("daily 返回空")

            # 前复权处理
            if adjust == "qfq":
                try:
                    adj_data = self._call_api(
                        "adj_factor",
                        params={"ts_code": ts_code, "start_date": start}
                    )

                    if adj_data:
                        # 简化处理：取最新复权因子
                        latest_factor = float(adj_data[0].get("adj_factor", 1.0))

                        # 构建复权因子字典
                        adj_map = {item["trade_date"]: float(item.get("adj_factor", 1.0)) for item in adj_data}

                        # 应用复权
                        for row in df_data:
                            trade_date = row.get("trade_date")
                            factor = adj_map.get(trade_date, 1.0)
                            ratio = factor / latest_factor

                            for col in ("open", "high", "low", "close", "pre_close"):
                                if col in row and row[col]:
                                    row[col] = float(row[col]) * ratio
                except:
                    pass  # 复权失败，返回未复权数据

            # 转换为标准格式
            result = []
            for row in sorted(df_data, key=lambda x: x.get("trade_date", "")):
                trade_date = str(row.get("trade_date", ""))
                result.append({
                    "日期": f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:8]}",
                    "开盘": float(row.get("open", 0) or 0),
                    "收盘": float(row.get("close", 0) or 0),
                    "最高": float(row.get("high", 0) or 0),
                    "最低": float(row.get("low", 0) or 0),
                    "成交量": float(row.get("vol", 0) or 0),
                    "成交额": float(row.get("amount", 0) or 0),
                    "涨跌幅": float(row.get("pct_chg", 0) or 0),
                })

            return result

        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"fetch_kline_a: {e}")

    def fetch_top10_holders(self, code: str) -> list[dict]:
        """前十大流通股东"""
        try:
            ts_code = self._ts_code(code)
            result = self._call_api(
                "top10_floatholders",
                params={"ts_code": ts_code}
            )
            return result or []

        except Exception as e:
            raise ProviderError(f"fetch_top10_holders: {e}")

    def fetch_top_list(self, code: str, start: str, end: str) -> list[dict]:
        """龙虎榜"""
        try:
            ts_code = self._ts_code(code)
            result = self._call_api(
                "top_list",
                params={"ts_code": ts_code, "start_date": start, "end_date": end}
            )
            return result or []

        except Exception as e:
            raise ProviderError(f"fetch_top_list: {e}")

    def fetch_hsgt_top10(self, code: str, start: str, end: str) -> list[dict]:
        """北向资金持股"""
        try:
            ts_code = self._ts_code(code)
            result = self._call_api(
                "hsgt_top10",
                params={"ts_code": ts_code, "start_date": start, "end_date": end}
            )
            return result or []

        except Exception as e:
            raise ProviderError(f"fetch_hsgt_top10: {e}")

    def fetch_valuation_a(self, code: str) -> dict:
        """估值指标 · v4.0.0 新增 · 每日基本面数据"""
        try:
            ts_code = self._ts_code(code)
            result = self._call_api(
                "daily_basic",
                params={"ts_code": ts_code},
                fields="ts_code,trade_date,turnover_rate,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,total_share,float_share,free_share,total_mv,circ_mv"
            )

            if not result:
                raise ProviderError("daily_basic 返回空")

            # 取最新一条
            return {"ok": True, "data": result[0]}

        except ProviderError:
            raise
        except Exception as e:
            raise ProviderError(f"fetch_valuation_a: {e}")

    def fetch_research_reports_a(self, code: str, start: str = "", end: str = "") -> list[dict]:
        """研报评级 · v4.0.0 新增 · 机构研报"""
        try:
            ts_code = self._ts_code(code)
            params = {"ts_code": ts_code}

            if start:
                params["start_date"] = start
            if end:
                params["end_date"] = end

            result = self._call_api(
                "report_rc",
                params=params,
                fields="ts_code,ann_date,title,report_type,rating,analyst"
            )

            return result or []

        except Exception as e:
            raise ProviderError(f"fetch_research_reports_a: {e}")

    def fetch_moneyflow_a(self, code: str, start: str = "", end: str = "") -> list[dict]:
        """资金流向详情 · v4.0.0 新增 · 大单中单小单"""
        try:
            ts_code = self._ts_code(code)
            params = {"ts_code": ts_code}

            if start:
                params["start_date"] = start
            if end:
                params["end_date"] = end

            result = self._call_api(
                "moneyflow",
                params=params,
                fields="ts_code,trade_date,buy_sm_amount,sell_sm_amount,buy_md_amount,sell_md_amount,buy_lg_amount,sell_lg_amount,buy_elg_amount,sell_elg_amount,net_mf_amount"
            )

            return result or []

        except Exception as e:
            raise ProviderError(f"fetch_moneyflow_a: {e}")


# 注册 Provider
if _REQUESTS_OK:
    provider = _TushareHttpProvider()
    register(provider)
