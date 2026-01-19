#!/usr/bin/env python3
"""Test script for the Financial Intelligence Agent API.

Usage:
    # Start the server first:
    python api_server.py

    # Then run the tests:
    python test_api.py

    # Run specific tests:
    python test_api.py --test health
    python test_api.py --test analyze
    python test_api.py --test track
    python test_api.py --test screen
    python test_api.py --test ask
    python test_api.py --test all
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime

import httpx

# Bypass proxy for localhost connections
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")

# API base URL
BASE_URL = "http://localhost:8000"

# Test data
TEST_TICKER = "AAPL"
TEST_INVESTOR = "Warren Buffett"
TEST_CRITERIA = "high dividend yield tech stocks"
TEST_QUERY = "分析一下苹果公司的股票"


class APITester:
    """Test client for the Financial Intelligence Agent API."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = 300.0):
        self.base_url = base_url
        self.timeout = timeout
        self.results: list[dict] = []
        # Disable proxy for local connections
        self.client_kwargs = {
            "timeout": timeout,
            "proxy": None,  # Disable proxy
        }

    async def test_health(self) -> bool:
        """Test health check endpoint."""
        print("\n" + "=" * 60)
        print("🏥 Testing Health Check")
        print("=" * 60)

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                print(f"Status Code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")

                if response.status_code != 200:
                    print(f"Raw Response: {response.text[:500]}")
                    self._record_result("health", False, response.text)
                    return False

                try:
                    data = response.json()
                    print(f"Response: {data}")
                    success = data.get("status") == "healthy"
                    self._record_result("health", success, data)
                    return success
                except Exception as json_err:
                    print(f"❌ JSON Parse Error: {json_err}")
                    print(f"Raw Response: {response.text[:500]}")
                    self._record_result("health", False, response.text)
                    return False

            except httpx.ConnectError as e:
                print(f"❌ Connection Error: Cannot connect to {self.base_url}")
                print(f"   Is the server running? Try: python api_server.py")
                self._record_result("health", False, str(e))
                return False
            except Exception as e:
                print(f"❌ Error: {type(e).__name__}: {e}")
                self._record_result("health", False, str(e))
                return False

    async def test_root(self) -> bool:
        """Test root endpoint."""
        print("\n" + "=" * 60)
        print("🏠 Testing Root Endpoint")
        print("=" * 60)

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.get(f"{self.base_url}/")
                print(f"Status Code: {response.status_code}")

                data = self._safe_json(response)
                if data:
                    print(f"Response: {data}")
                    success = response.status_code == 200
                    self._record_result("root", success, data)
                    return success
                return False
            except httpx.ConnectError:
                print(f"❌ Cannot connect to {self.base_url}")
                self._record_result("root", False, "Connection error")
                return False
            except Exception as e:
                print(f"❌ Error: {type(e).__name__}: {e}")
                self._record_result("root", False, str(e))
                return False

    async def test_agents(self) -> bool:
        """Test list agents endpoint."""
        print("\n" + "=" * 60)
        print("🤖 Testing List Agents")
        print("=" * 60)

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.get(f"{self.base_url}/api/v1/agents")
                data = response.json()

                print(f"Status Code: {response.status_code}")
                print(f"Available Agents: {data.get('available_agents', [])}")

                success = response.status_code == 200
                self._record_result("agents", success, data)
                return success
            except Exception as e:
                print(f"❌ Error: {e}")
                self._record_result("agents", False, str(e))
                return False

    async def test_analyze(self, ticker: str = TEST_TICKER) -> bool:
        """Test stock analysis endpoint."""
        print("\n" + "=" * 60)
        print(f"📈 Testing Stock Analysis: {ticker}")
        print("=" * 60)

        payload = {
            "ticker": ticker,
            "trade_date": datetime.now().strftime("%Y-%m-%d"),
            "look_back_days": 7,
        }
        print(f"Request: {payload}")

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/analyze",
                    json=payload,
                )
                data = response.json()

                print(f"\nStatus Code: {response.status_code}")
                print(f"Success: {data.get('success')}")

                if data.get("execution_summary"):
                    summary = data["execution_summary"]
                    print(f"Steps: {summary.get('total_steps', 0)} total, "
                          f"{summary.get('successful_steps', 0)} successful, "
                          f"{summary.get('failed_steps', 0)} failed")

                if data.get("report"):
                    print(f"\n📝 Report Preview (first 500 chars):")
                    print("-" * 40)
                    print(data["report"][:500])
                    if len(data["report"]) > 500:
                        print("...")
                    print("-" * 40)

                if data.get("error"):
                    print(f"❌ Error: {data['error']}")

                success = response.status_code == 200
                self._record_result("analyze", success, data)
                return success
            except Exception as e:
                print(f"❌ Error: {e}")
                self._record_result("analyze", False, str(e))
                return False

    async def test_track(self, investor: str = TEST_INVESTOR) -> bool:
        """Test holdings tracking endpoint."""
        print("\n" + "=" * 60)
        print(f"🔍 Testing Holdings Tracking: {investor}")
        print("=" * 60)

        payload = {
            "investor_name": investor,
            "trade_date": datetime.now().strftime("%Y-%m-%d"),
        }
        print(f"Request: {payload}")

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/track",
                    json=payload,
                )
                data = response.json()

                print(f"\nStatus Code: {response.status_code}")
                print(f"Success: {data.get('success')}")

                if data.get("execution_summary"):
                    summary = data["execution_summary"]
                    print(f"Steps: {summary.get('total_steps', 0)} total, "
                          f"{summary.get('successful_steps', 0)} successful, "
                          f"{summary.get('failed_steps', 0)} failed")

                if data.get("report"):
                    print(f"\n📝 Report Preview (first 500 chars):")
                    print("-" * 40)
                    print(data["report"][:500])
                    if len(data["report"]) > 500:
                        print("...")
                    print("-" * 40)

                if data.get("error"):
                    print(f"❌ Error: {data['error']}")

                success = response.status_code == 200
                self._record_result("track", success, data)
                return success
            except Exception as e:
                print(f"❌ Error: {e}")
                self._record_result("track", False, str(e))
                return False

    async def test_screen(self, criteria: str = TEST_CRITERIA) -> bool:
        """Test stock screening endpoint."""
        print("\n" + "=" * 60)
        print(f"🔎 Testing Stock Screening: {criteria}")
        print("=" * 60)

        payload = {
            "criteria": criteria,
            "trade_date": datetime.now().strftime("%Y-%m-%d"),
        }
        print(f"Request: {payload}")

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/screen",
                    json=payload,
                )
                data = response.json()

                print(f"\nStatus Code: {response.status_code}")
                print(f"Success: {data.get('success')}")

                if data.get("execution_summary"):
                    summary = data["execution_summary"]
                    print(f"Steps: {summary.get('total_steps', 0)} total, "
                          f"{summary.get('successful_steps', 0)} successful, "
                          f"{summary.get('failed_steps', 0)} failed")

                if data.get("report"):
                    print(f"\n📝 Report Preview (first 500 chars):")
                    print("-" * 40)
                    print(data["report"][:500])
                    if len(data["report"]) > 500:
                        print("..."
                              )
                    print("-" * 40)

                if data.get("error"):
                    print(f"❌ Error: {data['error']}")

                success = response.status_code == 200
                self._record_result("screen", success, data)
                return success
            except Exception as e:
                print(f"❌ Error: {e}")
                self._record_result("screen", False, str(e))
                return False

    async def test_ask(self, query: str = TEST_QUERY) -> bool:
        """Test natural language query endpoint."""
        print("\n" + "=" * 60)
        print(f"💬 Testing Natural Language Query: {query}")
        print("=" * 60)

        payload = {"query": query}
        print(f"Request: {payload}")

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/v1/ask",
                    json=payload,
                )
                data = response.json()

                print(f"\nStatus Code: {response.status_code}")
                print(f"Success: {data.get('success')}")
                print(f"Task Type: {data.get('task_type')}")
                print(f"Target: {data.get('target')}")

                if data.get("execution_summary"):
                    summary = data["execution_summary"]
                    print(f"Steps: {summary.get('total_steps', 0)} total, "
                          f"{summary.get('successful_steps', 0)} successful, "
                          f"{summary.get('failed_steps', 0)} failed")

                if data.get("report"):
                    print(f"\n📝 Report Preview (first 500 chars):")
                    print("-" * 40)
                    print(data["report"][:500])
                    if len(data["report"]) > 500:
                        print("...")
                    print("-" * 40)

                if data.get("error"):
                    print(f"❌ Error: {data['error']}")

                success = response.status_code == 200
                self._record_result("ask", success, data)
                return success
            except Exception as e:
                print(f"❌ Error: {e}")
                self._record_result("ask", False, str(e))
                return False

    async def test_files(self) -> bool:
        """Test planning files endpoints."""
        print("\n" + "=" * 60)
        print("📁 Testing Planning Files")
        print("=" * 60)

        file_types = ["task_plan", "findings", "progress"]
        all_success = True

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            for file_type in file_types:
                try:
                    response = await client.get(
                        f"{self.base_url}/api/v1/files/{file_type}"
                    )
                    print(f"\n{file_type}: Status {response.status_code}")

                    if response.status_code == 200:
                        content = response.text[:200]
                        print(f"Content preview: {content}...")
                    else:
                        print(f"Response: {response.text}")
                        all_success = False

                except Exception as e:
                    print(f"❌ Error for {file_type}: {e}")
                    all_success = False

        self._record_result("files", all_success, None)
        return all_success

    def _safe_json(self, response: httpx.Response) -> dict | None:
        """Safely parse JSON response, printing debug info on failure."""
        try:
            return response.json()
        except Exception as e:
            print(f"❌ JSON Parse Error: {e}")
            print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
            print(f"Raw Response ({len(response.text)} chars): {response.text[:500]}")
            if len(response.text) > 500:
                print("...")
            self._record_result("json_parse", False, response.text)
            return None

    def _record_result(self, test_name: str, success: bool, data: any) -> None:
        """Record test result."""
        self.results.append({
            "test": test_name,
            "success": success,
            "data": data,
        })

    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - passed

        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")

        print("-" * 60)
        print(f"Total: {len(self.results)} | Passed: {passed} | Failed: {failed}")

        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")


async def run_quick_tests(tester: APITester) -> None:
    """Run quick connection tests (no agent execution)."""
    await tester.test_health()
    await tester.test_root()
    await tester.test_agents()


async def run_all_tests(tester: APITester) -> None:
    """Run all tests including agent execution."""
    await tester.test_health()
    await tester.test_root()
    await tester.test_agents()
    await tester.test_analyze()
    await tester.test_track()
    await tester.test_screen()
    await tester.test_ask()
    await tester.test_files()


def main():
    parser = argparse.ArgumentParser(
        description="Test the Financial Intelligence Agent API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_api.py                    # Run quick tests (health, root, agents)
  python test_api.py --test all         # Run all tests
  python test_api.py --test analyze     # Test stock analysis
  python test_api.py --test track       # Test holdings tracking
  python test_api.py --test screen      # Test stock screening
  python test_api.py --test ask         # Test natural language query
  python test_api.py --ticker NVDA      # Test with specific ticker
  python test_api.py --investor "Ray Dalio"  # Test with specific investor
        """,
    )

    parser.add_argument(
        "--test", "-t",
        choices=["health", "agents", "analyze", "track", "screen", "ask", "files", "quick", "all"],
        default="quick",
        help="Which test(s) to run (default: quick)",
    )
    parser.add_argument(
        "--url", "-u",
        default=BASE_URL,
        help=f"API base URL (default: {BASE_URL})",
    )
    parser.add_argument(
        "--ticker",
        default=TEST_TICKER,
        help=f"Stock ticker for analyze test (default: {TEST_TICKER})",
    )
    parser.add_argument(
        "--investor",
        default=TEST_INVESTOR,
        help=f"Investor name for track test (default: {TEST_INVESTOR})",
    )
    parser.add_argument(
        "--criteria",
        default=TEST_CRITERIA,
        help=f"Screening criteria (default: {TEST_CRITERIA})",
    )
    parser.add_argument(
        "--query",
        default=TEST_QUERY,
        help=f"Natural language query (default: {TEST_QUERY})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300.0,
        help="Request timeout in seconds (default: 300)",
    )

    args = parser.parse_args()

    # Create tester
    tester = APITester(base_url=args.url, timeout=args.timeout)

    print("=" * 60)
    print("🧪 Financial Intelligence Agent API Tester")
    print("=" * 60)
    print(f"Base URL: {args.url}")
    print(f"Test: {args.test}")
    print(f"Timeout: {args.timeout}s")

    # Run tests
    async def run():
        if args.test == "quick":
            await run_quick_tests(tester)
        elif args.test == "all":
            await run_all_tests(tester)
        elif args.test == "health":
            await tester.test_health()
        elif args.test == "agents":
            await tester.test_agents()
        elif args.test == "analyze":
            await tester.test_analyze(args.ticker)
        elif args.test == "track":
            await tester.test_track(args.investor)
        elif args.test == "screen":
            await tester.test_screen(args.criteria)
        elif args.test == "ask":
            await tester.test_ask(args.query)
        elif args.test == "files":
            await tester.test_files()

        tester.print_summary()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except httpx.ConnectError:
        print(f"\n❌ Cannot connect to {args.url}")
        print("   Make sure the API server is running:")
        print("   python api_server.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
