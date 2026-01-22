"""Fundamentals Analyst SubAgent - Analyzes company fundamentals and financial data."""

from __future__ import annotations

import logging
from typing import Any

from ..base_agent import AgentResult, BaseSubAgent, ToolDefinition
from ..config import AgentConfig, AgentRole, TaskContext

logger = logging.getLogger(__name__)


class FundamentalsAnalyst(BaseSubAgent):
    """Analyzes company fundamental information including financial documents,
    company profile, financials history, insider sentiment, and transactions.
    """

    role = AgentRole.FUNDAMENTALS_ANALYST
    name = "FundamentalsAnalyst"
    description = (
        "Analyzes fundamental information about a company including financial "
        "documents (balance sheet, cash flow, income statement), company profile, "
        "insider sentiment, and insider transactions to provide a comprehensive "
        "view of the company's fundamental health."
    )

    def _setup_tools(self) -> None:
        """Setup fundamental analysis tools."""
        self.tools = [
            ToolDefinition(
                name="get_finnhub_insider_sentiment",
                description="Get insider sentiment data from SEC filings",
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
                handler=self._get_insider_sentiment,
            ),
            ToolDefinition(
                name="get_finnhub_insider_transactions",
                description="Get insider transaction data from SEC filings",
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
                handler=self._get_insider_transactions,
            ),
            ToolDefinition(
                name="get_balance_sheet",
                description="Get company balance sheet data",
                parameters={
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Stock ticker symbol"},
                        "freq": {
                            "type": "string",
                            "enum": ["annual", "quarterly"],
                            "description": "Reporting frequency",
                        },
                        "curr_date": {
                            "type": "string",
                            "description": "Current date in YYYY-MM-DD format",
                        },
                    },
                    "required": ["ticker", "freq", "curr_date"],
                },
                handler=self._get_balance_sheet,
            ),
            ToolDefinition(
                name="get_cashflow",
                description="Get company cash flow statement",
                parameters={
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Stock ticker symbol"},
                        "freq": {
                            "type": "string",
                            "enum": ["annual", "quarterly"],
                            "description": "Reporting frequency",
                        },
                        "curr_date": {
                            "type": "string",
                            "description": "Current date in YYYY-MM-DD format",
                        },
                    },
                    "required": ["ticker", "freq", "curr_date"],
                },
                handler=self._get_cashflow,
            ),
            ToolDefinition(
                name="get_income_statement",
                description="Get company income statement",
                parameters={
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "Stock ticker symbol"},
                        "freq": {
                            "type": "string",
                            "enum": ["annual", "quarterly"],
                            "description": "Reporting frequency",
                        },
                        "curr_date": {
                            "type": "string",
                            "description": "Current date in YYYY-MM-DD format",
                        },
                    },
                    "required": ["ticker", "freq", "curr_date"],
                },
                handler=self._get_income_statement,
            ),
        ]

    async def execute(self, context: TaskContext, **kwargs) -> AgentResult:
        """Execute fundamental analysis for the given context."""
        ticker = context.target
        trade_date = context.trade_date
        look_back_days = context.look_back_days

        logger.info(
            f"FundamentalsAnalyst: Analyzing {ticker} fundamentals as of {trade_date}"
        )

        collected_data = {}
        errors = []

        # If online_tools is True, use online APIs
        if self.config.online_tools:
            try:
                fundamentals = await self._get_fundamentals_online(ticker, trade_date)
                collected_data["fundamentals_online"] = fundamentals
            except Exception as e:
                errors.append(f"Online fundamentals error: {e}")
                logger.error(f"Error getting online fundamentals: {e}")

            try:
                financials = await self._get_yfinance_fundamentals(ticker)
                collected_data["yfinance_fundamentals"] = financials
            except Exception as e:
                errors.append(f"YFinance fundamentals error: {e}")
                logger.error(f"Error getting YFinance fundamentals: {e}")
        else:
            # Try offline data sources
            try:
                sentiment = await self._get_insider_sentiment(
                    ticker, trade_date, look_back_days
                )
                collected_data["insider_sentiment"] = sentiment
            except Exception as e:
                errors.append(f"Insider sentiment error: {e}")
                logger.error(f"Error getting insider sentiment: {e}")

            try:
                transactions = await self._get_insider_transactions(
                    ticker, trade_date, look_back_days
                )
                collected_data["insider_transactions"] = transactions
            except Exception as e:
                errors.append(f"Insider transactions error: {e}")
                logger.error(f"Error getting insider transactions: {e}")

            try:
                balance = await self._get_balance_sheet(ticker, "quarterly", trade_date)
                collected_data["balance_sheet"] = balance
            except Exception as e:
                errors.append(f"Balance sheet error: {e}")
                logger.error(f"Error getting balance sheet: {e}")

            try:
                cashflow = await self._get_cashflow(ticker, "quarterly", trade_date)
                collected_data["cashflow"] = cashflow
            except Exception as e:
                errors.append(f"Cash flow error: {e}")
                logger.error(f"Error getting cash flow: {e}")

            try:
                income = await self._get_income_statement(ticker, "quarterly", trade_date)
                collected_data["income_statement"] = income
            except Exception as e:
                errors.append(f"Income statement error: {e}")
                logger.error(f"Error getting income statement: {e}")

        # Generate report
        report = self._generate_report(ticker, trade_date, collected_data)

        # Consider success if we have at least some data
        success = len(collected_data) > 0

        return AgentResult(
            success=success,
            output=report,
            report=report,
            errors=errors,
            metadata={"ticker": ticker, "trade_date": trade_date, "data_keys": list(collected_data.keys())},
        )

    async def _get_insider_sentiment(
        self, ticker: str, curr_date: str, look_back_days: int
    ) -> str:
        """Get insider sentiment from FinnHub."""
        # Import here to avoid circular imports
        from ...dataflows.interface import get_finnhub_company_insider_sentiment

        return get_finnhub_company_insider_sentiment(ticker, curr_date, look_back_days)

    async def _get_insider_transactions(
        self, ticker: str, curr_date: str, look_back_days: int
    ) -> str:
        """Get insider transactions from FinnHub."""
        from ...dataflows.interface import get_finnhub_company_insider_transactions

        return get_finnhub_company_insider_transactions(ticker, curr_date, look_back_days)

    async def _get_balance_sheet(
        self, ticker: str, freq: str, curr_date: str
    ) -> str:
        """Get balance sheet from SimFin."""
        from ...dataflows.interface import get_simfin_balance_sheet

        return get_simfin_balance_sheet(ticker, freq, curr_date)

    async def _get_cashflow(self, ticker: str, freq: str, curr_date: str) -> str:
        """Get cash flow statement from SimFin."""
        from ...dataflows.interface import get_simfin_cashflow

        return get_simfin_cashflow(ticker, freq, curr_date)

    async def _get_income_statement(
        self, ticker: str, freq: str, curr_date: str
    ) -> str:
        """Get income statement from SimFin."""
        from ...dataflows.interface import get_simfin_income_statements

        return get_simfin_income_statements(ticker, freq, curr_date)

    async def _get_fundamentals_online(self, ticker: str, curr_date: str) -> str:
        """Get fundamentals using online API (web search)."""
        import os
        import httpx

        serper_api_key = self.config.serper_api_key or os.getenv("SERPER_API_KEY")
        if not serper_api_key:
            # Fall back to yfinance
            return await self._get_yfinance_fundamentals(ticker)

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": serper_api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": f"{ticker} stock fundamentals PE ratio earnings revenue {curr_date[:4]}",
            "num": 10,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("organic", [])[:10]:
            results.append(
                f"**{item.get('title', '')}**\n{item.get('snippet', '')}\n"
            )

        return f"## Fundamentals Search Results for {ticker}\n\n" + "\n\n".join(results)

    async def _get_yfinance_fundamentals(self, ticker: str) -> str:
        """Get fundamentals from Yahoo Finance."""
        try:
            import yfinance as yf

            stock = yf.Ticker(ticker)
            info = stock.info

            fundamentals = f"""## {ticker} Fundamentals (Yahoo Finance)

### Company Info
- **Name**: {info.get('longName', 'N/A')}
- **Sector**: {info.get('sector', 'N/A')}
- **Industry**: {info.get('industry', 'N/A')}

### Valuation
- **Market Cap**: ${info.get('marketCap', 0) / 1e9:.2f}B
- **P/E Ratio (Trailing)**: {info.get('trailingPE', 'N/A')}
- **P/E Ratio (Forward)**: {info.get('forwardPE', 'N/A')}
- **PEG Ratio**: {info.get('pegRatio', 'N/A')}
- **Price/Book**: {info.get('priceToBook', 'N/A')}
- **Price/Sales**: {info.get('priceToSalesTrailing12Months', 'N/A')}

### Profitability
- **Profit Margin**: {info.get('profitMargins', 'N/A')}
- **Operating Margin**: {info.get('operatingMargins', 'N/A')}
- **Return on Equity**: {info.get('returnOnEquity', 'N/A')}
- **Return on Assets**: {info.get('returnOnAssets', 'N/A')}

### Financial Health
- **Total Cash**: ${info.get('totalCash', 0) / 1e9:.2f}B
- **Total Debt**: ${info.get('totalDebt', 0) / 1e9:.2f}B
- **Current Ratio**: {info.get('currentRatio', 'N/A')}
- **Quick Ratio**: {info.get('quickRatio', 'N/A')}

### Growth
- **Revenue Growth**: {info.get('revenueGrowth', 'N/A')}
- **Earnings Growth**: {info.get('earningsGrowth', 'N/A')}

### Dividends
- **Dividend Yield**: {info.get('dividendYield', 'N/A')}
- **Dividend Rate**: {info.get('dividendRate', 'N/A')}
- **Payout Ratio**: {info.get('payoutRatio', 'N/A')}
"""
            return fundamentals
        except Exception as e:
            logger.error(f"Error getting YFinance fundamentals: {e}")
            return f"Error getting fundamentals for {ticker}: {e}"

    def _generate_report(
        self, ticker: str, trade_date: str, data: dict[str, Any]
    ) -> str:
        """Generate a comprehensive fundamentals analysis report."""
        report = f"""# Fundamentals Analysis Report: {ticker}

**Analysis Date:** {trade_date}

## Executive Summary

This report provides a comprehensive analysis of {ticker}'s fundamental health based on financial statements, insider activity, and key financial metrics.

## Insider Activity

### Insider Sentiment
{data.get('insider_sentiment', 'No data available')}

### Insider Transactions
{data.get('insider_transactions', 'No data available')}

## Financial Statements

### Balance Sheet
{data.get('balance_sheet', 'No data available')}

### Cash Flow Statement
{data.get('cashflow', 'No data available')}

### Income Statement
{data.get('income_statement', 'No data available')}

## Key Observations

Based on the collected data, the following key observations can be made:

1. **Insider Activity**: Analyze whether insiders are buying or selling
2. **Financial Health**: Review balance sheet strength and liquidity
3. **Profitability**: Examine income statement trends
4. **Cash Position**: Evaluate cash flow generation capability

## Summary Table

| Metric | Value | Implication |
|--------|-------|-------------|
| Insider Sentiment | TBD | Based on data |
| Financial Position | TBD | Based on balance sheet |
| Cash Flow | TBD | Based on cash flow |
| Profitability | TBD | Based on income statement |

---
*Report generated by FundamentalsAnalyst*
"""
        return report
