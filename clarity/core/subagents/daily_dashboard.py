# -*- coding: utf-8 -*-
"""
DailyDashboard 子智能体 - 每日决策仪表盘
===================================

职责：
1. 每日自动扫描大盘（A股、美股、港股）
2. 推荐 Top 10 值得关注
3. 生成分析报告，附上推荐理由和数据来源
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any

from ..base_agent import BaseSubAgent
from ..config import AgentConfig, TaskContext
from ..tools.dashboard_scanner import DashboardScanner, scan_daily_market

logger = logging.getLogger(__name__)


class DailyDashboard(BaseSubAgent):
    """
    每日决策仪表盘智能体
    
    功能：
    - 扫描全球市场（A股、美股、港股）
    - 筛选值得关注票，生成 Top 10 推荐
    - 提供推荐理由和数据来源
    """
    
    name = "daily_dashboard"
    description = "每日扫描大盘，推荐值得关注票"
    
    # 支持的市场
    SUPPORTED_MARKETS = ['A股', '美股', '港股']
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.scanner = DashboardScanner()
    
    async def run(self, task_context: TaskContext) -> str:
        """
        执行每日仪表盘扫描
        
        Args:
            task_context: 任务上下文，可包含：
                - target: 指定市场（如 "A股,美股"）或 "all"
                - trade_date: 日期
                
        Returns:
            Markdown 格式的分析报告
        """
        logger.info("开始执行每日仪表盘扫描...")
        
        # 解析要扫描的市场
        target = task_context.target if task_context.target else "A股,美股"
        
        if target.lower() == 'all':
            markets = self.SUPPORTED_MARKETS
        else:
            markets = [m.strip() for m in target.split(',') if m.strip() in self.SUPPORTED_MARKETS]
            if not markets:
                markets = ['A股', '美股']
        
        logger.info(f"扫描市场: {markets}")
        
        try:
            # 执行扫描
            result = self.scanner.scan_market(markets=markets, top_n=10)
            
            # 生成报告
            report = self._format_report(result)
            
            logger.info(f"仪表盘扫描完成，推荐 {len(result.get('recommendations', []))} 只股票")
            return report
            
        except Exception as e:
            logger.error(f"仪表盘扫描失败: {e}")
            return f"## ❌ 扫描失败\n\n错误信息: {str(e)}"
    
    def _format_report(self, result: Dict[str, Any]) -> str:
        """格式化扫描结果为报告"""
        lines = [
            f"# 📊 每日决策仪表盘",
            f"",
            f"**日期**: {result.get('date', datetime.now().strftime('%Y-%m-%d'))}",
            f"",
        ]
        
        # 市场概览
        overviews = result.get('market_overviews', [])
        if overviews:
            lines.append("## 🌍 市场概览")
            lines.append("")
            
            for overview in overviews:
                if hasattr(overview, 'market_type'):
                    # MarketOverview 对象
                    direction = "🔺" if overview.index_change_pct > 0 else "🔻"
                    lines.append(f"### {overview.market_type}")
                    lines.append(f"- **{overview.index_name}**: {overview.index_value:,.2f} "
                               f"({direction} {abs(overview.index_change_pct):.2f}%)")
                    if overview.up_count or overview.down_count:
                        lines.append(f"- 上涨: {overview.up_count} 家 | 下跌: {overview.down_count} 家")
                    if overview.total_amount > 0:
                        lines.append(f"- 两市成交额: {overview.total_amount:,.0f} 亿元")
                    lines.append("")
        
        # 推荐股票
        recommendations = result.get('recommendations', [])
        if recommendations:
            lines.append("## 🎯 Top 10 值得关注推荐")
            lines.append("")
            lines.append("| # | 代码 | 名称 | 市场 | 现价 | 涨跌 | 评分 | 信号 | 数据源 |")
            lines.append("|---|------|------|------|------|------|------|------|--------|")
            
            for i, rec in enumerate(recommendations[:10], 1):
                change_str = f"{rec['change_pct']:+.2f}%" if rec['change_pct'] else "-"
                lines.append(
                    f"| {i} | `{rec['code']}` | {rec['name']} | {rec['market']} | "
                    f"{rec['current_price']:.2f} | {change_str} | **{rec['score']}** | "
                    f"{rec['signal']} | {rec['data_source']} |"
                )
            lines.append("")
            
            # 详细分析
            lines.append("## 📝 详细分析")
            lines.append("")
            
            for i, rec in enumerate(recommendations[:5], 1):
                lines.append(f"### {i}. {rec['code']} - {rec['name']}")
                lines.append("")
                lines.append(f"**市场**: {rec['market']} | **评分**: {rec['score']}/100 | **信号**: {rec['signal']}")
                lines.append("")
                
                # 技术指标
                lines.append("**技术指标**:")
                lines.append(f"- 现价: {rec['current_price']:.2f}")
                lines.append(f"- MA5: {rec['ma5']:.2f} | MA10: {rec['ma10']:.2f} | MA20: {rec['ma20']:.2f}")
                lines.append(f"- RSI: {rec['rsi']:.1f} | 量比: {rec['volume_ratio']:.2f}")
                lines.append("")
                
                # 推荐理由
                if rec['reasons']:
                    lines.append("**推荐理由**:")
                    for reason in rec['reasons']:
                        lines.append(f"- {reason}")
                    lines.append("")
                
                lines.append(f"*数据来源: {rec['data_source']}*")
                lines.append("")
                lines.append("---")
                lines.append("")
        else:
            lines.append("## ⚠️ 暂无推荐")
            lines.append("")
            lines.append("当前市场条件下未找到符合标准的值得关注票。")
            lines.append("")
        
        # 风险提示
        lines.append("## ⚠️ 风险提示")
        lines.append("")
        lines.append("- 以上分析仅供参考，不构成投资建议")
        lines.append("- 股市有风险，投资需谨慎")
        lines.append("- 请结合自身风险承受能力做出投资决策")
        lines.append("")
        
        # 生成时间
        lines.append("---")
        lines.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "\n".join(lines)
    
    async def get_market_overview(self, market: str = 'A股') -> Dict[str, Any]:
        """获取指定市场概览"""
        result = self.scanner.scan_market(markets=[market], top_n=5)
        return {
            'market': market,
            'overview': result.get('market_overviews', []),
            'top_stocks': result.get('recommendations', [])[:5],
        }
    
    async def get_stock_recommendation(self, code: str) -> Dict[str, Any]:
        """获取单只股票的推荐分析"""
        try:
            rec = self.scanner._analyze_stock(code, 'Unknown')
            if rec:
                return rec.to_dict()
            return {'error': f'无法分析 {code}'}
        except Exception as e:
            return {'error': str(e)}
