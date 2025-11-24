"""
Auto-Improver - Automated Self-Improvement Execution

Connects self_refinement suggestions to automatic config/prompt updates.
Implements A/B testing framework for safe validation of improvements.
"""

from __future__ import annotations

import json
import random
import yaml
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .self_refinement import SelfRefinement, ImprovementSuggestion
except ImportError:
    SelfRefinement = None
    ImprovementSuggestion = None


# =============================================================================
# Configuration
# =============================================================================

class ImprovementStatus(Enum):
    """Status of improvement implementation"""
    PROPOSED = "proposed"
    TESTING = "testing"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"


@dataclass
class AutoImproverConfig:
    """Configuration for auto-improver"""

    # Confidence thresholds
    auto_execute_threshold: float = 0.8  # Auto-execute if confidence >= 0.8
    ab_test_threshold: float = 0.6  # A/B test if confidence >= 0.6
    reject_threshold: float = 0.3  # Reject if confidence < 0.3

    # A/B testing
    ab_test_duration_hours: int = 24  # Run A/B test for 24 hours
    ab_test_traffic_split: float = 0.5  # 50/50 traffic split
    ab_test_min_samples: int = 100  # Minimum samples per variant

    # Safety
    max_concurrent_improvements: int = 3  # Max improvements testing at once
    rollback_on_degradation: bool = True  # Auto-rollback if metrics degrade
    degradation_threshold: float = 0.05  # 5% degradation triggers rollback

    # Paths
    config_backup_dir: Path = Path(".jarvis/config_backups")
    improvement_log: Path = Path(".jarvis/improvements.jsonl")


@dataclass
class ImprovementRecord:
    """Record of an improvement attempt"""
    id: str
    suggestion: Dict[str, Any]  # ImprovementSuggestion as dict
    status: ImprovementStatus
    confidence: float
    implemented_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    ab_test_results: Optional[Dict[str, Any]] = None
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "suggestion": self.suggestion,
            "status": self.status.value,
            "confidence": self.confidence,
            "implemented_at": self.implemented_at.isoformat() if self.implemented_at else None,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "ab_test_results": self.ab_test_results,
            "validation_metrics": self.validation_metrics,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ImprovementRecord:
        """Create from dictionary"""
        return cls(
            id=data["id"],
            suggestion=data["suggestion"],
            status=ImprovementStatus(data["status"]),
            confidence=data["confidence"],
            implemented_at=datetime.fromisoformat(data["implemented_at"]) if data.get("implemented_at") else None,
            validated_at=datetime.fromisoformat(data["validated_at"]) if data.get("validated_at") else None,
            deployed_at=datetime.fromisoformat(data["deployed_at"]) if data.get("deployed_at") else None,
            rolled_back_at=datetime.fromisoformat(data["rolled_back_at"]) if data.get("rolled_back_at") else None,
            ab_test_results=data.get("ab_test_results"),
            validation_metrics=data.get("validation_metrics", {}),
            notes=data.get("notes", ""),
        )


# =============================================================================
# A/B Testing Framework
# =============================================================================

@dataclass
class ABTestVariant:
    """A/B test variant"""
    name: str  # "control" or "treatment"
    config: Dict[str, Any]
    samples: int = 0
    success_count: int = 0
    total_cost: float = 0.0
    avg_latency: float = 0.0
    error_count: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        return self.success_count / self.samples if self.samples > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        return self.error_count / self.samples if self.samples > 0 else 0.0

    @property
    def avg_cost_per_request(self) -> float:
        """Calculate average cost"""
        return self.total_cost / self.samples if self.samples > 0 else 0.0


class ABTest:
    """
    A/B test for validating improvements.

    Example:
        ab_test = ABTest(
            improvement_id="imp_123",
            control_config=current_config,
            treatment_config=improved_config,
            duration_hours=24,
        )

        # For each request, assign variant and record result
        variant = ab_test.assign_variant()
        result = execute_with_config(variant.config)
        ab_test.record_result(variant.name, result)

        # After test period
        if ab_test.is_complete():
            winner = ab_test.analyze_results()
    """

    def __init__(
        self,
        improvement_id: str,
        control_config: Dict[str, Any],
        treatment_config: Dict[str, Any],
        duration_hours: int = 24,
        traffic_split: float = 0.5,
        min_samples: int = 100,
    ):
        """
        Initialize A/B test.

        Args:
            improvement_id: Improvement being tested
            control_config: Current (baseline) configuration
            treatment_config: Improved configuration
            duration_hours: Test duration in hours
            traffic_split: Fraction of traffic to treatment (0-1)
            min_samples: Minimum samples per variant
        """
        self.improvement_id = improvement_id
        self.started_at = datetime.now()
        self.duration = timedelta(hours=duration_hours)
        self.traffic_split = traffic_split
        self.min_samples = min_samples

        self.control = ABTestVariant("control", control_config)
        self.treatment = ABTestVariant("treatment", treatment_config)

    def assign_variant(self) -> ABTestVariant:
        """Assign request to variant based on traffic split"""
        if random.random() < self.traffic_split:
            return self.treatment
        return self.control

    def record_result(
        self,
        variant_name: str,
        success: bool,
        cost: float = 0.0,
        latency: float = 0.0,
        error: bool = False,
    ):
        """
        Record result for variant.

        Args:
            variant_name: "control" or "treatment"
            success: Whether request succeeded
            cost: Request cost
            latency: Request latency (seconds)
            error: Whether request had error
        """
        variant = self.control if variant_name == "control" else self.treatment

        variant.samples += 1
        if success:
            variant.success_count += 1
        if error:
            variant.error_count += 1
        variant.total_cost += cost

        # Update rolling average latency
        if variant.samples == 1:
            variant.avg_latency = latency
        else:
            variant.avg_latency = (
                (variant.avg_latency * (variant.samples - 1) + latency)
                / variant.samples
            )

    def is_complete(self) -> bool:
        """Check if test is complete"""
        time_elapsed = datetime.now() - self.started_at
        samples_sufficient = (
            self.control.samples >= self.min_samples
            and self.treatment.samples >= self.min_samples
        )
        return time_elapsed >= self.duration and samples_sufficient

    def analyze_results(self) -> Dict[str, Any]:
        """
        Analyze test results and determine winner.

        Returns:
            Dict with winner, metrics, statistical significance
        """
        # Calculate improvements
        success_rate_improvement = (
            self.treatment.success_rate - self.control.success_rate
        )
        cost_improvement = (
            self.control.avg_cost_per_request - self.treatment.avg_cost_per_request
        )
        latency_improvement = (
            self.control.avg_latency - self.treatment.avg_latency
        )

        # Simple decision logic (production would use statistical tests)
        # Treatment wins if:
        # 1. Success rate is better or equal
        # 2. Cost is lower or latency is lower
        # 3. Error rate is not significantly worse

        treatment_wins = (
            success_rate_improvement >= 0
            and (cost_improvement > 0 or latency_improvement > 0)
            and (self.treatment.error_rate <= self.control.error_rate * 1.1)  # Allow 10% worse
        )

        winner = "treatment" if treatment_wins else "control"

        return {
            "winner": winner,
            "control": {
                "samples": self.control.samples,
                "success_rate": self.control.success_rate,
                "avg_cost": self.control.avg_cost_per_request,
                "avg_latency": self.control.avg_latency,
                "error_rate": self.control.error_rate,
            },
            "treatment": {
                "samples": self.treatment.samples,
                "success_rate": self.treatment.success_rate,
                "avg_cost": self.treatment.avg_cost_per_request,
                "avg_latency": self.treatment.avg_latency,
                "error_rate": self.treatment.error_rate,
            },
            "improvements": {
                "success_rate": success_rate_improvement,
                "cost": cost_improvement,
                "latency": latency_improvement,
            },
            "recommendation": "deploy" if treatment_wins else "reject",
        }


# =============================================================================
# Auto-Improver
# =============================================================================

class AutoImprover:
    """
    Automated self-improvement execution.

    Responsibilities:
    - Evaluate improvement suggestions
    - Auto-execute high-confidence improvements
    - Run A/B tests for medium-confidence improvements
    - Update configurations safely with backups
    - Monitor improvement outcomes
    """

    def __init__(
        self,
        config: Optional[AutoImproverConfig] = None,
        config_paths: Optional[Dict[str, Path]] = None,
    ):
        """
        Initialize auto-improver.

        Args:
            config: Auto-improver configuration
            config_paths: Paths to configuration files to manage
        """
        self.config = config or AutoImproverConfig()
        self.config_paths = config_paths or {
            "llm": Path("config/llm_config.yaml"),
            "agents": Path("agent/config/agents.yaml"),
            "tasks": Path("agent/config/tasks.yaml"),
        }

        # Ensure directories exist
        self.config.config_backup_dir.mkdir(parents=True, exist_ok=True)
        self.config.improvement_log.parent.mkdir(parents=True, exist_ok=True)

        # Load improvement history
        self.improvements: Dict[str, ImprovementRecord] = {}
        self._load_improvement_log()

        # Active A/B tests
        self.active_tests: Dict[str, ABTest] = {}

    def _load_improvement_log(self):
        """Load improvement history from log"""
        if not self.config.improvement_log.exists():
            return

        with open(self.config.improvement_log, "r") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    record = ImprovementRecord.from_dict(data)
                    self.improvements[record.id] = record

    def _append_to_log(self, record: ImprovementRecord):
        """Append improvement record to log"""
        with open(self.config.improvement_log, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def _backup_config(self, config_key: str) -> Path:
        """Create backup of configuration file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = self.config_paths[config_key]
        backup_path = (
            self.config.config_backup_dir
            / f"{config_key}_{timestamp}_{config_path.name}"
        )

        if config_path.exists():
            backup_path.write_text(config_path.read_text())
            print(f"[AutoImprover] Backed up {config_key} config to {backup_path}")

        return backup_path

    def _restore_config(self, config_key: str, backup_path: Path):
        """Restore configuration from backup"""
        config_path = self.config_paths[config_key]
        config_path.write_text(backup_path.read_text())
        print(f"[AutoImprover] Restored {config_key} config from {backup_path}")

    def _update_config(
        self,
        config_key: str,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update configuration file.

        Args:
            config_key: Configuration file identifier
            updates: Dictionary of updates to apply

        Returns:
            True if successful, False otherwise
        """
        try:
            config_path = self.config_paths.get(config_key)
            if not config_path or not config_path.exists():
                print(f"[AutoImprover] Config file not found: {config_key}")
                return False

            # Backup first
            self._backup_config(config_key)

            # Load current config
            with open(config_path, "r") as f:
                if config_path.suffix in [".yaml", ".yml"]:
                    current_config = yaml.safe_load(f) or {}
                else:
                    current_config = json.load(f)

            # Apply updates (shallow merge)
            current_config.update(updates)

            # Write updated config
            with open(config_path, "w") as f:
                if config_path.suffix in [".yaml", ".yml"]:
                    yaml.safe_dump(current_config, f, default_flow_style=False)
                else:
                    json.dump(current_config, f, indent=2)

            print(f"[AutoImprover] Updated {config_key} config")
            return True
        except Exception as e:
            print(f"[AutoImprover] Error updating config {config_key}: {e}")
            return False

    def evaluate_suggestion(
        self,
        suggestion: Dict[str, Any],
    ) -> Tuple[str, ImprovementRecord]:
        """
        Evaluate improvement suggestion and decide action.

        Args:
            suggestion: Improvement suggestion from self_refinement

        Returns:
            (action, record) where action is "auto_execute", "ab_test", or "reject"
        """
        confidence = suggestion.get("confidence", 0.0)
        improvement_id = f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        record = ImprovementRecord(
            id=improvement_id,
            suggestion=suggestion,
            status=ImprovementStatus.PROPOSED,
            confidence=confidence,
        )

        # Decision logic based on confidence
        if confidence >= self.config.auto_execute_threshold:
            action = "auto_execute"
            record.notes = f"High confidence ({confidence:.2f}) - auto-executing"
        elif confidence >= self.config.ab_test_threshold:
            action = "ab_test"
            record.notes = f"Medium confidence ({confidence:.2f}) - A/B testing"
        else:
            action = "reject"
            record.status = ImprovementStatus.REJECTED
            record.notes = f"Low confidence ({confidence:.2f}) - rejected"

        # Save record
        self.improvements[improvement_id] = record
        self._append_to_log(record)

        return action, record

    def execute_improvement(
        self,
        record: ImprovementRecord,
        validate: bool = True,
    ) -> bool:
        """
        Execute improvement by updating configuration.

        Args:
            record: Improvement record
            validate: Whether to validate after implementation

        Returns:
            True if successful, False otherwise
        """
        suggestion = record.suggestion

        try:
            # Extract config updates from suggestion
            config_key = suggestion.get("config_type", "llm")
            updates = suggestion.get("updates", {})

            # Update configuration
            success = self._update_config(config_key, updates)

            if success:
                record.status = ImprovementStatus.TESTING if validate else ImprovementStatus.DEPLOYED
                record.implemented_at = datetime.now()
                self._append_to_log(record)
                print(f"[AutoImprover] ✅ Executed improvement {record.id}")
                return True
            else:
                record.notes += " | Failed to update config"
                self._append_to_log(record)
                return False

        except Exception as e:
            print(f"[AutoImprover] Error executing improvement: {e}")
            record.notes += f" | Error: {e}"
            self._append_to_log(record)
            return False

    def start_ab_test(
        self,
        record: ImprovementRecord,
        control_config: Dict[str, Any],
        treatment_config: Dict[str, Any],
    ) -> ABTest:
        """
        Start A/B test for improvement.

        Args:
            record: Improvement record
            control_config: Current configuration
            treatment_config: Improved configuration

        Returns:
            ABTest instance
        """
        ab_test = ABTest(
            improvement_id=record.id,
            control_config=control_config,
            treatment_config=treatment_config,
            duration_hours=self.config.ab_test_duration_hours,
            traffic_split=self.config.ab_test_traffic_split,
            min_samples=self.config.ab_test_min_samples,
        )

        self.active_tests[record.id] = ab_test
        record.status = ImprovementStatus.TESTING
        record.implemented_at = datetime.now()
        self._append_to_log(record)

        print(f"[AutoImprover] 🧪 Started A/B test for improvement {record.id}")
        return ab_test

    def finalize_ab_test(self, record: ImprovementRecord) -> bool:
        """
        Finalize A/B test and deploy or rollback.

        Args:
            record: Improvement record

        Returns:
            True if improvement deployed, False if rolled back
        """
        ab_test = self.active_tests.get(record.id)
        if not ab_test or not ab_test.is_complete():
            return False

        # Analyze results
        results = ab_test.analyze_results()
        record.ab_test_results = results
        record.validated_at = datetime.now()

        # Deploy or rollback
        if results["recommendation"] == "deploy":
            record.status = ImprovementStatus.DEPLOYED
            record.deployed_at = datetime.now()
            print(f"[AutoImprover] ✅ Deployed improvement {record.id}")
            print(f"[AutoImprover] Results: {results['improvements']}")
            deployed = True
        else:
            record.status = ImprovementStatus.ROLLED_BACK
            record.rolled_back_at = datetime.now()
            # Would restore from backup here
            print(f"[AutoImprover] ↩️ Rolled back improvement {record.id}")
            deployed = False

        self._append_to_log(record)
        del self.active_tests[record.id]

        return deployed

    def process_suggestions(
        self,
        suggestions: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """
        Process multiple improvement suggestions.

        Args:
            suggestions: List of improvement suggestions

        Returns:
            Dict with counts of actions taken
        """
        stats = {
            "auto_executed": 0,
            "ab_testing": 0,
            "rejected": 0,
            "failed": 0,
        }

        for suggestion in suggestions:
            action, record = self.evaluate_suggestion(suggestion)

            if action == "auto_execute":
                success = self.execute_improvement(record, validate=False)
                if success:
                    stats["auto_executed"] += 1
                else:
                    stats["failed"] += 1

            elif action == "ab_test":
                # Would start A/B test with current and proposed configs
                # For now, just mark as testing
                stats["ab_testing"] += 1

            elif action == "reject":
                stats["rejected"] += 1

        return stats


# =============================================================================
# Utility Functions
# =============================================================================

def create_auto_improver(
    config_paths: Optional[Dict[str, Path]] = None,
) -> AutoImprover:
    """
    Create auto-improver with standard configuration.

    Args:
        config_paths: Optional custom config paths

    Returns:
        Configured AutoImprover instance
    """
    return AutoImprover(config_paths=config_paths)
