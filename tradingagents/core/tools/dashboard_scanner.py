# -*- coding: utf-8 -*-
"""
DashboardScanner - 决策仪表盘扫描器
===================================

功能：
1. 每日扫描大盘，获取市场概览
2. 筛选潜力股票，推荐 Top 10
3. 支持 A股、H股、美股（纳斯达克）

数据源：
- A股：akshare, efinance
- 美股：yfinance (NASDAQ/NYSE)
- 港股：yfinance
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

import pandas as pd

from .data_provider import DataFetcherManager, MarketType, detect_market_type
from .data_provider.yfinance_fetcher import YfinanceFetcher

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """信号强度"""
    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"


@dataclass
class StockRecommendation:
    """股票推荐结果"""
    code: str
    name: str
    market: str                      # A股/港股/美股
    current_price: float = 0.0
    change_pct: float = 0.0          # 当日涨跌幅
    
    # 技术指标
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    rsi: float = 0.0
    volume_ratio: float = 0.0
    
    # 评分与信号
    score: int = 0                   # 综合评分 0-100
    signal: SignalStrength = SignalStrength.HOLD
    
    # 推荐理由
    reasons: List[str] = field(default_factory=list)
    data_source: str = ""            # 数据来源
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'name': self.name,
            'market': self.market,
            'current_price': self.current_price,
            'change_pct': self.change_pct,
            'ma5': self.ma5,
            'ma10': self.ma10,
            'ma20': self.ma20,
            'rsi': self.rsi,
            'volume_ratio': self.volume_ratio,
            'score': self.score,
            'signal': self.signal.value,
            'reasons': self.reasons,
            'data_source': self.data_source,
        }


@dataclass
class MarketOverview:
    """市场概览"""
    date: str
    market_type: str                 # A股/美股/港股
    
    # 指数数据
    index_name: str = ""
    index_value: float = 0.0
    index_change_pct: float = 0.0
    
    # 市场统计
    up_count: int = 0
    down_count: int = 0
    total_amount: float = 0.0        # 成交额（亿）
    
    # 板块数据
    top_sectors: List[Dict] = field(default_factory=list)
    bottom_sectors: List[Dict] = field(default_factory=list)


class DashboardScanner:
    """
    决策仪表盘扫描器
    
    功能：
    1. 扫描大盘获取市场概览
    2. 筛选潜力股票
    3. 生成每日推荐报告
    """
    
    # A股热门股票池（用于扫描）
    A_SHARE_POOL = [
        '600519', '000858', '601318', '600036', '000001',  # 大盘蓝筹
        '300750', '002594', '300059', '300124', '002475',  # 创业板龙头
        '688981', '688012', '688036', '688599', '688008',  # 科创板
        '601899', '600900', '601088', '600887', '000568',  # 行业龙头
        '002352', '300274', '002415', '603259', '600809',
    ]
    
    # 港股热门
    HK_STOCK_POOL = [
        '00700', '09988', '03690', '01810', '02020',  # 科技
        '00941', '01398', '02318', '00939', '03988',  # 金融
    ]
    
    def __init__(self):
        self.data_manager = DataFetcherManager()
        self._stock_names: Dict[str, str] = {}  # 代码->名称缓存
    
    def scan_market(
        self,
        markets: List[str] = None,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        扫描市场，返回推荐结果
        
        Args:
            markets: 要扫描的市场列表 ['A股', '美股', '港股']
            top_n: 返回推荐股票数量
            
        Returns:
            {
                'date': '2025-01-19',
                'market_overviews': [...],
                'recommendations': [...],
                'summary': '...'
            }
        """
        if markets is None:
            markets = ['A股', '美股']
        
        today = datetime.now().strftime('%Y-%m-%d')
        result = {
            'date': today,
            'market_overviews': [],
            'recommendations': [],
            'summary': '',
        }
        
        all_candidates = []
        
        # 扫描各市场
        for market in markets:
            logger.info(f"开始扫描 {market} 市场...")
            
            if market == 'A股':
                overview = self._scan_a_share()
                candidates = self._scan_a_share_stocks()
            elif market == '美股':
                overview = self._scan_us_market()
                candidates = self._scan_us_stocks()
            elif market == '港股':
                overview = self._scan_hk_market()
                candidates = self._scan_hk_stocks()
            else:
                continue
            
            if overview:
                result['market_overviews'].append(overview)
            all_candidates.extend(candidates)
        
        # 按评分排序，取 Top N
        all_candidates.sort(key=lambda x: x.score, reverse=True)
        result['recommendations'] = [c.to_dict() for c in all_candidates[:top_n]]
        
        # 生成摘要
        result['summary'] = self._generate_summary(result)
        
        logger.info(f"扫描完成，推荐 {len(result['recommendations'])} 只股票")
        return result
    
    def _scan_a_share(self) -> Optional[MarketOverview]:
        """扫描 A 股大盘"""
        try:
            import akshare as ak
            
            # 获取上证指数
            df = ak.stock_zh_index_spot_sina()
            
            sh_row = df[df['代码'] == 'sh000001']
            if not sh_row.empty:
                row = sh_row.iloc[0]
                overview = MarketOverview(
                    date=datetime.now().strftime('%Y-%m-%d'),
                    market_type='A股',
                    index_name='上证指数',
                    index_value=float(row.get('最新价', 0) or 0),
                    index_change_pct=float(row.get('涨跌幅', 0) or 0),
                )
                
                # 获取涨跌统计
                try:
                    spot_df = ak.stock_zh_a_spot_em()
                    if not spot_df.empty and '涨跌幅' in spot_df.columns:
                        spot_df['涨跌幅'] = pd.to_numeric(spot_df['涨跌幅'], errors='coerce')
                        overview.up_count = len(spot_df[spot_df['涨跌幅'] > 0])
                        overview.down_count = len(spot_df[spot_df['涨跌幅'] < 0])
                        if '成交额' in spot_df.columns:
                            spot_df['成交额'] = pd.to_numeric(spot_df['成交额'], errors='coerce')
                            overview.total_amount = spot_df['成交额'].sum() / 1e8
                except Exception as e:
                    logger.warning(f"获取 A 股涨跌统计失败: {e}")
                
                return overview
                
        except Exception as e:
            logger.error(f"扫描 A 股大盘失败: {e}")
        
        return None
    
    def _scan_us_market(self) -> Optional[MarketOverview]:
        """扫描美股大盘（纳斯达克）"""
        try:
            import yfinance as yf
            
            # 获取纳斯达克指数
            ixic = yf.Ticker('^IXIC')
            hist = ixic.history(period='2d')
            
            if not hist.empty and len(hist) >= 1:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) >= 2 else latest
                
                change_pct = ((latest['Close'] - prev['Close']) / prev['Close'] * 100) if prev['Close'] > 0 else 0
                
                overview = MarketOverview(
                    date=datetime.now().strftime('%Y-%m-%d'),
                    market_type='美股',
                    index_name='纳斯达克综合指数',
                    index_value=float(latest['Close']),
                    index_change_pct=round(change_pct, 2),
                )
                return overview
                
        except Exception as e:
            logger.error(f"扫描美股大盘失败: {e}")
        
        return None
    
    def _scan_hk_market(self) -> Optional[MarketOverview]:
        """扫描港股大盘"""
        try:
            import yfinance as yf
            
            # 获取恒生指数
            hsi = yf.Ticker('^HSI')
            hist = hsi.history(period='2d')
            
            if not hist.empty and len(hist) >= 1:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) >= 2 else latest
                
                change_pct = ((latest['Close'] - prev['Close']) / prev['Close'] * 100) if prev['Close'] > 0 else 0
                
                overview = MarketOverview(
                    date=datetime.now().strftime('%Y-%m-%d'),
                    market_type='港股',
                    index_name='恒生指数',
                    index_value=float(latest['Close']),
                    index_change_pct=round(change_pct, 2),
                )
                return overview
                
        except Exception as e:
            logger.error(f"扫描港股大盘失败: {e}")
        
        return None
    
    def _scan_a_share_stocks(self) -> List[StockRecommendation]:
        """扫描 A 股股票池"""
        recommendations = []
        
        for code in self.A_SHARE_POOL:
            try:
                rec = self._analyze_stock(code, 'A股')
                if rec and rec.score >= 50:
                    recommendations.append(rec)
            except Exception as e:
                logger.warning(f"分析 {code} 失败: {e}")
        
        return recommendations
    
    def _scan_us_stocks(self) -> List[StockRecommendation]:
        """扫描美股股票池（纳斯达克）"""
        recommendations = []
        
        for code in YfinanceFetcher.get_nasdaq_top_stocks()[:30]:  # 取前30个
            try:
                rec = self._analyze_stock(code, '美股')
                if rec and rec.score >= 50:
                    recommendations.append(rec)
            except Exception as e:
                logger.warning(f"分析 {code} 失败: {e}")
        
        return recommendations
    
    def _scan_hk_stocks(self) -> List[StockRecommendation]:
        """扫描港股股票池"""
        recommendations = []
        
        for code in self.HK_STOCK_POOL:
            try:
                rec = self._analyze_stock(code, '港股')
                if rec and rec.score >= 50:
                    recommendations.append(rec)
            except Exception as e:
                logger.warning(f"分析 {code} 失败: {e}")
        
        return recommendations
    
    def _analyze_stock(self, code: str, market: str) -> Optional[StockRecommendation]:
        """分析单只股票"""
        try:
            df, source = self.data_manager.get_daily_data(code, days=60)
            
            if df is None or df.empty or len(df) < 20:
                return None
            
            latest = df.iloc[-1]
            
            rec = StockRecommendation(
                code=code,
                name=self._get_stock_name(code),
                market=market,
                current_price=float(latest['close']),
                change_pct=float(latest.get('pct_chg', 0)),
                ma5=float(latest.get('ma5', 0)),
                ma10=float(latest.get('ma10', 0)),
                ma20=float(latest.get('ma20', 0)),
                rsi=float(latest.get('rsi', 50)),
                volume_ratio=float(latest.get('volume_ratio', 1.0)),
                data_source=source,
            )
            
            # 计算评分
            self._calculate_score(rec, df)
            
            return rec
            
        except Exception as e:
            logger.debug(f"分析 {code} 失败: {e}")
            return None
    
    def _calculate_score(self, rec: StockRecommendation, df: pd.DataFrame) -> None:
        """计算综合评分"""
        score = 50  # 基础分
        reasons = []
        
        # 1. 趋势判断（40分）
        if rec.ma5 > rec.ma10 > rec.ma20:
            score += 30
            reasons.append("✅ 多头排列 MA5>MA10>MA20")
            if rec.ma5 > 0 and (rec.current_price - rec.ma5) / rec.ma5 < 0.03:
                score += 10
                reasons.append("✅ 价格贴近 MA5，买点良好")
        elif rec.ma5 < rec.ma10 < rec.ma20:
            score -= 20
            reasons.append("⚠️ 空头排列")
        
        # 2. RSI 判断（20分）
        if 30 <= rec.rsi <= 70:
            score += 10
            if 40 <= rec.rsi <= 60:
                score += 5
                reasons.append("✅ RSI 健康区间")
        elif rec.rsi < 30:
            score += 15
            reasons.append("✅ RSI 超卖，可能反弹")
        elif rec.rsi > 70:
            score -= 10
            reasons.append("⚠️ RSI 超买，注意风险")
        
        # 3. 量能判断（15分）
        if 0.7 <= rec.volume_ratio <= 1.5:
            score += 10
            reasons.append("✅ 量能正常")
        elif rec.volume_ratio < 0.7:
            score += 5
            reasons.append("📊 缩量，可能在洗盘")
        elif rec.volume_ratio > 2.0:
            if rec.change_pct > 0:
                score += 5
                reasons.append("📈 放量上涨")
            else:
                score -= 5
                reasons.append("⚠️ 放量下跌")
        
        # 4. 近期表现（15分）
        if len(df) >= 5:
            recent_5d_change = (df.iloc[-1]['close'] - df.iloc[-5]['close']) / df.iloc[-5]['close'] * 100
            if 0 < recent_5d_change < 10:
                score += 10
                reasons.append(f"📈 近5日涨 {recent_5d_change:.1f}%")
            elif recent_5d_change > 15:
                score -= 5
                reasons.append(f"⚠️ 近5日涨幅过大 {recent_5d_change:.1f}%")
        
        # 限制分数范围
        rec.score = max(0, min(100, score))
        rec.reasons = reasons
        
        # 生成信号
        if rec.score >= 80:
            rec.signal = SignalStrength.STRONG_BUY
        elif rec.score >= 65:
            rec.signal = SignalStrength.BUY
        elif rec.score >= 50:
            rec.signal = SignalStrength.HOLD
        elif rec.score >= 35:
            rec.signal = SignalStrength.SELL
        else:
            rec.signal = SignalStrength.STRONG_SELL
    
    def _get_stock_name(self, code: str) -> str:
        """获取股票名称"""
        if code in self._stock_names:
            return self._stock_names[code]
        
        # 美股直接使用代码作为名称
        market = detect_market_type(code)
        if market == MarketType.US_STOCK:
            return code
        
        # A股/港股尝试获取名称
        try:
            import akshare as ak
            if market == MarketType.A_SHARE:
                df = ak.stock_info_a_code_name()
                row = df[df['code'] == code]
                if not row.empty:
                    name = row.iloc[0]['name']
                    self._stock_names[code] = name
                    return name
        except:
            pass
        
        return code
    
    def _generate_summary(self, result: Dict) -> str:
        """生成摘要报告"""
        lines = [f"## 📊 {result['date']} 市场扫描报告\n"]
        
        # 市场概览
        if result['market_overviews']:
            lines.append("### 市场概览\n")
            for overview in result['market_overviews']:
                if isinstance(overview, MarketOverview):
                    direction = "↑" if overview.index_change_pct > 0 else "↓"
                    lines.append(f"- **{overview.market_type}** {overview.index_name}: "
                               f"{overview.index_value:.2f} ({direction}{abs(overview.index_change_pct):.2f}%)")
                    if overview.up_count or overview.down_count:
                        lines.append(f"  - 上涨: {overview.up_count} | 下跌: {overview.down_count}")
                    if overview.total_amount > 0:
                        lines.append(f"  - 成交额: {overview.total_amount:.0f}亿")
            lines.append("")
        
        # 推荐股票
        if result['recommendations']:
            lines.append("### Top 10 潜力股推荐\n")
            lines.append("| 排名 | 代码 | 名称 | 市场 | 现价 | 涨跌幅 | 评分 | 信号 |")
            lines.append("|------|------|------|------|------|--------|------|------|")
            
            for i, rec in enumerate(result['recommendations'][:10], 1):
                change_str = f"{rec['change_pct']:+.2f}%"
                lines.append(f"| {i} | {rec['code']} | {rec['name']} | {rec['market']} | "
                           f"{rec['current_price']:.2f} | {change_str} | {rec['score']} | {rec['signal']} |")
            lines.append("")
            
            # 详细理由
            lines.append("### 推荐理由\n")
            for i, rec in enumerate(result['recommendations'][:5], 1):
                lines.append(f"**{i}. {rec['code']} {rec['name']}** (评分: {rec['score']})")
                for reason in rec['reasons']:
                    lines.append(f"   - {reason}")
                lines.append(f"   - 数据来源: {rec['data_source']}")
                lines.append("")
        
        lines.append("---")
        lines.append(f"*生成时间: {datetime.now().strftime('%H:%M:%S')}*")
        
        return "\n".join(lines)


# 便捷函数
def scan_daily_market(markets: List[str] = None, top_n: int = 10) -> Dict[str, Any]:
    """每日市场扫描"""
    scanner = DashboardScanner()
    return scanner.scan_market(markets=markets, top_n=top_n)
