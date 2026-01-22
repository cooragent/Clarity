# clarity Core Module
# Claude-skill style refactored architecture with planning-with-files pattern

from .base_agent import AgentResult, BaseSubAgent, ToolDefinition
from .config import AgentConfig, AgentRole, MCPToolConfig, TaskContext, TaskType
from .master_agent import MasterAgent, TaskPlan
from .orchestrator import (
    FinancialAgentOrchestrator,
    analyze_stock,
    screen_stocks,
    track_holdings,
)
from .notification import (
    NotificationChannel,
    NotificationConfig,
    NotificationService,
    get_notification_service,
    send_notification,
)
from .planning_manager import PlanningManager
from .state_checker import CheckAction, StateCheckResult, StateCheckerAgent
from .working_agent import ExecutionState, ExecutionStep, WorkingAgent

__all__ = [
    # Config
    "AgentConfig",
    "AgentRole",
    "MCPToolConfig",
    "TaskContext",
    "TaskType",
    # Base
    "AgentResult",
    "BaseSubAgent",
    "ToolDefinition",
    # Agents
    "MasterAgent",
    "TaskPlan",
    "WorkingAgent",
    "ExecutionState",
    "ExecutionStep",
    "StateCheckerAgent",
    "StateCheckResult",
    "CheckAction",
    # Orchestrator
    "FinancialAgentOrchestrator",
    "analyze_stock",
    "track_holdings",
    "screen_stocks",
    # Planning
    "PlanningManager",
    # Notification
    "NotificationChannel",
    "NotificationConfig",
    "NotificationService",
    "get_notification_service",
    "send_notification",
]
