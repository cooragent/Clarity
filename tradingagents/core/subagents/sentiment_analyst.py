"""Sentiment Analyst SubAgent - Analyzes social media sentiment and public opinion."""

from __future__ import annotations

import logging
from typing import Any

from ..base_agent import AgentResult, BaseSubAgent, ToolDefinition
from ..config import AgentConfig, AgentRole, TaskContext

logger = logging.getLogger(__name__)


class SentimentAnalyst(BaseSubAgent):
    """Analyzes social media posts, public sentiment, and what people are saying
    about a specific company to gauge market sentiment.
    """

    role = AgentRole.SENTIMENT_ANALYST
    name = "SentimentAnalyst"
    description = (
        "Analyzes social media and public sentiment for a specific company. "
        "Examines Reddit discussions, Twitter/X posts, and other social platforms "
        "to understand market sentiment and public perception of the company."
    )

    def _setup_tools(self) -> None:
        """Setup sentiment analysis tools."""
        self.tools = [
            ToolDefinition(
                name="get_reddit_stock_info",
                description="Get Reddit discussions about a specific stock",
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
                        "max_limit_per_day": {
                            "type": "integer",
                            "description": "Maximum posts per day",
                            "default": 10,
                        },
                    },
                    "required": ["ticker", "curr_date", "look_back_days"],
                },
                handler=self._get_reddit_stock_info,
            ),
            ToolDefinition(
                name="web_search_sentiment",
                description="Search web for social media sentiment about a stock",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    },
                    "required": ["query", "ticker"],
                },
                handler=self._web_search_sentiment,
            ),
        ]

    async def execute(self, context: TaskContext, **kwargs) -> AgentResult:
        """Execute sentiment analysis for the given context."""
        ticker = context.target
        trade_date = context.trade_date
        look_back_days = context.look_back_days

        logger.info(
            f"SentimentAnalyst: Analyzing {ticker} sentiment as of {trade_date}"
        )

        collected_data = {}
        errors = []

        # If online tools are enabled, prioritize web search
        if self.config.online_tools:
            try:
                web_sentiment = await self._web_search_sentiment(
                    f"{ticker} stock sentiment social media analysis", ticker
                )
                collected_data["web_sentiment"] = web_sentiment
            except Exception as e:
                errors.append(f"Web sentiment error: {e}")
                logger.error(f"Error getting web sentiment: {e}")

            # Also try to get stock community sentiment
            try:
                community_sentiment = await self._web_search_sentiment(
                    f"{ticker} reddit wallstreetbets stocktwits sentiment", ticker
                )
                collected_data["community_sentiment"] = community_sentiment
            except Exception as e:
                errors.append(f"Community sentiment error: {e}")
                logger.error(f"Error getting community sentiment: {e}")
        else:
            # Try offline Reddit data
            try:
                reddit_data = await self._get_reddit_stock_info(
                    ticker, trade_date, look_back_days, max_limit_per_day=10
                )
                collected_data["reddit_sentiment"] = reddit_data
            except Exception as e:
                errors.append(f"Reddit sentiment error: {e}")
                logger.error(f"Error getting Reddit sentiment: {e}")

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

    async def _get_reddit_stock_info(
        self,
        ticker: str,
        curr_date: str,
        look_back_days: int,
        max_limit_per_day: int = 10,
    ) -> str:
        """Get Reddit discussions about the stock."""
        from ...dataflows.interface import get_reddit_company_news

        return get_reddit_company_news(
            ticker, curr_date, look_back_days, max_limit_per_day
        )

    async def _web_search_sentiment(self, query: str, ticker: str) -> str:
        """Search web for sentiment using SERPER API."""
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
        payload = {"q": query, "num": 10}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        # Format results
        results = []
        for item in data.get("organic", [])[:10]:
            results.append(
                f"**{item.get('title', '')}**\n{item.get('snippet', '')}\n"
            )

        return f"## Web Sentiment Search Results for {ticker}\n\n" + "\n\n".join(results)

    def _generate_report(
        self, ticker: str, trade_date: str, data: dict[str, Any]
    ) -> str:
        """Generate a comprehensive sentiment analysis report."""
        report = f"""# Sentiment Analysis Report: {ticker}

**Analysis Date:** {trade_date}

## Executive Summary

This report analyzes social media sentiment and public perception of {ticker} to understand the current market sentiment.

## Reddit Sentiment Analysis

{data.get('reddit_sentiment', 'No Reddit data available')}

## Web Sentiment Search

{data.get('web_sentiment', 'No web sentiment data available')}

## Sentiment Indicators

Based on the collected data:

1. **Overall Sentiment**: [Bullish/Bearish/Neutral]
2. **Sentiment Strength**: [Strong/Moderate/Weak]
3. **Key Themes**: [List main discussion themes]
4. **Risk Signals**: [Any concerning patterns]

## Key Observations

- Analyze the tone of discussions
- Identify bullish/bearish arguments
- Note any significant news being discussed
- Track sentiment trends over the period

## Summary Table

| Metric | Value | Signal |
|--------|-------|--------|
| Reddit Sentiment | TBD | Based on analysis |
| Discussion Volume | TBD | High/Medium/Low |
| Sentiment Trend | TBD | Improving/Declining/Stable |
| Key Risk Factors | TBD | Based on discussions |

---
*Report generated by SentimentAnalyst*
"""
        return report
