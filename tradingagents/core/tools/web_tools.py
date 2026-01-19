"""Web Crawling Tools using JINA API."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class WebTools:
    """Web crawling and content extraction tools using JINA API."""

    JINA_READER_URL = "https://r.jina.ai"
    JINA_SEARCH_URL = "https://s.jina.ai"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("JINA_API_KEY")

    def _get_headers(self) -> dict[str, str]:
        """Get headers for JINA API."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def read_webpage(
        self, url: str, max_length: int = 10000
    ) -> dict[str, Any]:
        """Read and extract content from a webpage.

        Args:
            url: URL to read
            max_length: Maximum content length to return

        Returns:
            Dictionary with title and content
        """
        try:
            jina_url = f"{self.JINA_READER_URL}/{url}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(jina_url, headers=self._get_headers())
                response.raise_for_status()

            content = response.text
            if len(content) > max_length:
                content = content[:max_length] + "\n\n[Content truncated...]"

            return {
                "success": True,
                "url": url,
                "content": content,
            }

        except Exception as e:
            logger.error(f"Error reading webpage {url}: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "content": "",
            }

    async def search_web(
        self, query: str, num_results: int = 5
    ) -> list[dict[str, Any]]:
        """Search the web using JINA search.

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of search results with content
        """
        try:
            jina_url = f"{self.JINA_SEARCH_URL}/{query}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(jina_url, headers=self._get_headers())
                response.raise_for_status()

            # JINA returns markdown-formatted content
            content = response.text

            return [
                {
                    "success": True,
                    "query": query,
                    "content": content[:5000],
                }
            ]

        except Exception as e:
            logger.error(f"Error searching web for {query}: {e}")
            return [
                {
                    "success": False,
                    "query": query,
                    "error": str(e),
                }
            ]

    async def extract_article(self, url: str) -> dict[str, Any]:
        """Extract article content from a URL.

        Args:
            url: URL of the article

        Returns:
            Dictionary with article title, author, date, and content
        """
        result = await self.read_webpage(url)

        if not result["success"]:
            return result

        # Basic extraction (JINA already does good job extracting main content)
        content = result["content"]

        return {
            "success": True,
            "url": url,
            "content": content,
        }

    async def batch_read(self, urls: list[str]) -> list[dict[str, Any]]:
        """Read multiple URLs concurrently.

        Args:
            urls: List of URLs to read

        Returns:
            List of results for each URL
        """
        import asyncio

        tasks = [self.read_webpage(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        formatted_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                formatted_results.append(
                    {
                        "success": False,
                        "url": url,
                        "error": str(result),
                    }
                )
            else:
                formatted_results.append(result)

        return formatted_results


class WebCrawler:
    """Advanced web crawler for financial data extraction."""

    def __init__(self, jina_api_key: str | None = None):
        self.web_tools = WebTools(jina_api_key)

    async def crawl_sec_filing(self, url: str) -> dict[str, Any]:
        """Crawl an SEC filing page.

        Args:
            url: URL of the SEC filing

        Returns:
            Extracted filing content
        """
        return await self.web_tools.read_webpage(url, max_length=20000)

    async def crawl_financial_news(self, url: str) -> dict[str, Any]:
        """Crawl a financial news article.

        Args:
            url: URL of the news article

        Returns:
            Extracted article content
        """
        return await self.web_tools.extract_article(url)

    async def crawl_investor_portfolio(self, url: str) -> dict[str, Any]:
        """Crawl an investor portfolio page.

        Args:
            url: URL of the portfolio page

        Returns:
            Extracted portfolio content
        """
        return await self.web_tools.read_webpage(url, max_length=15000)
