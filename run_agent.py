#!/usr/bin/env python3
"""Main entry point for the Financial Intelligence Agent.

Usage:
    # Analyze a stock
    python run_agent.py analyze AAPL

    # Track an investor's holdings
    python run_agent.py track "Warren Buffett"

    # Screen stocks
    python run_agent.py screen "high dividend yield low PE tech stocks"

    # Natural language query
    python run_agent.py ask "分析一下苹果公司的股票"
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    # Look for .env in current directory and project root
    env_paths = [
        Path(__file__).parent / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment from: {env_path}")
            break
    else:
        load_dotenv()  # Try default .env location
except ImportError:
    print("⚠️  python-dotenv not installed. Run: pip install python-dotenv")
    print("   Environment variables must be set manually.")

from tradingagents.core import (
    AgentConfig,
    FinancialAgentOrchestrator,
    TaskType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_analyze(ticker: str, trade_date: str | None = None) -> None:
    """Analyze a stock."""
    config = AgentConfig()
    orchestrator = FinancialAgentOrchestrator(config)

    print(f"\n{'='*60}")
    print(f"📈 Analyzing Stock: {ticker}")
    print(f"{'='*60}\n")

    result = await orchestrator.run(
        task_type=TaskType.STOCK_ANALYSIS,
        target=ticker,
        trade_date=trade_date or datetime.now().strftime("%Y-%m-%d"),
    )

    _print_result(result)


async def run_track(investor_name: str, trade_date: str | None = None) -> None:
    """Track an investor's holdings."""
    config = AgentConfig()
    orchestrator = FinancialAgentOrchestrator(config)

    print(f"\n{'='*60}")
    print(f"🔍 Tracking Holdings: {investor_name}")
    print(f"{'='*60}\n")

    result = await orchestrator.run(
        task_type=TaskType.HOLDINGS_TRACKING,
        target=investor_name,
        trade_date=trade_date or datetime.now().strftime("%Y-%m-%d"),
    )

    _print_result(result)


async def run_screen(criteria: str, trade_date: str | None = None) -> None:
    """Screen stocks based on criteria."""
    config = AgentConfig()
    orchestrator = FinancialAgentOrchestrator(config)

    print(f"\n{'='*60}")
    print(f"🔎 Screening Stocks: {criteria}")
    print(f"{'='*60}\n")

    result = await orchestrator.run(
        task_type=TaskType.STOCK_SCREENING,
        target=criteria,
        trade_date=trade_date or datetime.now().strftime("%Y-%m-%d"),
    )

    _print_result(result)


async def run_ask(query: str) -> None:
    """Process a natural language query."""
    config = AgentConfig()
    orchestrator = FinancialAgentOrchestrator(config)

    print(f"\n{'='*60}")
    print(f"💬 Processing Query: {query}")
    print(f"{'='*60}\n")

    result = await orchestrator.run_from_natural_language(query)

    _print_result(result)


def _print_result(result: dict) -> None:
    """Print the result in a formatted way."""
    print(f"\n{'='*60}")
    print("📊 RESULTS")
    print(f"{'='*60}\n")

    if result.get("success"):
        print("✅ Task completed successfully!\n")
    else:
        print("❌ Task completed with errors\n")
        if result.get("error"):
            print(f"Error: {result['error']}\n")

    # Print execution summary
    if "execution_summary" in result:
        summary = result["execution_summary"]
        print("📈 Execution Summary:")
        print(f"   Total Steps: {summary.get('total_steps', 0)}")
        print(f"   Successful: {summary.get('successful_steps', 0)}")
        print(f"   Failed: {summary.get('failed_steps', 0)}")
        print()

    # Print report
    if result.get("report"):
        print("📝 Report:")
        print("-" * 40)
        print(result["report"])
        print("-" * 40)

    # Print file locations
    if "files" in result:
        print("\n📁 Planning Files:")
        for name, path in result["files"].items():
            print(f"   {name}: {path}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Financial Intelligence Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_agent.py analyze AAPL
  python run_agent.py analyze NVDA --date 2025-01-15
  python run_agent.py track "Warren Buffett"
  python run_agent.py screen "high dividend yield tech stocks"
  python run_agent.py ask "分析一下苹果公司的股票"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a stock")
    analyze_parser.add_argument("ticker", help="Stock ticker symbol (e.g., AAPL)")
    analyze_parser.add_argument(
        "--date", "-d", help="Trade date (YYYY-MM-DD)", default=None
    )

    # Track command
    track_parser = subparsers.add_parser(
        "track", help="Track an investor's holdings"
    )
    track_parser.add_argument(
        "investor", help='Investor name (e.g., "Warren Buffett")'
    )
    track_parser.add_argument(
        "--date", "-d", help="Trade date (YYYY-MM-DD)", default=None
    )

    # Screen command
    screen_parser = subparsers.add_parser("screen", help="Screen stocks")
    screen_parser.add_argument(
        "criteria", help='Screening criteria (e.g., "high dividend yield")'
    )
    screen_parser.add_argument(
        "--date", "-d", help="Trade date (YYYY-MM-DD)", default=None
    )

    # Ask command
    ask_parser = subparsers.add_parser(
        "ask", help="Process a natural language query"
    )
    ask_parser.add_argument("query", help="Natural language query")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Run the appropriate command
    if args.command == "analyze":
        asyncio.run(run_analyze(args.ticker, args.date))
    elif args.command == "track":
        asyncio.run(run_track(args.investor, args.date))
    elif args.command == "screen":
        asyncio.run(run_screen(args.criteria, args.date))
    elif args.command == "ask":
        asyncio.run(run_ask(args.query))


if __name__ == "__main__":
    main()
