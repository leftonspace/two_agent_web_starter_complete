"""
PHASE 7.1: Sandbox Profile Loader

Loads and validates sandbox profiles from YAML configuration files.

Features:
- YAML-based configuration
- Profile validation with pydantic
- Caching for performance
- Default profile fallback
- Global constraints enforcement

Usage:
    from core.security.profiles import ProfileLoader

    loader = ProfileLoader()

    # Load a specific profile
    profile = loader.load_profile("code_generation")

    # Load all profiles
    all_profiles = loader.load_all()

    # Get the default profile
    default = loader.get_default()
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .sandbox import SandboxProfile

# Configure logging
logger = logging.getLogger(__name__)

# Default config path relative to project root
DEFAULT_CONFIG_PATH = "config/security/sandbox_profiles.yaml"


class ProfileValidationError(Exception):
    """Raised when a profile fails validation."""

    pass


class ProfileNotFoundError(Exception):
    """Raised when a requested profile doesn't exist."""

    pass


class ProfileLoader:
    """
    Loads and validates sandbox profiles from YAML configuration.

    Profiles are cached after first load for performance.
    Supports both file-based and dict-based configuration.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the profile loader.

        Args:
            config_path: Path to YAML config file (default: config/security/sandbox_profiles.yaml)
            config_dict: Direct configuration dict (overrides config_path if provided)
        """
        self._config_path = config_path
        self._config_dict = config_dict
        self._cache: Dict[str, SandboxProfile] = {}
        self._raw_config: Optional[Dict[str, Any]] = None
        self._loaded = False

    def _find_config_path(self) -> Path:
        """Find the configuration file path."""
        if self._config_path:
            return Path(self._config_path)

        # Try to find config relative to common locations
        search_paths = [
            # Relative to current working directory
            Path.cwd() / DEFAULT_CONFIG_PATH,
            # Relative to this file's location (core/security/profiles.py)
            Path(__file__).parent.parent.parent / DEFAULT_CONFIG_PATH,
            # Absolute path if CWD is project root
            Path(DEFAULT_CONFIG_PATH),
        ]

        for path in search_paths:
            if path.exists():
                return path

        # Return default path even if it doesn't exist (will raise later)
        return Path(DEFAULT_CONFIG_PATH)

    def _load_config(self) -> Dict[str, Any]:
        """Load and cache the raw configuration."""
        if self._raw_config is not None:
            return self._raw_config

        # If dict provided, use it directly
        if self._config_dict is not None:
            self._raw_config = self._config_dict
            return self._raw_config

        # Load from YAML file
        config_path = self._find_config_path()

        if not config_path.exists():
            logger.warning(
                f"Config file not found at {config_path}, using built-in defaults"
            )
            self._raw_config = {"profiles": {}, "default_profile": "minimal"}
            return self._raw_config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._raw_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded sandbox profiles from {config_path}")
        except yaml.YAMLError as e:
            raise ProfileValidationError(f"Invalid YAML in {config_path}: {e}")
        except OSError as e:
            raise ProfileValidationError(f"Failed to read {config_path}: {e}")

        return self._raw_config

    def _validate_profile_data(
        self,
        name: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate and normalize profile data.

        Args:
            name: Profile name
            data: Raw profile data from YAML

        Returns:
            Validated and normalized profile data

        Raises:
            ProfileValidationError: If validation fails
        """
        config = self._load_config()
        global_config = config.get("global", {})

        # Required fields
        if "allowed_paths" not in data:
            raise ProfileValidationError(
                f"Profile '{name}' missing required field: allowed_paths"
            )

        # Normalize paths to absolute
        allowed_paths = []
        for path in data.get("allowed_paths", []):
            abs_path = os.path.abspath(os.path.expanduser(path))
            allowed_paths.append(abs_path)

        # Check against blocked paths
        blocked_paths = global_config.get("blocked_paths", [])
        for allowed in allowed_paths:
            for blocked in blocked_paths:
                blocked_abs = os.path.abspath(os.path.expanduser(blocked))
                if allowed.startswith(blocked_abs) or blocked_abs.startswith(allowed):
                    raise ProfileValidationError(
                        f"Profile '{name}': path '{allowed}' conflicts with "
                        f"blocked path '{blocked}'"
                    )

        # Validate memory limit
        max_memory = data.get("max_memory_mb", 512)
        max_allowed = global_config.get("max_allowed_memory_mb", 8192)
        if max_memory > max_allowed:
            raise ProfileValidationError(
                f"Profile '{name}': max_memory_mb ({max_memory}) exceeds "
                f"global maximum ({max_allowed})"
            )

        # Validate time limit
        max_time = data.get("max_time_seconds", 60)
        max_allowed_time = global_config.get("max_allowed_time_seconds", 3600)
        if max_time > max_allowed_time:
            raise ProfileValidationError(
                f"Profile '{name}': max_time_seconds ({max_time}) exceeds "
                f"global maximum ({max_allowed_time})"
            )

        # Build validated data
        validated = {
            "name": name,
            "allowed_paths": allowed_paths,
            "allowed_domains": [
                d.lower().strip() for d in data.get("allowed_domains", [])
            ],
            "max_memory_mb": max_memory,
            "max_time_seconds": max_time,
            "allow_network": data.get("allow_network", False),
        }

        return validated

    def load_profile(self, name: str) -> SandboxProfile:
        """
        Load a sandbox profile by name.

        Args:
            name: Profile name (e.g., "code_generation", "minimal")

        Returns:
            SandboxProfile instance

        Raises:
            ProfileNotFoundError: If profile doesn't exist
            ProfileValidationError: If profile is invalid
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]

        config = self._load_config()
        profiles = config.get("profiles", {})

        if name not in profiles:
            # Try to use built-in default from sandbox.py
            from .sandbox import PROFILES as BUILTIN_PROFILES

            if name in BUILTIN_PROFILES:
                logger.debug(f"Using built-in profile: {name}")
                profile = BUILTIN_PROFILES[name].model_copy()
                self._cache[name] = profile
                return profile

            available = list(profiles.keys()) + list(BUILTIN_PROFILES.keys())
            raise ProfileNotFoundError(
                f"Profile '{name}' not found. Available: {available}"
            )

        # Validate and create profile
        profile_data = profiles[name]
        validated = self._validate_profile_data(name, profile_data)

        try:
            profile = SandboxProfile(**validated)
        except Exception as e:
            raise ProfileValidationError(
                f"Failed to create profile '{name}': {e}"
            )

        # Cache and return
        self._cache[name] = profile
        logger.debug(f"Loaded profile: {name}")
        return profile

    def load_all(self) -> Dict[str, SandboxProfile]:
        """
        Load all available profiles.

        Returns:
            Dictionary mapping profile names to SandboxProfile instances
        """
        config = self._load_config()
        profiles = config.get("profiles", {})

        # Load all profiles from config
        result = {}
        for name in profiles:
            try:
                result[name] = self.load_profile(name)
            except (ProfileNotFoundError, ProfileValidationError) as e:
                logger.warning(f"Failed to load profile '{name}': {e}")

        # Also include built-in profiles that aren't overridden
        from .sandbox import PROFILES as BUILTIN_PROFILES

        for name, profile in BUILTIN_PROFILES.items():
            if name not in result:
                result[name] = profile.model_copy()

        return result

    def get_default(self) -> SandboxProfile:
        """
        Get the default sandbox profile.

        Returns:
            The default SandboxProfile (typically 'minimal')
        """
        config = self._load_config()
        default_name = config.get("default_profile", "minimal")

        try:
            return self.load_profile(default_name)
        except ProfileNotFoundError:
            # Fall back to minimal if configured default doesn't exist
            logger.warning(
                f"Default profile '{default_name}' not found, using 'minimal'"
            )
            return self.load_profile("minimal")

    def clear_cache(self) -> None:
        """Clear the profile cache, forcing reload on next access."""
        self._cache.clear()
        self._raw_config = None
        logger.debug("Profile cache cleared")

    def get_global_config(self) -> Dict[str, Any]:
        """
        Get the global configuration settings.

        Returns:
            Dictionary with global settings (blocked_paths, max limits, etc.)
        """
        config = self._load_config()
        return config.get("global", {})

    def list_profiles(self) -> list[str]:
        """
        List all available profile names.

        Returns:
            List of profile names
        """
        config = self._load_config()
        profiles = set(config.get("profiles", {}).keys())

        # Include built-in profiles
        from .sandbox import PROFILES as BUILTIN_PROFILES

        profiles.update(BUILTIN_PROFILES.keys())

        return sorted(profiles)


# ============================================================================
# Module-level convenience functions
# ============================================================================

# Global loader instance (lazy initialized)
_default_loader: Optional[ProfileLoader] = None


def get_loader() -> ProfileLoader:
    """Get or create the default profile loader."""
    global _default_loader
    if _default_loader is None:
        _default_loader = ProfileLoader()
    return _default_loader


def load_profile(name: str) -> SandboxProfile:
    """
    Convenience function to load a profile.

    Args:
        name: Profile name

    Returns:
        SandboxProfile instance
    """
    return get_loader().load_profile(name)


def load_all_profiles() -> Dict[str, SandboxProfile]:
    """
    Convenience function to load all profiles.

    Returns:
        Dictionary of all profiles
    """
    return get_loader().load_all()


def get_default_profile() -> SandboxProfile:
    """
    Convenience function to get the default profile.

    Returns:
        Default SandboxProfile
    """
    return get_loader().get_default()


def list_profile_names() -> list[str]:
    """
    Convenience function to list profile names.

    Returns:
        List of available profile names
    """
    return get_loader().list_profiles()
