#!/usr/bin/env python3
"""
Clarity Web UI - 金融分析智能体 Web 界面

基于 Gradio 构建的现代化 Web 界面，支持：
- 股票分析
- 持仓跟踪
- 股票筛选
- 自然语言查询
- 决策仪表盘
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Bypass proxy for localhost (fix Gradio startup issue)
os.environ.setdefault("NO_PROXY", "localhost,127.0.0.1")
os.environ.setdefault("no_proxy", "localhost,127.0.0.1")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except (ImportError, PermissionError, OSError):
    pass

import gradio as gr

from clarity.core import (
    AgentConfig,
    FinancialAgentOrchestrator,
    TaskType,
)
from clarity.core.tools.dashboard_scanner import DashboardScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
_orchestrator = None


def get_orchestrator():
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        config = AgentConfig()
        _orchestrator = FinancialAgentOrchestrator(config)
    return _orchestrator


# ========== 股票分析 (流式输出) ==========

def analyze_stock_streaming(ticker: str, trade_date: str = None):
    """
    Analyze a stock with streaming output.
    """
    import time
    
    if not ticker.strip():
        yield "❌ 请输入股票代码"
        return
    
    ticker = ticker.strip().upper()
    date = trade_date if trade_date else datetime.now().strftime("%Y-%m-%d")
    
    # 开始动画
    yield f"# 📈 {ticker} 股票分析\n\n"
    yield f"> 🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    yield "---\n\n"
    
    try:
        # 阶段 1: 获取数据
        yield "## ⏳ 正在分析...\n\n"
        yield f"**⠋ 正在获取 {ticker} 的历史数据...**\n\n"
        time.sleep(0.5)
        
        # 使用 DashboardScanner 进行分析
        scanner = DashboardScanner()
        
        # 检测市场类型
        from clarity.core.tools.data_provider import detect_market_type, MarketType
        market_type = detect_market_type(ticker)
        
        if market_type == MarketType.A_SHARE:
            market = "A股"
        elif market_type == MarketType.US_STOCK:
            market = "美股"
        elif market_type == MarketType.HK_STOCK:
            market = "港股"
        else:
            market = "未知"
        
        yield f"  📍 检测到市场: {market}\n"
        yield f"  📥 正在下载K线数据...\n\n"
        
        # 阶段 2: 技术分析
        yield f"**⠹ 正在计算技术指标...**\n\n"
        time.sleep(0.3)
        
        rec = scanner._analyze_stock(ticker, market)
        
        if rec is None:
            yield f"\n❌ **无法获取 {ticker} 的数据**\n\n"
            yield "可能原因：\n"
            yield "- 股票代码不正确\n"
            yield "- 数据源暂时不可用\n"
            yield "- 该股票已停牌或退市\n"
            return
        
        yield "  ✅ 均线指标 (MA5/MA10/MA20/MA60)\n"
        yield "  ✅ 动量指标 (RSI/MACD/KDJ)\n"
        yield "  ✅ 趋势指标 (ADX/BIAS)\n"
        yield "  ✅ 波动指标 (ATR)\n"
        yield "  ✅ 支撑/阻力位\n\n"
        
        # 阶段 3: 生成检查清单
        yield f"**⠼ 正在生成交易检查清单...**\n\n"
        time.sleep(0.3)
        
        cl = rec.checklist
        yield f"  📋 检查清单: ✅{cl.pass_count()} ⚠️{cl.warning_count()} ❌{cl.fail_count()}\n\n"
        
        yield "---\n\n"
        yield "## ✅ 分析完成！\n\n"
        
        # 阶段 4: 输出详细报告
        yield f"# 📈 {rec.name} (`{rec.code}`) 分析报告\n\n"
        yield f"> 市场: {rec.market} | 数据来源: {rec.data_source}\n\n"
        
        # 核心信息
        yield "## 📊 核心指标\n\n"
        yield "| 指标 | 数值 | 指标 | 数值 |\n"
        yield "|:-----|-----:|:-----|-----:|\n"
        yield f"| **现价** | ¥{rec.current_price:.2f} | **涨跌幅** | {rec.change_pct:+.2f}% |\n"
        yield f"| **评分** | {rec.score}/100 | **信号** | {rec.signal.value} |\n"
        yield f"| **乖离率** | {rec.bias:+.1f}% | **RSI** | {rec.rsi:.0f} |\n"
        yield f"| **ADX** | {rec.adx:.1f} | **量比** | {rec.volume_ratio:.2f} |\n\n"
        
        # 精确点位
        yield "## 📍 精确点位\n\n"
        yield "| 买入价 | 止损价 | 目标价 | 盈亏比 |\n"
        yield "|-------:|-------:|-------:|:------:|\n"
        yield f"| ¥{cl.entry_price:.2f} | ¥{cl.stop_loss:.2f} | ¥{cl.target_price:.2f} | {cl.risk_reward_ratio:.1f}:1 |\n\n"
        
        yield f"- **支撑位**: ¥{rec.support:.2f}\n"
        yield f"- **阻力位**: ¥{rec.resistance:.2f}\n\n"
        
        # 均线状态
        yield "## 📈 均线分析\n\n"
        if rec.ma5 > rec.ma10 > rec.ma20:
            yield "**✅ 多头排列** - MA5 > MA10 > MA20\n\n"
        elif rec.ma5 < rec.ma10 < rec.ma20:
            yield "**❌ 空头排列** - MA5 < MA10 < MA20\n\n"
        else:
            yield "**⚠️ 均线交叉** - 趋势不明朗\n\n"
        
        yield f"| MA5 | MA10 | MA20 | MA60 |\n"
        yield f"|----:|-----:|-----:|-----:|\n"
        yield f"| {rec.ma5:.2f} | {rec.ma10:.2f} | {rec.ma20:.2f} | {rec.ma60:.2f} |\n\n"
        
        # MACD
        yield "## 📊 MACD 分析\n\n"
        if rec.macd_hist > 0:
            yield f"**{'✅ 金叉向上' if rec.macd > rec.macd_signal else '⚠️ 金叉但动能减弱'}**\n\n"
        else:
            yield f"**{'❌ 死叉向下' if rec.macd < rec.macd_signal else '⚠️ 死叉但有反弹迹象'}**\n\n"
        
        yield f"- MACD: {rec.macd:.2f}\n"
        yield f"- 信号线: {rec.macd_signal:.2f}\n"
        yield f"- 柱状图: {rec.macd_hist:+.2f}\n\n"
        
        # KDJ
        yield "## 📉 KDJ 分析\n\n"
        yield f"| K | D | J |\n"
        yield f"|--:|--:|--:|\n"
        yield f"| {rec.kdj_k:.1f} | {rec.kdj_d:.1f} | {rec.kdj_j:.1f} |\n\n"
        
        if rec.kdj_k > rec.kdj_d:
            yield "**✅ KDJ 金叉**\n\n"
        else:
            yield "**❌ KDJ 死叉**\n\n"
        
        # 检查清单
        yield "## 📋 交易检查清单\n\n"
        yield "### 趋势确认\n"
        yield f"- {cl.ma_alignment} MA 排列\n"
        yield f"- {cl.macd_cross} MACD 状态\n"
        yield f"- {cl.trend_strength} 趋势强度 (ADX={rec.adx:.1f})\n"
        yield f"- {cl.price_position} 价格位置\n\n"
        
        yield "### 风险控制\n"
        yield f"- {cl.bias_check} 乖离率 ({rec.bias:+.1f}%)\n"
        yield f"- {cl.volatility_ok} 波动率\n"
        yield f"- {cl.volume_confirm} 量价配合\n"
        yield f"- {cl.stop_loss_clear} 止损清晰\n\n"
        
        yield "### 买入时机\n"
        yield f"- {cl.rsi_zone} RSI 区间 ({rec.rsi:.0f})\n"
        yield f"- {cl.kdj_signal} KDJ 信号\n"
        yield f"- {cl.support_near} 支撑位距离\n"
        yield f"- {cl.pullback_buy} 回调买入\n\n"
        
        yield "### 盈利空间\n"
        yield f"- {cl.upside_room} 上涨空间\n"
        yield f"- {cl.risk_reward} 盈亏比 ({cl.risk_reward_ratio:.1f}:1)\n\n"
        
        # 风险提示
        if abs(rec.bias) > 5:
            yield "---\n\n"
            yield f"## ⚠️ 风险提示\n\n"
            yield f"**乖离率 {rec.bias:+.1f}% 超过 5%，存在追高风险！**\n\n"
        
        # 分析要点
        yield "---\n\n"
        yield "## 📝 分析要点\n\n"
        for reason in rec.reasons:
            if reason and not reason.startswith("📍") and not reason.startswith("   "):
                yield f"- {reason}\n"
        
        yield "\n---\n\n"
        yield f"*本报告由 Clarity 金融智能体生成，仅供参考，不构成投资建议。*\n"
        
    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}", exc_info=True)
        yield f"\n\n❌ **分析出错**: {str(e)}\n"


def analyze_stock(ticker: str, trade_date: str = None):
    """Non-streaming version for backwards compatibility."""
    result = ""
    for chunk in analyze_stock_streaming(ticker, trade_date):
        result += chunk
    return result


# ========== 持仓跟踪 (流式输出) ==========

def track_holdings_streaming(investor_name: str, trade_date: str = None):
    """Track investor holdings with streaming output."""
    import time
    
    if not investor_name.strip():
        yield "❌ 请输入投资者姓名"
        return
    
    investor = investor_name.strip()
    date = trade_date if trade_date else datetime.now().strftime("%Y-%m-%d")
    
    yield f"# 🔍 {investor} 持仓跟踪\n\n"
    yield f"> 🕐 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    yield "---\n\n"
    
    yield "## ⏳ 正在查询...\n\n"
    
    # 模拟步骤
    steps = [
        ("⠋ 搜索投资者公开持仓信息...", 1.0),
        ("⠹ 解析 SEC 13F 报告...", 0.8),
        ("⠼ 获取最新持仓变动...", 0.6),
        ("⠴ 分析持仓策略...", 0.5),
        ("⠧ 生成报告...", 0.3),
    ]
    
    for step_text, delay in steps:
        yield f"**{step_text}**\n\n"
        time.sleep(delay)
    
    try:
        orchestrator = get_orchestrator()
        
        # 使用 asyncio 运行异步函数
        async def _run():
            return await orchestrator.run(
                task_type=TaskType.HOLDINGS_TRACKING,
                target=investor,
                trade_date=date,
            )
        
        result = asyncio.run(_run())
        
        yield "---\n\n"
        
        if result.get("success"):
            report = result.get("report", "跟踪完成，但未生成报告")
            yield f"## ✅ 查询完成！\n\n"
            yield report
        else:
            error = result.get("error", "未知错误")
            yield f"## ❌ 跟踪失败\n\n{error}\n"
            
    except Exception as e:
        logger.error(f"Error tracking {investor}: {e}", exc_info=True)
        yield f"\n\n❌ **跟踪出错**: {str(e)}\n"


def track_holdings(investor_name: str, trade_date: str = None):
    """Non-streaming version."""
    result = ""
    for chunk in track_holdings_streaming(investor_name, trade_date):
        result += chunk
    return result


# ========== 股票筛选 (流式输出) ==========

def screen_stocks_streaming(criteria: str, trade_date: str = None):
    """Screen stocks with streaming output."""
    import time
    
    if not criteria.strip():
        yield "❌ 请输入筛选条件"
        return
    
    criteria = criteria.strip()
    date = trade_date if trade_date else datetime.now().strftime("%Y-%m-%d")
    
    yield f"# 🔎 股票筛选\n\n"
    yield f"> 筛选条件: **{criteria}**\n\n"
    yield f"> 🕐 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    yield "---\n\n"
    
    yield "## ⏳ 正在筛选...\n\n"
    
    # 模拟步骤
    steps = [
        ("⠋ 解析筛选条件...", 0.5),
        ("⠹ 获取股票列表...", 0.8),
        ("⠼ 应用筛选规则...", 1.0),
        ("⠴ 计算技术指标...", 0.8),
        ("⠧ 排序并生成结果...", 0.5),
    ]
    
    for step_text, delay in steps:
        yield f"**{step_text}**\n\n"
        time.sleep(delay)
    
    try:
        orchestrator = get_orchestrator()
        
        async def _run():
            return await orchestrator.run(
                task_type=TaskType.STOCK_SCREENING,
                target=criteria,
                trade_date=date,
            )
        
        result = asyncio.run(_run())
        
        yield "---\n\n"
        
        if result.get("success"):
            report = result.get("report", "筛选完成，但未生成报告")
            yield f"## ✅ 筛选完成！\n\n"
            yield report
        else:
            error = result.get("error", "未知错误")
            yield f"## ❌ 筛选失败\n\n{error}\n"
            
    except Exception as e:
        logger.error(f"Error screening stocks: {e}", exc_info=True)
        yield f"\n\n❌ **筛选出错**: {str(e)}\n"


def screen_stocks(criteria: str, trade_date: str = None):
    """Non-streaming version."""
    result = ""
    for chunk in screen_stocks_streaming(criteria, trade_date):
        result += chunk
    return result


# ========== 自然语言查询 (流式输出) ==========

def ask_query_streaming(query: str):
    """Process natural language query with streaming output."""
    import time
    
    if not query.strip():
        yield "❌ 请输入查询内容"
        return
    
    query = query.strip()
    
    yield f"# 💬 智能问答\n\n"
    yield f"> **问题**: {query}\n\n"
    yield f"> 🕐 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    yield "---\n\n"
    
    yield "## ⏳ 正在思考...\n\n"
    
    # 模拟思考步骤
    steps = [
        ("⠋ 理解问题意图...", 0.5),
        ("⠹ 确定任务类型...", 0.4),
        ("⠼ 收集相关数据...", 0.8),
        ("⠴ 分析并生成回答...", 0.6),
    ]
    
    for step_text, delay in steps:
        yield f"**{step_text}**\n\n"
        time.sleep(delay)
    
    try:
        orchestrator = get_orchestrator()
        
        async def _run():
            return await orchestrator.run_from_natural_language(query)
        
        result = asyncio.run(_run())
        
        yield "---\n\n"
        
        if result.get("success"):
            report = result.get("report", "查询完成，但未生成报告")
            yield f"## ✅ 回答完成！\n\n"
            yield report
        else:
            error = result.get("error", "未知错误")
            yield f"## ❌ 查询失败\n\n{error}\n"
            
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        yield f"\n\n❌ **查询出错**: {str(e)}\n"


def ask_query(query: str):
    """Non-streaming version."""
    result = ""
    for chunk in ask_query_streaming(query):
        result += chunk
    return result


# ========== 决策仪表盘 (流式输出) ==========

def run_dashboard_streaming(markets: list, top_n: int = 10):
    """
    Run dashboard scan with streaming output.
    
    使用 yield 逐步输出结果，让用户看到执行进度。
    """
    import time
    
    if not markets:
        markets = ["A股", "美股"]
    
    # 动画帧
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    try:
        # ===== 阶段 1: 初始化 =====
        yield "# 📊 每日决策仪表盘\n\n"
        yield f"> 🕐 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        yield "---\n\n"
        yield "## ⏳ 正在扫描...\n\n"
        
        scanner = DashboardScanner()
        
        # ===== 阶段 2: 扫描市场概览 =====
        yield "### 📡 获取市场概览\n\n"
        
        all_overviews = []
        all_candidates = []
        
        for i, market in enumerate(markets):
            # 显示当前正在扫描的市场
            yield f"**{spinner_frames[i % len(spinner_frames)]} 正在扫描 {market} 市场...**\n\n"
            time.sleep(0.3)  # 小延迟让用户看到动画
            
            try:
                if market == 'A股':
                    overview = scanner._scan_a_share()
                    yield f"  ✅ {market} 大盘数据获取成功\n"
                elif market == '美股':
                    overview = scanner._scan_us_market()
                    yield f"  ✅ {market} 大盘数据获取成功\n"
                elif market == '港股':
                    overview = scanner._scan_hk_market()
                    yield f"  ✅ {market} 大盘数据获取成功\n"
                else:
                    overview = None
                
                if overview:
                    all_overviews.append(overview)
                    # 显示概览信息
                    if hasattr(overview, 'index_name'):
                        change_emoji = "🟢" if overview.index_change_pct > 0 else "🔴" if overview.index_change_pct < 0 else "⚪"
                        yield f"  📈 {overview.index_name}: {overview.index_value:,.2f} ({change_emoji} {overview.index_change_pct:+.2f}%)\n"
                    yield "\n"
                    
            except Exception as e:
                yield f"  ⚠️ {market} 大盘获取失败: {str(e)[:50]}\n\n"
        
        yield "---\n\n"
        
        # ===== 阶段 3: 扫描个股 =====
        yield "### 🔍 扫描热门股票\n\n"
        
        for market in markets:
            yield f"**{spinner_frames[0]} 正在扫描 {market} 热门股票...**\n\n"
            
            try:
                if market == 'A股':
                    hot_stocks = scanner._get_hot_a_shares(limit=50)
                    yield f"  📋 获取到 {len(hot_stocks)} 只 A股 热门股票\n"
                    yield "  ⏳ 正在分析技术指标...\n\n"
                    
                    # 进度条模拟
                    analyzed = 0
                    for j, code in enumerate(hot_stocks):
                        try:
                            rec = scanner._analyze_stock(code, 'A股')
                            if rec and rec.score >= 50:
                                all_candidates.append(rec)
                            analyzed += 1
                            
                            # 每分析10只股票更新一次进度
                            if (j + 1) % 10 == 0 or j == len(hot_stocks) - 1:
                                progress = (j + 1) / len(hot_stocks) * 100
                                bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
                                yield f"  [{bar}] {progress:.0f}% ({j+1}/{len(hot_stocks)})\n"
                                
                        except Exception:
                            pass
                    
                    yield f"  ✅ A股 分析完成，找到 {len([c for c in all_candidates if c.market == 'A股'])} 只值得关注\n\n"
                    
                elif market == '美股':
                    hot_stocks = scanner._get_hot_us_stocks(limit=50)
                    yield f"  📋 获取到 {len(hot_stocks)} 只 美股 热门股票\n"
                    yield "  ⏳ 正在分析技术指标...\n\n"
                    
                    analyzed = 0
                    for j, code in enumerate(hot_stocks):
                        try:
                            rec = scanner._analyze_stock(code, '美股')
                            if rec and rec.score >= 50:
                                all_candidates.append(rec)
                            analyzed += 1
                            
                            if (j + 1) % 10 == 0 or j == len(hot_stocks) - 1:
                                progress = (j + 1) / len(hot_stocks) * 100
                                bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
                                yield f"  [{bar}] {progress:.0f}% ({j+1}/{len(hot_stocks)})\n"
                                
                        except Exception:
                            pass
                    
                    yield f"  ✅ 美股 分析完成，找到 {len([c for c in all_candidates if c.market == '美股'])} 只值得关注\n\n"
                    
                elif market == '港股':
                    hot_stocks = scanner._get_hot_hk_stocks(limit=30)
                    yield f"  📋 获取到 {len(hot_stocks)} 只 港股 热门股票\n"
                    yield "  ⏳ 正在分析技术指标...\n\n"
                    
                    for j, code in enumerate(hot_stocks):
                        try:
                            rec = scanner._analyze_stock(code, '港股')
                            if rec and rec.score >= 50:
                                all_candidates.append(rec)
                            
                            if (j + 1) % 10 == 0 or j == len(hot_stocks) - 1:
                                progress = (j + 1) / len(hot_stocks) * 100
                                bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
                                yield f"  [{bar}] {progress:.0f}% ({j+1}/{len(hot_stocks)})\n"
                                
                        except Exception:
                            pass
                    
                    yield f"  ✅ 港股 分析完成，找到 {len([c for c in all_candidates if c.market == '港股'])} 只值得关注\n\n"
                    
            except Exception as e:
                yield f"  ❌ {market} 扫描失败: {str(e)[:100]}\n\n"
        
        yield "---\n\n"
        
        # ===== 阶段 4: 排序并生成报告 =====
        yield "### 📊 生成分析报告\n\n"
        yield f"**{spinner_frames[3]} 正在对 {len(all_candidates)} 只值得关注进行排序...**\n\n"
        
        # 排序
        all_candidates.sort(key=lambda x: x.score, reverse=True)
        top_candidates = all_candidates[:top_n]
        
        yield f"  ✅ 筛选出 Top {len(top_candidates)} 值得关注\n\n"
        
        # 构建结果
        result = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'market_overviews': [ov.to_dict() if hasattr(ov, 'to_dict') else ov for ov in all_overviews],
            'recommendations': [c.to_dict() for c in top_candidates],
            'summary': '',
        }
        
        # ===== 阶段 5: 清空之前的进度信息，输出最终报告 =====
        yield "\n---\n\n"
        yield "## ✅ 扫描完成！\n\n"
        
        # 生成最终的 markdown 报告
        final_report = generate_dashboard_markdown(result)
        yield final_report
        
    except Exception as e:
        logger.error(f"Error running dashboard: {e}", exc_info=True)
        yield f"\n\n❌ **仪表盘扫描出错**: {str(e)}\n"


def run_dashboard(markets: list, top_n: int = 10):
    """Non-streaming version for backwards compatibility."""
    if not markets:
        markets = ["A股", "美股"]
    
    try:
        scanner = DashboardScanner()
        result = scanner.scan_market(markets=markets, top_n=top_n)
        markdown = generate_dashboard_markdown(result)
        return markdown
    except Exception as e:
        logger.error(f"Error running dashboard: {e}", exc_info=True)
        return f"❌ 仪表盘扫描出错: {str(e)}"


def generate_dashboard_markdown(result: dict) -> str:
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
        lines.append("| 市场 | 指数 | 点位 | 涨跌幅 | 上涨家数 | 下跌家数 |")
        lines.append("|:----:|:----:|-----:|-------:|---------:|---------:|")
        for ov in overviews:
            if isinstance(ov, dict):
                market = ov.get("market_type", "-")
                index_name = ov.get("index_name", "-")
                index_value = ov.get("index_value", 0)
                change = ov.get("index_change_pct", 0)
                up = ov.get("up_count", 0)
                down = ov.get("down_count", 0)
                change_emoji = "🔴" if change < 0 else "🟢" if change > 0 else "⚪"
                lines.append(
                    f"| {market} | {index_name} | {index_value:,.2f} | "
                    f"{change_emoji} {change:+.2f}% | {up} | {down} |"
                )
    else:
        lines.append("_暂无市场数据_")

    lines.append("")

    # Top Recommendations
    lines.append("## 🏆 今日值得关注 Top 10")
    lines.append("")

    recommendations = result.get("recommendations", [])
    if recommendations:
        lines.append("| 排名 | 代码 | 名称 | 市场 | 现价 | 涨跌幅 | 评分 | 信号 |")
        lines.append("|:----:|:----:|:----:|:----:|-----:|-------:|:----:|:----:|")

        signal_map = {
            "极具潜力": "🚀",
            "值得关注": "📈",
            "观望": "⏸️",
            "谨慎对待": "📉",
            "风险较高": "🔻",
        }

        for i, rec in enumerate(recommendations, 1):
            code = rec.get("code", "-")
            name = rec.get("name", "-")
            market = rec.get("market", "-")
            price = rec.get("current_price", 0)
            change = rec.get("change_pct", 0)
            score = rec.get("score", 0)
            signal = rec.get("signal", "-")
            signal_emoji = signal_map.get(signal, "❓")
            change_emoji = "🔴" if change < 0 else "🟢" if change > 0 else "⚪"

            lines.append(
                f"| {i} | `{code}` | {name} | {market} | "
                f"{price:.2f} | {change_emoji} {change:+.2f}% | "
                f"{score} | {signal_emoji} {signal} |"
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
            
            # 关键点位
            entry_price = rec.get("entry_price", price)
            stop_loss = rec.get("stop_loss", 0)
            target_price = rec.get("target_price", 0)
            risk_reward = rec.get("risk_reward_ratio", 0)
            
            # 检查清单统计
            checklist_pass = rec.get("checklist_pass", 0)
            checklist_warn = rec.get("checklist_warn", 0)
            checklist_fail = rec.get("checklist_fail", 0)
            
            # 关键指标
            bias = rec.get("bias", 0)
            rsi = rec.get("rsi", 50)
            adx = rec.get("adx", 0)
            macd_hist = rec.get("macd_hist", 0)

            lines.append(f"#### {i}. {name} (`{code}`) - {market}")
            lines.append("")
            lines.append(f"| 指标 | 数值 | 指标 | 数值 |")
            lines.append(f"|:-----|-----:|:-----|-----:|")
            lines.append(f"| **现价** | ¥{price:.2f} | **评分** | {score}/100 |")
            lines.append(f"| **乖离率** | {bias:+.1f}% | **RSI** | {rsi:.0f} |")
            lines.append(f"| **ADX** | {adx:.1f} | **MACD柱** | {macd_hist:+.2f} |")
            lines.append("")
            
            # 关键点位（精确点位）
            lines.append("**📍 精确点位**")
            lines.append("")
            lines.append(f"| 买入价 | 止损价 | 目标价 | 盈亏比 |")
            lines.append(f"|-------:|-------:|-------:|:------:|")
            lines.append(f"| ¥{entry_price:.2f} | ¥{stop_loss:.2f} | ¥{target_price:.2f} | {risk_reward:.1f}:1 |")
            lines.append("")
            
            # 检查清单统计
            lines.append(f"**📋 检查清单**: ✅{checklist_pass} ⚠️{checklist_warn} ❌{checklist_fail}")
            lines.append("")
            
            # 推荐理由（过滤空行和点位信息，因为已单独展示）
            if reasons:
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

    return "\n".join(lines)


# ========== 构建 Web UI ==========

def create_ui():
    """Create the Gradio UI."""
    
    # Custom CSS for better styling
    custom_css = """
    .gradio-container {
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .gr-button-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
    }
    .gr-button-primary:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    .markdown-text h1 {
        color: #1a1a2e;
        border-bottom: 2px solid #667eea;
        padding-bottom: 10px;
    }
    .markdown-text h2 {
        color: #16213e;
        margin-top: 20px;
    }
    .tab-nav button {
        font-weight: 600 !important;
    }
    .tab-nav button.selected {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    """
    
    # Store theme and css for launch()
    theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="purple",
        neutral_hue="slate",
    )
    
    with gr.Blocks(title="Clarity - 金融分析智能体") as demo:
        # Store theme and css as attributes for launch
        demo._custom_theme = theme
        demo._custom_css = custom_css
        
        # Header
        gr.Markdown(
            """
            <div style="text-align: center; padding: 20px 0;">
                <h1 style="font-size: 2.5em; margin-bottom: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    🔮 Clarity
                </h1>
                <p style="font-size: 1.2em; color: #666;">
                    基于 Claude-skill 架构的金融分析智能体
                </p>
                <p style="color: #888; font-size: 0.9em;">
                    Powered by <a href="https://www.cooragent.com/" target="_blank" style="color: #667eea;">Cooragent</a>
                </p>
            </div>
            """
        )
        
        with gr.Tabs():
            
            # ===== 决策仪表盘 Tab =====
            with gr.TabItem("📊 决策仪表盘", id="dashboard"):
                gr.Markdown("### 每日市场扫描，发现值得关注票")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        dashboard_markets = gr.CheckboxGroup(
                            choices=["A股", "美股", "港股"],
                            value=["A股", "美股"],
                            label="扫描市场",
                        )
                        dashboard_top_n = gr.Slider(
                            minimum=5,
                            maximum=30,
                            value=10,
                            step=5,
                            label="推荐数量",
                        )
                        dashboard_btn = gr.Button(
                            "🔍 开始扫描",
                            variant="primary",
                            size="lg",
                        )
                    
                    with gr.Column(scale=3):
                        dashboard_output = gr.Markdown(
                            value="点击「开始扫描」生成今日决策仪表盘...",
                            elem_classes=["markdown-text"],
                            height=600,
                        )
                
                dashboard_btn.click(
                    fn=run_dashboard_streaming,
                    inputs=[dashboard_markets, dashboard_top_n],
                    outputs=dashboard_output,
                )
            
            # ===== 股票分析 Tab =====
            with gr.TabItem("📈 股票分析", id="analyze"):
                gr.Markdown("### 深度分析特定股票的技术面、基本面、新闻和市场情绪")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        analyze_ticker = gr.Textbox(
                            label="股票代码",
                            placeholder="例如: AAPL, NVDA, 600519",
                            lines=1,
                        )
                        analyze_date = gr.Textbox(
                            label="交易日期（可选）",
                            placeholder="YYYY-MM-DD，留空使用今天",
                            lines=1,
                        )
                        analyze_btn = gr.Button(
                            "🔍 开始分析",
                            variant="primary",
                            size="lg",
                        )
                        
                        gr.Markdown(
                            """
                            **支持的股票代码格式：**
                            - 美股: `AAPL`, `NVDA`, `TSLA`
                            - A股: `600519`, `000001`, `300750`
                            - 港股: `00700`, `09988`
                            """
                        )
                    
                    with gr.Column(scale=3):
                        analyze_output = gr.Markdown(
                            value="输入股票代码后点击「开始分析」...",
                            elem_classes=["markdown-text"],
                            height=600,  # 设置固定高度，使内容可滚动
                        )
                
                analyze_btn.click(
                    fn=analyze_stock_streaming,
                    inputs=[analyze_ticker, analyze_date],
                    outputs=analyze_output,
                )
            
            # ===== 持仓跟踪 Tab =====
            with gr.TabItem("🔍 持仓跟踪", id="track"):
                gr.Markdown("### 追踪知名投资者的最新持仓变化")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        track_investor = gr.Textbox(
                            label="投资者姓名",
                            placeholder="例如: Warren Buffett",
                            lines=1,
                        )
                        track_date = gr.Textbox(
                            label="交易日期（可选）",
                            placeholder="YYYY-MM-DD，留空使用今天",
                            lines=1,
                        )
                        track_btn = gr.Button(
                            "🔍 开始跟踪",
                            variant="primary",
                            size="lg",
                        )
                        
                        gr.Markdown(
                            """
                            **热门投资者：**
                            - Warren Buffett
                            - Ray Dalio
                            - Cathie Wood
                            - Michael Burry
                            """
                        )
                    
                    with gr.Column(scale=3):
                        track_output = gr.Markdown(
                            value="输入投资者姓名后点击「开始跟踪」...",
                            elem_classes=["markdown-text"],
                            height=600,
                        )
                
                track_btn.click(
                    fn=track_holdings_streaming,
                    inputs=[track_investor, track_date],
                    outputs=track_output,
                )
            
            # ===== 股票筛选 Tab =====
            with gr.TabItem("🔎 股票筛选", id="screen"):
                gr.Markdown("### 根据自定义条件筛选符合要求的股票")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        screen_criteria = gr.Textbox(
                            label="筛选条件",
                            placeholder="例如: 高股息科技股",
                            lines=3,
                        )
                        screen_date = gr.Textbox(
                            label="交易日期（可选）",
                            placeholder="YYYY-MM-DD，留空使用今天",
                            lines=1,
                        )
                        screen_btn = gr.Button(
                            "🔍 开始筛选",
                            variant="primary",
                            size="lg",
                        )
                        
                        gr.Markdown(
                            """
                            **筛选条件示例：**
                            - 高股息科技股
                            - PE低于15的蓝筹股
                            - 近期突破新高的股票
                            - high dividend yield tech stocks
                            """
                        )
                    
                    with gr.Column(scale=3):
                        screen_output = gr.Markdown(
                            value="输入筛选条件后点击「开始筛选」...",
                            elem_classes=["markdown-text"],
                            height=600,
                        )
                
                screen_btn.click(
                    fn=screen_stocks_streaming,
                    inputs=[screen_criteria, screen_date],
                    outputs=screen_output,
                )
            
            # ===== 智能问答 Tab =====
            with gr.TabItem("💬 智能问答", id="ask"):
                gr.Markdown("### 用自然语言提问，获取智能分析")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        ask_query_input = gr.Textbox(
                            label="您的问题",
                            placeholder="例如: 分析一下苹果公司的股票",
                            lines=4,
                        )
                        ask_btn = gr.Button(
                            "🚀 获取答案",
                            variant="primary",
                            size="lg",
                        )
                        
                        gr.Markdown(
                            """
                            **问题示例：**
                            - 分析一下苹果公司的股票
                            - 巴菲特最近买了什么股票？
                            - 推荐几只高股息的科技股
                            - What are the best AI stocks?
                            """
                        )
                    
                    with gr.Column(scale=3):
                        ask_output = gr.Markdown(
                            value="输入问题后点击「获取答案」...",
                            elem_classes=["markdown-text"],
                            height=600,
                        )
                
                ask_btn.click(
                    fn=ask_query_streaming,
                    inputs=[ask_query_input],
                    outputs=ask_output,
                )
        
        # Footer
        gr.Markdown(
            """
            <div style="text-align: center; padding: 30px 0 10px 0; color: #888; font-size: 0.85em;">
                <p>
                    ⭐ <a href="https://github.com/cooragent/Clarity" target="_blank" style="color: #667eea;">GitHub</a> |
                    🌐 <a href="https://www.cooragent.com/" target="_blank" style="color: #667eea;">Cooragent</a> |
                    📝 <a href="https://github.com/cooragent/Clarity/issues" target="_blank" style="color: #667eea;">反馈问题</a>
                </p>
                <p style="margin-top: 5px;">
                    本工具仅供参考，不构成投资建议
                </p>
            </div>
            """
        )
    
    return demo


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clarity Web UI")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=7860, help="Port to bind to")
    parser.add_argument("--share", action="store_true", help="Create a public link")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   🔮 Clarity - 金融分析智能体 Web UI                      ║
    ║                                                          ║
    ║   Local:   http://localhost:{args.port}                       ║
    ║   Network: http://{args.host}:{args.port}                       ║
    ║                                                          ║
    ║   Powered by Cooragent                                   ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    demo = create_ui()
    
    # Get theme and css from demo attributes (Gradio 6.0 compatibility)
    theme = getattr(demo, '_custom_theme', None)
    css = getattr(demo, '_custom_css', None)
    
    demo.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        show_error=True,
        theme=theme,
        css=css,
    )


if __name__ == "__main__":
    main()
