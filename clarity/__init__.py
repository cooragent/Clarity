"""clarity - AI-powered Financial Intelligence Agent.

A multi-agent framework for financial analysis using Claude-skill patterns.

Usage:
    from clarity.core import (
        FinancialAgentOrchestrator,
        AgentConfig,
        TaskType,
    )

    config = AgentConfig()
    orchestrator = FinancialAgentOrchestrator(config)

    # Analyze a stock
    result = await orchestrator.run(
        task_type=TaskType.STOCK_ANALYSIS,
        target="AAPL",
        trade_date="2025-01-18",
    )
"""

__version__ = "0.2.0"
__author__ = "clarity Team"

# Core exports
from .core import (
    AgentConfig,
    FinancialAgentOrchestrator,
    TaskType,
)

__all__ = [
    "AgentConfig",
    "FinancialAgentOrchestrator",
    "TaskType",
    "__version__",
]
