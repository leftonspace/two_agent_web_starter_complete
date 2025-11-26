"""
PHASE 7.5: Benchmark Loader

Load benchmark YAML files from /benchmarks/ directory.
Benchmarks define test suites for evaluating specialists.

Usage:
    from core.benchmark import BenchmarkLoader, get_benchmark_loader

    loader = get_benchmark_loader()

    # Discover available benchmarks
    available = loader.discover()
    # {"code_generation": ["basic_functions", "api_integrations"], ...}

    # Load specific benchmark
    benchmark = loader.load("benchmarks/code_generation/basic_functions.yaml")

    # Load all benchmarks for a domain
    benchmarks = loader.load_domain("code_generation")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import yaml
from pydantic import BaseModel, Field


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Verification Rule
# ============================================================================


class VerificationRule(BaseModel):
    """Single verification rule for a benchmark task."""

    type: str = Field(..., description="Type of verification check")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for the check",
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Weight of this rule in scoring",
    )


# ============================================================================
# Benchmark Task
# ============================================================================


class BenchmarkTask(BaseModel):
    """Single task within a benchmark."""

    id: str = Field(..., description="Unique task identifier")
    difficulty: Literal["easy", "medium", "hard"] = Field(
        ...,
        description="Task difficulty level",
    )
    prompt: str = Field(..., description="The task prompt to execute")
    verification: List[VerificationRule] = Field(
        default_factory=list,
        description="Rules to verify task completion",
    )
    expected_domain: Optional[str] = Field(
        default=None,
        description="Expected domain classification (for routing tests)",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for filtering tasks",
    )
    timeout_seconds: int = Field(
        default=60,
        ge=1,
        description="Maximum execution time",
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "difficulty": self.difficulty,
            "prompt": self.prompt[:100] + "..." if len(self.prompt) > 100 else self.prompt,
            "verification_count": len(self.verification),
            "expected_domain": self.expected_domain,
            "tags": self.tags,
        }


# ============================================================================
# Benchmark
# ============================================================================


class Benchmark(BaseModel):
    """Complete benchmark definition."""

    name: str = Field(..., description="Benchmark name")
    domain: str = Field(..., description="Target domain")
    version: str = Field(default="1.0", description="Benchmark version")
    description: str = Field(default="", description="Benchmark description")
    created_by: str = Field(default="unknown", description="Benchmark creator")
    tasks: List[BenchmarkTask] = Field(
        default_factory=list,
        description="List of benchmark tasks",
    )

    @property
    def total_tasks(self) -> int:
        """Get total number of tasks."""
        return len(self.tasks)

    @property
    def easy_count(self) -> int:
        """Get number of easy tasks."""
        return sum(1 for t in self.tasks if t.difficulty == "easy")

    @property
    def medium_count(self) -> int:
        """Get number of medium tasks."""
        return sum(1 for t in self.tasks if t.difficulty == "medium")

    @property
    def hard_count(self) -> int:
        """Get number of hard tasks."""
        return sum(1 for t in self.tasks if t.difficulty == "hard")

    def get_tasks_by_difficulty(
        self,
        difficulty: Literal["easy", "medium", "hard"],
    ) -> List[BenchmarkTask]:
        """Get tasks filtered by difficulty."""
        return [t for t in self.tasks if t.difficulty == difficulty]

    def get_tasks_by_tag(self, tag: str) -> List[BenchmarkTask]:
        """Get tasks filtered by tag."""
        return [t for t in self.tasks if tag in t.tags]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "domain": self.domain,
            "version": self.version,
            "description": self.description,
            "created_by": self.created_by,
            "total_tasks": self.total_tasks,
            "easy_count": self.easy_count,
            "medium_count": self.medium_count,
            "hard_count": self.hard_count,
        }


# ============================================================================
# Benchmark Loader
# ============================================================================


class BenchmarkLoader:
    """
    Load benchmark YAML files from /benchmarks/ directory.

    Directory structure:
    /benchmarks/
    ├── code_generation/
    │   ├── basic_functions.yaml
    │   └── api_integrations.yaml
    └── business_documents/
        └── reports.yaml

    Usage:
        loader = BenchmarkLoader()
        benchmark = loader.load("benchmarks/code_generation/basic_functions.yaml")
        all_code = loader.load_domain("code_generation")
    """

    DEFAULT_BENCHMARK_DIR = "benchmarks"

    def __init__(self, benchmark_dir: Optional[str] = None):
        """
        Initialize the loader.

        Args:
            benchmark_dir: Root directory for benchmarks
        """
        self._benchmark_dir = Path(benchmark_dir or self.DEFAULT_BENCHMARK_DIR)
        self._cache: Dict[str, Benchmark] = {}

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def benchmark_dir(self) -> Path:
        """Get benchmark directory."""
        return self._benchmark_dir

    # -------------------------------------------------------------------------
    # Loading
    # -------------------------------------------------------------------------

    def load(self, path: str) -> Benchmark:
        """
        Load a single benchmark file.

        Args:
            path: Path to benchmark YAML file

        Returns:
            Loaded Benchmark

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        # Check cache
        if path in self._cache:
            return self._cache[path]

        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Benchmark file not found: {path}")

        try:
            with open(file_path, "r") as f:
                raw = yaml.safe_load(f)

            benchmark = self._parse_benchmark(raw, file_path)
            self._cache[path] = benchmark
            return benchmark

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in benchmark file: {e}")

    def load_domain(self, domain: str) -> List[Benchmark]:
        """
        Load all benchmarks for a domain.

        Args:
            domain: Domain name (matches directory name)

        Returns:
            List of Benchmarks for the domain
        """
        domain_dir = self._benchmark_dir / domain
        if not domain_dir.exists():
            logger.warning(f"No benchmark directory for domain: {domain}")
            return []

        benchmarks = []
        for yaml_file in domain_dir.glob("*.yaml"):
            try:
                benchmark = self.load(str(yaml_file))
                benchmarks.append(benchmark)
            except Exception as e:
                logger.error(f"Failed to load benchmark {yaml_file}: {e}")

        return benchmarks

    def load_all(self) -> List[Benchmark]:
        """
        Load all benchmarks from all domains.

        Returns:
            List of all Benchmarks
        """
        benchmarks = []

        if not self._benchmark_dir.exists():
            logger.warning(f"Benchmark directory not found: {self._benchmark_dir}")
            return []

        # Iterate through domain directories
        for domain_dir in self._benchmark_dir.iterdir():
            if domain_dir.is_dir() and not domain_dir.name.startswith("."):
                domain_benchmarks = self.load_domain(domain_dir.name)
                benchmarks.extend(domain_benchmarks)

        return benchmarks

    # -------------------------------------------------------------------------
    # Discovery
    # -------------------------------------------------------------------------

    def discover(self) -> Dict[str, List[str]]:
        """
        Discover available benchmarks without loading them.

        Returns:
            Dict mapping domain -> list of benchmark names
        """
        result: Dict[str, List[str]] = {}

        if not self._benchmark_dir.exists():
            return result

        for domain_dir in self._benchmark_dir.iterdir():
            if domain_dir.is_dir() and not domain_dir.name.startswith("."):
                benchmarks = []
                for yaml_file in domain_dir.glob("*.yaml"):
                    benchmarks.append(yaml_file.stem)
                if benchmarks:
                    result[domain_dir.name] = sorted(benchmarks)

        return result

    def get_benchmark_info(self, domain: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Get info about a specific benchmark without full loading.

        Args:
            domain: Domain name
            name: Benchmark name (without .yaml)

        Returns:
            Basic benchmark info or None if not found
        """
        path = self._benchmark_dir / domain / f"{name}.yaml"
        if not path.exists():
            return None

        try:
            with open(path, "r") as f:
                raw = yaml.safe_load(f)

            return {
                "name": raw.get("name", name),
                "domain": raw.get("domain", domain),
                "version": raw.get("version", "1.0"),
                "description": raw.get("description", ""),
                "task_count": len(raw.get("tasks", [])),
                "path": str(path),
            }
        except Exception as e:
            logger.error(f"Failed to get benchmark info: {e}")
            return None

    # -------------------------------------------------------------------------
    # Parsing
    # -------------------------------------------------------------------------

    def _parse_benchmark(self, raw: Dict[str, Any], path: Path) -> Benchmark:
        """Parse raw YAML data into Benchmark."""
        # Infer domain from directory if not specified
        domain = raw.get("domain")
        if not domain:
            domain = path.parent.name

        # Parse tasks
        tasks = []
        for task_data in raw.get("tasks", []):
            task = self._parse_task(task_data)
            tasks.append(task)

        return Benchmark(
            name=raw.get("name", path.stem),
            domain=domain,
            version=raw.get("version", "1.0"),
            description=raw.get("description", ""),
            created_by=raw.get("created_by", "unknown"),
            tasks=tasks,
        )

    def _parse_task(self, task_data: Dict[str, Any]) -> BenchmarkTask:
        """Parse task data into BenchmarkTask."""
        # Parse verification rules
        verification = []
        for rule_data in task_data.get("verification", []):
            if isinstance(rule_data, str):
                # Simple string format: "syntax_valid"
                verification.append(VerificationRule(type=rule_data))
            elif isinstance(rule_data, dict):
                # Full format: {type: "tests_pass", params: {...}}
                verification.append(VerificationRule(**rule_data))

        return BenchmarkTask(
            id=task_data.get("id", "unknown"),
            difficulty=task_data.get("difficulty", "medium"),
            prompt=task_data.get("prompt", ""),
            verification=verification,
            expected_domain=task_data.get("expected_domain"),
            tags=task_data.get("tags", []),
            timeout_seconds=task_data.get("timeout_seconds", 60),
        )

    # -------------------------------------------------------------------------
    # Cache Management
    # -------------------------------------------------------------------------

    def clear_cache(self) -> int:
        """Clear benchmark cache. Returns items cleared."""
        count = len(self._cache)
        self._cache.clear()
        return count

    def get_cache_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get loader statistics."""
        discovered = self.discover()
        total_benchmarks = sum(len(b) for b in discovered.values())

        return {
            "benchmark_dir": str(self._benchmark_dir),
            "domains": list(discovered.keys()),
            "total_benchmarks": total_benchmarks,
            "benchmarks_per_domain": {k: len(v) for k, v in discovered.items()},
            "cache_size": len(self._cache),
        }


# ============================================================================
# Singleton Instance
# ============================================================================


_benchmark_loader: Optional[BenchmarkLoader] = None


def get_benchmark_loader() -> BenchmarkLoader:
    """Get the global benchmark loader."""
    global _benchmark_loader
    if _benchmark_loader is None:
        _benchmark_loader = BenchmarkLoader()
    return _benchmark_loader


def reset_benchmark_loader() -> None:
    """Reset the global benchmark loader (for testing)."""
    global _benchmark_loader
    _benchmark_loader = None
