"""Web Search Tools using SERPER API."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class SearchTools:
    """Web search tools using SERPER API.

    Reference: MiroFlow tool implementation pattern
    """

    SERPER_BASE_URL = "https://google.serper.dev"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("SERPER_API_KEY")

    def _get_headers(self) -> dict[str, str]:
        """Get headers for SERPER API."""
        return {
            "X-API-KEY": self.api_key or "",
            "Content-Type": "application/json",
        }

    async def web_search(
        self, query: str, num_results: int = 10
    ) -> list[dict[str, Any]]:
        """Perform a web search.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        if not self.api_key:
            return [{"error": "SERPER_API_KEY not configured"}]

        url = f"{self.SERPER_BASE_URL}/search"
        payload = {"q": query, "num": num_results}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

        return data.get("organic", [])

    async def news_search(
        self, query: str, num_results: int = 10
    ) -> list[dict[str, Any]]:
        """Search for news articles.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of news articles
        """
        if not self.api_key:
            return [{"error": "SERPER_API_KEY not configured"}]

        url = f"{self.SERPER_BASE_URL}/news"
        payload = {"q": query, "num": num_results}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

        return data.get("news", [])

    async def scholar_search(
        self, query: str, num_results: int = 10
    ) -> list[dict[str, Any]]:
        """Search Google Scholar.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of scholarly articles
        """
        if not self.api_key:
            return [{"error": "SERPER_API_KEY not configured"}]

        url = f"{self.SERPER_BASE_URL}/scholar"
        payload = {"q": query, "num": num_results}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

        return data.get("organic", [])

    async def image_search(
        self, query: str, num_results: int = 10
    ) -> list[dict[str, Any]]:
        """Search for images.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of image results
        """
        if not self.api_key:
            return [{"error": "SERPER_API_KEY not configured"}]

        url = f"{self.SERPER_BASE_URL}/images"
        payload = {"q": query, "num": num_results}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, json=payload, headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

        return data.get("images", [])

    def format_results(self, results: list[dict[str, Any]]) -> str:
        """Format search results as readable string.

        Args:
            results: List of search results

        Returns:
            Formatted string
        """
        formatted = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            snippet = result.get("snippet", "No description")
            link = result.get("link", "")

            formatted.append(f"{i}. **{title}**")
            formatted.append(f"   {snippet}")
            if link:
                formatted.append(f"   Source: {link}")
            formatted.append("")

        return "\n".join(formatted)
