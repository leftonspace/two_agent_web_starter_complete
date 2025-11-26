"""
PHASE 7.4: Domain Configuration System

Load domain configurations from YAML files to define specialist behavior.
Adding a new domain is as simple as adding a new YAML file to config/domains/.

Usage:
    from core.specialists import DomainConfigLoader, DomainConfig

    loader = DomainConfigLoader()

    # Discover all domains
    domains = loader.discover_domains()
    print(f"Available domains: {domains}")

    # Load specific domain
    config = loader.load("code_generation")
    print(f"System prompt: {config.default_config.system_prompt}")

    # Load all domains
    all_configs = loader.load_all()
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from .specialist import SpecialistConfig


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Models
# ============================================================================


class VerificationRule(BaseModel):
    """A verification rule for domain output."""

    type: str = Field(
        ...,
        description="Type of verification (syntax_valid, lint_check, tests_pass, etc.)",
    )
    description: str = Field(
        default="",
        description="Human-readable description of the rule",
    )
    fail_action: Literal["retry", "warn", "fail", "auto_fix"] = Field(
        default="warn",
        description="Action to take on failure",
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Rule-specific configuration",
    )


class QualityThresholds(BaseModel):
    """Quality thresholds for specialist lifecycle."""

    min_score_for_active: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum score to be promoted from probation",
    )
    min_score_to_avoid_culling: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum score to avoid being culled",
    )
    probation_tasks: int = Field(
        default=10,
        ge=1,
        description="Tasks to complete before promotion evaluation",
    )
    min_tasks_before_culling: int = Field(
        default=5,
        ge=1,
        description="Minimum tasks before culling can occur",
    )


class EvolutionSettings(BaseModel):
    """Settings for automatic specialist evolution."""

    enabled: bool = Field(
        default=True,
        description="Whether auto-evolution is enabled",
    )
    auto_evolve_threshold: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Score threshold to trigger evolution",
    )
    mutation_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="How much to vary parameters on evolution",
    )


class DefaultSpecialistConfig(BaseModel):
    """
    Default configuration for specialists in a domain.

    This maps to SpecialistConfig but allows YAML-friendly field names.
    """

    system_prompt: str = Field(
        ...,
        min_length=10,
        description="System prompt defining specialist behavior",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
    )
    tools_enabled: List[str] = Field(
        default_factory=list,
        description="Tools the specialist can use",
    )
    tools_required: List[str] = Field(
        default_factory=list,
        description="Tools that must be available",
    )
    preferred_model_tier: str = Field(
        default="high",
        description="Preferred model tier",
    )
    min_model_tier: str = Field(
        default="low",
        description="Minimum model tier",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Max retry attempts",
    )

    def to_specialist_config(
        self,
        avoid_patterns: Optional[List[str]] = None,
    ) -> SpecialistConfig:
        """Convert to SpecialistConfig for specialist creation."""
        return SpecialistConfig(
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            tools_enabled=self.tools_enabled,
            tools_required=self.tools_required,
            preferred_model_tier=self.preferred_model_tier,
            min_model_tier=self.min_model_tier,
            max_retries=self.max_retries,
            avoid_patterns=avoid_patterns or [],
        )


class DomainConfig(BaseModel):
    """
    Complete domain configuration loaded from YAML.

    Defines how specialists in this domain should behave,
    what verification rules apply, and quality thresholds.
    """

    domain: str = Field(
        ...,
        min_length=1,
        description="Domain identifier",
    )
    description: str = Field(
        default="",
        description="Human-readable description",
    )
    is_jarvis_domain: bool = Field(
        default=False,
        description="Whether best specialist becomes JARVIS",
    )
    default_config: DefaultSpecialistConfig = Field(
        ...,
        description="Default specialist configuration",
    )
    verification: List[VerificationRule] = Field(
        default_factory=list,
        description="Verification rules for output",
    )
    quality_thresholds: QualityThresholds = Field(
        default_factory=QualityThresholds,
        description="Quality thresholds for lifecycle",
    )
    evolution: EvolutionSettings = Field(
        default_factory=EvolutionSettings,
        description="Evolution settings",
    )

    @field_validator("domain")
    @classmethod
    def normalize_domain(cls, v: str) -> str:
        """Normalize domain name to lowercase with underscores."""
        return v.lower().replace(" ", "_").replace("-", "_")

    def create_specialist_config(
        self,
        avoid_patterns: Optional[List[str]] = None,
        override_temperature: Optional[float] = None,
        additional_tools: Optional[List[str]] = None,
    ) -> SpecialistConfig:
        """
        Create a SpecialistConfig from this domain config.

        Args:
            avoid_patterns: Patterns to avoid (from graveyard)
            override_temperature: Override default temperature
            additional_tools: Additional tools to enable

        Returns:
            SpecialistConfig ready for specialist creation
        """
        config = self.default_config.to_specialist_config(avoid_patterns)

        if override_temperature is not None:
            config.temperature = override_temperature

        if additional_tools:
            config.tools_enabled = list(set(config.tools_enabled + additional_tools))

        return config


# ============================================================================
# Domain Config Loader
# ============================================================================


class DomainConfigLoader:
    """
    Load domain configurations from YAML files.

    Looks for YAML files in config/domains/ directory.
    Each file represents one domain configuration.

    Usage:
        loader = DomainConfigLoader()

        # List available domains
        domains = loader.discover_domains()

        # Load specific domain
        config = loader.load("code_generation")

        # Load all domains
        all_configs = loader.load_all()
    """

    DEFAULT_CONFIG_PATH = "config/domains"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the loader.

        Args:
            config_path: Path to domain configs directory
        """
        self._config_path = Path(config_path or self.DEFAULT_CONFIG_PATH)
        self._cache: Dict[str, DomainConfig] = {}

    @property
    def config_path(self) -> Path:
        """Get the config directory path."""
        return self._config_path

    def discover_domains(self) -> List[str]:
        """
        Discover available domain names from YAML files.

        Returns:
            List of domain names (file stems)
        """
        if not self._config_path.exists():
            logger.warning(f"Config path does not exist: {self._config_path}")
            return []

        domains = []

        # Check .yaml files
        for config_file in self._config_path.glob("*.yaml"):
            domains.append(config_file.stem)

        # Check .yml files
        for config_file in self._config_path.glob("*.yml"):
            if config_file.stem not in domains:
                domains.append(config_file.stem)

        return sorted(domains)

    def load(self, domain: str, use_cache: bool = True) -> DomainConfig:
        """
        Load configuration for a specific domain.

        Args:
            domain: Domain name (matches YAML filename)
            use_cache: Whether to use cached config

        Returns:
            DomainConfig for the domain

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        # Check cache
        if use_cache and domain in self._cache:
            return self._cache[domain]

        # Find config file
        yaml_path = self._config_path / f"{domain}.yaml"
        yml_path = self._config_path / f"{domain}.yml"

        if yaml_path.exists():
            config_file = yaml_path
        elif yml_path.exists():
            config_file = yml_path
        else:
            raise FileNotFoundError(
                f"No config file found for domain '{domain}' "
                f"(looked in {self._config_path})"
            )

        # Load YAML
        try:
            with open(config_file, "r") as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {config_file}: {e}")

        # Parse config
        try:
            config = DomainConfig(**raw_config)
        except Exception as e:
            raise ValueError(f"Invalid config in {config_file}: {e}")

        # Cache and return
        self._cache[domain] = config
        logger.info(f"Loaded domain config: {domain}")

        return config

    def load_all(self, use_cache: bool = True) -> Dict[str, DomainConfig]:
        """
        Load all domain configurations.

        Args:
            use_cache: Whether to use cached configs

        Returns:
            Dict mapping domain names to configs
        """
        configs = {}
        domains = self.discover_domains()

        for domain in domains:
            try:
                configs[domain] = self.load(domain, use_cache=use_cache)
            except Exception as e:
                logger.error(f"Failed to load domain '{domain}': {e}")

        return configs

    def reload(self, domain: Optional[str] = None) -> None:
        """
        Reload configuration(s), clearing cache.

        Args:
            domain: Specific domain to reload, or None for all
        """
        if domain:
            if domain in self._cache:
                del self._cache[domain]
            self.load(domain, use_cache=False)
        else:
            self._cache.clear()
            self.load_all(use_cache=False)

    def get_jarvis_domain(self) -> Optional[DomainConfig]:
        """
        Get the JARVIS domain configuration.

        Returns:
            DomainConfig marked as JARVIS domain, or None
        """
        for domain in self.discover_domains():
            try:
                config = self.load(domain)
                if config.is_jarvis_domain:
                    return config
            except Exception:
                continue

        return None

    def validate_all(self) -> Dict[str, Optional[str]]:
        """
        Validate all domain configurations.

        Returns:
            Dict mapping domain names to error messages (None if valid)
        """
        results = {}

        for domain in self.discover_domains():
            try:
                self.load(domain, use_cache=False)
                results[domain] = None
            except Exception as e:
                results[domain] = str(e)

        return results


# ============================================================================
# Singleton Instance
# ============================================================================


_domain_loader: Optional[DomainConfigLoader] = None


def get_domain_loader() -> DomainConfigLoader:
    """Get the global domain config loader."""
    global _domain_loader
    if _domain_loader is None:
        _domain_loader = DomainConfigLoader()
    return _domain_loader


def reset_domain_loader() -> None:
    """Reset the global domain config loader (for testing)."""
    global _domain_loader
    _domain_loader = None
