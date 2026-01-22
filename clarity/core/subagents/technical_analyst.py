"""Technical Analyst SubAgent - Analyzes market data and technical indicators."""

from __future__ import annotations

import logging
from typing import Any

from ..base_agent import AgentResult, BaseSubAgent, ToolDefinition
from ..config import AgentConfig, AgentRole, TaskContext

logger = logging.getLogger(__name__)


class TechnicalAnalyst(BaseSubAgent):
    """Analyzes market data and technical indicators to identify trading signals
    and price trends.
    """

    role = AgentRole.TECHNICAL_ANALYST
    name = "TechnicalAnalyst"
    description = (
        "Analyzes market data and technical indicators including moving averages, "
        "MACD, RSI, Bollinger Bands, and volume indicators to identify trading "
        "signals, support/resistance levels, and price trends."
    )

    # Supported technical indicators
    INDICATORS = [
        "close_50_sma",
        "close_200_sma",
        "close_10_ema",
        "macd",
        "macds",
        "macdh",
        "rsi",
        "boll",
        "boll_ub",
        "boll_lb",
        "atr",
        "vwma",
    ]

    def _setup_tools(self) -> None:
        """Setup technical analysis tools."""
        self.tools = [
            ToolDefinition(
                name="get_yfin_data",
                description="Get historical price data from Yahoo Finance",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker symbol"},
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format",
                        },
                    },
                    "required": ["symbol", "start_date", "end_date"],
                },
                handler=self._get_yfin_data,
            ),
            ToolDefinition(
                name="get_technical_indicator",
                description="Get a specific technical indicator for analysis",
                parameters={
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock ticker symbol"},
                        "indicator": {
                            "type": "string",
                            "enum": self.INDICATORS,
                            "description": "Technical indicator to calculate",
                        },
                        "curr_date": {
                            "type": "string",
                            "description": "Current date in YYYY-MM-DD format",
                        },
                        "look_back_days": {
                            "type": "integer",
                            "description": "Number of days to look back",
                        },
                    },
                    "required": ["symbol", "indicator", "curr_date", "look_back_days"],
                },
                handler=self._get_technical_indicator,
            ),
        ]

    async def execute(self, context: TaskContext, **kwargs) -> AgentResult:
        """Execute technical analysis for the given context."""
        ticker = context.target
        trade_date = context.trade_date
        look_back_days = context.look_back_days

        logger.info(
            f"TechnicalAnalyst: Analyzing {ticker} technicals as of {trade_date}"
        )

        collected_data = {}
        errors = []

        # Get price data
        try:
            from datetime import datetime, timedelta

            end_date = trade_date
            start_dt = datetime.strptime(trade_date, "%Y-%m-%d") - timedelta(
                days=look_back_days
            )
            start_date = start_dt.strftime("%Y-%m-%d")

            price_data = await self._get_yfin_data(ticker, start_date, end_date)
            collected_data["price_data"] = price_data
        except Exception as e:
            errors.append(f"Price data error: {e}")
            logger.error(f"Error getting price data: {e}")

        # Get key technical indicators
        key_indicators = ["rsi", "macd", "close_50_sma", "close_200_sma", "boll", "atr"]

        for indicator in key_indicators:
            try:
                ind_data = await self._get_technical_indicator(
                    ticker, indicator, trade_date, look_back_days
                )
                collected_data[indicator] = ind_data
            except Exception as e:
                errors.append(f"{indicator} error: {e}")
                logger.error(f"Error getting {indicator}: {e}")

        # Generate report
        report = self._generate_report(ticker, trade_date, collected_data)

        return AgentResult(
            success=len(collected_data) > 0,
            output=report,
            report=report,
            errors=errors,
            metadata={"ticker": ticker, "trade_date": trade_date},
        )

    async def _get_yfin_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> str:
        """Get historical price data."""
        if self.config.online_tools:
            from ...dataflows.interface import get_YFin_data_online

            return get_YFin_data_online(symbol, start_date, end_date)
        else:
            from ...dataflows.interface import get_YFin_data

            df = get_YFin_data(symbol, start_date, end_date)
            return df.to_string() if hasattr(df, "to_string") else str(df)

    async def _get_technical_indicator(
        self, symbol: str, indicator: str, curr_date: str, look_back_days: int
    ) -> str:
        """Get technical indicator data."""
        from ...dataflows.interface import get_stock_stats_indicators_window

        return get_stock_stats_indicators_window(
            symbol, indicator, curr_date, look_back_days, self.config.online_tools
        )

    def _generate_report(
        self, ticker: str, trade_date: str, data: dict[str, Any]
    ) -> str:
        """Generate a comprehensive technical analysis report."""
        report = f"""# Technical Analysis Report: {ticker}

**Analysis Date:** {trade_date}

## Executive Summary

This report provides technical analysis of {ticker} including price action, trend indicators, momentum indicators, and volatility measures.

## Price Data

{data.get('price_data', 'No price data available')}

## Trend Indicators

### 50-Day Simple Moving Average
{data.get('close_50_sma', 'No data available')}

### 200-Day Simple Moving Average
{data.get('close_200_sma', 'No data available')}

## Momentum Indicators

### MACD (Moving Average Convergence Divergence)
{data.get('macd', 'No data available')}

### RSI (Relative Strength Index)
{data.get('rsi', 'No data available')}

## Volatility Indicators

### Bollinger Bands
{data.get('boll', 'No data available')}

### ATR (Average True Range)
{data.get('atr', 'No data available')}

## Technical Signals

Based on the analysis:

1. **Trend Direction**: [Uptrend/Downtrend/Sideways]
2. **Momentum**: [Bullish/Bearish/Neutral]
3. **Volatility**: [High/Medium/Low]
4. **Key Levels**: [Support/Resistance levels]

## Signal Summary

| Indicator | Current Value | Signal | Strength |
|-----------|---------------|--------|----------|
| RSI | TBD | Overbought/Oversold/Neutral | Strong/Weak |
| MACD | TBD | Bullish/Bearish | Strong/Weak |
| SMA Cross | TBD | Golden/Death/None | N/A |
| Bollinger | TBD | Upper/Lower/Middle | N/A |

## Trading Implications

- Entry/Exit considerations based on technicals
- Key levels to watch
- Risk management suggestions based on ATR

---
*Report generated by TechnicalAnalyst*
"""
        return report
