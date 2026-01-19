"""Configuration for the trading agents system."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class TaskType(Enum):
    """Supported task types for the financial agent."""

    STOCK_SCREENING = "stock_screening"  # 根据复杂条件深度查询并筛选股票
    HOLDINGS_TRACKING = "holdings_tracking"  # 跟踪某个金融大佬的最新持仓
    STOCK_ANALYSIS = "stock_analysis"  # 深度分析某只特定股票
    DAILY_DASHBOARD = "daily_dashboard"  # 每日决策仪表盘


class AgentRole(Enum):
    """Agent roles in the system."""

    MASTER = "master"  # 规划任务
    WORKING = "working"  # 执行任务
    STATE_CHECKER = "state_checker"  # 检查状态
    FUNDAMENTALS_ANALYST = "fundamentals_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    NEWS_ANALYST = "news_analyst"
    TECHNICAL_ANALYST = "technical_analyst"
    HOLDINGS_HUNTER = "holdings_hunter"
    ALPHA_HOUND = "alpha_hound"


@dataclass
class MCPToolConfig:
    """MCP tool configuration."""

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for the trading agents system."""

    # Project paths
    project_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    results_dir: Path = field(
        default_factory=lambda: Path(os.getenv("TRADINGAGENTS_RESULTS_DIR", "./runtime/results"))
    )
    data_dir: Path | None = None
    templates_dir: Path | None = None

    # LLM settings
    llm_provider: str = "anthropic"  # anthropic, openai, google
    deep_think_llm: str = "claude-sonnet-4-20250514"
    quick_think_llm: str = "claude-sonnet-4-20250514"
    backend_url: str | None = None

    # API Keys (load from environment)
    anthropic_api_key: str | None = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY")
    )
    openai_api_key: str | None = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )
    finnhub_api_key: str | None = field(
        default_factory=lambda: os.getenv("FINNHUB_API_KEY")
    )
    serper_api_key: str | None = field(
        default_factory=lambda: os.getenv("SERPER_API_KEY")
    )
    jina_api_key: str | None = field(default_factory=lambda: os.getenv("JINA_API_KEY"))

    # Agent settings
    max_retry_count: int = 3
    max_debate_rounds: int = 1
    max_risk_discuss_rounds: int = 1

    # Tool settings
    online_tools: bool = True

    # MCP tool configurations
    mcp_tools: list[MCPToolConfig] = field(default_factory=list)

    def __post_init__(self):
        if self.templates_dir is None:
            self.templates_dir = self.project_dir / "templates"

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "project_dir": str(self.project_dir),
            "results_dir": str(self.results_dir),
            "data_dir": str(self.data_dir) if self.data_dir else None,
            "llm_provider": self.llm_provider,
            "deep_think_llm": self.deep_think_llm,
            "quick_think_llm": self.quick_think_llm,
            "backend_url": self.backend_url,
            "online_tools": self.online_tools,
            "max_retry_count": self.max_retry_count,
        }


@dataclass
class TaskContext:
    """Context for a single task execution."""

    task_type: TaskType
    target: str  # 股票代码 / 投资大佬名称 / 筛选条件
    trade_date: str  # YYYY-MM-DD
    look_back_days: int = 7
    constraints: dict[str, Any] = field(default_factory=dict)

    # Runtime state
    current_phase: int = 1
    retry_counts: dict[str, int] = field(default_factory=dict)
    collected_reports: dict[str, str] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for state management."""
        return {
            "task_type": self.task_type.value,
            "target": self.target,
            "trade_date": self.trade_date,
            "look_back_days": self.look_back_days,
            "constraints": self.constraints,
            "current_phase": self.current_phase,
            "retry_counts": self.retry_counts,
            "collected_reports": self.collected_reports,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskContext:
        """Create context from dictionary."""
        return cls(
            task_type=TaskType(data["task_type"]),
            target=data["target"],
            trade_date=data["trade_date"],
            look_back_days=data.get("look_back_days", 7),
            constraints=data.get("constraints", {}),
            current_phase=data.get("current_phase", 1),
            retry_counts=data.get("retry_counts", {}),
            collected_reports=data.get("collected_reports", {}),
            errors=data.get("errors", []),
        )
