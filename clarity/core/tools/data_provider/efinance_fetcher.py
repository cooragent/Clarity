# -*- coding: utf-8 -*-
"""
EfinanceFetcher - A股备选数据源 (Priority 1)
===================================

数据来源：efinance 库
覆盖市场：A股
"""

import logging
from typing import List

import pandas as pd

from .base import BaseFetcher, DataFetchError, MarketType, STANDARD_COLUMNS

logger = logging.getLogger(__name__)


class EfinanceFetcher(BaseFetcher):
    """
    Efinance 数据源实现
    
    优先级：1（A股备选）
    覆盖市场：A股
    """
    
    name = "EfinanceFetcher"
    priority = 1
    supported_markets: List[MarketType] = [MarketType.A_SHARE]
    
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从 efinance 获取原始数据"""
        try:
            import efinance as ef
        except ImportError:
            raise DataFetchError("efinance 库未安装，请运行: pip install efinance")
        
        code = stock_code.strip()
        if '.' in code:
            code = code.split('.')[0]
        
        logger.debug(f"调用 ef.stock.get_quote_history({code})")
        
        self.random_sleep(0.5, 1.5)
        
        try:
            df = ef.stock.get_quote_history(
                stock_codes=code,
                beg=start_date.replace('-', ''),
                end=end_date.replace('-', ''),
                fqt=1  # 前复权
            )
            
            if df.empty:
                raise DataFetchError(f"Efinance 未查询到 {stock_code} 的数据")
            
            return df
            
        except Exception as e:
            if isinstance(e, DataFetchError):
                raise
            raise DataFetchError(f"Efinance 获取数据失败: {e}") from e
    
    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化 efinance 数据"""
        df = df.copy()
        
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
            '成交额': 'amount',
            '涨跌幅': 'pct_chg',
        }
        
        df = df.rename(columns=column_mapping)
        df['code'] = stock_code
        
        keep_cols = ['code'] + STANDARD_COLUMNS
        existing_cols = [col for col in keep_cols if col in df.columns]
        df = df[existing_cols]
        
        return df
