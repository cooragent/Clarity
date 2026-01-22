# -*- coding: utf-8 -*-
"""
YfinanceFetcher - 全球市场数据源 (Priority 2)
===================================

数据来源：Yahoo Finance（通过 yfinance 库）
覆盖市场：美股(NASDAQ/NYSE)、港股、A股(兜底)

代码格式：
- 美股：直接使用 ticker (AAPL, NVDA, MSFT)
- 港股：xxxxx.HK (00700.HK, 09988.HK)
- A股：xxxxxx.SS(沪) / xxxxxx.SZ(深)
"""

import logging
from typing import List

import pandas as pd

from .base import BaseFetcher, DataFetchError, MarketType, STANDARD_COLUMNS

logger = logging.getLogger(__name__)


class YfinanceFetcher(BaseFetcher):
    """
    Yahoo Finance 数据源实现
    
    优先级：2（全球市场兜底）
    覆盖市场：美股、港股、A股
    """
    
    name = "YfinanceFetcher"
    priority = 2
    supported_markets: List[MarketType] = [
        MarketType.US_STOCK,
        MarketType.HK_STOCK,
        MarketType.A_SHARE,
    ]
    
    # 热门美股（用于大盘扫描）
    NASDAQ_TOP_STOCKS = [
        'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'BRK-B',
        'AVGO', 'JPM', 'LLY', 'V', 'UNH', 'XOM', 'MA', 'COST', 'HD', 'PG',
        'JNJ', 'ABBV', 'MRK', 'NFLX', 'CRM', 'AMD', 'ORCL', 'BAC', 'KO',
        'PEP', 'TMO', 'CSCO', 'MCD', 'ABT', 'ADBE', 'WMT', 'ACN', 'DHR',
        'NKE', 'TXN', 'PM', 'LIN', 'NEE', 'UNP', 'INTC', 'QCOM', 'INTU',
        'CMCSA', 'VZ', 'HON', 'COP', 'IBM',
    ]
    
    def _convert_stock_code(self, stock_code: str) -> str:
        """
        转换股票代码为 Yahoo Finance 格式
        
        规则：
        - 美股：直接使用 (AAPL -> AAPL)
        - 港股：添加 .HK (00700 -> 0700.HK)
        - A股：添加 .SS/.SZ (600519 -> 600519.SS)
        """
        code = stock_code.strip().upper()
        
        # 已经包含后缀
        if '.SS' in code or '.SZ' in code or '.HK' in code:
            return code
        
        # 纯数字判断
        pure_code = code.replace('.', '')
        
        if pure_code.isdigit():
            if len(pure_code) == 6:
                # A股
                if pure_code.startswith(('600', '601', '603', '688')):
                    return f"{pure_code}.SS"
                else:
                    return f"{pure_code}.SZ"
            elif len(pure_code) == 5:
                # 港股
                return f"{pure_code}.HK"
            elif len(pure_code) < 5:
                # 可能是港股短代码
                return f"{pure_code.zfill(4)}.HK"
        
        # 字母代码 -> 美股
        return code
    
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从 Yahoo Finance 获取原始数据"""
        import yfinance as yf
        
        yf_code = self._convert_stock_code(stock_code)
        
        logger.debug(f"调用 yfinance.download({yf_code}, {start_date}, {end_date})")
        
        try:
            df = yf.download(
                tickers=yf_code,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True,
            )
            
            if df.empty:
                raise DataFetchError(f"Yahoo Finance 未查询到 {stock_code} 的数据")
            
            return df
            
        except Exception as e:
            if isinstance(e, DataFetchError):
                raise
            raise DataFetchError(f"Yahoo Finance 获取数据失败: {e}") from e
    
    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化 Yahoo Finance 数据"""
        df = df.copy()
        
        # 重置索引
        df = df.reset_index()
        
        # 处理多层列索引（yfinance 有时返回 MultiIndex）
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
        }
        
        df = df.rename(columns=column_mapping)
        
        # 计算涨跌幅
        if 'close' in df.columns:
            df['pct_chg'] = df['close'].pct_change() * 100
            df['pct_chg'] = df['pct_chg'].fillna(0).round(2)
        
        # 估算成交额
        if 'volume' in df.columns and 'close' in df.columns:
            df['amount'] = df['volume'] * df['close']
        else:
            df['amount'] = 0
        
        df['code'] = stock_code
        
        keep_cols = ['code'] + STANDARD_COLUMNS
        existing_cols = [col for col in keep_cols if col in df.columns]
        df = df[existing_cols]
        
        return df
    
    @classmethod
    def get_nasdaq_top_stocks(cls) -> List[str]:
        """获取纳斯达克热门股票列表"""
        return cls.NASDAQ_TOP_STOCKS.copy()
