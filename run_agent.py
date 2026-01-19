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

    # Daily dashboard (scan markets for potential stocks)
    python run_agent.py dashboard
    python run_agent.py dashboard -m A股 港股 -n 20
    
    # Dashboard with push notification
    python run_agent.py dashboard --push                   # 推送到所有已配置渠道
    python run_agent.py dashboard --push --push-to wechat  # 仅推送到企业微信
    python run_agent.py dashboard -p --push-to feishu telegram  # 推送到飞书和Telegram

Notification Channels (configure in .env):
    - WECHAT_WEBHOOK_URL: 企业微信机器人
    - FEISHU_WEBHOOK_URL: 飞书机器人
    - TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID: Telegram Bot
    - EMAIL_SENDER + EMAIL_PASSWORD: 邮件通知（SMTP）
    - PUSHOVER_USER_KEY + PUSHOVER_API_TOKEN: Pushover（iOS/Android 推送）
    - CUSTOM_WEBHOOK_URLS: 自定义 Webhook（钉钉、Discord、Slack、Bark 等）
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


async def run_dashboard(
    markets: list[str] | None = None,
    top_n: int = 10,
    output_file: str | None = None,
    push: bool = False,
    push_channels: list[str] | None = None,
) -> None:
    """Run daily dashboard scan and output markdown report."""
    from tradingagents.core.tools.dashboard_scanner import DashboardScanner
    from tradingagents.core.notification import NotificationService

    if markets is None:
        markets = ["A股", "美股"]

    print(f"\n{'='*60}")
    print(f"📊 每日决策仪表盘")
    print(f"   扫描市场: {', '.join(markets)}")
    print(f"   推荐数量: Top {top_n}")
    if push:
        print(f"   推送通知: 开启")
    print(f"{'='*60}\n")

    scanner = DashboardScanner()

    print("⏳ 正在扫描市场，请稍候...\n")
    result = scanner.scan_market(markets=markets, top_n=top_n)

    # Generate beautiful markdown report
    markdown = _generate_dashboard_markdown(result)

    # Print to console
    print(markdown)

    # Save to file
    if output_file:
        output_path = Path(output_file)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"\n📁 报告已保存至: {output_path.absolute()}")
    else:
        # Default save to runtime directory
        runtime_dir = Path(__file__).parent / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        default_file = runtime_dir / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        default_file.write_text(markdown, encoding="utf-8")
        print(f"\n📁 报告已保存至: {default_file.absolute()}")

    # Push notification
    if push:
        print("\n📤 正在推送通知...")
        notification = NotificationService()
        
        if not notification.is_available():
            print("⚠️  未配置通知渠道。请在 .env 中配置以下任一渠道：")
            print("   - WECHAT_WEBHOOK_URL (企业微信)")
            print("   - FEISHU_WEBHOOK_URL (飞书)")
            print("   - TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID (Telegram)")
            print("   - EMAIL_SENDER + EMAIL_PASSWORD (邮件)")
            print("   - PUSHOVER_USER_KEY + PUSHOVER_API_TOKEN (Pushover)")
            print("   - CUSTOM_WEBHOOK_URLS (自定义 Webhook)")
            return
        
        print(f"   已配置渠道: {notification.get_channel_names()}")
        
        # 如果指定了特定渠道，只推送到指定渠道
        if push_channels:
            success = False
            for channel_name in push_channels:
                channel_lower = channel_name.lower()
                if "wechat" in channel_lower or "微信" in channel_lower:
                    success = notification.send_to_wechat(markdown) or success
                elif "feishu" in channel_lower or "飞书" in channel_lower:
                    success = notification.send_to_feishu(markdown) or success
                elif "telegram" in channel_lower:
                    success = notification.send_to_telegram(markdown) or success
                elif "email" in channel_lower or "邮件" in channel_lower:
                    success = notification.send_to_email(markdown) or success
                elif "pushover" in channel_lower:
                    success = notification.send_to_pushover(markdown) or success
                elif "custom" in channel_lower or "webhook" in channel_lower:
                    success = notification.send_to_custom(markdown) or success
        else:
            # 推送到所有已配置的渠道
            success = notification.send(markdown)
        
        if success:
            print("✅ 通知推送成功！")
        else:
            print("❌ 通知推送失败，请检查日志")


def _generate_dashboard_markdown(result: dict) -> str:
    """Generate beautiful markdown report from dashboard scan result."""
    lines = []
    date = result.get("date", datetime.now().strftime("%Y-%m-%d"))

    # Header
    lines.append(f"# 📊 每日决策仪表盘")
    lines.append(f"> 生成时间: {date} {datetime.now().strftime('%H:%M:%S')}")
    lines.append("")

    # Market Overview
    lines.append("## 🌐 市场概览")
    lines.append("")

    overviews = result.get("market_overviews", [])
    if overviews:
        lines.append("| 市场 | 指数 | 点位 | 涨跌幅 | 上涨家数 | 下跌家数 | 成交额(亿) |")
        lines.append("|:----:|:----:|-----:|-------:|---------:|---------:|-----------:|")
        for ov in overviews:
            if isinstance(ov, dict):
                market = ov.get("market_type", "-")
                index_name = ov.get("index_name", "-")
                index_value = ov.get("index_value", 0)
                change = ov.get("index_change_pct", 0)
                up = ov.get("up_count", 0)
                down = ov.get("down_count", 0)
                amount = ov.get("total_amount", 0)
                change_emoji = "🔴" if change < 0 else "🟢" if change > 0 else "⚪"
                lines.append(
                    f"| {market} | {index_name} | {index_value:,.2f} | "
                    f"{change_emoji} {change:+.2f}% | {up} | {down} | {amount:,.1f} |"
                )
    else:
        lines.append("_暂无市场数据_")

    lines.append("")

    # Top Recommendations
    lines.append("## 🏆 今日潜力股 Top 10")
    lines.append("")

    recommendations = result.get("recommendations", [])
    if recommendations:
        lines.append("| 排名 | 代码 | 名称 | 市场 | 现价 | 涨跌幅 | 评分 | 信号 | 推荐理由 |")
        lines.append("|:----:|:----:|:----:|:----:|-----:|-------:|:----:|:----:|:---------|")

        for i, rec in enumerate(recommendations, 1):
            code = rec.get("code", "-")
            name = rec.get("name", "-")
            market = rec.get("market", "-")
            price = rec.get("current_price", 0)
            change = rec.get("change_pct", 0)
            score = rec.get("score", 0)
            signal = rec.get("signal", "-")
            reasons = rec.get("reasons", [])

            # Signal emoji
            signal_map = {
                "极具潜力": "🚀",
                "值得关注": "📈",
                "观望": "⏸️",
                "谨慎对待": "📉",
                "风险较高": "🔻",
            }
            signal_emoji = signal_map.get(signal, "❓")

            # Score color
            if score >= 80:
                score_display = f"**{score}**"
            elif score >= 60:
                score_display = f"{score}"
            else:
                score_display = f"_{score}_"

            # Change emoji
            change_emoji = "🔴" if change < 0 else "🟢" if change > 0 else "⚪"

            # Reasons (first 2)
            reason_text = "; ".join(reasons[:2]) if reasons else "-"

            lines.append(
                f"| {i} | `{code}` | {name} | {market} | "
                f"{price:.2f} | {change_emoji} {change:+.2f}% | "
                f"{score_display} | {signal_emoji} {signal} | {reason_text} |"
            )

        lines.append("")

        # Detailed analysis for top 3
        lines.append("### 📋 重点推荐详情")
        lines.append("")

        for i, rec in enumerate(recommendations[:3], 1):
            code = rec.get("code", "-")
            name = rec.get("name", "-")
            market = rec.get("market", "-")
            price = rec.get("current_price", 0)
            score = rec.get("score", 0)
            signal = rec.get("signal", "-")
            reasons = rec.get("reasons", [])
            data_source = rec.get("data_source", "-")

            # Technical indicators (improved)
            ma5 = rec.get("ma5", 0)
            ma10 = rec.get("ma10", 0)
            ma20 = rec.get("ma20", 0)
            ma60 = rec.get("ma60", 0)
            rsi = rec.get("rsi", 50)
            adx = rec.get("adx", 0)
            bias = rec.get("bias", 0)
            macd_hist = rec.get("macd_hist", 0)
            volume_ratio = rec.get("volume_ratio", 1)
            
            # Key price levels
            entry_price = rec.get("entry_price", price)
            stop_loss = rec.get("stop_loss", 0)
            target_price = rec.get("target_price", 0)
            risk_reward = rec.get("risk_reward_ratio", 0)
            support = rec.get("support", 0)
            resistance = rec.get("resistance", 0)
            
            # Checklist stats
            checklist_pass = rec.get("checklist_pass", 0)
            checklist_warn = rec.get("checklist_warn", 0)
            checklist_fail = rec.get("checklist_fail", 0)

            lines.append(f"#### {i}. {name} (`{code}`) - {market}")
            lines.append("")
            
            # 核心信息表格
            lines.append("| 指标 | 数值 | 指标 | 数值 |")
            lines.append("|:-----|-----:|:-----|-----:|")
            lines.append(f"| **现价** | ¥{price:.2f} | **评分** | {score}/100 |")
            lines.append(f"| **乖离率** | {bias:+.1f}% | **RSI** | {rsi:.0f} |")
            lines.append(f"| **ADX** | {adx:.1f} | **MACD柱** | {macd_hist:+.2f} |")
            lines.append(f"| **量比** | {volume_ratio:.2f} | **信号** | {signal} |")
            lines.append("")
            
            # 精确点位（核心！）
            lines.append("**📍 精确点位**")
            lines.append("")
            lines.append("| 买入价 | 止损价 | 目标价 | 盈亏比 |")
            lines.append("|-------:|-------:|-------:|:------:|")
            lines.append(f"| ¥{entry_price:.2f} | ¥{stop_loss:.2f} | ¥{target_price:.2f} | {risk_reward:.1f}:1 |")
            lines.append("")
            
            # 支撑/阻力
            lines.append(f"- **支撑位**: ¥{support:.2f} | **阻力位**: ¥{resistance:.2f}")
            lines.append("")
            
            # 检查清单统计
            lines.append(f"**📋 检查清单**: ✅ {checklist_pass} 通过 | ⚠️ {checklist_warn} 警告 | ❌ {checklist_fail} 失败")
            lines.append("")
            
            # MA 排列
            if ma5 > ma10 > ma20:
                ma_status = "✅ 多头排列"
            elif ma5 < ma10 < ma20:
                ma_status = "❌ 空头排列"
            else:
                ma_status = "⚠️ 均线交叉"
            lines.append(f"**均线状态**: {ma_status}")
            lines.append(f"- MA5: {ma5:.2f} | MA10: {ma10:.2f} | MA20: {ma20:.2f} | MA60: {ma60:.2f}")
            lines.append("")
            
            # 风险提示
            if abs(bias) > 5:
                lines.append(f"⚠️ **风险提示**: 乖离率 {bias:+.1f}% 超过 5%，注意追高风险！")
                lines.append("")
            
            # 分析要点（过滤点位信息）
            lines.append("**分析要点**:")
            for reason in reasons:
                if reason and not reason.startswith("📍") and not reason.startswith("   "):
                    lines.append(f"- {reason}")
            lines.append("")
            
            lines.append(f"*数据来源: {data_source}*")
            lines.append("")
            lines.append("---")
            lines.append("")
    else:
        lines.append("_暂无推荐股票_")

    lines.append("")

    # Summary
    summary = result.get("summary", "")
    if summary:
        lines.append("## 📝 市场总结")
        lines.append("")
        lines.append(summary)
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append("*本报告由 Clarity 金融智能体自动生成，仅供参考，不构成投资建议。*")
    lines.append("")

    return "\n".join(lines)


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
  python run_agent.py dashboard                           # 扫描 A股+美股
  python run_agent.py dashboard -m A股 港股              # 扫描指定市场
  python run_agent.py dashboard -n 20 -o report.md       # 推荐20只，保存到文件
  python run_agent.py dashboard --push                   # 扫描并推送通知
  python run_agent.py dashboard --push --push-to wechat  # 仅推送到企业微信
  python run_agent.py dashboard -p --push-to feishu telegram  # 推送到飞书和Telegram
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

    # Dashboard command
    dashboard_parser = subparsers.add_parser(
        "dashboard", help="Run daily dashboard scan"
    )
    dashboard_parser.add_argument(
        "--markets",
        "-m",
        nargs="+",
        default=["A股", "美股"],
        choices=["A股", "美股", "港股"],
        help="Markets to scan (default: A股 美股)",
    )
    dashboard_parser.add_argument(
        "--top",
        "-n",
        type=int,
        default=10,
        help="Number of top stocks to recommend (default: 10)",
    )
    dashboard_parser.add_argument(
        "--output",
        "-o",
        help="Output file path for markdown report",
    )
    dashboard_parser.add_argument(
        "--push",
        "-p",
        action="store_true",
        help="Push report to configured notification channels",
    )
    dashboard_parser.add_argument(
        "--push-to",
        nargs="+",
        choices=["wechat", "feishu", "telegram", "email", "pushover", "custom"],
        help="Specify notification channels to push to (default: all configured)",
    )

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
    elif args.command == "dashboard":
        push_channels = getattr(args, "push_to", None)
        asyncio.run(run_dashboard(args.markets, args.top, args.output, args.push, push_channels))


if __name__ == "__main__":
    main()
