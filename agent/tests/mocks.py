# tests/mocks.py
"""
PHASE 1.5: Mock implementations for dependency injection testing.

Provides mock implementations of all Protocol interfaces defined in orchestrator_context.py.
These mocks can be used to test orchestrator logic without requiring real LLM calls,
file system access, or external services.

Usage:
    >>> from tests.mocks import create_mock_context
    >>> mock_context = create_mock_context()
    >>> result = orchestrator.main(context=mock_context, cfg_override=test_config)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from orchestrator_context import OrchestratorContext


# ══════════════════════════════════════════════════════════════════════
# Mock LLM Provider
# ══════════════════════════════════════════════════════════════════════


@dataclass
class MockLLMProvider:
    """Mock LLM provider for testing."""

    responses: List[Dict[str, Any]] = field(default_factory=list)
    call_count: int = 0
    call_history: List[Dict[str, Any]] = field(default_factory=list)

    def chat_json(
        self,
        role: str,
        system_prompt: Optional[str] = None,
        user_content: str = "",
        *,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        expect_json: bool = True,
        task_type: Optional[str] = None,
        complexity: Optional[str] = None,
        interaction_index: int = 1,
        is_very_important: bool = False,
        run_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        max_cost_usd: float = 0.0,
    ) -> Dict[str, Any]:
        """Mock LLM call that returns pre-configured responses."""
        # Record the call
        self.call_history.append({
            "role": role,
            "system_prompt": system_prompt,
            "user_content": user_content,
            "model": model,
            "task_type": task_type,
            "complexity": complexity,
        })

        # Return next response or default
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            # Default response based on role
            if role == "manager" and "plan" in (task_type or ""):
                response = {
                    "plan": ["Step 1: Create HTML structure", "Step 2: Add styling"],
                    "acceptance_criteria": ["HTML is valid", "CSS is applied"],
                }
            elif role == "supervisor":
                response = {
                    "phases": [
                        {"name": "Phase 1", "categories": ["layout_structure"], "plan_steps": [0, 1]}
                    ]
                }
            elif role == "employee":
                response = {
                    "files": {
                        "index.html": "<html><body>Test</body></html>",
                    }
                }
            elif role == "manager" and "review" in (task_type or ""):
                response = {
                    "status": "approved",
                    "feedback": None,
                }
            else:
                response = {"result": "mock response"}

        self.call_count += 1
        return response


# ══════════════════════════════════════════════════════════════════════
# Mock Cost Tracker
# ══════════════════════════════════════════════════════════════════════


@dataclass
class MockCostTracker:
    """Mock cost tracker for testing."""

    total_cost: float = 0.0
    history: List[Dict[str, Any]] = field(default_factory=list)

    def reset(self) -> None:
        """Reset cost tracking state."""
        self.total_cost = 0.0
        self.history = []

    def get_total_cost_usd(self) -> float:
        """Get total cost in USD."""
        return self.total_cost

    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        return {
            "total_usd": self.total_cost,
            "total_calls": len(self.history),
            "by_role": {"manager": 0.5, "employee": 0.3},
        }

    def register_call(
        self,
        role: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Register an LLM call for cost tracking."""
        call_cost = (prompt_tokens + completion_tokens) * 0.00001  # Mock pricing
        self.total_cost += call_cost
        self.history.append({
            "role": role,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": call_cost,
        })

    def append_history(
        self,
        total_usd: float,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> None:
        """Append to cost history."""
        self.history.append({
            "total_usd": total_usd,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "model": model,
        })

    def check_cost_cap(
        self,
        max_cost_usd: float,
        estimated_tokens: int,
        model: str,
    ) -> tuple[bool, float, str]:
        """Check if cost cap would be exceeded."""
        estimated_cost = estimated_tokens * 0.00001
        would_exceed = (self.total_cost + estimated_cost) > max_cost_usd
        return (would_exceed, estimated_cost, "Cost cap check")


# ══════════════════════════════════════════════════════════════════════
# Mock Logging Provider
# ══════════════════════════════════════════════════════════════════════


@dataclass
class MockLoggingProvider:
    """Mock logging provider for testing."""

    run_id_counter: int = 0
    events: List[Dict[str, Any]] = field(default_factory=list)

    def new_run_id(self) -> str:
        """Generate a new run ID."""
        self.run_id_counter += 1
        return f"test_run_{self.run_id_counter}"

    def log_event(
        self,
        run_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        """Log an event."""
        self.events.append({
            "run_id": run_id,
            "event_type": event_type,
            "payload": payload,
        })

    def log_start(
        self,
        run_id: str,
        project_folder: str,
        task_description: str,
        config: Dict[str, Any],
    ) -> None:
        """Log run start."""
        self.events.append({
            "type": "run_start",
            "run_id": run_id,
            "project_folder": project_folder,
            "task": task_description,
        })

    def log_llm_call(
        self,
        run_id: str,
        role: str,
        model: str,
        prompt_length: int,
        phase: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Log LLM call."""
        self.events.append({
            "type": "llm_call",
            "run_id": run_id,
            "role": role,
            "model": model,
        })

    def log_cost_checkpoint(
        self,
        run_id: str,
        checkpoint: str,
        total_cost_usd: float,
        max_cost_usd: float,
        cost_summary: Dict[str, Any],
        **kwargs,
    ) -> None:
        """Log cost checkpoint."""
        self.events.append({
            "type": "cost_checkpoint",
            "run_id": run_id,
            "checkpoint": checkpoint,
            "cost": total_cost_usd,
        })

    def log_iteration_begin(
        self,
        run_id: str,
        iteration: int,
        mode: str,
        max_rounds: int,
    ) -> None:
        """Log iteration begin."""
        self.events.append({
            "type": "iteration_begin",
            "run_id": run_id,
            "iteration": iteration,
        })

    def log_iteration_end(
        self,
        run_id: str,
        iteration: int,
        status: str,
        tests_all_passed: bool,
        safety_status: Optional[str] = None,
    ) -> None:
        """Log iteration end."""
        self.events.append({
            "type": "iteration_end",
            "run_id": run_id,
            "iteration": iteration,
            "status": status,
        })

    def log_file_write(
        self,
        run_id: str,
        files: List[str],
        summary: str,
        **kwargs,
    ) -> None:
        """Log file write."""
        self.events.append({
            "type": "file_write",
            "run_id": run_id,
            "files": files,
            "summary": summary,
        })

    def log_safety_check(
        self,
        run_id: str,
        summary_status: str,
        error_count: int,
        warning_count: int,
        safety_run_id: str,
        **kwargs,
    ) -> None:
        """Log safety check."""
        self.events.append({
            "type": "safety_check",
            "run_id": run_id,
            "status": summary_status,
            "errors": error_count,
            "warnings": warning_count,
        })

    def log_final_status(
        self,
        run_id: str,
        status: str,
        reason: str,
        iterations: int,
        total_cost_usd: float,
    ) -> None:
        """Log final status."""
        self.events.append({
            "type": "final_status",
            "run_id": run_id,
            "status": status,
            "reason": reason,
        })


# ══════════════════════════════════════════════════════════════════════
# Mock Providers (Simple)
# ══════════════════════════════════════════════════════════════════════


@dataclass
class MockPromptsProvider:
    """Mock prompts provider."""

    prompts: Dict[str, str] = field(default_factory=lambda: {
        "manager_plan_sys": "You are a manager. Create a plan.",
        "manager_review_sys": "You are a manager. Review the work.",
        "employee_sys": "You are an employee. Build the project.",
    })

    def load_prompts(self, prompts_file: str) -> Dict[str, str]:
        """Load prompts from JSON file (mocked)."""
        return self.prompts


@dataclass
class MockGitUtilsProvider:
    """Mock Git utilities."""

    repo_exists: bool = True
    commit_success: bool = True

    def ensure_repo(self, root: Path) -> bool:
        """Ensure Git repository exists."""
        return self.repo_exists

    def commit_all(
        self,
        root: Path,
        message: str,
        secret_scanning_enabled: bool = True,
    ) -> bool:
        """Commit all changes."""
        return self.commit_success


@dataclass
class MockExecToolsProvider:
    """Mock execution tools."""

    def get_tool_metadata(self) -> str:
        """Get tool metadata as JSON string."""
        return '[]'


@dataclass
class MockExecSafetyProvider:
    """Mock safety checks."""

    safety_result: Dict[str, Any] = field(default_factory=lambda: {
        "summary_status": "passed",
        "static_issues": [],
        "dependency_issues": [],
        "docker_tests": {"status": "passed"},
    })

    def run_safety_checks(
        self,
        project_path: Path,
        run_id: str,
        context: str = "pre_delivery",
    ) -> Dict[str, Any]:
        """Run safety checks on generated files."""
        return self.safety_result


@dataclass
class MockSiteToolsProvider:
    """Mock site analysis tools."""

    existing_files: Dict[str, str] = field(default_factory=dict)

    def analyze_site(
        self,
        project_path: Path,
        use_visual_review: bool = False,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze generated site."""
        return {
            "dom_info": {"tag_count": 10},
            "screenshot_path": None,
        }

    def load_existing_files(
        self,
        project_path: Path,
        context: str = "orchestrator",
    ) -> Dict[str, str]:
        """Load existing files from project."""
        return self.existing_files.copy()

    def summarize_files_for_manager(
        self,
        files_dict: Dict[str, str],
    ) -> str:
        """Summarize files for manager review."""
        return f"Generated {len(files_dict)} files"

    def write_files_to_disk(
        self,
        out_dir: Path,
        files_dict: Dict[str, str],
        run_id: Optional[str] = None,
    ) -> None:
        """Write files to disk (mocked - does nothing)."""
        pass


@dataclass
class MockRunLoggerProvider:
    """Mock run logging."""

    runs: List[Dict[str, Any]] = field(default_factory=list)

    def start_run(
        self,
        cfg: Dict[str, Any],
        mode: str,
        out_dir: Path,
    ) -> Dict[str, Any]:
        """Start a new run."""
        run = {"cfg": cfg, "mode": mode, "iterations": []}
        self.runs.append(run)
        return run

    def finish_run_legacy(
        self,
        run_record: Dict[str, Any],
        final_status: str,
        final_cost_summary: Dict[str, Any],
        out_dir: Path,
    ) -> None:
        """Finish a run (legacy API)."""
        run_record["final_status"] = final_status
        run_record["final_cost_summary"] = final_cost_summary

    def log_iteration(
        self,
        run_summary: Any,
        iteration_data: Dict[str, Any] = None,
        **kwargs,
    ) -> None:
        """Log an iteration (new API)."""
        # Support both dict and kwargs style
        if iteration_data is None:
            iteration_data = kwargs
        # Store iteration data
        if hasattr(run_summary, "iterations"):
            run_summary.iterations.append(iteration_data)

    def log_iteration_legacy(
        self,
        run_record: Dict[str, Any],
        iteration_data: Dict[str, Any],
    ) -> None:
        """Log an iteration (legacy API)."""
        run_record["iterations"].append(iteration_data)


@dataclass
class MockModelRouterProvider:
    """Mock model routing."""

    def estimate_complexity(self, task: str, config: Optional[Dict] = None) -> str:
        """Estimate task complexity."""
        return "medium"

    def is_stage_important(self, stage_id: str, config: Optional[Dict] = None) -> bool:
        """Check if a stage is marked as important."""
        return False

    def choose_model(
        self,
        task_type: str,
        complexity: str,
        role: str,
        interaction_index: int = 1,
        is_very_important: bool = False,
        config: Optional[Dict] = None,
    ) -> str:
        """Choose appropriate model for task."""
        return "gpt-5-mini"


@dataclass
class MockConfigProvider:
    """Mock configuration."""

    config: Any = None

    def get_config(self) -> Any:
        """Get configuration object."""
        return self.config


@dataclass
class MockMergeManagerProvider:
    """Mock merge management."""

    def summarize_diff(
        self,
        project_path: Path,
        run_id: str,
    ) -> Dict[str, Any]:
        """Summarize diff for project."""
        return {"summary": "No changes", "risks": []}

    def summarize_diff_with_llm(
        self,
        run_id: str,
        repo_path: Path,
        context: Dict[str, Any],
        max_cost_usd: float = 0.0,
    ) -> Dict[str, Any]:
        """Summarize diff with LLM."""
        return {"summary": "No changes detected", "risks": []}

    def summarize_session(
        self,
        run_id: str,
        repo_path: Path,
        task: str,
        max_cost_usd: float = 0.0,
    ) -> Dict[str, Any]:
        """Summarize session for commit message."""
        return {"title": "Test commit", "body": "Test changes"}

    def make_commit(
        self,
        repo_path: Path,
        title: str,
        body: str,
    ) -> bool:
        """Make a commit."""
        return True


# ══════════════════════════════════════════════════════════════════════
# Context Factory
# ══════════════════════════════════════════════════════════════════════


def create_mock_context(
    llm: Optional[MockLLMProvider] = None,
    cost_tracker: Optional[MockCostTracker] = None,
    logger: Optional[MockLoggingProvider] = None,
    **overrides,
) -> OrchestratorContext:
    """
    Factory function to create a mock OrchestratorContext for testing.

    Args:
        llm: Optional custom LLM mock (default: MockLLMProvider())
        cost_tracker: Optional custom cost tracker mock
        logger: Optional custom logger mock
        **overrides: Additional provider overrides

    Returns:
        OrchestratorContext with mock implementations

    Example:
        >>> # Create context with default mocks
        >>> context = create_mock_context()
        >>>
        >>> # Create context with custom LLM responses
        >>> mock_llm = MockLLMProvider(responses=[
        ...     {"plan": ["Step 1"], "acceptance_criteria": ["AC1"]},
        ...     {"phases": [{"name": "Phase 1", "categories": [], "plan_steps": [0]}]},
        ...     {"files": {"index.html": "<html>...</html>"}},
        ...     {"status": "approved", "feedback": None},
        ... ])
        >>> context = create_mock_context(llm=mock_llm)
        >>>
        >>> # Use in orchestrator
        >>> result = orchestrator.main(context=context, cfg_override=config)
    """
    return OrchestratorContext(
        # Core services
        llm=llm or MockLLMProvider(),
        cost_tracker=cost_tracker or MockCostTracker(),
        logger=logger or MockLoggingProvider(),
        prompts=overrides.get("prompts", MockPromptsProvider()),
        site_tools=overrides.get("site_tools", MockSiteToolsProvider()),
        run_logger=overrides.get("run_logger", MockRunLoggerProvider()),
        # Git and safety
        git_utils=overrides.get("git_utils", MockGitUtilsProvider()),
        exec_safety=overrides.get("exec_safety", MockExecSafetyProvider()),
        exec_tools=overrides.get("exec_tools", MockExecToolsProvider()),
        # Model routing and config
        model_router=overrides.get("model_router", MockModelRouterProvider()),
        config=overrides.get("config", MockConfigProvider()),
        # Optional features (can remain None or provide mocks)
        domain_router=overrides.get("domain_router", None),
        project_stats=overrides.get("project_stats", None),
        specialists=overrides.get("specialists", None),
        overseer=overrides.get("overseer", None),
        workflow_manager=overrides.get("workflow_manager", None),
        memory_store=overrides.get("memory_store", None),
        inter_agent_bus=overrides.get("inter_agent_bus", None),
        merge_manager=overrides.get("merge_manager", MockMergeManagerProvider()),
        repo_router=overrides.get("repo_router", None),
    )
