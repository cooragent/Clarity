# SubAgents Module
# Specialized analysis agents for the trading system

from .fundamentals_analyst import FundamentalsAnalyst
from .sentiment_analyst import SentimentAnalyst
from .news_analyst import NewsAnalyst
from .technical_analyst import TechnicalAnalyst
from .holdings_hunter import HoldingsHunter
from .alpha_hound import AlphaHound
from .daily_dashboard import DailyDashboard

__all__ = [
    "FundamentalsAnalyst",
    "SentimentAnalyst",
    "NewsAnalyst",
    "TechnicalAnalyst",
    "HoldingsHunter",
    "AlphaHound",
    "DailyDashboard",
]

# Map agent names to classes for dynamic loading
SUBAGENT_MAP = {
    "fundamentals_analyst": FundamentalsAnalyst,
    "sentiment_analyst": SentimentAnalyst,
    "news_analyst": NewsAnalyst,
    "technical_analyst": TechnicalAnalyst,
    "holdings_hunter": HoldingsHunter,
    "alpha_hound": AlphaHound,
    "daily_dashboard": DailyDashboard,
}
