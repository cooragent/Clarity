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

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """信号强度"""
    STRONG_BUY = "极具潜力"
    BUY = "值得关注"
    HOLD = "观望"
    SELL = "谨慎对待"
    STRONG_SELL = "风险较高"


@dataclass
class TradingChecklist:
    """
    交易检查清单 - 每项条件用 ✅⚠️❌ 标记
    
    交易原则：
    1. 严禁追高 - 乖离率超限自动标记危险
    2. 趋势交易 - 顺势而为
    3. 精确点位 - 明确买入/止损/目标
    4. 风险优先 - 盈亏比至少 2:1
    """
    # === 趋势确认（权重 30%）===
    ma_alignment: str = "❓"        # MA 多头/空头排列
    macd_cross: str = "❓"          # MACD 金叉/死叉状态
    trend_strength: str = "❓"      # ADX 趋势强度 (>25 强趋势)
    price_position: str = "❓"      # 价格位置（MA 上方/下方）
    
    # === 风险控制（权重 30%）===
    bias_check: str = "❓"          # 乖离率检查 (>5% 危险)
    volatility_ok: str = "❓"       # ATR 波动率合理性
    volume_confirm: str = "❓"      # 量价配合确认
    stop_loss_clear: str = "❓"     # 止损位清晰
    
    # === 买入时机（权重 25%）===
    rsi_zone: str = "❓"            # RSI 区间 (30-70 健康)
    kdj_signal: str = "❓"          # KDJ 金叉/死叉
    support_near: str = "❓"        # 接近支撑位
    pullback_buy: str = "❓"        # 回调到位
    
    # === 盈利空间（权重 15%）===
    upside_room: str = "❓"         # 上涨空间（到阻力位）
    risk_reward: str = "❓"         # 盈亏比 >= 2:1
    
    # === 计算出的关键点位 ===
    entry_price: float = 0.0       # 建议买入价
    stop_loss: float = 0.0         # 止损价（基于 ATR）
    target_price: float = 0.0      # 目标价（基于阻力位）
    risk_reward_ratio: float = 0.0 # 实际盈亏比
    
    def pass_count(self) -> int:
        """统计通过的检查项数量"""
        checks = [
            self.ma_alignment, self.macd_cross, self.trend_strength, self.price_position,
            self.bias_check, self.volatility_ok, self.volume_confirm, self.stop_loss_clear,
            self.rsi_zone, self.kdj_signal, self.support_near, self.pullback_buy,
            self.upside_room, self.risk_reward
        ]
        return sum(1 for c in checks if c == "✅")
    
    def warning_count(self) -> int:
        """统计警告项数量"""
        checks = [
            self.ma_alignment, self.macd_cross, self.trend_strength, self.price_position,
            self.bias_check, self.volatility_ok, self.volume_confirm, self.stop_loss_clear,
            self.rsi_zone, self.kdj_signal, self.support_near, self.pullback_buy,
            self.upside_room, self.risk_reward
        ]
        return sum(1 for c in checks if c == "⚠️")
    
    def fail_count(self) -> int:
        """统计失败项数量"""
        checks = [
            self.ma_alignment, self.macd_cross, self.trend_strength, self.price_position,
            self.bias_check, self.volatility_ok, self.volume_confirm, self.stop_loss_clear,
            self.rsi_zone, self.kdj_signal, self.support_near, self.pullback_buy,
            self.upside_room, self.risk_reward
        ]
        return sum(1 for c in checks if c == "❌")


@dataclass
class StockRecommendation:
    """股票推荐结果"""
    code: str
    name: str
    market: str                      # A股/港股/美股
    current_price: float = 0.0
    change_pct: float = 0.0          # 当日涨跌幅
    
    # === 均线指标 ===
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma60: float = 0.0                # 季线（中期趋势）
    
    # === 动量指标 ===
    rsi: float = 50.0                # RSI (0-100)
    macd: float = 0.0                # MACD 线
    macd_signal: float = 0.0         # 信号线
    macd_hist: float = 0.0           # MACD 柱状图
    kdj_k: float = 50.0
    kdj_d: float = 50.0
    kdj_j: float = 50.0
    
    # === 趋势与波动指标 ===
    adx: float = 0.0                 # 趋势强度 (>25 强趋势, >40 极强)
    atr: float = 0.0                 # 真实波幅 (用于计算止损)
    bias: float = 0.0                # 乖离率 (>5% 超买风险)
    
    # === 量能指标 ===
    volume_ratio: float = 1.0        # 量比
    obv_trend: str = ""              # OBV 趋势方向
    
    # === 关键点位 ===
    support: float = 0.0             # 支撑位
    resistance: float = 0.0          # 阻力位
    
    # === 评分与信号 ===
    score: int = 0                   # 综合评分 0-100
    signal: SignalStrength = SignalStrength.HOLD
    
    # === 详细信息 ===
    reasons: List[str] = field(default_factory=list)
    checklist: TradingChecklist = field(default_factory=TradingChecklist)
    data_source: str = ""            # 数据来源
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'name': self.name,
            'market': self.market,
            'current_price': self.current_price,
            'change_pct': self.change_pct,
            # 均线
            'ma5': self.ma5,
            'ma10': self.ma10,
            'ma20': self.ma20,
            'ma60': self.ma60,
            # 动量
            'rsi': self.rsi,
            'macd': self.macd,
            'macd_hist': self.macd_hist,
            'kdj_k': self.kdj_k,
            'kdj_d': self.kdj_d,
            # 趋势
            'adx': self.adx,
            'atr': self.atr,
            'bias': self.bias,
            # 量能
            'volume_ratio': self.volume_ratio,
            # 点位
            'support': self.support,
            'resistance': self.resistance,
            'entry_price': self.checklist.entry_price,
            'stop_loss': self.checklist.stop_loss,
            'target_price': self.checklist.target_price,
            'risk_reward_ratio': self.checklist.risk_reward_ratio,
            # 评分
            'score': self.score,
            'signal': self.signal.value,
            'reasons': self.reasons,
            'checklist_pass': self.checklist.pass_count(),
            'checklist_warn': self.checklist.warning_count(),
            'checklist_fail': self.checklist.fail_count(),
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
    2. 动态获取热门股票池
    3. 筛选潜力股票
    4. 生成每日推荐报告
    """
    
    # 备用静态股票池（当动态获取失败时使用）
    FALLBACK_A_SHARE = ['600519', '000858', '601318', '600036', '000001', '300750']
    FALLBACK_HK = ['00700', '09988', '03690', '01810', '02020']
    FALLBACK_US = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA']
    
    def __init__(self):
        self.data_manager = DataFetcherManager()
        self._stock_names: Dict[str, str] = {}  # 代码->名称缓存
        self._hot_stocks_cache: Dict[str, List[str]] = {}  # 热门股票缓存
    
    def _get_hot_a_shares(self, limit: int = 50) -> List[str]:
        """
        动态获取 A 股热门股票
        
        数据来源：
        1. 涨幅榜前 N 名
        2. 成交额前 N 名
        3. 龙虎榜股票
        """
        hot_stocks = set()
        
        try:
            import akshare as ak
            
            # 1. 获取实时行情，按成交额排序（热门股）
            logger.info("获取 A 股热门股票...")
            df = ak.stock_zh_a_spot_em()
            
            if df is not None and not df.empty:
                # 清理数据
                df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce')
                df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
                
                # 过滤 ST 股票和新股
                if '名称' in df.columns:
                    df = df[~df['名称'].str.contains('ST|N|C', na=False)]
                
                # 成交额 Top N
                top_amount = df.nlargest(limit // 2, '成交额')
                hot_stocks.update(top_amount['代码'].tolist())
                
                # 涨幅 Top N（过滤涨停）
                gainers = df[(df['涨跌幅'] > 0) & (df['涨跌幅'] < 9.9)]
                top_gainers = gainers.nlargest(limit // 3, '涨跌幅')
                hot_stocks.update(top_gainers['代码'].tolist())
                
                logger.info(f"获取到 {len(hot_stocks)} 只 A 股热门股票")
            
            # 2. 获取龙虎榜股票（可选）
            try:
                lhb_df = ak.stock_lhb_detail_em(start_date="", end_date="")
                if lhb_df is not None and not lhb_df.empty and '代码' in lhb_df.columns:
                    lhb_codes = lhb_df['代码'].head(20).tolist()
                    hot_stocks.update(lhb_codes)
                    logger.info(f"添加龙虎榜 {len(lhb_codes)} 只股票")
            except Exception as e:
                logger.debug(f"获取龙虎榜失败: {e}")
            
        except Exception as e:
            logger.warning(f"动态获取 A 股热门股票失败: {e}，使用备用列表")
            return self.FALLBACK_A_SHARE
        
        result = list(hot_stocks)[:limit]
        return result if result else self.FALLBACK_A_SHARE
    
    def _get_hot_us_stocks(self, limit: int = 50) -> List[str]:
        """
        动态获取美股热门股票
        
        数据来源：
        1. 纳斯达克 100 成分股
        2. 标普 500 热门股
        """
        hot_stocks = []
        
        try:
            import yfinance as yf
            
            logger.info("获取美股热门股票...")
            
            # 获取纳斯达克 100 和标普 500 的部分成分股
            # yfinance 可以通过 ETF 获取成分股信息
            major_tickers = [
                # 科技巨头
                'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA',
                # 半导体
                'AVGO', 'AMD', 'QCOM', 'INTC', 'TXN', 'MU', 'AMAT', 'LRCX',
                # 软件/云
                'CRM', 'ORCL', 'ADBE', 'NOW', 'INTU', 'SNOW', 'PANW', 'CRWD',
                # 金融
                'JPM', 'V', 'MA', 'BAC', 'WFC', 'GS', 'MS', 'BLK',
                # 消费
                'WMT', 'COST', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW',
                # 医疗
                'UNH', 'JNJ', 'LLY', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT',
                # 能源
                'XOM', 'CVX', 'COP', 'SLB', 'EOG',
                # 其他
                'BRK-B', 'PG', 'KO', 'PEP', 'DIS', 'NFLX', 'PYPL',
            ]
            
            # 获取这些股票的涨跌幅，按涨幅排序
            hot_with_change = []
            
            for ticker in major_tickers[:min(len(major_tickers), limit * 2)]:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='2d')
                    if len(hist) >= 2:
                        change = (hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100
                        hot_with_change.append((ticker, change))
                except:
                    hot_with_change.append((ticker, 0))
            
            # 按涨幅排序
            hot_with_change.sort(key=lambda x: x[1], reverse=True)
            hot_stocks = [t[0] for t in hot_with_change[:limit]]
            
            logger.info(f"获取到 {len(hot_stocks)} 只美股热门股票")
            
        except Exception as e:
            logger.warning(f"动态获取美股热门股票失败: {e}，使用备用列表")
            return self.FALLBACK_US
        
        return hot_stocks if hot_stocks else self.FALLBACK_US
    
    def _get_hot_hk_stocks(self, limit: int = 30) -> List[str]:
        """
        动态获取港股热门股票
        
        数据来源：
        1. 恒生指数成分股
        2. 恒生科技指数成分股
        """
        hot_stocks = []
        
        try:
            import akshare as ak
            
            logger.info("获取港股热门股票...")
            
            # 获取港股实时行情
            try:
                df = ak.stock_hk_spot_em()
                if df is not None and not df.empty:
                    df['成交额'] = pd.to_numeric(df['成交额'], errors='coerce')
                    
                    # 按成交额排序
                    top_amount = df.nlargest(limit, '成交额')
                    if '代码' in top_amount.columns:
                        hot_stocks = top_amount['代码'].tolist()
                    
                    logger.info(f"获取到 {len(hot_stocks)} 只港股热门股票")
            except Exception as e:
                logger.debug(f"通过 akshare 获取港股失败: {e}")
            
            # 备用：恒生指数主要成分股
            if not hot_stocks:
                hot_stocks = [
                    '00700', '09988', '03690', '01810', '02020',  # 科技
                    '00941', '01398', '02318', '00939', '03988',  # 金融
                    '00005', '00011', '00016', '00066', '00388',  # 蓝筹
                    '01299', '02269', '02382', '00868', '01024',  # 其他
                ]
            
        except Exception as e:
            logger.warning(f"动态获取港股热门股票失败: {e}，使用备用列表")
            return self.FALLBACK_HK
        
        return hot_stocks[:limit] if hot_stocks else self.FALLBACK_HK
    
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
        """扫描 A 股热门股票（动态获取）"""
        recommendations = []
        
        # 动态获取热门 A 股
        hot_stocks = self._get_hot_a_shares(limit=50)
        logger.info(f"扫描 {len(hot_stocks)} 只 A 股热门股票...")
        
        for code in hot_stocks:
            try:
                rec = self._analyze_stock(code, 'A股')
                if rec and rec.score >= 50:
                    recommendations.append(rec)
            except Exception as e:
                logger.warning(f"分析 {code} 失败: {e}")
        
        return recommendations
    
    def _scan_us_stocks(self) -> List[StockRecommendation]:
        """扫描美股热门股票（动态获取）"""
        recommendations = []
        
        # 动态获取热门美股
        hot_stocks = self._get_hot_us_stocks(limit=50)
        logger.info(f"扫描 {len(hot_stocks)} 只美股热门股票...")
        
        for code in hot_stocks:
            try:
                rec = self._analyze_stock(code, '美股')
                if rec and rec.score >= 50:
                    recommendations.append(rec)
            except Exception as e:
                logger.warning(f"分析 {code} 失败: {e}")
        
        return recommendations
    
    def _scan_hk_stocks(self) -> List[StockRecommendation]:
        """扫描港股热门股票（动态获取）"""
        recommendations = []
        
        # 动态获取热门港股
        hot_stocks = self._get_hot_hk_stocks(limit=30)
        logger.info(f"扫描 {len(hot_stocks)} 只港股热门股票...")
        
        for code in hot_stocks:
            try:
                rec = self._analyze_stock(code, '港股')
                if rec and rec.score >= 50:
                    recommendations.append(rec)
            except Exception as e:
                logger.warning(f"分析 {code} 失败: {e}")
        
        return recommendations
    
    def _analyze_stock(self, code: str, market: str) -> Optional[StockRecommendation]:
        """
        分析单只股票
        
        返回包含完整技术分析和检查清单的推荐结果
        """
        try:
            df, source = self.data_manager.get_daily_data(code, days=60)
            
            if df is None or df.empty or len(df) < 20:
                return None
            
            latest = df.iloc[-1]
            
            # 创建推荐对象（基础数据）
            rec = StockRecommendation(
                code=code,
                name=self._get_stock_name(code),
                market=market,
                current_price=float(latest['close']),
                change_pct=float(latest.get('pct_chg', 0)),
                data_source=source,
            )
            
            # 计算完整评分（内部会计算所有技术指标和检查清单）
            self._calculate_score(rec, df)
            
            return rec
            
        except Exception as e:
            logger.debug(f"分析 {code} 失败: {e}")
            return None
    
    def _calculate_technical_indicators(self, rec: StockRecommendation, df: pd.DataFrame) -> None:
        """计算高级技术指标"""
        if len(df) < 20:
            return
        
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']
        
        # === 均线 ===
        rec.ma5 = float(close.rolling(5).mean().iloc[-1]) if len(df) >= 5 else 0
        rec.ma10 = float(close.rolling(10).mean().iloc[-1]) if len(df) >= 10 else 0
        rec.ma20 = float(close.rolling(20).mean().iloc[-1]) if len(df) >= 20 else 0
        rec.ma60 = float(close.rolling(60).mean().iloc[-1]) if len(df) >= 60 else rec.ma20
        
        # === 乖离率 BIAS (严禁追高核心指标) ===
        if rec.ma20 > 0:
            rec.bias = (rec.current_price - rec.ma20) / rec.ma20 * 100
        
        # === MACD ===
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        rec.macd = float(ema12.iloc[-1] - ema26.iloc[-1])
        rec.macd_signal = float((ema12 - ema26).ewm(span=9, adjust=False).mean().iloc[-1])
        rec.macd_hist = rec.macd - rec.macd_signal
        
        # === KDJ ===
        if len(df) >= 9:
            low_min = low.rolling(9).min()
            high_max = high.rolling(9).max()
            rsv = (close - low_min) / (high_max - low_min) * 100
            rsv = rsv.fillna(50)
            rec.kdj_k = float(rsv.ewm(com=2, adjust=False).mean().iloc[-1])
            rec.kdj_d = float(pd.Series([rec.kdj_k]).ewm(com=2, adjust=False).mean().iloc[-1])
            rec.kdj_j = 3 * rec.kdj_k - 2 * rec.kdj_d
        
        # === RSI ===
        if len(df) >= 14:
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss.replace(0, 1e-10)
            rec.rsi = float(100 - (100 / (1 + rs)).iloc[-1])
        
        # === ADX (趋势强度) ===
        if len(df) >= 14:
            tr = pd.concat([
                high - low,
                abs(high - close.shift(1)),
                abs(low - close.shift(1))
            ], axis=1).max(axis=1)
            atr14 = tr.rolling(14).mean()
            rec.atr = float(atr14.iloc[-1])
            
            # 简化的 ADX 计算
            plus_dm = (high - high.shift(1)).where((high - high.shift(1)) > (low.shift(1) - low), 0)
            minus_dm = (low.shift(1) - low).where((low.shift(1) - low) > (high - high.shift(1)), 0)
            plus_di = 100 * (plus_dm.rolling(14).mean() / atr14)
            minus_di = 100 * (minus_dm.rolling(14).mean() / atr14)
            dx = abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10) * 100
            rec.adx = float(dx.rolling(14).mean().iloc[-1]) if not dx.isna().all() else 0
        
        # === 支撑/阻力位 ===
        if len(df) >= 20:
            recent_lows = low.rolling(20).min()
            recent_highs = high.rolling(20).max()
            rec.support = float(recent_lows.iloc[-1])
            rec.resistance = float(recent_highs.iloc[-1])
        
        # === 量比 ===
        if len(df) >= 5:
            avg_vol_5 = volume.rolling(5).mean().iloc[-1]
            rec.volume_ratio = float(volume.iloc[-1] / avg_vol_5) if avg_vol_5 > 0 else 1.0

    def _build_checklist(self, rec: StockRecommendation, df: pd.DataFrame) -> None:
        """
        构建交易检查清单
        
        核心原则：
        - ❌ 严禁追高：乖离率 > 5% 自动标记「危险」
        - ✅ 趋势交易：顺势操作，多头排列优先
        - 📍 精确点位：基于 ATR 计算止损，基于阻力位设目标
        - 📋 盈亏比：至少 2:1
        """
        cl = rec.checklist
        
        # ========== 趋势确认（30%）==========
        
        # 1. MA 多头排列
        if rec.ma5 > rec.ma10 > rec.ma20:
            cl.ma_alignment = "✅"
        elif rec.ma5 < rec.ma10 < rec.ma20:
            cl.ma_alignment = "❌"
        else:
            cl.ma_alignment = "⚠️"
        
        # 2. MACD 金叉/死叉
        if rec.macd_hist > 0:
            if rec.macd > rec.macd_signal:
                cl.macd_cross = "✅"  # 金叉且柱状图向上
            else:
                cl.macd_cross = "⚠️"
        else:
            cl.macd_cross = "❌" if rec.macd < rec.macd_signal else "⚠️"
        
        # 3. 趋势强度 (ADX)
        if rec.adx >= 25:
            cl.trend_strength = "✅"  # 强趋势
        elif rec.adx >= 15:
            cl.trend_strength = "⚠️"  # 弱趋势
        else:
            cl.trend_strength = "❌"  # 无趋势/震荡
        
        # 4. 价格位置
        if rec.current_price > rec.ma20:
            cl.price_position = "✅"
        elif rec.current_price > rec.ma60:
            cl.price_position = "⚠️"
        else:
            cl.price_position = "❌"
        
        # ========== 风险控制（30%）==========
        
        # 5. 乖离率检查（核心！严禁追高）
        if abs(rec.bias) <= 3:
            cl.bias_check = "✅"  # 安全区间
        elif abs(rec.bias) <= 5:
            cl.bias_check = "⚠️"  # 警惕区间
        else:
            cl.bias_check = "❌"  # 危险！超买/超卖
        
        # 6. 波动率检查
        if rec.atr > 0 and rec.current_price > 0:
            atr_pct = rec.atr / rec.current_price * 100
            if atr_pct <= 3:
                cl.volatility_ok = "✅"  # 波动适中
            elif atr_pct <= 5:
                cl.volatility_ok = "⚠️"
            else:
                cl.volatility_ok = "❌"  # 波动过大
        
        # 7. 量价配合
        if 0.8 <= rec.volume_ratio <= 2.0:
            if rec.change_pct >= 0:
                cl.volume_confirm = "✅"  # 量价配合
            else:
                cl.volume_confirm = "⚠️"
        elif rec.volume_ratio > 3.0:
            cl.volume_confirm = "❌" if rec.change_pct < 0 else "⚠️"  # 异常放量
        else:
            cl.volume_confirm = "⚠️"  # 量能不足
        
        # 8. 止损位计算（基于 ATR）
        if rec.atr > 0:
            cl.stop_loss = rec.current_price - 2 * rec.atr  # 2倍ATR止损
            cl.stop_loss_clear = "✅" if cl.stop_loss > 0 else "⚠️"
        else:
            cl.stop_loss = rec.support * 0.98 if rec.support > 0 else rec.current_price * 0.95
            cl.stop_loss_clear = "⚠️"
        
        # ========== 买入时机（25%）==========
        
        # 9. RSI 区间
        if 30 <= rec.rsi <= 50:
            cl.rsi_zone = "✅"  # 理想买入区间
        elif 50 < rec.rsi <= 70:
            cl.rsi_zone = "⚠️"  # 中性
        elif rec.rsi < 30:
            cl.rsi_zone = "✅"  # 超卖反弹机会
        else:
            cl.rsi_zone = "❌"  # 超买风险
        
        # 10. KDJ 信号
        if rec.kdj_k > rec.kdj_d and rec.kdj_j < 80:
            cl.kdj_signal = "✅"  # 金叉且未超买
        elif rec.kdj_k < rec.kdj_d:
            cl.kdj_signal = "❌"  # 死叉
        else:
            cl.kdj_signal = "⚠️"
        
        # 11. 接近支撑位
        if rec.support > 0 and rec.current_price > 0:
            dist_to_support = (rec.current_price - rec.support) / rec.current_price * 100
            if dist_to_support <= 3:
                cl.support_near = "✅"  # 接近支撑
            elif dist_to_support <= 8:
                cl.support_near = "⚠️"
            else:
                cl.support_near = "❌"  # 远离支撑
        
        # 12. 回调买入（价格接近 MA10/MA20）
        if rec.ma10 > 0:
            dist_to_ma10 = abs(rec.current_price - rec.ma10) / rec.ma10 * 100
            if dist_to_ma10 <= 2:
                cl.pullback_buy = "✅"  # 回调到 MA10 附近
            elif dist_to_ma10 <= 5:
                cl.pullback_buy = "⚠️"
            else:
                cl.pullback_buy = "❌"
        
        # ========== 盈利空间（15%）==========
        
        # 13. 上涨空间
        if rec.resistance > rec.current_price:
            upside = (rec.resistance - rec.current_price) / rec.current_price * 100
            if upside >= 10:
                cl.upside_room = "✅"  # 空间 >= 10%
            elif upside >= 5:
                cl.upside_room = "⚠️"
            else:
                cl.upside_room = "❌"
        else:
            cl.upside_room = "❌"
        
        # 14. 计算目标价和盈亏比
        cl.entry_price = rec.current_price
        cl.target_price = rec.resistance if rec.resistance > rec.current_price else rec.current_price * 1.10
        
        potential_profit = cl.target_price - cl.entry_price
        potential_loss = cl.entry_price - cl.stop_loss
        
        if potential_loss > 0:
            cl.risk_reward_ratio = potential_profit / potential_loss
            if cl.risk_reward_ratio >= 3:
                cl.risk_reward = "✅"  # 盈亏比 >= 3:1
            elif cl.risk_reward_ratio >= 2:
                cl.risk_reward = "⚠️"  # 盈亏比 >= 2:1
            else:
                cl.risk_reward = "❌"  # 盈亏比不足
        else:
            cl.risk_reward = "❌"
        
        rec.checklist = cl

    def _calculate_score(self, rec: StockRecommendation, df: pd.DataFrame) -> None:
        """
        改进的综合评分系统
        
        评分维度：
        1. 趋势确认 (30分)
        2. 风险控制 (30分) - 核心！
        3. 买入时机 (25分)
        4. 盈利空间 (15分)
        """
        # 先计算技术指标
        self._calculate_technical_indicators(rec, df)
        
        # 构建检查清单
        self._build_checklist(rec, df)
        
        cl = rec.checklist
        score = 0
        reasons = []
        
        # ========== 1. 趋势确认 (30分) ==========
        trend_score = 0
        
        # MA 排列 (10分)
        if cl.ma_alignment == "✅":
            trend_score += 10
            reasons.append("✅ MA 多头排列")
        elif cl.ma_alignment == "❌":
            trend_score -= 5
            reasons.append("❌ MA 空头排列")
        
        # MACD (8分)
        if cl.macd_cross == "✅":
            trend_score += 8
            reasons.append("✅ MACD 金叉向上")
        elif cl.macd_cross == "❌":
            trend_score -= 3
            reasons.append("❌ MACD 死叉")
        
        # 趋势强度 (7分)
        if cl.trend_strength == "✅":
            trend_score += 7
            reasons.append(f"✅ 强趋势 ADX={rec.adx:.1f}")
        elif cl.trend_strength == "❌":
            reasons.append(f"⚠️ 震荡行情 ADX={rec.adx:.1f}")
        
        # 价格位置 (5分)
        if cl.price_position == "✅":
            trend_score += 5
        
        score += max(0, trend_score)
        
        # ========== 2. 风险控制 (30分) - 核心！ ==========
        risk_score = 30  # 从满分开始扣
        
        # 乖离率检查 (最重要！严禁追高)
        if cl.bias_check == "❌":
            risk_score -= 20  # 严重扣分
            if rec.bias > 5:
                reasons.append(f"❌ 严禁追高！乖离率 {rec.bias:.1f}% > 5%")
            else:
                reasons.append(f"❌ 超卖风险！乖离率 {rec.bias:.1f}%")
        elif cl.bias_check == "⚠️":
            risk_score -= 8
            reasons.append(f"⚠️ 乖离率偏高 {rec.bias:.1f}%")
        else:
            reasons.append(f"✅ 乖离率安全 {rec.bias:.1f}%")
        
        # 波动率 (5分)
        if cl.volatility_ok == "❌":
            risk_score -= 5
            reasons.append("⚠️ 波动率过大")
        
        # 量价配合 (5分)
        if cl.volume_confirm == "✅":
            reasons.append("✅ 量价配合良好")
        elif cl.volume_confirm == "❌":
            risk_score -= 5
            reasons.append("❌ 量价背离")
        
        score += max(0, risk_score)
        
        # ========== 3. 买入时机 (25分) ==========
        timing_score = 0
        
        # RSI (8分)
        if cl.rsi_zone == "✅":
            timing_score += 8
            if rec.rsi < 30:
                reasons.append(f"✅ RSI 超卖 {rec.rsi:.0f}，反弹机会")
            else:
                reasons.append(f"✅ RSI 健康 {rec.rsi:.0f}")
        elif cl.rsi_zone == "❌":
            timing_score -= 5
            reasons.append(f"❌ RSI 超买 {rec.rsi:.0f}，风险高")
        
        # KDJ (7分)
        if cl.kdj_signal == "✅":
            timing_score += 7
            reasons.append("✅ KDJ 金叉")
        elif cl.kdj_signal == "❌":
            timing_score -= 3
        
        # 支撑位 (5分)
        if cl.support_near == "✅":
            timing_score += 5
            reasons.append(f"✅ 接近支撑位 ¥{rec.support:.2f}")
        
        # 回调买入 (5分)
        if cl.pullback_buy == "✅":
            timing_score += 5
            reasons.append("✅ 回调到 MA10 附近，良好买点")
        
        score += max(0, timing_score)
        
        # ========== 4. 盈利空间 (15分) ==========
        profit_score = 0
        
        # 上涨空间 (8分)
        if cl.upside_room == "✅":
            profit_score += 8
            upside_pct = (cl.target_price - rec.current_price) / rec.current_price * 100
            reasons.append(f"✅ 上涨空间 {upside_pct:.1f}%")
        elif cl.upside_room == "❌":
            reasons.append("⚠️ 上涨空间有限")
        
        # 盈亏比 (7分)
        if cl.risk_reward == "✅":
            profit_score += 7
            reasons.append(f"✅ 盈亏比 {cl.risk_reward_ratio:.1f}:1")
        elif cl.risk_reward == "⚠️":
            profit_score += 3
            reasons.append(f"⚠️ 盈亏比 {cl.risk_reward_ratio:.1f}:1")
        else:
            reasons.append(f"❌ 盈亏比不足 {cl.risk_reward_ratio:.1f}:1")
        
        score += profit_score
        
        # ========== 添加关键点位信息 ==========
        reasons.append("")  # 空行分隔
        reasons.append("📍 **关键点位**")
        reasons.append(f"   买入价: ¥{cl.entry_price:.2f}")
        reasons.append(f"   止损价: ¥{cl.stop_loss:.2f}")
        reasons.append(f"   目标价: ¥{cl.target_price:.2f}")
        
        # ========== 最终评分 ==========
        rec.score = max(0, min(100, score))
        rec.reasons = reasons
        
        # 检查清单统计
        pass_count = cl.pass_count()
        fail_count = cl.fail_count()
        
        # 生成信号（结合评分和检查清单）
        if fail_count >= 3 or cl.bias_check == "❌":
            # 有严重风险项，降级处理
            if rec.score >= 60:
                rec.signal = SignalStrength.HOLD
            else:
                rec.signal = SignalStrength.SELL
        elif rec.score >= 80 and pass_count >= 10:
            rec.signal = SignalStrength.STRONG_BUY
        elif rec.score >= 65 and pass_count >= 7:
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
