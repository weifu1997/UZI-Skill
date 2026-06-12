"""Pipeline Fetcher: 相似股票推荐 (Similar Stocks).

维度 ID: 21_similar_stocks
数据来源: 硬编码行业映射 + fetch_basic

功能:
  1. 根据股票行业查找同行业股票
  2. 获取同行业股票实时数据
  3. 计算相似度评分（基于 PE 接近度）
"""
from __future__ import annotations

from typing import Any

from ..base_fetcher import BaseFetcher, FetchContext
from ..schema import DimResult
from ...market_router import TickerInfo

# 导入 Legacy 实现的行业映射表和逻辑
from ...fetch_similar_stocks import INDUSTRY_PEERS, _fetch_peer_basics


class SimilarStocksFetcher(BaseFetcher):
    """相似股票推荐 Fetcher (21_similar_stocks)"""

    dim_id = "21_similar_stocks"
    dim_name_zh = "相似股票"
    dim_name_en = "Similar Stocks"

    # 数据源优先级
    source_priority = ["industry_peers", "fallback"]

    def fetch_data_impl(self, ti: TickerInfo, ctx: FetchContext) -> DimResult:
        """实现数据获取逻辑

        Args:
            ti: Ticker 信息
            ctx: 获取上下文

        Returns:
            DimResult: 标准化结果
        """
        try:
            # 获取股票基本信息以确定行业
            from ... import data_sources as ds

            basic_result = ds.fetch_basic(ti.full)
            if not basic_result or not basic_result.get("data"):
                return DimResult.empty(
                    dim_id=self.dim_id,
                    ticker=ti.full,
                    reason="无法获取股票基本信息"
                )

            basic = basic_result["data"]
            industry = basic.get("industry", "").strip()

            if not industry:
                return DimResult.empty(
                    dim_id=self.dim_id,
                    ticker=ti.full,
                    reason="股票行业信息缺失"
                )

            # 在行业映射表中查找同行业股票
            if industry not in INDUSTRY_PEERS:
                return DimResult.empty(
                    dim_id=self.dim_id,
                    ticker=ti.full,
                    reason=f"行业 {industry} 暂无预设同行业股票"
                )

            peers = INDUSTRY_PEERS[industry]

            # 获取同行业股票的实时数据
            top_n = ctx.extra.get("top_n", 4) if ctx.extra else 4
            peer_basics = _fetch_peer_basics(peers, ti.code, top_n)

            if not peer_basics:
                return DimResult.empty(
                    dim_id=self.dim_id,
                    ticker=ti.full,
                    reason=f"无法获取 {industry} 同行业股票数据"
                )

            # 计算相似度并构建结果
            similar_stocks = []
            self_pe = basic.get("pe_ttm") or 0

            for p in peer_basics:
                # 相似度 = PE 接近度（归一化）
                pe_sim = 0
                if self_pe and p.get("pe_ttm"):
                    pe_ratio = min(self_pe, p["pe_ttm"]) / max(self_pe, p["pe_ttm"])
                    pe_sim = pe_ratio * 100

                # 相似度评分: 75-98 之间
                similarity_score = int(max(75, min(98, pe_sim if pe_sim > 0 else 85)))

                similar_stocks.append({
                    "name": p["name"],
                    "code": p["code"],
                    "price": p.get("price"),
                    "pe_ttm": p.get("pe_ttm"),
                    "market_cap": p.get("market_cap"),
                    "change_pct": p.get("change_pct"),
                    "similarity": f"{similarity_score}%",
                    "reason": f"同属{industry} · PE {p.get('pe_ttm', '—')} · 市值 {p.get('market_cap', '—')}",
                    "url": p.get("url"),
                })

            return DimResult.ok(
                dim_id=self.dim_id,
                ticker=ti.full,
                data={
                    "similar_stocks": similar_stocks,
                    "industry": industry,
                    "peers_attempted": len(peers),
                },
                source="INDUSTRY_PEERS + fetch_basic",
                extra={
                    "peer_count": len(similar_stocks),
                    "industry": industry,
                }
            )

        except Exception as e:
            return DimResult.error(
                dim_id=self.dim_id,
                ticker=ti.full,
                error=str(e),
                source="similar_stocks_fetcher"
            )
