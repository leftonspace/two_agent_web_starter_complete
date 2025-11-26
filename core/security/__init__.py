"""
PHASE 7: Security Foundation

OS-level sandboxing for secure code execution and output guardrails.

Components:
- sandbox: OS-level isolation using bubblewrap (Linux) or sandbox-exec (macOS)
- profiles: YAML-based profile configuration and loading
- network: Domain validation and network configuration for sandboxes
- guardrails: Output validation and PII detection

Usage:
    from core.security import Sandbox, SandboxProfile, ExecutionResult

    # Create profile manually
    profile = SandboxProfile(
        name="my_profile",
        allowed_paths=["/workspace", "/tmp"],
        allowed_domains=["github.com"],
        max_memory_mb=4096,
        max_time_seconds=300,
    )

    # Execute in sandbox
    sandbox = Sandbox(profile)
    result = await sandbox.execute("python script.py", working_dir="/workspace")

    # Or load profile from YAML configuration
    from core.security import ProfileLoader, load_profile

    loader = ProfileLoader()
    profile = loader.load_profile("code_generation")

    # Validate network domains
    from core.security import DomainValidator, NetworkConfig

    validator = DomainValidator(["github.com", "pypi.org"])
    if validator.is_allowed("https://api.github.com/repos"):
        print("URL allowed")

    # Validate outputs with guardrails
    from core.security import OutputGuardrails, GuardrailContext

    guardrails = OutputGuardrails()
    context = GuardrailContext(pii_policy="redact")
    result = guardrails.validate(output_text, context)
"""

from .sandbox import (
    # Models
    SandboxProfile,
    ExecutionResult,
    # Main class
    Sandbox,
    # Pre-defined profiles (built-in)
    PROFILES,
    get_profile,
    # Convenience functions
    run_sandboxed,
    is_sandbox_available,
    get_platform,
)

from .profiles import (
    # Profile loader
    ProfileLoader,
    ProfileValidationError,
    ProfileNotFoundError,
    # Convenience functions
    get_loader,
    load_profile,
    load_all_profiles,
    get_default_profile,
    list_profile_names,
)

from .network import (
    # Network validation
    DomainValidator,
    NetworkConfig,
    # Convenience functions
    create_validator,
    is_domain_allowed,
    get_sandbox_network_env,
)

from .guardrails import (
    # Enums and models
    PIIPattern,
    IssueSeverity,
    PIIMatch,
    Anomaly,
    Issue,
    GuardrailContext,
    ValidationResult,
    # Main classes
    PIIDetector,
    AnomalyDetector,
    OutputGuardrails,
    # Convenience functions
    create_guardrails,
    validate_output,
    redact_pii,
    hash_system_prompt,
)

from .pii_patterns import (
    # Patterns
    SSN_PATTERN,
    CREDIT_CARD_PATTERN,
    US_PHONE_PATTERN,
    EMAIL_PATTERN,
    API_KEY_PATTERNS,
    PII_PATTERNS,
    # Utilities
    luhn_checksum,
    analyze_script_distribution,
)

__all__ = [
    # Models
    "SandboxProfile",
    "ExecutionResult",
    # Main class
    "Sandbox",
    # Pre-defined profiles (built-in)
    "PROFILES",
    "get_profile",
    # Sandbox convenience functions
    "run_sandboxed",
    "is_sandbox_available",
    "get_platform",
    # Profile loader
    "ProfileLoader",
    "ProfileValidationError",
    "ProfileNotFoundError",
    # Profile convenience functions
    "get_loader",
    "load_profile",
    "load_all_profiles",
    "get_default_profile",
    "list_profile_names",
    # Network validation
    "DomainValidator",
    "NetworkConfig",
    "create_validator",
    "is_domain_allowed",
    "get_sandbox_network_env",
    # Guardrails - enums and models
    "PIIPattern",
    "IssueSeverity",
    "PIIMatch",
    "Anomaly",
    "Issue",
    "GuardrailContext",
    "ValidationResult",
    # Guardrails - main classes
    "PIIDetector",
    "AnomalyDetector",
    "OutputGuardrails",
    # Guardrails - convenience functions
    "create_guardrails",
    "validate_output",
    "redact_pii",
    "hash_system_prompt",
    # PII patterns
    "SSN_PATTERN",
    "CREDIT_CARD_PATTERN",
    "US_PHONE_PATTERN",
    "EMAIL_PATTERN",
    "API_KEY_PATTERNS",
    "PII_PATTERNS",
    "luhn_checksum",
    "analyze_script_distribution",
]
