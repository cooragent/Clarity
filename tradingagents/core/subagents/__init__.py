# SubAgents Module
# Specialized analysis agents for the trading system

from .fundamentals_analyst import FundamentalsAnalyst
from .sentiment_analyst import SentimentAnalyst
from .news_analyst import NewsAnalyst
from .technical_analyst import TechnicalAnalyst
from .holdings_hunter import HoldingsHunter
from .alpha_hound import AlphaHound

__all__ = [
    "FundamentalsAnalyst",
    "SentimentAnalyst",
    "NewsAnalyst",
    "TechnicalAnalyst",
    "HoldingsHunter",
    "AlphaHound",
]

# Map agent names to classes for dynamic loading
SUBAGENT_MAP = {
    "fundamentals_analyst": FundamentalsAnalyst,
    "sentiment_analyst": SentimentAnalyst,
    "news_analyst": NewsAnalyst,
    "technical_analyst": TechnicalAnalyst,
    "holdings_hunter": HoldingsHunter,
    "alpha_hound": AlphaHound,
}
