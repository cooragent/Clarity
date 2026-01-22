"""News Analyst SubAgent - Analyzes news and market trends."""

from __future__ import annotations

import logging
from typing import Any

from ..base_agent import AgentResult, BaseSubAgent, ToolDefinition
from ..config import AgentConfig, AgentRole, TaskContext

logger = logging.getLogger(__name__)


class NewsAnalyst(BaseSubAgent):
    """Analyzes news articles, global market trends, and current events
    that may impact trading decisions.
    """

    role = AgentRole.NEWS_ANALYST
    name = "NewsAnalyst"
    description = (
        "Analyzes recent news and market trends. Examines news from multiple "
        "sources including FinnHub, Reddit, Google News to provide comprehensive "
        "coverage of events that may impact the stock or overall market."
    )

    def _setup_tools(self) -> None:
        """Setup news analysis tools."""
        self.tools = [
            ToolDefinition(
                name="get_finnhub_news",
                description="Get company-specific news from FinnHub",
                parameters={
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Stock ticker symbol"},
                        "curr_date": {
                            "type": "string",
                            "description": "Current date in YYYY-MM-DD format",
                        },
                        "look_back_days": {
                            "type": "integer",
                            "description": "Number of days to look back",
                        },
                    },
                    "required": ["ticker", "curr_date", "look_back_days"],
                },
                handler=self._get_finnhub_news,
            ),
            ToolDefinition(
                name="get_google_news",
                description="Search Google News for relevant articles",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "curr_date": {
                            "type": "string",
                            "description": "Current date in YYYY-MM-DD format",
                        },
                        "look_back_days": {
                            "type": "integer",
                            "description": "Number of days to look back",
                        },
                    },
                    "required": ["query", "curr_date", "look_back_days"],
                },
                handler=self._get_google_news,
            ),
            ToolDefinition(
                name="get_reddit_global_news",
                description="Get global market news from Reddit",
                parameters={
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format",
                        },
                        "look_back_days": {
                            "type": "integer",
                            "description": "Number of days to look back",
                        },
                        "max_limit_per_day": {
                            "type": "integer",
                            "description": "Maximum news items per day",
                            "default": 5,
                        },
                    },
                    "required": ["start_date", "look_back_days"],
                },
                handler=self._get_reddit_global_news,
            ),
            ToolDefinition(
                name="web_search_news",
                description="Search web for news using SERPER API",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                    },
                    "required": ["query"],
                },
                handler=self._web_search_news,
            ),
        ]

    async def execute(self, context: TaskContext, **kwargs) -> AgentResult:
        """Execute news analysis for the given context."""
        ticker = context.target
        trade_date = context.trade_date
        look_back_days = context.look_back_days

        logger.info(f"NewsAnalyst: Analyzing {ticker} news as of {trade_date}")

        collected_data = {}
        errors = []

        # If online_tools is True, prioritize online sources
        if self.config.online_tools:
            # Use web search for news
            try:
                web_news = await self._web_search_news(f"{ticker} stock news latest")
                collected_data["web_news"] = web_news
            except Exception as e:
                errors.append(f"Web news error: {e}")
                logger.error(f"Error getting web news: {e}")

            # Try Google News
            try:
                google_news = await self._get_google_news(
                    f"{ticker} stock", trade_date, look_back_days
                )
                if google_news:  # Only add if not empty
                    collected_data["google_news"] = google_news
            except Exception as e:
                errors.append(f"Google news error: {e}")
                logger.error(f"Error getting Google news: {e}")
        else:
            # Try offline sources
            try:
                finnhub_news = await self._get_finnhub_news(
                    ticker, trade_date, look_back_days
                )
                collected_data["finnhub_news"] = finnhub_news
            except Exception as e:
                errors.append(f"FinnHub news error: {e}")
                logger.error(f"Error getting FinnHub news: {e}")

            try:
                google_news = await self._get_google_news(
                    f"{ticker} stock", trade_date, look_back_days
                )
                collected_data["google_news"] = google_news
            except Exception as e:
                errors.append(f"Google news error: {e}")
                logger.error(f"Error getting Google news: {e}")

            try:
                reddit_news = await self._get_reddit_global_news(
                    trade_date, look_back_days, max_limit_per_day=5
                )
                collected_data["reddit_news"] = reddit_news
            except Exception as e:
                errors.append(f"Reddit news error: {e}")
                logger.error(f"Error getting Reddit news: {e}")

        # Generate report
        report = self._generate_report(ticker, trade_date, collected_data)

        # Consider success if we have at least some data
        success = len(collected_data) > 0

        return AgentResult(
            success=success,
            output=report,
            report=report,
            errors=errors,
            metadata={"ticker": ticker, "trade_date": trade_date},
        )

    async def _get_finnhub_news(
        self, ticker: str, curr_date: str, look_back_days: int
    ) -> str:
        """Get news from FinnHub."""
        from ...dataflows.interface import get_finnhub_news

        return get_finnhub_news(ticker, curr_date, look_back_days)

    async def _get_google_news(
        self, query: str, curr_date: str, look_back_days: int
    ) -> str:
        """Get news from Google."""
        from ...dataflows.interface import get_google_news

        return get_google_news(query, curr_date, look_back_days)

    async def _get_reddit_global_news(
        self, start_date: str, look_back_days: int, max_limit_per_day: int = 5
    ) -> str:
        """Get global news from Reddit."""
        from ...dataflows.interface import get_reddit_global_news

        return get_reddit_global_news(start_date, look_back_days, max_limit_per_day)

    async def _web_search_news(self, query: str) -> str:
        """Search web for news using SERPER API."""
        import os
        import httpx

        serper_api_key = self.config.serper_api_key or os.getenv("SERPER_API_KEY")
        if not serper_api_key:
            return "SERPER_API_KEY not configured"

        url = "https://google.serper.dev/news"
        headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": 10}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("news", [])[:10]:
            results.append(
                f"**{item.get('title', '')}** ({item.get('source', '')})\n"
                f"{item.get('snippet', '')}\n"
            )

        return "## Web News Search Results\n\n" + "\n\n".join(results)

    def _generate_report(
        self, ticker: str, trade_date: str, data: dict[str, Any]
    ) -> str:
        """Generate a comprehensive news analysis report."""
        report = f"""# News Analysis Report: {ticker}

**Analysis Date:** {trade_date}

## Executive Summary

This report provides a comprehensive analysis of news and events that may impact {ticker} and the broader market.

## Company-Specific News (FinnHub)

{data.get('finnhub_news', 'No FinnHub news available')}

## Google News Coverage

{data.get('google_news', 'No Google news available')}

## Reddit Market News

{data.get('reddit_news', 'No Reddit news available')}

## Web News Search

{data.get('web_news', 'No web news available')}

## Key News Themes

Based on the collected news:

1. **Major Events**: [List significant events]
2. **Market Impact**: [Assess potential market impact]
3. **Industry Trends**: [Note relevant industry developments]
4. **Macroeconomic Factors**: [Identify macro influences]

## Sentiment from News

| Source | Sentiment | Key Topics |
|--------|-----------|------------|
| FinnHub | TBD | Company-specific |
| Google | TBD | Broad coverage |
| Reddit | TBD | Community sentiment |

## Trading Implications

- What the news suggests for near-term price action
- Key events to watch
- Risk factors identified from news

---
*Report generated by NewsAnalyst*
"""
        return report
