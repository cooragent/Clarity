"""Master Agent - Responsible for task planning and orchestration."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from .base_agent import AgentResult, BaseSubAgent, ToolDefinition
from .config import AgentConfig, AgentRole, TaskContext, TaskType
from .planning_manager import PlanningManager
from .subagents import SUBAGENT_MAP

logger = logging.getLogger(__name__)


@dataclass
class TaskPlan:
    """A structured task plan for execution."""

    task_id: str
    task_type: TaskType
    target: str
    phases: list[dict[str, Any]]
    subagent_assignments: dict[str, list[str]]  # agent_name -> list of tasks
    priority_order: list[str]  # Order of subagent execution

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "target": self.target,
            "phases": self.phases,
            "subagent_assignments": self.subagent_assignments,
            "priority_order": self.priority_order,
        }


class MasterAgent:
    """Master Agent responsible for task planning and orchestration.

    The Master Agent:
    1. Analyzes incoming tasks
    2. Creates task plans based on task_plan.md templates
    3. Loads and manages SubAgents
    4. Loads MCP tools
    5. Assigns tasks to appropriate SubAgents
    """

    name = "MasterAgent"
    role = AgentRole.MASTER

    def __init__(self, config: AgentConfig, llm: Any = None):
        self.config = config
        self.llm = llm
        self.planning_manager = PlanningManager(config)

        # Initialize SubAgents
        self.subagents: dict[str, BaseSubAgent] = {}
        self._load_subagents()

        # MCP tools
        self.mcp_tools: list[ToolDefinition] = []
        self._mcp_servers: list[Any] = []

    def _load_subagents(self) -> None:
        """Load all available SubAgents."""
        for name, agent_class in SUBAGENT_MAP.items():
            try:
                self.subagents[name] = agent_class(config=self.config, llm=self.llm)
                logger.info(f"Loaded SubAgent: {name}")
            except Exception as e:
                logger.error(f"Failed to load SubAgent {name}: {e}")

    async def load_mcp_tools(self) -> None:
        """Load MCP tools from configuration.

        Reference: youtu-agent MCP loading pattern.
        """
        try:
            from mcp import StdioServerParameters

            for mcp_config in self.config.mcp_tools:
                try:
                    server_params = StdioServerParameters(
                        command=mcp_config.command,
                        args=mcp_config.args,
                        env=mcp_config.env,
                    )
                    # Store server params for later connection
                    self._mcp_servers.append(
                        {
                            "name": mcp_config.name,
                            "params": server_params,
                        }
                    )
                    logger.info(f"Loaded MCP tool config: {mcp_config.name}")
                except Exception as e:
                    logger.error(f"Failed to load MCP tool {mcp_config.name}: {e}")
        except ImportError:
            logger.warning("MCP package not available, skipping MCP tool loading")

    def get_subagent_tools(self) -> list[ToolDefinition]:
        """Get all SubAgents exposed as tools."""
        tools = []
        for name, agent in self.subagents.items():
            tools.append(agent.expose_as_tool())
        return tools

    def analyze_task(self, user_input: str) -> TaskType:
        """Analyze user input to determine task type.

        Returns:
            TaskType indicating what kind of task this is.
        """
        input_lower = user_input.lower()

        # Check for holdings tracking keywords
        holdings_keywords = [
            "持仓",
            "holdings",
            "大佬",
            "巴菲特",
            "buffett",
            "dalio",
            "burry",
            "ackman",
            "wood",
            "soros",
            "投资者",
            "investor",
            "13f",
            "portfolio",
        ]
        if any(kw in input_lower for kw in holdings_keywords):
            return TaskType.HOLDINGS_TRACKING

        # Check for stock screening keywords
        screening_keywords = [
            "筛选",
            "screen",
            "filter",
            "找出",
            "寻找",
            "搜索股票",
            "条件",
            "criteria",
            "低pe",
            "高分红",
            "undervalued",
            "growth stocks",
        ]
        if any(kw in input_lower for kw in screening_keywords):
            return TaskType.STOCK_SCREENING

        # Default to stock analysis
        return TaskType.STOCK_ANALYSIS

    def create_task_plan(self, context: TaskContext) -> TaskPlan:
        """Create a task plan based on the task context.

        This implements the planning-with-files pattern by:
        1. Analyzing the task type
        2. Determining which SubAgents are needed
        3. Creating execution order
        4. Initializing planning files
        """
        task_type = context.task_type

        # Initialize planning files
        self.planning_manager.initialize_files(context)

        # Determine SubAgents needed based on task type
        if task_type == TaskType.STOCK_ANALYSIS:
            subagent_assignments = {
                "technical_analyst": ["Analyze technical indicators and price trends"],
                "fundamentals_analyst": [
                    "Analyze financial statements and fundamental metrics"
                ],
                "news_analyst": ["Gather and analyze relevant news"],
                "sentiment_analyst": ["Analyze social media sentiment"],
            }
            priority_order = [
                "technical_analyst",
                "fundamentals_analyst",
                "news_analyst",
                "sentiment_analyst",
            ]

        elif task_type == TaskType.HOLDINGS_TRACKING:
            subagent_assignments = {
                "holdings_hunter": ["Track and analyze investor holdings"],
                "news_analyst": ["Find related news about the investor"],
            }
            priority_order = ["holdings_hunter", "news_analyst"]

        elif task_type == TaskType.STOCK_SCREENING:
            subagent_assignments = {
                "alpha_hound": ["Screen stocks based on criteria"],
                "technical_analyst": ["Analyze technicals of top picks"],
                "fundamentals_analyst": ["Analyze fundamentals of top picks"],
            }
            priority_order = ["alpha_hound", "technical_analyst", "fundamentals_analyst"]

        else:
            subagent_assignments = {}
            priority_order = []

        # Create phases
        phases = [
            {
                "phase": 1,
                "name": "Requirements & Discovery",
                "status": "in_progress",
                "tasks": ["Understand task requirements", "Initialize planning files"],
            },
            {
                "phase": 2,
                "name": "Data Collection & Analysis",
                "status": "pending",
                "tasks": list(subagent_assignments.keys()),
            },
            {
                "phase": 3,
                "name": "Synthesis & Report",
                "status": "pending",
                "tasks": ["Combine SubAgent reports", "Generate insights"],
            },
            {
                "phase": 4,
                "name": "Decision & Recommendation",
                "status": "pending",
                "tasks": ["Generate recommendation", "Risk assessment"],
            },
            {
                "phase": 5,
                "name": "Delivery",
                "status": "pending",
                "tasks": ["Final review", "Deliver to user"],
            },
        ]

        task_plan = TaskPlan(
            task_id=f"{task_type.value}_{context.target}_{context.trade_date}",
            task_type=task_type,
            target=context.target,
            phases=phases,
            subagent_assignments=subagent_assignments,
            priority_order=priority_order,
        )

        # Update planning files with the plan
        self.planning_manager.update_phase_status(1, "in_progress", self.name)
        self.planning_manager.append_progress(
            1,
            f"Task plan created:\n"
            f"- Task Type: {task_type.value}\n"
            f"- Target: {context.target}\n"
            f"- SubAgents: {', '.join(priority_order)}",
            self.name,
        )

        return task_plan

    async def execute_plan(
        self, task_plan: TaskPlan, context: TaskContext
    ) -> dict[str, AgentResult]:
        """Execute the task plan by coordinating SubAgents.

        Note: This is a simplified version. The actual execution
        is handled by WorkingAgent with StateCheckerAgent monitoring.
        """
        results = {}

        # Update phase 1 as complete
        self.planning_manager.update_phase_status(1, "complete", self.name)
        self.planning_manager.update_phase_status(2, "in_progress", self.name)

        # Execute SubAgents in priority order
        for agent_name in task_plan.priority_order:
            if agent_name not in self.subagents:
                logger.warning(f"SubAgent {agent_name} not available")
                continue

            agent = self.subagents[agent_name]
            tasks = task_plan.subagent_assignments.get(agent_name, [])

            logger.info(f"Executing SubAgent: {agent_name} with tasks: {tasks}")

            # Update planning files
            self.planning_manager.update_subagent_status(
                agent.name, ", ".join(tasks), "in_progress"
            )

            try:
                result = await agent.execute(context)
                results[agent_name] = result

                # Update planning files
                status = "complete" if result.success else "failed"
                self.planning_manager.update_subagent_status(
                    agent.name, ", ".join(tasks), status
                )

                if result.report:
                    self.planning_manager.append_findings(
                        f"{agent.name} Analysis", result.report[:2000]
                    )

            except Exception as e:
                logger.error(f"Error executing {agent_name}: {e}")
                self.planning_manager.log_error(agent_name, str(e), 1)
                results[agent_name] = AgentResult(
                    success=False, output="", errors=[str(e)]
                )

        # Update phase 2 as complete
        self.planning_manager.update_phase_status(2, "complete", self.name)

        return results

    def get_system_prompt(self, context: TaskContext) -> str:
        """Get the system prompt for the Master Agent."""
        # Read current plan for context
        plan_excerpt = self.planning_manager.read_task_plan()

        return f"""You are the MasterAgent, responsible for orchestrating financial analysis tasks.

Your role is to:
1. Analyze the user's request and determine the appropriate task type
2. Create a comprehensive task plan
3. Assign tasks to specialized SubAgents
4. Coordinate the execution of the plan
5. Synthesize results into actionable insights

Current Task Context:
- Task Type: {context.task_type.value}
- Target: {context.target}
- Trade Date: {context.trade_date}

Available SubAgents:
{', '.join(self.subagents.keys())}

Current Task Plan:
{plan_excerpt}

Instructions:
- Follow the planning-with-files pattern
- Update planning files after each major decision
- Ensure all SubAgents complete their tasks
- Handle errors gracefully with retry logic
- Synthesize results into a coherent analysis
"""

    def synthesize_results(
        self, results: dict[str, AgentResult], context: TaskContext
    ) -> str:
        """Synthesize results from all SubAgents into a final report."""
        report_sections = []

        report_sections.append(f"# Financial Analysis Report: {context.target}")
        report_sections.append(f"\n**Analysis Date:** {context.trade_date}")
        report_sections.append(f"**Task Type:** {context.task_type.value}\n")

        report_sections.append("## Executive Summary\n")
        report_sections.append(
            "This report synthesizes analysis from multiple specialized agents.\n"
        )

        # Add each agent's report
        for agent_name, result in results.items():
            if result.success and result.report:
                report_sections.append(f"\n## {agent_name.replace('_', ' ').title()}\n")
                # Truncate if too long
                report_text = (
                    result.report[:3000] + "..."
                    if len(result.report) > 3000
                    else result.report
                )
                report_sections.append(report_text)
            elif not result.success:
                report_sections.append(f"\n## {agent_name.replace('_', ' ').title()}\n")
                report_sections.append(
                    f"*Analysis incomplete. Errors: {', '.join(result.errors)}*\n"
                )

        # Add recommendation section
        report_sections.append("\n## Recommendation\n")
        report_sections.append(
            "*Based on the combined analysis, a recommendation will be generated.*\n"
        )

        # Add risk factors
        report_sections.append("\n## Risk Factors\n")
        all_errors = []
        for result in results.values():
            all_errors.extend(result.errors)
        if all_errors:
            report_sections.append("Noted issues during analysis:\n")
            for error in all_errors[:5]:
                report_sections.append(f"- {error}\n")

        return "\n".join(report_sections)
