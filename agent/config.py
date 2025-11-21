"""
PHASE 0.1: Centralized Configuration Module

This module provides centralized configuration for the multi-agent orchestrator system.
All configuration parameters, defaults, and validation logic are consolidated here.

Configuration Sources (in priority order):
1. Environment variables (highest priority)
2. Local config overrides (config_local.py, if exists)
3. Project config file (project_config.json)
4. Built-in defaults (lowest priority)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ══════════════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════════════


class ExecutionMode(str, Enum):
    """Orchestrator execution modes."""

    TWO_LOOP = "2loop"  # Manager ↔ Employee
    THREE_LOOP = "3loop"  # Manager ↔ Supervisor ↔ Employee
    AUTO_PILOT = "autopilot"  # Self-evaluating loop


class SimulationMode(str, Enum):
    """Simulation modes for zero-cost testing."""

    OFF = "off"  # Normal execution
    PLAN_ONLY = "plan"  # Simulate planning only
    ALL = "all"  # Simulate all LLM calls


class InteractiveCostMode(str, Enum):
    """Interactive cost confirmation modes."""

    OFF = "off"  # No prompts
    ONCE = "once"  # Prompt once at start
    ALWAYS = "always"  # Prompt before each expensive operation


# ══════════════════════════════════════════════════════════════════════
# Configuration Dataclasses
# ══════════════════════════════════════════════════════════════════════


@dataclass
class ModelDefaults:
    """
    Default LLM models for each role.

    ⚠️  DEPRECATED (Phase 1.7): This class is deprecated in favor of ModelRegistry.
    Models are now configured in agent/models.json and resolved via model_registry.py.

    For backward compatibility, these defaults are still used if model_registry is
    unavailable, but they should not be relied upon for new code.

    Migration: Use model_router.choose_model() which automatically uses the registry.
    """

    manager: str = "gpt-5-mini-2025-08-07"
    supervisor: str = "gpt-5-nano"
    employee: str = "gpt-5-2025-08-07"
    merge_manager: str = "gpt-5-mini"
    qa_reviewer: str = "gpt-5-mini"

    @classmethod
    def from_env(cls) -> ModelDefaults:
        """
        Load model defaults from environment variables.

        ⚠️  DEPRECATED: Use ModelRegistry instead (agent/models.json).
        """
        return cls(
            manager=os.getenv("DEFAULT_MANAGER_MODEL", cls.manager),
            supervisor=os.getenv("DEFAULT_SUPERVISOR_MODEL", cls.supervisor),
            employee=os.getenv("DEFAULT_EMPLOYEE_MODEL", cls.employee),
            merge_manager=os.getenv("DEFAULT_MERGE_MANAGER_MODEL", cls.merge_manager),
            qa_reviewer=os.getenv("DEFAULT_QA_REVIEWER_MODEL", cls.qa_reviewer),
        )


@dataclass
class CostLimits:
    """Cost control configuration."""

    max_cost_usd: float = 0.0  # 0 = no cap
    warning_threshold_usd: float = 0.0  # 0 = no warning
    interactive_mode: InteractiveCostMode = InteractiveCostMode.OFF

    def validate(self) -> None:
        """Validate cost limits configuration."""
        if self.max_cost_usd < 0:
            raise ValueError("max_cost_usd must be >= 0")
        if self.warning_threshold_usd < 0:
            raise ValueError("warning_threshold_usd must be >= 0")
        if self.max_cost_usd > 0 and self.warning_threshold_usd > self.max_cost_usd:
            print(
                f"[Config Warning] warning_threshold_usd ({self.warning_threshold_usd}) > "
                f"max_cost_usd ({self.max_cost_usd})"
            )


@dataclass
class SafetyConfig:
    """Safety check configuration."""

    run_before_final: bool = True
    allow_extra_iteration_on_failure: bool = True
    max_static_errors: int = 0  # 0 = fail on any error
    max_dependency_warnings: int = 5


@dataclass
class GitConfig:
    """Git integration configuration."""

    enabled: bool = False
    auto_commit: bool = False
    commit_mode: str = "semantic"  # "semantic" | "simple"
    auto_commit_repos: List[str] = field(default_factory=lambda: ["default"])


@dataclass
class QAConfig:
    """Quality assurance configuration."""

    enabled: bool = True
    require_title: bool = True
    require_meta_description: bool = True
    require_lang_attribute: bool = True
    require_h1: bool = True
    max_empty_links: int = 10
    max_images_missing_alt: int = 0
    max_duplicate_ids: int = 0
    max_console_logs: int = 5
    allow_large_files: bool = True
    max_large_files: int = 5
    large_file_threshold: int = 5000


@dataclass
class RuntimeConfig:
    """Runtime behavior configuration."""

    max_rounds: int = 3
    use_visual_review: bool = False
    use_snapshots: bool = True
    timeout_seconds: int = 180
    max_retries: int = 3


@dataclass
class SandboxConfig:
    """PHASE 3.2: Sandbox execution configuration."""

    enabled: bool = False  # Enable sandboxed execution
    timeout_seconds: int = 120  # Default timeout for sandbox execution
    memory_limit_mb: Optional[int] = None  # Memory limit (None = no limit)
    network_isolation: bool = False  # Enable network isolation (Linux only)
    use_docker: bool = False  # Use Docker for maximum isolation
    docker_image: str = "python:3.11-slim"  # Docker image to use


@dataclass
class AuthConfig:
    """
    PHASE 1.1: Authentication and authorization configuration.

    Controls web dashboard authentication for both API keys and sessions.
    """

    enabled: bool = True  # Enable authentication (set False for development)
    session_ttl_hours: int = 24  # Session expiration time
    api_key_ttl_days: int = 90  # Default API key expiration (0 = no expiration)
    require_https: bool = True  # Enforce HTTPS in production
    allow_registration: bool = False  # Allow self-registration (disabled by default)

    # Security settings
    bcrypt_rounds: int = 12  # Bcrypt work factor for password hashing
    session_cookie_name: str = "session_id"
    session_cookie_secure: bool = True  # Require HTTPS for cookies
    session_cookie_httponly: bool = True  # Prevent JavaScript access
    session_cookie_samesite: str = "lax"  # CSRF protection

    # Admin key generation on first run
    create_default_admin_key: bool = True


@dataclass
class ToolConfig:
    """
    PHASE 2.1: Tool plugin system configuration.
    PHASE 2.2: Enhanced with role-based permissions and audit logging.

    Controls tool plugin discovery, loading, execution, and access control.
    """

    # Plugin discovery
    plugin_dirs: List[str] = field(default_factory=list)  # Additional plugin directories
    disabled_tools: List[str] = field(default_factory=list)  # Blacklist specific tools by name
    enable_custom_plugins: bool = True  # Allow loading custom plugins from agent/tools/custom/

    # Execution controls
    tool_execution_timeout: int = 300  # Global maximum timeout for all tools (seconds)
    log_tool_usage: bool = True  # Log all tool executions for audit trail
    enforce_permissions: bool = True  # Enforce permission checking (False for development only)

    # Resource limits
    max_concurrent_tools: int = 5  # Maximum number of tools executing simultaneously
    enable_cost_tracking: bool = True  # Track tool execution costs

    # Feature flags
    auto_reload_plugins: bool = False  # Automatically reload plugins when files change (dev mode)

    # PHASE 2.2: Role-based permissions
    permissions_matrix_path: Optional[str] = None  # Path to permissions_matrix.json (None = default)
    enable_rbac: bool = True  # Enable role-based access control
    require_role_id: bool = False  # Require role_id in execution context (strict mode)

    # PHASE 2.2: Audit logging
    enable_audit_logging: bool = True  # Enable comprehensive audit logging
    audit_log_path: Optional[str] = None  # Path to audit log (None = default: data/tool_access_log.jsonl)
    audit_log_retention_days: int = 90  # Delete audit logs older than N days (0 = keep forever)
    audit_log_denied_only: bool = False  # Log only denied access attempts (saves space)


@dataclass
class HRConfig:
    """
    PHASE 2.3: HR tools configuration.

    Configuration for HR department tools: email, calendar, HRIS.
    """

    # SMTP Email Configuration
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_address: Optional[str] = None
    smtp_use_tls: bool = True

    # Google Calendar Configuration
    google_calendar_credentials_path: Optional[str] = None  # Path to OAuth2 credentials JSON
    google_calendar_calendar_id: str = "primary"

    # HRIS Configuration
    hris_system: str = "bamboohr"  # "bamboohr" | "workday" | "generic"

    # BambooHR
    hris_bamboohr_api_key: Optional[str] = None
    hris_bamboohr_subdomain: Optional[str] = None

    # Workday
    hris_workday_api_key: Optional[str] = None
    hris_workday_tenant: Optional[str] = None

    # Generic HRIS
    hris_generic_base_url: Optional[str] = None
    hris_generic_api_key: Optional[str] = None
    hris_generic_auth_header: str = "Authorization"
    hris_generic_endpoint: str = "/api/employees"


@dataclass
class ConversationalConfig:
    """
    PHASE 7.1: Conversational agent configuration.

    Configuration for natural language chat interface.
    """

    # Agent settings
    enabled: bool = True  # Enable conversational agent
    default_model: str = "gpt-4o"  # Default LLM for intent parsing and chat
    intent_model: str = "gpt-4o"  # Model for intent classification
    planning_model: str = "gpt-4o"  # Model for task planning

    # Conversation settings
    max_history_messages: int = 50  # Maximum messages to keep in history
    context_window_messages: int = 10  # Messages to include in prompts
    temperature: float = 0.7  # Default temperature for conversational responses

    # Task execution settings
    max_concurrent_tasks: int = 3  # Maximum tasks executing simultaneously
    task_timeout_seconds: int = 3600  # Default task timeout (1 hour)
    enable_background_execution: bool = True  # Allow async task execution

    # Security settings
    require_approval_for_destructive: bool = True  # Require approval for destructive operations
    allowed_tools: Optional[List[str]] = None  # Whitelist of allowed tools (None = all)
    denied_tools: List[str] = field(default_factory=list)  # Blacklist of denied tools

    # UI settings
    enable_web_chat: bool = True  # Enable web chat interface at /chat
    enable_cli_chat: bool = True  # Enable CLI chat interface


@dataclass
class WorkflowConfig:
    """
    PHASE 7.2: Workflow enforcement configuration.

    Controls quality gates and approval requirements for agent execution.
    Prevents agents from proceeding with subpar work.
    """

    # Enforcement mode
    enforcement_mode: str = "strict"  # "strict", "warn", "disabled"

    # Blocking behavior
    block_on_failure: bool = True  # Block file writes if validation fails
    rollback_on_failure: bool = True  # Rollback changes on validation failure

    # Approval requirements
    require_supervisor_approval: bool = True  # Require supervisor sign-off
    require_user_approval_for_destructive: bool = True  # User approval for destructive ops
    require_user_approval_for_external: bool = True  # User approval for external API calls

    # Retry controls (R1 reliability fix)
    max_retries: int = 3  # Maximum retry attempts
    detect_infinite_loops: bool = True  # Enable infinite loop detection
    max_consecutive_identical_feedback: int = 2  # Threshold for loop detection

    # Quality gates
    require_tests_pass: bool = False  # Require tests to pass before proceeding
    require_linting_pass: bool = False  # Require linting to pass
    min_qa_score: float = 0.0  # Minimum QA score (0-100, 0 = no requirement)


@dataclass
class MemoryConfig:
    """
    PHASE 7.3: Business memory configuration.

    Configuration for persistent business knowledge learned from conversations.
    """

    # Core settings
    enabled: bool = True  # Enable business memory system
    memory_db_path: str = "data/business_memory.db"  # Path to SQLite database
    auto_learn: bool = True  # Automatically learn facts from conversations

    # Learning settings
    extraction_model: str = "gpt-4o-mini"  # LLM for fact extraction (cheaper/faster)
    min_confidence: float = 0.6  # Minimum confidence to store a fact (0.0-1.0)
    context_messages: int = 5  # Number of recent messages to use for extraction context

    # Privacy and GDPR
    strict_privacy_mode: bool = True  # Enable strict privacy filtering
    enable_data_export: bool = True  # Allow data export for GDPR compliance
    enable_data_deletion: bool = True  # Allow data deletion (right to be forgotten)

    # Data retention (days)
    retention_company: int = 365  # Company info retention (1 year)
    retention_team: int = 180  # Team member info retention (6 months)
    retention_preferences: int = 365  # Preference retention (1 year)
    retention_projects: int = 90  # Project info retention (3 months)
    retention_general: int = 90  # General facts retention (3 months)

    # Feature flags
    enable_conflict_detection: bool = True  # Detect conflicts between facts
    enable_context_injection: bool = True  # Inject memory context into queries
    enable_manual_memory: bool = True  # Allow manual fact storage ("remember that...")


@dataclass
class ActionToolsConfig:
    """
    PHASE 7.4: Action execution tools configuration.

    Configuration for tools that interact with external services to perform
    real-world actions (domain purchases, deployments, payments, SMS).
    """

    # Approval settings
    require_approval_for_paid_actions: bool = True  # Require approval for any action with cost > $0
    require_2fa_above_usd: float = 100.0  # Require 2FA for actions costing more than this
    approval_timeout_seconds: int = 300  # Maximum time to wait for approval (5 minutes)

    # Cost limits
    daily_spending_limit_usd: float = 500.0  # Maximum spending per day (0 = no limit)
    per_action_limit_usd: float = 200.0  # Maximum cost per action (0 = no limit)

    # Rollback settings
    auto_rollback_on_failure: bool = True  # Automatically attempt rollback if action fails
    rollback_timeout_seconds: int = 60  # Maximum time for rollback attempt

    # API credentials (from environment)
    # These should be set as environment variables for security
    namecheap_api_key: str = field(default_factory=lambda: os.getenv("NAMECHEAP_API_KEY", ""))
    namecheap_api_user: str = field(default_factory=lambda: os.getenv("NAMECHEAP_API_USER", ""))
    vercel_token: str = field(default_factory=lambda: os.getenv("VERCEL_TOKEN", ""))
    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    twilio_account_sid: str = field(default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID", ""))
    twilio_auth_token: str = field(default_factory=lambda: os.getenv("TWILIO_AUTH_TOKEN", ""))
    twilio_phone_number: str = field(default_factory=lambda: os.getenv("TWILIO_PHONE_NUMBER", ""))
    stripe_api_key: str = field(default_factory=lambda: os.getenv("STRIPE_API_KEY", ""))

    # Sandbox/testing mode
    use_sandbox_apis: bool = False  # Use sandbox/test APIs when available

    # Audit logging
    log_all_action_attempts: bool = True  # Log all action attempts (approved and declined)
    log_approval_decisions: bool = True  # Log user approval decisions


@dataclass
class MeetingConfig:
    """
    PHASE 7A.1: Meeting platform integration configuration.

    Configuration for meeting bots that join Zoom, Teams, and other platforms
    to capture audio and participate in real-time conversations.
    """

    # Core settings
    enabled: bool = True  # Enable meeting bot integration
    auto_join_scheduled: bool = False  # Automatically join scheduled meetings from calendar
    send_join_notification: bool = True  # Send chat message when joining meeting

    # Platform credentials (from environment)
    # Zoom
    zoom_api_key: str = field(default_factory=lambda: os.getenv("ZOOM_API_KEY", ""))
    zoom_api_secret: str = field(default_factory=lambda: os.getenv("ZOOM_API_SECRET", ""))
    zoom_sdk_key: str = field(default_factory=lambda: os.getenv("ZOOM_SDK_KEY", ""))
    zoom_sdk_secret: str = field(default_factory=lambda: os.getenv("ZOOM_SDK_SECRET", ""))

    # Microsoft Teams
    azure_tenant_id: str = field(default_factory=lambda: os.getenv("AZURE_TENANT_ID", ""))
    azure_client_id: str = field(default_factory=lambda: os.getenv("AZURE_CLIENT_ID", ""))
    azure_client_secret: str = field(default_factory=lambda: os.getenv("AZURE_CLIENT_SECRET", ""))

    # Audio settings
    audio_sample_rate: int = 16000  # Audio sample rate (Hz)
    audio_channels: int = 1  # Mono audio
    audio_chunk_duration_ms: int = 1000  # Chunk size in milliseconds

    # Behavior settings
    leave_after_minutes: int = 0  # Auto-leave after N minutes (0 = stay until meeting ends)
    max_meeting_duration_hours: int = 4  # Maximum meeting duration to handle
    record_audio: bool = True  # Capture audio stream for transcription

    # Privacy settings
    announce_recording: bool = True  # Announce that meeting is being recorded
    obfuscate_participant_info: bool = False  # Hide participant email/details in logs


@dataclass
class Config:
    """
    Main configuration container.

    This class aggregates all configuration subsystems and provides
    validation and environment integration.
    """

    # Execution settings
    mode: ExecutionMode = ExecutionMode.THREE_LOOP
    simulation: SimulationMode = SimulationMode.OFF

    # LLM settings
    models: ModelDefaults = field(default_factory=ModelDefaults)  # DEPRECATED: Use model_registry_path
    model_registry_path: Optional[str] = None  # PHASE 1.7: Path to models.json (None = default location)
    very_important_stages: List[str] = field(default_factory=list)

    # Cost controls
    costs: CostLimits = field(default_factory=CostLimits)

    # Safety
    safety: SafetyConfig = field(default_factory=SafetyConfig)

    # Git
    git: GitConfig = field(default_factory=GitConfig)

    # QA
    qa: QAConfig = field(default_factory=QAConfig)

    # Runtime
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    # PHASE 3.2: Sandbox execution
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)

    # PHASE 1.1: Authentication
    auth: AuthConfig = field(default_factory=AuthConfig)

    # PHASE 2.1: Tool plugins
    tools: ToolConfig = field(default_factory=ToolConfig)

    # PHASE 2.3: HR tools
    hr: HRConfig = field(default_factory=HRConfig)

    # PHASE 7.1: Conversational agent
    conversational: ConversationalConfig = field(default_factory=ConversationalConfig)

    # PHASE 7.2: Workflow enforcement
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)

    # PHASE 7.3: Business memory
    memory: MemoryConfig = field(default_factory=MemoryConfig)

    # PHASE 7.4: Action execution tools
    action_tools: ActionToolsConfig = field(default_factory=ActionToolsConfig)

    # PHASE 7A.1: Meeting platform integration
    meetings: MeetingConfig = field(default_factory=MeetingConfig)

    # Project-specific
    project_name: str = "Unknown Project"
    project_subdir: str = "output"
    task: str = ""
    prompts_file: str = "prompts_default.json"

    # Multi-repo support
    repos: List[Dict[str, Any]] = field(default_factory=list)

    # Analytics
    analytics_enabled: bool = True
    analytics_monthly_budget: float = 50.0

    # Auto-tune
    auto_tune_enabled: bool = False

    def validate(self) -> None:
        """
        Validate all configuration settings.

        Raises:
            ValueError: If any configuration is invalid
        """
        # Validate cost limits
        self.costs.validate()

        # Validate max_rounds
        if self.runtime.max_rounds < 1:
            raise ValueError("max_rounds must be >= 1")

        # Validate mode
        if self.mode not in ExecutionMode:
            raise ValueError(f"Invalid mode: {self.mode}")

        # Validate very_important_stages
        if not isinstance(self.very_important_stages, list):
            raise ValueError("very_important_stages must be a list")

        print("[Config] Configuration validated successfully.")

    @classmethod
    def from_file(cls, config_path: Path) -> Config:
        """
        Load configuration from a JSON file.

        Args:
            config_path: Path to project_config.json

        Returns:
            Config instance populated from file + environment
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with config_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Parse subsystems
        models = ModelDefaults.from_env()  # Start with env vars

        costs = CostLimits(
            max_cost_usd=float(data.get("max_cost_usd", 0.0) or 0.0),
            warning_threshold_usd=float(data.get("cost_warning_usd", 0.0) or 0.0),
            interactive_mode=InteractiveCostMode(data.get("interactive_cost_mode", "off")),
        )

        safety_data = data.get("safety", {})
        safety = SafetyConfig(
            run_before_final=bool(safety_data.get("run_safety_before_final", True)),
            allow_extra_iteration_on_failure=bool(
                safety_data.get("allow_extra_iteration_on_failure", True)
            ),
        )

        git = GitConfig(
            enabled=bool(data.get("use_git", False)),
            auto_commit=bool(data.get("auto_git_commit", False)),
            commit_mode=data.get("auto_git_commit_mode", "semantic"),
            auto_commit_repos=data.get("auto_git_commit_repos", ["default"]),
        )

        qa_data = data.get("qa", {})
        qa = QAConfig(
            enabled=bool(qa_data.get("enabled", True)),
            require_title=bool(qa_data.get("require_title", True)),
            require_meta_description=bool(qa_data.get("require_meta_description", True)),
            require_lang_attribute=bool(qa_data.get("require_lang_attribute", True)),
            require_h1=bool(qa_data.get("require_h1", True)),
            max_empty_links=int(qa_data.get("max_empty_links", 10)),
            max_images_missing_alt=int(qa_data.get("max_images_missing_alt", 0)),
            max_duplicate_ids=int(qa_data.get("max_duplicate_ids", 0)),
            max_console_logs=int(qa_data.get("max_console_logs", 5)),
            allow_large_files=bool(qa_data.get("allow_large_files", True)),
            max_large_files=int(qa_data.get("max_large_files", 5)),
            large_file_threshold=int(qa_data.get("large_file_threshold", 5000)),
        )

        runtime = RuntimeConfig(
            max_rounds=int(data.get("max_rounds", 3)),
            use_visual_review=bool(data.get("use_visual_review", False)),
            use_snapshots=bool(data.get("use_snapshots", True)),
        )

        auth_data = data.get("auth", {})
        auth = AuthConfig(
            enabled=bool(auth_data.get("enabled", True)),
            session_ttl_hours=int(auth_data.get("session_ttl_hours", 24)),
            api_key_ttl_days=int(auth_data.get("api_key_ttl_days", 90)),
            require_https=bool(auth_data.get("require_https", True)),
            allow_registration=bool(auth_data.get("allow_registration", False)),
            create_default_admin_key=bool(auth_data.get("create_default_admin_key", True)),
        )

        # Create config
        config = cls(
            mode=ExecutionMode(data.get("mode", "3loop")),
            models=models,
            very_important_stages=data.get("llm_very_important_stages", []),
            costs=costs,
            safety=safety,
            git=git,
            qa=qa,
            runtime=runtime,
            auth=auth,
            project_name=data.get("project_name", "Unknown Project"),
            project_subdir=data.get("project_subdir", "output"),
            task=data.get("task", ""),
            prompts_file=data.get("prompts_file", "prompts_default.json"),
            repos=data.get("repos", []),
            analytics_enabled=bool(data.get("analytics", {}).get("enabled", True)),
            analytics_monthly_budget=float(
                data.get("analytics", {}).get("monthly_budget", 50.0)
            ),
            auto_tune_enabled=bool(data.get("auto_tune", {}).get("enabled", False)),
        )

        # Apply local overrides if they exist
        config._apply_local_overrides()

        return config

    def _apply_local_overrides(self) -> None:
        """
        Apply local configuration overrides from config_local.py if it exists.

        This allows developers to override settings without modifying tracked files.
        """
        try:
            # Try to import config_local (not tracked in git)
            import config_local

            if hasattr(config_local, "apply_overrides"):
                config_local.apply_overrides(self)
                print("[Config] Applied local overrides from config_local.py")
        except ImportError:
            # No local overrides - this is fine
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for backward compatibility."""
        return {
            "mode": self.mode.value,
            "max_rounds": self.runtime.max_rounds,
            "use_visual_review": self.runtime.use_visual_review,
            "use_snapshots": self.runtime.use_snapshots,
            "use_git": self.git.enabled,
            "max_cost_usd": self.costs.max_cost_usd,
            "cost_warning_usd": self.costs.warning_threshold_usd,
            "interactive_cost_mode": self.costs.interactive_mode.value,
            "llm_very_important_stages": self.very_important_stages,
            "project_name": self.project_name,
            "project_subdir": self.project_subdir,
            "task": self.task,
            "prompts_file": self.prompts_file,
            "safety": {
                "run_safety_before_final": self.safety.run_before_final,
                "allow_extra_iteration_on_failure": self.safety.allow_extra_iteration_on_failure,
            },
            "auto_git_commit": self.git.auto_commit,
            "auto_git_commit_mode": self.git.commit_mode,
            "auto_git_commit_repos": self.git.auto_commit_repos,
            "repos": self.repos,
            "qa": {
                "enabled": self.qa.enabled,
                "require_title": self.qa.require_title,
                "require_meta_description": self.qa.require_meta_description,
                "require_lang_attribute": self.qa.require_lang_attribute,
                "require_h1": self.qa.require_h1,
                "max_empty_links": self.qa.max_empty_links,
                "max_images_missing_alt": self.qa.max_images_missing_alt,
                "max_duplicate_ids": self.qa.max_duplicate_ids,
                "max_console_logs": self.qa.max_console_logs,
                "allow_large_files": self.qa.allow_large_files,
                "max_large_files": self.qa.max_large_files,
                "large_file_threshold": self.qa.large_file_threshold,
            },
            "analytics": {
                "enabled": self.analytics_enabled,
                "monthly_budget": self.analytics_monthly_budget,
            },
            "auto_tune": {
                "enabled": self.auto_tune_enabled,
            },
        }


# ══════════════════════════════════════════════════════════════════════
# Global Configuration Instance
# ══════════════════════════════════════════════════════════════════════

# Singleton instance - loaded on first access
_CONFIG: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Loads configuration on first call from the default location.

    Returns:
        Global Config instance
    """
    global _CONFIG
    if _CONFIG is None:
        # Default config path (can be overridden via environment)
        config_path = Path(os.getenv("AGENT_CONFIG_PATH", "agent/project_config.json"))

        # If path is relative, resolve it from repo root
        if not config_path.is_absolute():
            repo_root = Path(__file__).resolve().parent.parent
            config_path = repo_root / config_path

        _CONFIG = Config.from_file(config_path)
        _CONFIG.validate()

    return _CONFIG


def reload_config() -> Config:
    """
    Force reload of configuration from disk.

    Useful for testing or when config file has been modified.

    Returns:
        Newly loaded Config instance
    """
    global _CONFIG
    _CONFIG = None
    return get_config()


# ══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ══════════════════════════════════════════════════════════════════════


def get_model_for_role(role: str) -> str:
    """Get the default model for a given role."""
    config = get_config()
    role_lower = role.lower()

    if role_lower == "manager":
        return config.models.manager
    elif role_lower == "supervisor":
        return config.models.supervisor
    elif role_lower == "employee":
        return config.models.employee
    elif role_lower == "merge_manager":
        return config.models.merge_manager
    elif role_lower in ("qa", "qa_reviewer"):
        return config.models.qa_reviewer
    else:
        # Default to employee model
        return config.models.employee


def is_simulation_mode() -> bool:
    """Check if any simulation mode is enabled."""
    config = get_config()
    return config.simulation != SimulationMode.OFF


def get_max_cost_usd() -> float:
    """Get the maximum cost cap in USD."""
    config = get_config()
    return config.costs.max_cost_usd
