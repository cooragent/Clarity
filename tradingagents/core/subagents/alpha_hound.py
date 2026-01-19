"""Alpha Hound SubAgent - Screens and filters stocks based on complex conditions."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..base_agent import AgentResult, BaseSubAgent, ToolDefinition
from ..config import AgentConfig, AgentRole, TaskContext

logger = logging.getLogger(__name__)


@dataclass
class ScreeningCriteria:
    """Criteria for stock screening."""

    # Market cap filters
    min_market_cap: float | None = None
    max_market_cap: float | None = None

    # Valuation filters
    max_pe_ratio: float | None = None
    min_pe_ratio: float | None = None
    max_pb_ratio: float | None = None
    max_ps_ratio: float | None = None

    # Growth filters
    min_revenue_growth: float | None = None
    min_earnings_growth: float | None = None

    # Dividend filters
    min_dividend_yield: float | None = None
    max_dividend_yield: float | None = None

    # Technical filters
    above_sma_50: bool | None = None
    above_sma_200: bool | None = None
    rsi_oversold: bool | None = None  # RSI < 30
    rsi_overbought: bool | None = None  # RSI > 70

    # Sector filters
    sectors: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)

    # Custom criteria
    custom_query: str = ""


class AlphaHound(BaseSubAgent):
    """Screens and filters stocks based on complex conditions to find
    alpha-generating opportunities.
    """

    role = AgentRole.ALPHA_HOUND
    name = "AlphaHound"
    description = (
        "Screens and filters stocks based on complex conditions including "
        "fundamental metrics, technical indicators, and market conditions. "
        "Uses FinnHub API, web search, and financial databases to identify "
        "stocks matching specific criteria."
    )

    def _setup_tools(self) -> None:
        """Setup stock screening tools."""
        self.tools = [
            ToolDefinition(
                name="screen_by_fundamentals",
                description="Screen stocks by fundamental metrics (PE, PB, market cap, etc.)",
                parameters={
                    "type": "object",
                    "properties": {
                        "min_market_cap": {
                            "type": "number",
                            "description": "Minimum market cap in billions",
                        },
                        "max_pe": {
                            "type": "number",
                            "description": "Maximum P/E ratio",
                        },
                        "min_dividend_yield": {
                            "type": "number",
                            "description": "Minimum dividend yield percentage",
                        },
                        "sector": {
                            "type": "string",
                            "description": "Sector to filter (e.g., Technology, Healthcare)",
                        },
                    },
                },
                handler=self._screen_by_fundamentals,
            ),
            ToolDefinition(
                name="screen_by_technicals",
                description="Screen stocks by technical indicators",
                parameters={
                    "type": "object",
                    "properties": {
                        "above_sma_50": {
                            "type": "boolean",
                            "description": "Stock price above 50-day SMA",
                        },
                        "above_sma_200": {
                            "type": "boolean",
                            "description": "Stock price above 200-day SMA",
                        },
                        "rsi_range": {
                            "type": "string",
                            "enum": ["oversold", "neutral", "overbought"],
                            "description": "RSI condition",
                        },
                    },
                },
                handler=self._screen_by_technicals,
            ),
            ToolDefinition(
                name="web_search_screener",
                description="Search web for stock screening results",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Complex screening query",
                        },
                    },
                    "required": ["query"],
                },
                handler=self._web_search_screener,
            ),
            ToolDefinition(
                name="get_finnhub_stock_list",
                description="Get list of stocks from FinnHub API",
                parameters={
                    "type": "object",
                    "properties": {
                        "exchange": {
                            "type": "string",
                            "description": "Stock exchange (e.g., US, NASDAQ)",
                        },
                    },
                },
                handler=self._get_finnhub_stock_list,
            ),
            ToolDefinition(
                name="analyze_screened_stocks",
                description="Perform quick analysis on screened stocks",
                parameters={
                    "type": "object",
                    "properties": {
                        "tickers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of stock tickers to analyze",
                        },
                    },
                    "required": ["tickers"],
                },
                handler=self._analyze_screened_stocks,
            ),
        ]

    async def execute(self, context: TaskContext, **kwargs) -> AgentResult:
        """Execute stock screening based on the given criteria."""
        criteria_str = context.target  # Contains screening criteria as string
        trade_date = context.trade_date

        logger.info(f"AlphaHound: Screening stocks with criteria: {criteria_str}")

        collected_data = {}
        errors = []

        # Parse and execute screening based on criteria
        try:
            # Use web search to find matching stocks
            web_results = await self._web_search_screener(
                f"stock screener {criteria_str} 2025"
            )
            collected_data["web_screening"] = web_results
        except Exception as e:
            errors.append(f"Web screening error: {e}")
            logger.error(f"Error in web screening: {e}")

        # If specific conditions are mentioned, do targeted searches
        keywords = criteria_str.lower()

        if "value" in keywords or "pe" in keywords or "undervalued" in keywords:
            try:
                value_results = await self._screen_by_fundamentals(
                    max_pe=15, min_market_cap=1
                )
                collected_data["value_screen"] = value_results
            except Exception as e:
                errors.append(f"Value screening error: {e}")

        if "growth" in keywords:
            try:
                growth_results = await self._web_search_screener(
                    "high growth stocks revenue growth earnings growth 2025"
                )
                collected_data["growth_screen"] = growth_results
            except Exception as e:
                errors.append(f"Growth screening error: {e}")

        if "dividend" in keywords:
            try:
                dividend_results = await self._web_search_screener(
                    "high dividend yield stocks safe dividend 2025"
                )
                collected_data["dividend_screen"] = dividend_results
            except Exception as e:
                errors.append(f"Dividend screening error: {e}")

        if "momentum" in keywords or "technical" in keywords:
            try:
                momentum_results = await self._screen_by_technicals(
                    above_sma_50=True, above_sma_200=True
                )
                collected_data["momentum_screen"] = momentum_results
            except Exception as e:
                errors.append(f"Momentum screening error: {e}")

        # Generate report
        report = self._generate_report(criteria_str, trade_date, collected_data)

        return AgentResult(
            success=len(collected_data) > 0,
            output=report,
            report=report,
            errors=errors,
            metadata={"criteria": criteria_str, "trade_date": trade_date},
        )

    async def _screen_by_fundamentals(
        self,
        min_market_cap: float | None = None,
        max_pe: float | None = None,
        min_dividend_yield: float | None = None,
        sector: str | None = None,
    ) -> str:
        """Screen stocks by fundamental criteria using web search."""
        query_parts = ["stock screener"]

        if min_market_cap:
            query_parts.append(f"market cap over {min_market_cap} billion")
        if max_pe:
            query_parts.append(f"PE ratio under {max_pe}")
        if min_dividend_yield:
            query_parts.append(f"dividend yield over {min_dividend_yield}%")
        if sector:
            query_parts.append(f"{sector} sector")

        query = " ".join(query_parts)
        return await self._web_search_screener(query)

    async def _screen_by_technicals(
        self,
        above_sma_50: bool | None = None,
        above_sma_200: bool | None = None,
        rsi_range: str | None = None,
    ) -> str:
        """Screen stocks by technical criteria using web search."""
        query_parts = ["stocks"]

        if above_sma_50:
            query_parts.append("above 50 day moving average")
        if above_sma_200:
            query_parts.append("above 200 day moving average")
        if rsi_range == "oversold":
            query_parts.append("RSI oversold")
        elif rsi_range == "overbought":
            query_parts.append("RSI overbought")

        query = " ".join(query_parts) + " screener 2025"
        return await self._web_search_screener(query)

    async def _web_search_screener(self, query: str) -> str:
        """Search web for stock screening results."""
        import os
        import httpx

        serper_api_key = self.config.serper_api_key or os.getenv("SERPER_API_KEY")
        if not serper_api_key:
            return "SERPER_API_KEY not configured"

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": 15}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic", [])[:15]:
            results.append(
                f"**{item.get('title', '')}**\n"
                f"{item.get('snippet', '')}\n"
                f"Source: {item.get('link', '')}\n"
            )

        return f"## Screening Results for: {query}\n\n" + "\n\n".join(results)

    async def _get_finnhub_stock_list(self, exchange: str = "US") -> str:
        """Get list of stocks from FinnHub."""
        import os
        import httpx

        finnhub_key = self.config.finnhub_api_key or os.getenv("FINNHUB_API_KEY")
        if not finnhub_key:
            return "FINNHUB_API_KEY not configured"

        url = f"https://finnhub.io/api/v1/stock/symbol?exchange={exchange}&token={finnhub_key}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        # Return first 50 stocks as sample
        sample = data[:50] if len(data) > 50 else data
        stocks = [f"{s.get('symbol', '')}: {s.get('description', '')}" for s in sample]

        return f"## Sample Stocks from {exchange}\n\n" + "\n".join(stocks)

    async def _analyze_screened_stocks(self, tickers: list[str]) -> str:
        """Quick analysis of screened stocks."""
        try:
            import yfinance as yf

            results = []
            for ticker in tickers[:10]:  # Limit to 10 stocks
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info

                    result = f"""### {ticker}
- **Name**: {info.get('longName', 'N/A')}
- **Sector**: {info.get('sector', 'N/A')}
- **Market Cap**: ${info.get('marketCap', 0) / 1e9:.2f}B
- **P/E Ratio**: {info.get('trailingPE', 'N/A')}
- **52W High**: ${info.get('fiftyTwoWeekHigh', 'N/A')}
- **52W Low**: ${info.get('fiftyTwoWeekLow', 'N/A')}
"""
                    results.append(result)
                except Exception as e:
                    results.append(f"### {ticker}\nError: {e}\n")

            return "## Screened Stock Analysis\n\n" + "\n".join(results)
        except ImportError:
            return "yfinance not available for stock analysis"

    def _generate_report(
        self, criteria: str, trade_date: str, data: dict[str, Any]
    ) -> str:
        """Generate a comprehensive stock screening report."""
        report = f"""# Stock Screening Report

**Screening Criteria:** {criteria}
**Analysis Date:** {trade_date}

## Executive Summary

This report presents stocks that match the specified screening criteria.

## Web Screening Results

{data.get('web_screening', 'No web screening results available')}

## Value Screening

{data.get('value_screen', 'N/A - Value criteria not specified')}

## Growth Screening

{data.get('growth_screen', 'N/A - Growth criteria not specified')}

## Dividend Screening

{data.get('dividend_screen', 'N/A - Dividend criteria not specified')}

## Momentum Screening

{data.get('momentum_screen', 'N/A - Momentum criteria not specified')}

## Screening Summary

Based on the screening criteria:

1. **Matching Stocks**: [List of stocks matching criteria]
2. **Top Picks**: [Best matches with rationale]
3. **Sector Distribution**: [Sectors represented]
4. **Risk Considerations**: [Key risks of screened stocks]

## Recommended for Further Analysis

| Ticker | Reason | Score |
|--------|--------|-------|
| TBD | Meets criteria | High |
| TBD | Partial match | Medium |

## Next Steps

1. Perform detailed analysis on top picks
2. Check recent news and catalysts
3. Review technical setup for entry timing
4. Assess portfolio fit and position sizing

---
*Report generated by AlphaHound*
"""
        return report
