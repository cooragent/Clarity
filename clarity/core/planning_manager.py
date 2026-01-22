"""Planning file manager for claude-skill style planning-with-files."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .config import AgentConfig, TaskContext, TaskType


class PlanningManager:
    """Manages planning files (task_plan.md, findings.md, progress.md)."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.project_root = config.project_dir.parent
        self.templates_dir = config.templates_dir

        # Runtime directory for generated files
        self.runtime_dir = self.project_root / "runtime"
        self.runtime_dir.mkdir(exist_ok=True)

        self.task_plan_path = self.runtime_dir / "task_plan.md"
        self.findings_path = self.runtime_dir / "findings.md"
        self.progress_path = self.runtime_dir / "progress.md"

    def initialize_files(self, context: TaskContext) -> None:
        """Initialize planning files from templates with task context."""
        self._init_task_plan(context)
        self._init_findings(context)
        self._init_progress(context)

    def _init_task_plan(self, context: TaskContext) -> None:
        """Initialize task_plan.md with task context."""
        template_path = self.templates_dir / "task_plan.md"
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
        else:
            content = self._default_task_plan()

        # Replace placeholders
        task_type_map = {
            TaskType.STOCK_SCREENING: "stock_screening",
            TaskType.HOLDINGS_TRACKING: "holdings_tracking",
            TaskType.STOCK_ANALYSIS: "stock_analysis",
        }

        goal_map = {
            TaskType.STOCK_SCREENING: f"根据条件筛选股票: {context.target}",
            TaskType.HOLDINGS_TRACKING: f"跟踪 {context.target} 的最新持仓",
            TaskType.STOCK_ANALYSIS: f"深度分析股票 {context.target}",
        }

        content = content.replace(
            "[一句话描述最终目标，例如：深度分析 AAPL 股票并给出投资建议]",
            goal_map.get(context.task_type, context.target),
        )
        content = content.replace("[task_type]", task_type_map.get(context.task_type, ""))
        content = content.replace(
            "[股票代码 / 投资大佬名称 / 筛选条件]", context.target
        )
        content = content.replace(
            "[开始日期] - [结束日期]",
            f"{context.trade_date} (lookback: {context.look_back_days} days)",
        )

        self.task_plan_path.write_text(content, encoding="utf-8")

    def _init_findings(self, context: TaskContext) -> None:
        """Initialize findings.md."""
        template_path = self.templates_dir / "findings.md"
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
        else:
            content = "# Findings & Decisions\n\n## Requirements\n-\n"

        self.findings_path.write_text(content, encoding="utf-8")

    def _init_progress(self, context: TaskContext) -> None:
        """Initialize progress.md."""
        template_path = self.templates_dir / "progress.md"
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
        else:
            content = "# Progress Log\n\n"

        # Replace session date placeholder
        today = datetime.now().strftime("%Y-%m-%d")
        content = content.replace("[DATE]", today)

        self.progress_path.write_text(content, encoding="utf-8")

    def read_task_plan(self, max_lines: int = 60) -> str:
        """Read task plan excerpt for attention manipulation."""
        if not self.task_plan_path.exists():
            return ""
        content = self.task_plan_path.read_text(encoding="utf-8")
        lines = content.splitlines()[:max_lines]
        return "\n".join(lines)

    def read_full_plan(self) -> str:
        """Read full task plan."""
        if not self.task_plan_path.exists():
            return ""
        return self.task_plan_path.read_text(encoding="utf-8")

    def update_phase_status(
        self, phase: int, status: str, agent_name: str | None = None
    ) -> None:
        """Update phase status in task_plan.md.

        Args:
            phase: Phase number (1-5)
            status: One of 'pending', 'in_progress', 'complete'
            agent_name: Optional agent name for the update
        """
        if not self.task_plan_path.exists():
            return

        content = self.task_plan_path.read_text(encoding="utf-8")

        # Find and update the phase status
        phase_pattern = rf"(### Phase {phase}:.*?- \*\*Status:\*\*) (pending|in_progress|complete)"
        content = re.sub(phase_pattern, rf"\1 {status}", content, flags=re.DOTALL)

        # Update Current Phase if moving to next
        if status == "in_progress":
            content = re.sub(
                r"(## Current Phase\n)Phase \d", rf"\1Phase {phase}", content
            )

        self.task_plan_path.write_text(content, encoding="utf-8")

    def update_subagent_status(
        self, agent_name: str, task: str, status: str, retry_count: int = 0
    ) -> None:
        """Update subagent assignment table in task_plan.md."""
        if not self.task_plan_path.exists():
            return

        content = self.task_plan_path.read_text(encoding="utf-8")

        # Update the SubAgent Assignments table
        # Pattern: | AgentName | Task | Status | Retry Count |
        pattern = rf"(\| {agent_name} \|)[^\n]+"
        replacement = f"| {agent_name} | {task} | {status} | {retry_count} |"
        content = re.sub(pattern, replacement, content)

        self.task_plan_path.write_text(content, encoding="utf-8")

    def append_findings(self, section: str, content: str) -> None:
        """Append content to a section in findings.md."""
        if not self.findings_path.exists():
            self.findings_path.write_text("# Findings & Decisions\n\n", encoding="utf-8")

        findings = self.findings_path.read_text(encoding="utf-8")

        # Find the section and append content
        section_pattern = rf"(### {section}.*?)\n-"
        if re.search(section_pattern, findings, flags=re.DOTALL):
            findings = re.sub(
                section_pattern, rf"\1\n{content}\n\n-", findings, flags=re.DOTALL
            )
        else:
            # Section not found, append at end
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            findings += f"\n\n### {section}\n*Updated: {timestamp}*\n\n{content}\n"

        self.findings_path.write_text(findings, encoding="utf-8")

    def append_progress(self, phase: int, content: str, agent_name: str = "") -> None:
        """Append progress update."""
        if not self.progress_path.exists():
            self.progress_path.write_text("# Progress Log\n\n", encoding="utf-8")

        progress = self.progress_path.read_text(encoding="utf-8")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = f"\n**[{timestamp}] Phase {phase}"
        if agent_name:
            entry += f" ({agent_name})"
        entry += f":**\n{content}\n"

        progress += entry
        self.progress_path.write_text(progress, encoding="utf-8")

    def log_error(
        self, agent_name: str, error: str, attempt: int, resolution: str = ""
    ) -> None:
        """Log error to both task_plan.md and progress.md."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update task_plan.md errors table
        if self.task_plan_path.exists():
            content = self.task_plan_path.read_text(encoding="utf-8")
            error_entry = f"| {error[:50]}... | {attempt} | {resolution} |"
            content = content.replace(
                "| Error | Attempt | Resolution |\n|-------|---------|------------|",
                f"| Error | Attempt | Resolution |\n|-------|---------|------------|\n{error_entry}",
            )
            self.task_plan_path.write_text(content, encoding="utf-8")

        # Append to progress.md error log
        if self.progress_path.exists():
            progress = self.progress_path.read_text(encoding="utf-8")
            error_entry = (
                f"| {timestamp} | {error[:30]}... | {agent_name} | {attempt} | {resolution} |"
            )
            # Find error log table and append
            if "## Error Log" in progress:
                progress = progress.replace(
                    "|           |       |          | 1       |            |",
                    f"{error_entry}\n|           |       |          | 1       |            |",
                )
            self.progress_path.write_text(progress, encoding="utf-8")

    def get_decision_context(self) -> str:
        """Get context for decision making - combines plan excerpt and recent findings."""
        plan = self.read_task_plan(max_lines=40)

        findings = ""
        if self.findings_path.exists():
            findings = self.findings_path.read_text(encoding="utf-8")
            # Get last 50 lines of findings
            findings_lines = findings.splitlines()[-50:]
            findings = "\n".join(findings_lines)

        return f"## Current Task Plan\n{plan}\n\n## Recent Findings\n{findings}"

    def _default_task_plan(self) -> str:
        """Default task plan template."""
        return """# Task Plan: Financial Intelligence Agent Task

## Goal
[一句话描述最终目标]

## Current Phase
Phase 1

## Task Type
[task_type]

## Phases
### Phase 1: Requirements & Discovery
- **Status:** in_progress

### Phase 2: Data Collection & Analysis
- **Status:** pending

### Phase 3: Synthesis & Report
- **Status:** pending

### Phase 4: Decision & Recommendation
- **Status:** pending

### Phase 5: Delivery
- **Status:** pending

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## Notes
- Update phase status as you progress
"""
