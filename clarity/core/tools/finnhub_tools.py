"""FinnHub API Tools for the trading agents system."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class FinnHubTools:
    """Tools for interacting with FinnHub API.

    Reference: MiroFlow tool_utils.py pattern
    """

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")

    async def get_company_profile(self, symbol: str) -> dict[str, Any]:
        """Get company profile."""
        if not self.api_key:
            return {"error": "FINNHUB_API_KEY not configured"}

        url = f"{self.BASE_URL}/stock/profile2"
        params = {"symbol": symbol, "token": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_quote(self, symbol: str) -> dict[str, Any]:
        """Get real-time quote."""
        if not self.api_key:
            return {"error": "FINNHUB_API_KEY not configured"}

        url = f"{self.BASE_URL}/quote"
        params = {"symbol": symbol, "token": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_company_news(
        self, symbol: str, from_date: str, to_date: str
    ) -> list[dict[str, Any]]:
        """Get company news."""
        if not self.api_key:
            return [{"error": "FINNHUB_API_KEY not configured"}]

        url = f"{self.BASE_URL}/company-news"
        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date,
            "token": self.api_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_insider_sentiment(
        self, symbol: str, from_date: str, to_date: str
    ) -> dict[str, Any]:
        """Get insider sentiment."""
        if not self.api_key:
            return {"error": "FINNHUB_API_KEY not configured"}

        url = f"{self.BASE_URL}/stock/insider-sentiment"
        params = {
            "symbol": symbol,
            "from": from_date,
            "to": to_date,
            "token": self.api_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_insider_transactions(
        self, symbol: str, from_date: str, to_date: str
    ) -> dict[str, Any]:
        """Get insider transactions."""
        if not self.api_key:
            return {"error": "FINNHUB_API_KEY not configured"}

        url = f"{self.BASE_URL}/stock/insider-transactions"
        params = {"symbol": symbol, "token": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_recommendation_trends(self, symbol: str) -> list[dict[str, Any]]:
        """Get analyst recommendation trends."""
        if not self.api_key:
            return [{"error": "FINNHUB_API_KEY not configured"}]

        url = f"{self.BASE_URL}/stock/recommendation"
        params = {"symbol": symbol, "token": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_earnings_surprises(self, symbol: str) -> list[dict[str, Any]]:
        """Get earnings surprises."""
        if not self.api_key:
            return [{"error": "FINNHUB_API_KEY not configured"}]

        url = f"{self.BASE_URL}/stock/earnings"
        params = {"symbol": symbol, "token": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_basic_financials(
        self, symbol: str, metric: str = "all"
    ) -> dict[str, Any]:
        """Get basic financials."""
        if not self.api_key:
            return {"error": "FINNHUB_API_KEY not configured"}

        url = f"{self.BASE_URL}/stock/metric"
        params = {"symbol": symbol, "metric": metric, "token": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def stock_symbols(self, exchange: str = "US") -> list[dict[str, Any]]:
        """Get list of stock symbols."""
        if not self.api_key:
            return [{"error": "FINNHUB_API_KEY not configured"}]

        url = f"{self.BASE_URL}/stock/symbol"
        params = {"exchange": exchange, "token": self.api_key}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
