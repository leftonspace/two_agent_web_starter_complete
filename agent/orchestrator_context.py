# orchestrator_context.py
"""
PHASE 1.5: Dependency Injection for Orchestrator

Defines protocols (interfaces) and context container for orchestrator dependencies.
Enables loose coupling, easier testing, and independent module evolution.

Addresses vulnerability A1: Tight coupling to 12+ modules.

Usage:
    >>> from orchestrator_context import OrchestratorContext
    >>> context = OrchestratorContext.create_default(config)
    >>> result = orchestrator.run(task, config, context=context)

For testing:
    >>> from tests.mocks import create_mock_context, MockLLM
    >>> mock_llm = MockLLM(responses=[...])
    >>> context = create_mock_context(llm=mock_llm)
    >>> result = orchestrator.run(task, config, context=context)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


# ══════════════════════════════════════════════════════════════════════
# Protocol Definitions (Interfaces)
# ══════════════════════════════════════════════════════════════════════


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM service (chat completions)."""

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
        """Call LLM with chat completion and return parsed JSON."""
        ...


@runtime_checkable
class CostTrackerProvider(Protocol):
    """Protocol for cost tracking service."""

    def reset(self) -> None:
        """Reset cost tracking state."""
        ...

    def get_total_cost_usd(self) -> float:
        """Get total cost in USD."""
        ...

    def get_summary(self) -> Dict[str, Any]:
        """Get cost summary."""
        ...

    def register_call(
        self,
        role: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Register an LLM call for cost tracking."""
        ...

    def append_history(
        self,
        total_usd: float,
        prompt_tokens: int,
        completion_tokens: int,
        model: str,
    ) -> None:
        """Append to cost history."""
        ...

    def check_cost_cap(
        self,
        max_cost_usd: float,
        estimated_tokens: int,
        model: str,
    ) -> tuple[bool, float, str]:
        """Check if cost cap would be exceeded."""
        ...


@runtime_checkable
class LoggingProvider(Protocol):
    """Protocol for logging service."""

    def new_run_id(self) -> str:
        """Generate a new run ID."""
        ...

    def log_event(
        self,
        run_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        """Log an event."""
        ...

    def log_start(
        self,
        run_id: str,
        project_folder: str,
        task_description: str,
        config: Dict[str, Any],
    ) -> None:
        """Log run start."""
        ...

    def log_llm_call(
        self,
        run_id: str,
        role: str,
        model: str,
        prompt_length: int,
        phase: str,
    ) -> None:
        """Log LLM call."""
        ...

    def log_cost_checkpoint(
        self,
        run_id: str,
        checkpoint: str,
        total_cost_usd: float,
        max_cost_usd: float,
        cost_summary: Dict[str, Any],
    ) -> None:
        """Log cost checkpoint."""
        ...


@runtime_checkable
class ModelRouterProvider(Protocol):
    """Protocol for model routing service."""

    def estimate_complexity(self, task: str, config: Optional[Dict] = None) -> str:
        """Estimate task complexity (low/medium/high)."""
        ...

    def is_stage_important(self, stage_id: str, config: Optional[Dict] = None) -> bool:
        """Check if a stage is marked as important."""
        ...

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
        ...


@runtime_checkable
class PromptsProvider(Protocol):
    """Protocol for prompt loading service."""

    def load_prompts(self, prompts_file: str) -> Dict[str, str]:
        """Load prompts from JSON file."""
        ...


@runtime_checkable
class GitUtilsProvider(Protocol):
    """Protocol for Git utilities."""

    def ensure_repo(self, root: Path) -> bool:
        """Ensure Git repository exists."""
        ...

    def commit_all(
        self,
        root: Path,
        message: str,
        secret_scanning_enabled: bool = True,
    ) -> bool:
        """Commit all changes."""
        ...


@runtime_checkable
class ExecToolsProvider(Protocol):
    """Protocol for execution tools."""

    def get_tool_metadata(self) -> str:
        """Get tool metadata as JSON string."""
        ...


@runtime_checkable
class ExecSafetyProvider(Protocol):
    """Protocol for safety checks."""

    def run_safety_checks(
        self,
        project_path: Path,
        run_id: str,
        context: str = "pre_delivery",
    ) -> Dict[str, Any]:
        """Run safety checks on generated files."""
        ...


@runtime_checkable
class SiteToolsProvider(Protocol):
    """Protocol for site analysis tools."""

    def analyze_site(
        self,
        project_path: Path,
        use_visual_review: bool = False,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze generated site."""
        ...

    def load_existing_files(
        self,
        project_path: Path,
        context: str = "orchestrator",
    ) -> Dict[str, str]:
        """Load existing files from project."""
        ...

    def summarize_files_for_manager(
        self,
        files_dict: Dict[str, str],
    ) -> str:
        """Summarize files for manager review."""
        ...

    def write_files_to_disk(
        self,
        out_dir: Path,
        files_dict: Dict[str, str],
        run_id: Optional[str] = None,
    ) -> None:
        """Write files to disk."""
        ...


@runtime_checkable
class RunLoggerProvider(Protocol):
    """Protocol for run logging."""

    def start_run(
        self,
        cfg: Dict[str, Any],
        mode: str,
        out_dir: Path,
    ) -> Dict[str, Any]:
        """Start a new run."""
        ...

    def finish_run_legacy(
        self,
        run_record: Dict[str, Any],
        final_status: str,
        final_cost_summary: Dict[str, Any],
        out_dir: Path,
    ) -> None:
        """Finish a run (legacy API)."""
        ...

    def log_iteration(
        self,
        run_summary: Any,  # RunSummary type
        iteration_data: Dict[str, Any],
    ) -> None:
        """Log an iteration."""
        ...


@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for configuration service."""

    def get_config(self) -> Any:
        """Get configuration object."""
        ...


@runtime_checkable
class DomainRouterProvider(Protocol):
    """Protocol for domain routing."""

    def classify_domain(self, task: str) -> Any:
        """Classify task domain."""
        ...

    def get_domain_prompts(self, domain: Any) -> Dict[str, str]:
        """Get domain-specific prompts."""
        ...

    def get_domain_tools(self, domain: Any) -> List[str]:
        """Get domain-specific tools."""
        ...


@runtime_checkable
class ProjectStatsProvider(Protocol):
    """Protocol for project statistics."""

    def get_risky_files(
        self,
        project_path: Path,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get risky files."""
        ...

    def format_risk_summary(
        self,
        risky_files: List[Dict[str, Any]],
    ) -> str:
        """Format risk summary."""
        ...


@runtime_checkable
class SpecialistsProvider(Protocol):
    """Protocol for specialist agents."""

    def recommend_specialist(
        self,
        task: str,
        domain: Optional[str] = None,
        budget: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Recommend a specialist for task."""
        ...

    def get_specialist(self, specialist_type: str) -> Any:
        """Get specialist by type."""
        ...


@runtime_checkable
class OverseerProvider(Protocol):
    """Protocol for overseer (meta-orchestration)."""

    def analyze_plan_quality(
        self,
        plan: List[str],
        task: str,
        run_id: str,
    ) -> Dict[str, Any]:
        """Analyze plan quality."""
        ...

    def suggest_plan_improvements(
        self,
        plan: List[str],
        analysis: Dict[str, Any],
    ) -> List[str]:
        """Suggest plan improvements."""
        ...


@runtime_checkable
class WorkflowManagerProvider(Protocol):
    """Protocol for workflow management."""

    def create_workflow(
        self,
        task: str,
        config: Dict[str, Any],
    ) -> Any:
        """Create workflow for task."""
        ...

    def execute_workflow(
        self,
        workflow: Any,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute workflow."""
        ...


@runtime_checkable
class MemoryStoreProvider(Protocol):
    """Protocol for memory storage."""

    def store_memory(
        self,
        run_id: str,
        memory_type: str,
        content: Any,
    ) -> None:
        """Store memory."""
        ...

    def retrieve_memories(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant memories."""
        ...


@runtime_checkable
class InterAgentBusProvider(Protocol):
    """Protocol for inter-agent messaging."""

    def publish(
        self,
        topic: str,
        message: Dict[str, Any],
    ) -> None:
        """Publish message to topic."""
        ...

    def subscribe(
        self,
        topic: str,
        callback: Any,
    ) -> None:
        """Subscribe to topic."""
        ...


@runtime_checkable
class MergeManagerProvider(Protocol):
    """Protocol for merge management."""

    def summarize_diff(
        self,
        project_path: Path,
        run_id: str,
    ) -> Dict[str, Any]:
        """Summarize diff for project."""
        ...


@runtime_checkable
class RepoRouterProvider(Protocol):
    """Protocol for repository routing."""

    def resolve_repo_path(
        self,
        project_subdir: str,
        config: Optional[Dict] = None,
    ) -> Path:
        """Resolve repository path."""
        ...

    def get_all_repo_paths(self) -> List[Path]:
        """Get all repository paths."""
        ...


# ══════════════════════════════════════════════════════════════════════
# Orchestrator Context
# ══════════════════════════════════════════════════════════════════════


@dataclass
class OrchestratorContext:
    """
    Dependency injection container for orchestrator.

    Contains all external dependencies as protocol-typed fields,
    enabling easy mocking and testing.

    Usage:
        # Production (real implementations)
        context = OrchestratorContext.create_default(config)

        # Testing (mock implementations)
        context = OrchestratorContext(
            llm=MockLLM(),
            cost_tracker=MockCostTracker(),
            ...
        )
    """

    # Core services (always required)
    llm: LLMProvider
    cost_tracker: CostTrackerProvider
    logger: LoggingProvider
    prompts: PromptsProvider
    site_tools: SiteToolsProvider
    run_logger: RunLoggerProvider

    # Git and safety
    git_utils: GitUtilsProvider
    exec_safety: ExecSafetyProvider
    exec_tools: ExecToolsProvider

    # Model routing and config
    model_router: ModelRouterProvider
    config: ConfigProvider

    # Optional advanced features (may not be available)
    domain_router: Optional[DomainRouterProvider] = None
    project_stats: Optional[ProjectStatsProvider] = None
    specialists: Optional[SpecialistsProvider] = None
    overseer: Optional[OverseerProvider] = None
    workflow_manager: Optional[WorkflowManagerProvider] = None
    memory_store: Optional[MemoryStoreProvider] = None
    inter_agent_bus: Optional[InterAgentBusProvider] = None
    merge_manager: Optional[MergeManagerProvider] = None
    repo_router: Optional[RepoRouterProvider] = None

    @classmethod
    def create_default(cls, config_dict: Optional[Dict[str, Any]] = None) -> OrchestratorContext:
        """
        Factory method that creates context with real implementations.

        This is the production entry point - imports real modules
        and creates actual service instances.

        Args:
            config_dict: Optional configuration dictionary

        Returns:
            OrchestratorContext with real implementations

        Example:
            >>> context = OrchestratorContext.create_default({"task": "..."})
            >>> result = orchestrator.run(task, config, context=context)
        """
        # Import real implementations here (lazy loading)
        import llm as llm_module
        import cost_tracker as cost_tracker_module
        import core_logging as core_logging_module
        import model_router as model_router_module
        import prompts as prompts_module
        import git_utils as git_utils_module
        import exec_safety as exec_safety_module
        import exec_tools as exec_tools_module
        import site_tools as site_tools_module
        import run_logger as run_logger_module
        import merge_manager as merge_manager_module

        # Try to import optional modules
        try:
            import config as config_module
            config_provider = config_module
        except ImportError:
            config_provider = None  # type: ignore

        try:
            import domain_router as domain_router_module
            domain_router = domain_router_module
        except ImportError:
            domain_router = None

        try:
            import project_stats as project_stats_module
            project_stats = project_stats_module
        except ImportError:
            project_stats = None

        try:
            import specialist_market as specialist_market_module
            specialists = specialist_market_module
        except ImportError:
            specialists = None

        try:
            import overseer as overseer_module
            overseer = overseer_module
        except ImportError:
            overseer = None

        try:
            import workflow_manager as workflow_manager_module
            workflow_manager_provider = workflow_manager_module
        except ImportError:
            workflow_manager_provider = None

        try:
            import memory_store as memory_store_module
            memory_store_provider = memory_store_module
        except ImportError:
            memory_store_provider = None

        try:
            import inter_agent_bus as inter_agent_bus_module
            inter_agent_bus_provider = inter_agent_bus_module
        except ImportError:
            inter_agent_bus_provider = None

        try:
            import repo_router as repo_router_module
            repo_router_provider = repo_router_module
        except ImportError:
            repo_router_provider = None

        # Create context with real implementations
        return cls(
            # Core services
            llm=llm_module,  # type: ignore
            cost_tracker=cost_tracker_module,  # type: ignore
            logger=core_logging_module,  # type: ignore
            prompts=prompts_module,  # type: ignore
            site_tools=site_tools_module,  # type: ignore
            run_logger=run_logger_module,  # type: ignore
            # Git and safety
            git_utils=git_utils_module,  # type: ignore
            exec_safety=exec_safety_module,  # type: ignore
            exec_tools=exec_tools_module,  # type: ignore
            # Model routing and config
            model_router=model_router_module,  # type: ignore
            config=config_provider,  # type: ignore
            # Optional features
            domain_router=domain_router,  # type: ignore
            project_stats=project_stats,  # type: ignore
            specialists=specialists,  # type: ignore
            overseer=overseer,  # type: ignore
            workflow_manager=workflow_manager_provider,  # type: ignore
            memory_store=memory_store_provider,  # type: ignore
            inter_agent_bus=inter_agent_bus_provider,  # type: ignore
            merge_manager=merge_manager_module,  # type: ignore
            repo_router=repo_router_provider,  # type: ignore
        )

    def is_feature_available(self, feature_name: str) -> bool:
        """
        Check if an optional feature is available.

        Args:
            feature_name: Name of the feature (e.g., "domain_router", "specialists")

        Returns:
            True if feature is available, False otherwise

        Example:
            >>> if context.is_feature_available("specialists"):
            ...     specialist = context.specialists.recommend_specialist(task)
        """
        return getattr(self, feature_name, None) is not None


# ══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ══════════════════════════════════════════════════════════════════════


def create_production_context(config_dict: Optional[Dict[str, Any]] = None) -> OrchestratorContext:
    """
    Convenience function to create production context.

    Alias for OrchestratorContext.create_default().

    Args:
        config_dict: Optional configuration dictionary

    Returns:
        OrchestratorContext with real implementations
    """
    return OrchestratorContext.create_default(config_dict)
