# -*- coding: utf-8 -*-
"""
AkshareFetcher - A股首选数据源 (Priority 0)
===================================

数据来源：akshare 库（东方财富等接口）
覆盖市场：A股
"""

import logging
from typing import List

import pandas as pd

from .base import BaseFetcher, DataFetchError, MarketType, STANDARD_COLUMNS

logger = logging.getLogger(__name__)


class AkshareFetcher(BaseFetcher):
    """
    Akshare 数据源实现
    
    优先级：0（A股最高）
    覆盖市场：A股
    """
    
    name = "AkshareFetcher"
    priority = 0
    supported_markets: List[MarketType] = [MarketType.A_SHARE]
    
    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从 akshare 获取原始数据"""
        import akshare as ak
        
        # 标准化代码格式
        code = stock_code.strip()
        if '.' in code:
            code = code.split('.')[0]
        
        logger.debug(f"调用 ak.stock_zh_a_hist({code}, {start_date}, {end_date})")
        
        self.random_sleep(0.5, 1.5)
        
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                raise DataFetchError(f"Akshare 未查询到 {stock_code} 的数据")
            
            return df
            
        except Exception as e:
            if isinstance(e, DataFetchError):
                raise
            raise DataFetchError(f"Akshare 获取数据失败: {e}") from e
    
    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        """标准化 akshare 数据"""
        df = df.copy()
        
        # akshare 返回的列名映射
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
