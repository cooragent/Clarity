"""Working Agent - Responsible for executing task plans step by step."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base_agent import AgentResult, BaseSubAgent
from .config import AgentConfig, AgentRole, TaskContext
from .master_agent import MasterAgent, TaskPlan
from .planning_manager import PlanningManager

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStep:
    """A single step in the execution plan."""

    step_id: int
    agent_name: str
    task: str
    status: str = "pending"  # pending, in_progress, complete, failed
    retry_count: int = 0
    result: AgentResult | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str = ""


@dataclass
class ExecutionState:
    """Current state of task execution."""

    task_plan: TaskPlan
    context: TaskContext
    current_phase: int = 1
    current_step: int = 0
    steps: list[ExecutionStep] = field(default_factory=list)
    is_complete: bool = False
    has_error: bool = False
    final_report: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_plan": self.task_plan.to_dict(),
            "context": self.context.to_dict(),
            "current_phase": self.current_phase,
            "current_step": self.current_step,
            "steps": [
                {
                    "step_id": s.step_id,
                    "agent_name": s.agent_name,
                    "task": s.task,
                    "status": s.status,
                    "retry_count": s.retry_count,
                }
                for s in self.steps
            ],
            "is_complete": self.is_complete,
            "has_error": self.has_error,
        }


class WorkingAgent:
    """Working Agent responsible for executing task plans step by step.

    The Working Agent:
    1. Receives a task plan from MasterAgent
    2. Executes each step in the plan sequentially
    3. Handles step execution with proper error handling
    4. Updates progress.md and findings.md after each step
    5. Works with StateCheckerAgent for validation and retry logic
    """

    name = "WorkingAgent"
    role = AgentRole.WORKING

    def __init__(
        self,
        config: AgentConfig,
        master_agent: MasterAgent,
        llm: Any = None,
    ):
        self.config = config
        self.llm = llm
        self.master_agent = master_agent
        self.planning_manager = PlanningManager(config)

        # State checker will be set after initialization
        self.state_checker: Any = None

        # Current execution state
        self.execution_state: ExecutionState | None = None

    def set_state_checker(self, state_checker: Any) -> None:
        """Set the state checker agent."""
        self.state_checker = state_checker

    def prepare_execution(
        self, task_plan: TaskPlan, context: TaskContext
    ) -> ExecutionState:
        """Prepare execution state from task plan."""
        steps = []
        step_id = 0

        for agent_name in task_plan.priority_order:
            tasks = task_plan.subagent_assignments.get(agent_name, [])
            for task in tasks:
                steps.append(
                    ExecutionStep(
                        step_id=step_id,
                        agent_name=agent_name,
                        task=task,
                    )
                )
                step_id += 1

        self.execution_state = ExecutionState(
            task_plan=task_plan,
            context=context,
            steps=steps,
        )

        return self.execution_state

    async def execute_plan(
        self, task_plan: TaskPlan, context: TaskContext
    ) -> ExecutionState:
        """Execute the entire task plan.

        This is the main execution loop that:
        1. Prepares execution state
        2. Executes each step
        3. Checks state after each step
        4. Handles retries and errors
        """
        # Prepare execution
        state = self.prepare_execution(task_plan, context)

        logger.info(
            f"WorkingAgent: Starting execution of {len(state.steps)} steps"
        )

        # Log start
        self.planning_manager.append_progress(
            2,
            f"Starting execution with {len(state.steps)} steps:\n"
            + "\n".join(
                f"  {s.step_id + 1}. {s.agent_name}: {s.task}" for s in state.steps
            ),
            self.name,
        )

        # Execute each step
        for step in state.steps:
            state.current_step = step.step_id

            # Execute the step
            success = await self._execute_step(step, context)

            # Check state with StateCheckerAgent
            if self.state_checker:
                check_result = await self.state_checker.check_step(step, context)

                if not check_result.is_ok:
                    # Handle the issue based on checker recommendation
                    if check_result.action == "retry":
                        success = await self._retry_step(step, context)
                    elif check_result.action == "skip":
                        logger.warning(f"Skipping step {step.step_id}: {step.task}")
                        step.status = "skipped"
                    elif check_result.action == "replan":
                        logger.error("Replanning required - stopping execution")
                        state.has_error = True
                        break

            if not success and step.status != "skipped":
                state.has_error = True
                # Continue with remaining steps if possible

        # Mark execution complete
        state.is_complete = True

        # Update phases
        self.planning_manager.update_phase_status(2, "complete", self.name)
        self.planning_manager.update_phase_status(3, "in_progress", self.name)

        # Generate final report
        state.final_report = self._synthesize_results(state)

        # Update findings and progress
        self.planning_manager.append_findings(
            "Final Synthesis", state.final_report[:3000]
        )
        self.planning_manager.update_phase_status(3, "complete", self.name)
        self.planning_manager.update_phase_status(4, "complete", self.name)
        self.planning_manager.update_phase_status(5, "complete", self.name)

        self.planning_manager.append_progress(
            5,
            f"Execution complete. Steps: {len(state.steps)}, "
            f"Successful: {sum(1 for s in state.steps if s.status == 'complete')}, "
            f"Failed: {sum(1 for s in state.steps if s.status == 'failed')}",
            self.name,
        )

        return state

    async def _execute_step(
        self, step: ExecutionStep, context: TaskContext
    ) -> bool:
        """Execute a single step."""
        step.status = "in_progress"
        step.started_at = datetime.now()

        logger.info(
            f"WorkingAgent: Executing step {step.step_id}: "
            f"{step.agent_name} - {step.task}"
        )

        # Update planning files
        self.planning_manager.update_subagent_status(
            step.agent_name, step.task, "in_progress", step.retry_count
        )

        try:
            # Get the SubAgent and execute
            agent = self.master_agent.subagents.get(step.agent_name)

            if agent is None:
                raise ValueError(f"SubAgent {step.agent_name} not found")

            # Execute the agent
            result = await agent.execute(context)
            step.result = result

            if result.success:
                step.status = "complete"
                step.completed_at = datetime.now()

                # Log to findings
                if result.report:
                    self.planning_manager.append_findings(
                        f"{agent.name} Report", result.report[:2000]
                    )

                # Log to progress
                self.planning_manager.append_progress(
                    2,
                    f"Step {step.step_id + 1} complete: {step.agent_name}\n"
                    f"Task: {step.task}\n"
                    f"Duration: {(step.completed_at - step.started_at).total_seconds():.1f}s",
                    self.name,
                )

                # Update planning files
                self.planning_manager.update_subagent_status(
                    step.agent_name, step.task, "complete", step.retry_count
                )

                return True
            else:
                step.status = "failed"
                step.error_message = ", ".join(result.errors)

                # Log error
                self.planning_manager.log_error(
                    step.agent_name,
                    step.error_message,
                    step.retry_count + 1,
                )

                return False

        except Exception as e:
            step.status = "failed"
            step.error_message = str(e)
            step.completed_at = datetime.now()

            logger.error(f"Error executing step {step.step_id}: {e}")

            # Log error
            self.planning_manager.log_error(
                step.agent_name, str(e), step.retry_count + 1
            )

            return False

    async def _retry_step(
        self, step: ExecutionStep, context: TaskContext
    ) -> bool:
        """Retry a failed step."""
        max_retries = self.config.max_retry_count

        # Check if already exceeded max retries
        if step.retry_count >= max_retries:
            logger.error(
                f"Step {step.step_id} already exceeded max retries ({max_retries})"
            )
            return False

        while step.retry_count < max_retries:
            step.retry_count += 1
            logger.info(
                f"Retrying step {step.step_id} (attempt {step.retry_count}/{max_retries})"
            )

            # Wait a bit before retry
            await asyncio.sleep(1.0)

            # Try again
            success = await self._execute_step(step, context)

            if success:
                return True

        logger.error(
            f"Step {step.step_id} failed after {max_retries} retries"
        )
        return False

    def _synthesize_results(self, state: ExecutionState) -> str:
        """Synthesize results from all completed steps."""
        sections = []

        sections.append(f"# Execution Summary: {state.task_plan.target}")
        sections.append(f"\n**Task Type:** {state.task_plan.task_type.value}")
        sections.append(f"**Execution Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sections.append(f"**Total Steps:** {len(state.steps)}")
        sections.append(
            f"**Successful:** {sum(1 for s in state.steps if s.status == 'complete')}"
        )
        sections.append(
            f"**Failed:** {sum(1 for s in state.steps if s.status == 'failed')}\n"
        )

        sections.append("## Step Results\n")

        for step in state.steps:
            status_icon = "✓" if step.status == "complete" else "✗"
            sections.append(f"### {status_icon} Step {step.step_id + 1}: {step.agent_name}")
            sections.append(f"- **Task:** {step.task}")
            sections.append(f"- **Status:** {step.status}")
            sections.append(f"- **Retries:** {step.retry_count}")

            if step.result and step.result.success and step.result.report:
                # Add abbreviated report
                report_preview = step.result.report[:500]
                if len(step.result.report) > 500:
                    report_preview += "..."
                sections.append(f"- **Summary:** {report_preview}\n")
            elif step.error_message:
                sections.append(f"- **Error:** {step.error_message}\n")
            else:
                sections.append("")

        # Overall synthesis
        sections.append("## Combined Analysis\n")
        sections.append(
            "Based on the analysis from all agents, the following conclusions can be drawn:\n"
        )

        # Collect key findings from successful steps
        for step in state.steps:
            if step.status == "complete" and step.result and step.result.report:
                sections.append(f"- **{step.agent_name}**: Analysis completed successfully")

        sections.append("\n## Recommendation\n")
        sections.append("*[Recommendation based on combined analysis]*\n")

        sections.append("## Risk Factors\n")
        for step in state.steps:
            if step.status == "failed":
                sections.append(f"- {step.agent_name} analysis incomplete: {step.error_message}")

        return "\n".join(sections)

    async def execute_single_step(
        self, step_id: int, context: TaskContext
    ) -> ExecutionStep:
        """Execute a single step by ID (useful for retries)."""
        if self.execution_state is None:
            raise ValueError("No execution state available")

        step = next(
            (s for s in self.execution_state.steps if s.step_id == step_id),
            None,
        )

        if step is None:
            raise ValueError(f"Step {step_id} not found")

        await self._execute_step(step, context)
        return step
