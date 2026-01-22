"""Financial Agent Orchestrator - Main entry point for the trading agents system."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

# Auto-load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    # Look for .env in common locations
    _env_paths = [
        Path(__file__).parent.parent.parent / ".env",  # clarity/.env
        Path.cwd() / ".env",
    ]
    for _env_path in _env_paths:
        if _env_path.exists():
            load_dotenv(_env_path)
            break
    else:
        load_dotenv()  # Try default
except ImportError:
    pass  # python-dotenv not installed, user must set env vars manually

from .config import AgentConfig, TaskContext, TaskType
from .master_agent import MasterAgent
from .planning_manager import PlanningManager
from .state_checker import StateCheckerAgent
from .working_agent import WorkingAgent

logger = logging.getLogger(__name__)


class FinancialAgentOrchestrator:
    """Main orchestrator for the financial agent system.

    This class coordinates all agents and manages the overall workflow:
    1. Receives user input
    2. MasterAgent analyzes and plans the task
    3. WorkingAgent executes the plan
    4. StateCheckerAgent monitors execution
    5. Results are synthesized and returned

    Usage:
        ```python
        from clarity.core import FinancialAgentOrchestrator, AgentConfig

        config = AgentConfig()
        orchestrator = FinancialAgentOrchestrator(config)

        # Analyze a stock
        result = await orchestrator.run(
            task_type="stock_analysis",
            target="AAPL",
            trade_date="2025-01-18",
        )

        # Track holdings
        result = await orchestrator.run(
            task_type="holdings_tracking",
            target="Warren Buffett",
            trade_date="2025-01-18",
        )

        # Screen stocks
        result = await orchestrator.run(
            task_type="stock_screening",
            target="high dividend yield low PE tech stocks",
            trade_date="2025-01-18",
        )
        ```
    """

    def __init__(
        self,
        config: AgentConfig | None = None,
        llm: Any = None,
    ):
        """Initialize the orchestrator.

        Args:
            config: Agent configuration. Uses defaults if not provided.
            llm: Optional LLM instance to use for agents.
        """
        self.config = config or AgentConfig()
        self.llm = llm

        # Initialize planning manager
        self.planning_manager = PlanningManager(self.config)

        # Initialize agents
        self.master_agent = MasterAgent(self.config, llm=self.llm)
        self.state_checker = StateCheckerAgent(self.config, llm=self.llm)
        self.working_agent = WorkingAgent(
            self.config, self.master_agent, llm=self.llm
        )

        # Connect working agent to state checker
        self.working_agent.set_state_checker(self.state_checker)

        logger.info("FinancialAgentOrchestrator initialized")

    async def run(
        self,
        task_type: str | TaskType,
        target: str,
        trade_date: str | None = None,
        look_back_days: int = 7,
        constraints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the financial agent system.

        Args:
            task_type: Type of task (stock_analysis, holdings_tracking, stock_screening)
            target: Target for the task (stock ticker, investor name, or search criteria)
            trade_date: Date for analysis (defaults to today)
            look_back_days: Number of days to look back for historical data
            constraints: Additional constraints for the task

        Returns:
            Dictionary containing the analysis results
        """
        # Parse task type
        if isinstance(task_type, str):
            task_type = TaskType(task_type)

        # Default trade date to today
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y-%m-%d")

        # Create task context
        context = TaskContext(
            task_type=task_type,
            target=target,
            trade_date=trade_date,
            look_back_days=look_back_days,
            constraints=constraints or {},
        )

        logger.info(
            f"Starting task: {task_type.value} for {target} on {trade_date}"
        )

        try:
            # Phase 1: Master Agent creates plan
            task_plan = self.master_agent.create_task_plan(context)
            logger.info(f"Task plan created with {len(task_plan.priority_order)} agents")

            # Phase 2-4: Working Agent executes plan
            self.state_checker.reset_counters()
            execution_state = await self.working_agent.execute_plan(task_plan, context)

            # Phase 5: Validate final state
            final_check = await self.state_checker.validate_final_state(
                execution_state
            )

            # Synthesize results
            final_report = self.master_agent.synthesize_results(
                {
                    s.agent_name: s.result
                    for s in execution_state.steps
                    if s.result is not None
                },
                context,
            )

            return {
                "success": final_check.is_ok,
                "task_type": task_type.value,
                "target": target,
                "trade_date": trade_date,
                "report": final_report,
                "execution_summary": {
                    "total_steps": len(execution_state.steps),
                    "successful_steps": sum(
                        1 for s in execution_state.steps if s.status == "complete"
                    ),
                    "failed_steps": sum(
                        1 for s in execution_state.steps if s.status == "failed"
                    ),
                },
                "health_status": self.state_checker.get_health_status(),
                "files": {
                    "task_plan": str(self.planning_manager.task_plan_path),
                    "findings": str(self.planning_manager.findings_path),
                    "progress": str(self.planning_manager.progress_path),
                },
            }

        except Exception as e:
            logger.error(f"Error running task: {e}", exc_info=True)

            # Log error to planning files
            self.planning_manager.log_error(
                "Orchestrator", str(e), 1, "Task failed"
            )

            return {
                "success": False,
                "task_type": task_type.value,
                "target": target,
                "trade_date": trade_date,
                "error": str(e),
                "report": "",
            }

    async def run_from_natural_language(self, user_input: str) -> dict[str, Any]:
        """Run the agent from natural language input.

        The MasterAgent will analyze the input to determine:
        - Task type
        - Target (stock ticker, investor name, or criteria)
        - Any constraints

        Args:
            user_input: Natural language description of the task

        Returns:
            Dictionary containing the analysis results
        """
        # Analyze the task
        task_type = self.master_agent.analyze_task(user_input)

        # Extract target from input
        target = self._extract_target(user_input, task_type)

        logger.info(
            f"Analyzed input: task_type={task_type.value}, target={target}"
        )

        # Run with analyzed parameters
        return await self.run(
            task_type=task_type,
            target=target,
            trade_date=datetime.now().strftime("%Y-%m-%d"),
        )

    def _extract_target(self, user_input: str, task_type: TaskType) -> str:
        """Extract target from user input based on task type."""
        input_upper = user_input.upper()

        # Common stock tickers
        common_tickers = [
            "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA",
            "BRK.A", "BRK.B", "JPM", "V", "JNJ", "WMT", "PG", "MA", "UNH",
            "HD", "DIS", "PYPL", "NFLX", "INTC", "CSCO", "PFE", "VZ",
        ]

        # Check for stock tickers
        for ticker in common_tickers:
            if ticker in input_upper:
                return ticker

        # Check for investor names
        investors = {
            "巴菲特": "Warren Buffett",
            "buffett": "Warren Buffett",
            "达利欧": "Ray Dalio",
            "dalio": "Ray Dalio",
            "木头姐": "Cathie Wood",
            "wood": "Cathie Wood",
            "burry": "Michael Burry",
            "阿克曼": "Bill Ackman",
            "ackman": "Bill Ackman",
            "soros": "George Soros",
            "索罗斯": "George Soros",
        }

        input_lower = user_input.lower()
        for key, name in investors.items():
            if key in input_lower:
                return name

        # For screening, use the whole input as criteria
        if task_type == TaskType.STOCK_SCREENING:
            return user_input

        # Default: try to find any 1-5 letter uppercase word as ticker
        import re

        potential_tickers = re.findall(r"\b[A-Z]{1,5}\b", user_input)
        if potential_tickers:
            return potential_tickers[0]

        return user_input

    async def load_mcp_tools(self) -> None:
        """Load MCP tools from configuration."""
        await self.master_agent.load_mcp_tools()

    def get_available_agents(self) -> list[str]:
        """Get list of available SubAgents."""
        return list(self.master_agent.subagents.keys())

    def get_planning_files(self) -> dict[str, Path]:
        """Get paths to planning files."""
        return {
            "task_plan": self.planning_manager.task_plan_path,
            "findings": self.planning_manager.findings_path,
            "progress": self.planning_manager.progress_path,
        }


# Convenience function for simple usage
async def analyze_stock(
    ticker: str,
    trade_date: str | None = None,
    config: AgentConfig | None = None,
) -> dict[str, Any]:
    """Convenience function to analyze a stock.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        trade_date: Date for analysis (defaults to today)
        config: Optional configuration

    Returns:
        Analysis results
    """
    orchestrator = FinancialAgentOrchestrator(config)
    return await orchestrator.run(
        task_type=TaskType.STOCK_ANALYSIS,
        target=ticker,
        trade_date=trade_date,
    )


async def track_holdings(
    investor_name: str,
    trade_date: str | None = None,
    config: AgentConfig | None = None,
) -> dict[str, Any]:
    """Convenience function to track an investor's holdings.

    Args:
        investor_name: Name of the investor (e.g., "Warren Buffett")
        trade_date: Date for analysis (defaults to today)
        config: Optional configuration

    Returns:
        Holdings tracking results
    """
    orchestrator = FinancialAgentOrchestrator(config)
    return await orchestrator.run(
        task_type=TaskType.HOLDINGS_TRACKING,
        target=investor_name,
        trade_date=trade_date,
    )


async def screen_stocks(
    criteria: str,
    trade_date: str | None = None,
    config: AgentConfig | None = None,
) -> dict[str, Any]:
    """Convenience function to screen stocks.

    Args:
        criteria: Screening criteria (e.g., "high dividend yield low PE")
        trade_date: Date for analysis (defaults to today)
        config: Optional configuration

    Returns:
        Screening results
    """
    orchestrator = FinancialAgentOrchestrator(config)
    return await orchestrator.run(
        task_type=TaskType.STOCK_SCREENING,
        target=criteria,
        trade_date=trade_date,
    )
