"""Holdings Hunter SubAgent - Tracks institutional and guru holdings."""

from __future__ import annotations

import logging
from typing import Any

from ..base_agent import AgentResult, BaseSubAgent, ToolDefinition
from ..config import AgentConfig, AgentRole, TaskContext

logger = logging.getLogger(__name__)


class HoldingsHunter(BaseSubAgent):
    """Tracks institutional investors and famous investors' (gurus) holdings
    to identify their latest positions and trading activity.
    """

    role = AgentRole.HOLDINGS_HUNTER
    name = "HoldingsHunter"
    description = (
        "Tracks and analyzes holdings of institutional investors and famous "
        "investors (gurus). Uses SEC 13F filings, web searches, and financial "
        "APIs to discover what top investors are buying and selling."
    )

    # Well-known investors to track
    KNOWN_GURUS = [
        "Warren Buffett",
        "Charlie Munger",
        "Ray Dalio",
        "Cathie Wood",
        "Michael Burry",
        "Bill Ackman",
        "David Tepper",
        "Stanley Druckenmiller",
        "George Soros",
        "Carl Icahn",
        "Seth Klarman",
        "Howard Marks",
        "Peter Lynch",
        "Joel Greenblatt",
    ]

    def _setup_tools(self) -> None:
        """Setup holdings tracking tools."""
        self.tools = [
            ToolDefinition(
                name="search_guru_holdings",
                description="Search for a specific investor's current holdings",
                parameters={
                    "type": "object",
                    "properties": {
                        "investor_name": {
                            "type": "string",
                            "description": "Name of the investor/guru to search",
                        },
                    },
                    "required": ["investor_name"],
                },
                handler=self._search_guru_holdings,
            ),
            ToolDefinition(
                name="search_13f_filings",
                description="Search SEC 13F filings for institutional holdings",
                parameters={
                    "type": "object",
                    "properties": {
                        "investor_name": {
                            "type": "string",
                            "description": "Name of the investor or fund",
                        },
                        "quarter": {
                            "type": "string",
                            "description": "Quarter to search (e.g., Q4 2024)",
                        },
                    },
                    "required": ["investor_name"],
                },
                handler=self._search_13f_filings,
            ),
            ToolDefinition(
                name="get_stock_institutional_holders",
                description="Get institutional holders of a specific stock",
                parameters={
                    "type": "object",
                    "properties": {
                        "ticker": {
                            "type": "string",
                            "description": "Stock ticker symbol",
                        },
                    },
                    "required": ["ticker"],
                },
                handler=self._get_stock_institutional_holders,
            ),
            ToolDefinition(
                name="web_crawl_holdings",
                description="Crawl web page for holdings information using JINA API",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to crawl for holdings data",
                        },
                    },
                    "required": ["url"],
                },
                handler=self._web_crawl_holdings,
            ),
        ]

    async def execute(self, context: TaskContext, **kwargs) -> AgentResult:
        """Execute holdings tracking for the given context."""
        target = context.target  # Could be investor name or stock ticker
        trade_date = context.trade_date

        logger.info(f"HoldingsHunter: Tracking holdings for {target} as of {trade_date}")

        collected_data = {}
        errors = []

        # Determine if target is an investor name or a stock ticker
        is_investor = any(
            guru.lower() in target.lower() for guru in self.KNOWN_GURUS
        ) or len(target) > 5  # Assume longer names are investor names

        if is_investor:
            # Search for investor's holdings
            try:
                holdings = await self._search_guru_holdings(target)
                collected_data["guru_holdings"] = holdings
            except Exception as e:
                errors.append(f"Guru holdings search error: {e}")
                logger.error(f"Error searching guru holdings: {e}")

            try:
                filings = await self._search_13f_filings(target)
                collected_data["13f_filings"] = filings
            except Exception as e:
                errors.append(f"13F filings error: {e}")
                logger.error(f"Error searching 13F filings: {e}")
        else:
            # Search for institutional holders of the stock
            try:
                holders = await self._get_stock_institutional_holders(target)
                collected_data["institutional_holders"] = holders
            except Exception as e:
                errors.append(f"Institutional holders error: {e}")
                logger.error(f"Error getting institutional holders: {e}")

        # Generate report
        report = self._generate_report(target, trade_date, collected_data, is_investor)

        return AgentResult(
            success=len(collected_data) > 0,
            output=report,
            report=report,
            errors=errors,
            metadata={
                "target": target,
                "trade_date": trade_date,
                "is_investor_search": is_investor,
            },
        )

    async def _search_guru_holdings(self, investor_name: str) -> str:
        """Search for an investor's current holdings using web search."""
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

        # Search for latest holdings
        queries = [
            f"{investor_name} portfolio holdings 2025",
            f"{investor_name} 13F filing latest",
            f"{investor_name} stocks buying selling",
        ]

        all_results = []
        async with httpx.AsyncClient() as client:
            for query in queries:
                payload = {"q": query, "num": 5}
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("organic", [])[:3]:
                        all_results.append(
                            f"**{item.get('title', '')}**\n"
                            f"{item.get('snippet', '')}\n"
                            f"Source: {item.get('link', '')}\n"
                        )

        return f"## Holdings Search Results for {investor_name}\n\n" + "\n\n".join(
            all_results[:10]
        )

    async def _search_13f_filings(
        self, investor_name: str, quarter: str = ""
    ) -> str:
        """Search SEC 13F filings for institutional holdings."""
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

        query = f"{investor_name} 13F SEC filing site:sec.gov"
        if quarter:
            query += f" {quarter}"

        payload = {"q": query, "num": 10}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic", [])[:10]:
            results.append(
                f"**{item.get('title', '')}**\n"
                f"{item.get('snippet', '')}\n"
                f"Link: {item.get('link', '')}\n"
            )

        return f"## 13F Filing Results for {investor_name}\n\n" + "\n\n".join(results)

    async def _get_stock_institutional_holders(self, ticker: str) -> str:
        """Get institutional holders of a stock using yfinance."""
        try:
            import yfinance as yf

            stock = yf.Ticker(ticker)
            holders = stock.institutional_holders

            if holders is None or holders.empty:
                return f"No institutional holder data available for {ticker}"

            result = f"## Institutional Holders of {ticker}\n\n"
            result += holders.to_markdown() if hasattr(holders, "to_markdown") else holders.to_string()
            return result
        except Exception as e:
            logger.error(f"Error getting institutional holders: {e}")
            return f"Error getting institutional holders for {ticker}: {e}"

    async def _web_crawl_holdings(self, url: str) -> str:
        """Crawl a web page for holdings information using JINA API."""
        import os
        import httpx

        jina_api_key = self.config.jina_api_key or os.getenv("JINA_API_KEY")
        if not jina_api_key:
            return "JINA_API_KEY not configured"

        jina_url = f"https://r.jina.ai/{url}"
        headers = {"Authorization": f"Bearer {jina_api_key}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(jina_url, headers=headers)
            response.raise_for_status()

        # Return first 5000 chars to avoid token limits
        content = response.text[:5000]
        return f"## Web Content from {url}\n\n{content}"

    def _generate_report(
        self,
        target: str,
        trade_date: str,
        data: dict[str, Any],
        is_investor: bool,
    ) -> str:
        """Generate a comprehensive holdings tracking report."""
        if is_investor:
            report = f"""# Holdings Tracking Report: {target}

**Analysis Date:** {trade_date}

## Executive Summary

This report tracks the investment holdings and recent trading activity of {target}.

## Portfolio Holdings Search

{data.get('guru_holdings', 'No holdings data available')}

## SEC 13F Filings

{data.get('13f_filings', 'No 13F filing data available')}

## Key Holdings Analysis

Based on the available data:

1. **Top Holdings**: [List major positions]
2. **Recent Buys**: [New positions or increases]
3. **Recent Sells**: [Reduced or eliminated positions]
4. **Sector Focus**: [Key sectors of investment]

## Investment Style Insights

- Investment philosophy indicators
- Position sizing patterns
- Sector/industry preferences
- Typical holding period

## Summary Table

| Category | Details |
|----------|---------|
| Top Holding | TBD |
| Recent Buy | TBD |
| Recent Sell | TBD |
| Portfolio Focus | TBD |

---
*Report generated by HoldingsHunter*
"""
        else:
            report = f"""# Institutional Holdings Report: {target}

**Analysis Date:** {trade_date}

## Executive Summary

This report analyzes the institutional ownership of {target}.

## Institutional Holders

{data.get('institutional_holders', 'No institutional holder data available')}

## Ownership Analysis

1. **Institutional Ownership %**: [Percentage owned by institutions]
2. **Top Holders**: [Major institutional investors]
3. **Recent Changes**: [Notable increases/decreases]
4. **Insider Activity**: [Related insider transactions]

## Key Observations

- Ownership concentration
- Recent institutional activity
- Implications for stock price

---
*Report generated by HoldingsHunter*
"""
        return report
