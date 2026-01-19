"""State Checker Agent - Monitors execution state and handles retry logic."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .config import AgentConfig, AgentRole, TaskContext
from .planning_manager import PlanningManager

logger = logging.getLogger(__name__)


class CheckAction(Enum):
    """Actions recommended by the state checker."""

    CONTINUE = "continue"  # Proceed to next step
    RETRY = "retry"  # Retry the current step
    SKIP = "skip"  # Skip the current step
    REPLAN = "replan"  # Need to replan the entire task


@dataclass
class StateCheckResult:
    """Result from a state check."""

    is_ok: bool
    action: str  # continue, retry, skip, replan
    message: str
    retry_recommended: bool = False
    max_retries_exceeded: bool = False
    requires_replanning: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_ok": self.is_ok,
            "action": self.action,
            "message": self.message,
            "retry_recommended": self.retry_recommended,
            "max_retries_exceeded": self.max_retries_exceeded,
            "requires_replanning": self.requires_replanning,
        }


class StateCheckerAgent:
    """State Checker Agent responsible for monitoring execution state.

    The State Checker Agent:
    1. Checks each step after execution
    2. Determines if the step was successful
    3. Decides whether to retry, skip, or replan
    4. Enforces retry limits (3 retries per step)
    5. Triggers replanning if necessary
    """

    name = "StateCheckerAgent"
    role = AgentRole.STATE_CHECKER

    def __init__(self, config: AgentConfig, llm: Any = None):
        self.config = config
        self.llm = llm
        self.max_retries = config.max_retry_count
        self.planning_manager = PlanningManager(config)

        # Track global state
        self.total_failures = 0
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3

    async def check_step(
        self, step: Any, context: TaskContext
    ) -> StateCheckResult:
        """Check the state after a step execution.

        Args:
            step: The ExecutionStep that was just executed
            context: The current task context

        Returns:
            StateCheckResult with recommended action
        """
        logger.info(
            f"StateCheckerAgent: Checking step {step.step_id} ({step.agent_name})"
        )

        # Check if step completed successfully
        if step.status == "complete":
            self.consecutive_failures = 0
            return self._success_result(step)

        # Step failed - analyze the failure
        self.total_failures += 1
        self.consecutive_failures += 1

        # Check retry count
        if step.retry_count >= self.max_retries:
            return self._max_retries_exceeded(step)

        # Check for consecutive failures
        if self.consecutive_failures >= self.max_consecutive_failures:
            return self._too_many_consecutive_failures(step)

        # Analyze error type to determine action
        return self._analyze_failure(step)

    def _success_result(self, step: Any) -> StateCheckResult:
        """Create a success result."""
        logger.info(f"Step {step.step_id} completed successfully")

        # Log to progress
        self.planning_manager.append_progress(
            step.step_id + 1,
            f"State check: Step {step.step_id} ({step.agent_name}) - OK",
            self.name,
        )

        return StateCheckResult(
            is_ok=True,
            action=CheckAction.CONTINUE.value,
            message=f"Step {step.step_id} completed successfully",
        )

    def _max_retries_exceeded(self, step: Any) -> StateCheckResult:
        """Handle case when max retries exceeded."""
        logger.warning(
            f"Step {step.step_id} exceeded max retries ({self.max_retries})"
        )

        # Log to planning files
        self.planning_manager.log_error(
            step.agent_name,
            f"Max retries ({self.max_retries}) exceeded",
            step.retry_count,
            "Skipping step",
        )

        # Decide: skip or replan based on step importance
        critical_agents = ["alpha_hound", "holdings_hunter", "technical_analyst"]

        if step.agent_name in critical_agents:
            # Critical step failed - need to replan
            return StateCheckResult(
                is_ok=False,
                action=CheckAction.REPLAN.value,
                message=f"Critical step {step.agent_name} failed after {self.max_retries} retries",
                max_retries_exceeded=True,
                requires_replanning=True,
            )
        else:
            # Non-critical step - can skip
            return StateCheckResult(
                is_ok=False,
                action=CheckAction.SKIP.value,
                message=f"Step {step.agent_name} skipped after {self.max_retries} retries",
                max_retries_exceeded=True,
            )

    def _too_many_consecutive_failures(self, step: Any) -> StateCheckResult:
        """Handle too many consecutive failures."""
        logger.error(
            f"Too many consecutive failures ({self.consecutive_failures})"
        )

        self.planning_manager.log_error(
            step.agent_name,
            f"{self.consecutive_failures} consecutive failures",
            step.retry_count,
            "Triggering replan",
        )

        return StateCheckResult(
            is_ok=False,
            action=CheckAction.REPLAN.value,
            message=f"Too many consecutive failures ({self.consecutive_failures})",
            requires_replanning=True,
        )

    def _analyze_failure(self, step: Any) -> StateCheckResult:
        """Analyze the failure and recommend action."""
        error_msg = step.error_message.lower() if step.error_message else ""

        # Transient errors - retry
        transient_keywords = [
            "timeout",
            "connection",
            "rate limit",
            "temporary",
            "503",
            "429",
            "network",
        ]

        if any(kw in error_msg for kw in transient_keywords):
            logger.info(f"Transient error detected, recommending retry")
            return StateCheckResult(
                is_ok=False,
                action=CheckAction.RETRY.value,
                message=f"Transient error detected: {step.error_message}",
                retry_recommended=True,
            )

        # Data not available - skip
        data_keywords = ["no data", "not found", "empty", "unavailable"]

        if any(kw in error_msg for kw in data_keywords):
            logger.info(f"Data unavailable, recommending skip")
            return StateCheckResult(
                is_ok=False,
                action=CheckAction.SKIP.value,
                message=f"Data unavailable: {step.error_message}",
            )

        # API key issues - cannot continue
        auth_keywords = ["api key", "unauthorized", "forbidden", "401", "403"]

        if any(kw in error_msg for kw in auth_keywords):
            logger.error(f"Authentication error, recommending replan")
            return StateCheckResult(
                is_ok=False,
                action=CheckAction.REPLAN.value,
                message=f"Authentication error: {step.error_message}",
                requires_replanning=True,
            )

        # Default: retry
        return StateCheckResult(
            is_ok=False,
            action=CheckAction.RETRY.value,
            message=f"Unknown error, attempting retry: {step.error_message}",
            retry_recommended=True,
        )

    async def validate_final_state(
        self, execution_state: Any
    ) -> StateCheckResult:
        """Validate the final state after all steps complete."""
        successful_steps = sum(
            1 for s in execution_state.steps if s.status == "complete"
        )
        total_steps = len(execution_state.steps)
        success_rate = successful_steps / total_steps if total_steps > 0 else 0

        logger.info(
            f"Final state validation: {successful_steps}/{total_steps} steps "
            f"successful ({success_rate:.1%})"
        )

        # Log summary to progress
        self.planning_manager.append_progress(
            5,
            f"Final state validation:\n"
            f"- Total steps: {total_steps}\n"
            f"- Successful: {successful_steps}\n"
            f"- Success rate: {success_rate:.1%}",
            self.name,
        )

        if success_rate >= 0.5:
            # At least 50% success - acceptable
            return StateCheckResult(
                is_ok=True,
                action=CheckAction.CONTINUE.value,
                message=f"Execution complete with {success_rate:.1%} success rate",
            )
        else:
            # Less than 50% success - problematic
            return StateCheckResult(
                is_ok=False,
                action=CheckAction.REPLAN.value,
                message=f"Low success rate ({success_rate:.1%}), replanning recommended",
                requires_replanning=True,
            )

    def reset_counters(self) -> None:
        """Reset failure counters for a new execution."""
        self.total_failures = 0
        self.consecutive_failures = 0

    def get_health_status(self) -> dict[str, Any]:
        """Get the current health status of the execution."""
        return {
            "total_failures": self.total_failures,
            "consecutive_failures": self.consecutive_failures,
            "max_retries": self.max_retries,
            "max_consecutive_failures": self.max_consecutive_failures,
            "is_healthy": self.consecutive_failures < self.max_consecutive_failures,
        }
