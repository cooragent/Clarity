"""Base class for all SubAgents in the trading system."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from .config import AgentConfig, AgentRole, TaskContext

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition for a tool that can be used by agents."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., str]

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_anthropic_schema(self) -> dict[str, Any]:
        """Convert to Anthropic tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


@dataclass
class AgentResult:
    """Result from agent execution."""

    success: bool
    output: str
    report: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "report": self.report,
            "tool_calls": self.tool_calls,
            "errors": self.errors,
            "metadata": self.metadata,
        }


class BaseSubAgent(ABC):
    """Base class for all SubAgents.

    Each SubAgent is a specialized analyzer that can be called as a tool by the MasterAgent.
    SubAgents follow the planning-with-files pattern and update the shared planning files.
    """

    role: AgentRole = AgentRole.FUNDAMENTALS_ANALYST  # Override in subclasses
    name: str = "BaseSubAgent"
    description: str = "Base sub-agent"

    def __init__(self, config: AgentConfig, llm: Any = None):
        self.config = config
        self.llm = llm
        self.tools: list[ToolDefinition] = []
        self._setup_tools()

    @abstractmethod
    def _setup_tools(self) -> None:
        """Setup tools available to this agent. Override in subclasses."""
        pass

    @abstractmethod
    async def execute(self, context: TaskContext, **kwargs) -> AgentResult:
        """Execute the agent's task.

        Args:
            context: The current task context
            **kwargs: Additional arguments specific to the agent

        Returns:
            AgentResult with the execution result
        """
        pass

    def get_system_prompt(self, context: TaskContext) -> str:
        """Get the system prompt for this agent.

        Override in subclasses for specialized prompts.
        """
        return f"""You are {self.name}, a specialized financial analyst.

Your role: {self.description}

Current task context:
- Task Type: {context.task_type.value}
- Target: {context.target}
- Trade Date: {context.trade_date}
- Look Back Days: {context.look_back_days}

Available tools: {', '.join(t.name for t in self.tools)}

Instructions:
1. Use the available tools to gather relevant data
2. Analyze the data thoroughly
3. Provide a detailed report with your findings
4. Include a summary table at the end of your report
5. Be specific and data-driven in your analysis

Do not simply state that trends are mixed - provide detailed and fine-grained analysis.
"""

    def expose_as_tool(self) -> ToolDefinition:
        """Expose this agent as a tool for the MasterAgent to use."""
        return ToolDefinition(
            name=f"call_{self.name.lower().replace(' ', '_')}",
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "context_json": {
                        "type": "string",
                        "description": "JSON-encoded TaskContext for the analysis",
                    },
                    "specific_focus": {
                        "type": "string",
                        "description": "Optional specific aspect to focus on",
                    },
                },
                "required": ["context_json"],
            },
            handler=self._handle_tool_call,
        )

    async def _handle_tool_call(
        self, context_json: str, specific_focus: str = ""
    ) -> str:
        """Handle a tool call from MasterAgent."""
        try:
            context_data = json.loads(context_json)
            context = TaskContext.from_dict(context_data)
            result = await self.execute(context, specific_focus=specific_focus)
            return json.dumps(result.to_dict())
        except Exception as e:
            logger.error(f"Error in {self.name} tool call: {e}")
            return json.dumps(
                AgentResult(
                    success=False, output="", errors=[str(e)]
                ).to_dict()
            )

    def _format_report_with_table(self, content: str, key_points: list[dict]) -> str:
        """Format a report with a summary table at the end."""
        table = "\n\n## Summary Table\n\n"
        table += "| Category | Key Point | Impact |\n"
        table += "|----------|-----------|--------|\n"
        for point in key_points:
            table += f"| {point.get('category', '')} | {point.get('point', '')} | {point.get('impact', '')} |\n"

        return content + table
