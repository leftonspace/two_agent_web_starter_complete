"""
Rollback and Deployment Safety System

Provides:
- State snapshots before changes
- Automated rollback on failures
- Canary deployments for gradual rollouts
- Health monitoring and automatic recovery
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Configuration
# =============================================================================

class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class DeploymentStrategy(Enum):
    """Deployment strategy"""
    ALL_AT_ONCE = "all_at_once"  # Immediate full deployment
    CANARY = "canary"  # Gradual rollout with monitoring
    BLUE_GREEN = "blue_green"  # Two environments, instant switch


@dataclass
class SnapshotConfig:
    """Configuration for state snapshots"""
    snapshot_dir: Path = Path(".jarvis/snapshots")
    max_snapshots: int = 10  # Keep last 10 snapshots
    compress: bool = True
    include_patterns: List[str] = field(default_factory=lambda: [
        "config/**/*.yaml",
        "config/**/*.json",
        "agent/config/**/*.yaml",
        ".jarvis/improvements.jsonl",
        ".jarvis/memory.db",
    ])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "**/__pycache__/**",
        "**/*.pyc",
        "**/.git/**",
        "**/node_modules/**",
    ])


# =============================================================================
# State Snapshot
# =============================================================================

@dataclass
class StateSnapshot:
    """
    State snapshot for rollback.

    Captures:
    - Configuration files
    - Memory databases
    - Improvement logs
    - Model configurations
    - Checksums for integrity
    """

    id: str
    timestamp: datetime
    description: str
    snapshot_path: Path
    files: Dict[str, str]  # file_path -> checksum
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "snapshot_path": str(self.snapshot_path),
            "files": self.files,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StateSnapshot:
        """Create from dictionary"""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            description=data["description"],
            snapshot_path=Path(data["snapshot_path"]),
            files=data["files"],
            metadata=data.get("metadata", {}),
        )

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """
        Verify snapshot integrity.

        Returns:
            (valid, errors) tuple
        """
        errors = []

        for file_path, expected_checksum in self.files.items():
            snapshot_file = self.snapshot_path / file_path
            if not snapshot_file.exists():
                errors.append(f"Missing file: {file_path}")
                continue

            actual_checksum = self._compute_checksum(snapshot_file)
            if actual_checksum != expected_checksum:
                errors.append(f"Checksum mismatch: {file_path}")

        return len(errors) == 0, errors

    @staticmethod
    def _compute_checksum(file_path: Path) -> str:
        """Compute SHA-256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


# =============================================================================
# Rollback Manager
# =============================================================================

class RollbackManager:
    """
    Manages state snapshots and rollbacks.

    Usage:
        rollback = RollbackManager()

        # Before making changes
        snapshot = rollback.create_snapshot("Before prompt optimization")

        # Make changes...
        update_configs()

        # If something goes wrong
        if metrics_degraded():
            rollback.restore_snapshot(snapshot.id)
    """

    def __init__(
        self,
        config: Optional[SnapshotConfig] = None,
        workspace_root: Optional[Path] = None,
    ):
        """
        Initialize rollback manager.

        Args:
            config: Snapshot configuration
            workspace_root: Root directory of workspace
        """
        self.config = config or SnapshotConfig()
        self.workspace_root = workspace_root or Path.cwd()

        # Ensure snapshot directory exists
        self.config.snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Snapshot database
        self.db_path = self.config.snapshot_dir / "snapshots.db"
        self._init_database()

    def _init_database(self):
        """Initialize snapshot tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                description TEXT,
                snapshot_path TEXT NOT NULL,
                files TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

    def create_snapshot(
        self,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateSnapshot:
        """
        Create state snapshot.

        Args:
            description: Snapshot description
            metadata: Optional metadata

        Returns:
            StateSnapshot object
        """
        snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        timestamp = datetime.now()

        # Create snapshot directory
        snapshot_path = self.config.snapshot_dir / snapshot_id
        snapshot_path.mkdir(parents=True, exist_ok=True)

        # Copy files and compute checksums
        files_with_checksums = {}

        for pattern in self.config.include_patterns:
            for file_path in self.workspace_root.glob(pattern):
                if file_path.is_file() and self._should_include(file_path):
                    relative_path = file_path.relative_to(self.workspace_root)
                    dest_path = snapshot_path / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    shutil.copy2(file_path, dest_path)

                    # Compute checksum
                    checksum = StateSnapshot._compute_checksum(dest_path)
                    files_with_checksums[str(relative_path)] = checksum

        # Create snapshot object
        snapshot = StateSnapshot(
            id=snapshot_id,
            timestamp=timestamp,
            description=description,
            snapshot_path=snapshot_path,
            files=files_with_checksums,
            metadata=metadata or {},
        )

        # Save to database
        self._save_snapshot(snapshot)

        print(f"[Rollback] Created snapshot: {snapshot_id}")
        print(f"[Rollback] Files: {len(files_with_checksums)}")

        # Cleanup old snapshots
        self._cleanup_old_snapshots()

        return snapshot

    def _should_include(self, file_path: Path) -> bool:
        """Check if file should be included in snapshot"""
        file_str = str(file_path)
        for pattern in self.config.exclude_patterns:
            if Path(file_str).match(pattern):
                return False
        return True

    def _save_snapshot(self, snapshot: StateSnapshot):
        """Save snapshot to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """INSERT OR REPLACE INTO snapshots
               (id, timestamp, description, snapshot_path, files, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot.id,
                snapshot.timestamp.isoformat(),
                snapshot.description,
                str(snapshot.snapshot_path),
                json.dumps(snapshot.files),
                json.dumps(snapshot.metadata),
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

    def get_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """Get snapshot by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM snapshots WHERE id = ?",
            (snapshot_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return StateSnapshot(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            description=row[2],
            snapshot_path=Path(row[3]),
            files=json.loads(row[4]),
            metadata=json.loads(row[5]) if row[5] else {},
        )

    def list_snapshots(self, limit: int = 10) -> List[StateSnapshot]:
        """List recent snapshots"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()

        snapshots = []
        for row in rows:
            snapshots.append(StateSnapshot(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                description=row[2],
                snapshot_path=Path(row[3]),
                files=json.loads(row[4]),
                metadata=json.loads(row[5]) if row[5] else {},
            ))

        return snapshots

    def restore_snapshot(
        self,
        snapshot_id: str,
        verify: bool = True,
    ) -> bool:
        """
        Restore from snapshot.

        Args:
            snapshot_id: Snapshot ID to restore
            verify: Verify integrity before restore

        Returns:
            True if successful, False otherwise
        """
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            print(f"[Rollback] Snapshot not found: {snapshot_id}")
            return False

        # Verify integrity
        if verify:
            valid, errors = snapshot.verify_integrity()
            if not valid:
                print(f"[Rollback] Snapshot integrity check failed:")
                for error in errors:
                    print(f"[Rollback]   - {error}")
                return False

        print(f"[Rollback] Restoring snapshot: {snapshot_id}")
        print(f"[Rollback] Description: {snapshot.description}")

        # Restore files
        restored_count = 0
        failed_count = 0

        for file_path in snapshot.files.keys():
            source = snapshot.snapshot_path / file_path
            dest = self.workspace_root / file_path

            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                restored_count += 1
            except Exception as e:
                print(f"[Rollback] Failed to restore {file_path}: {e}")
                failed_count += 1

        print(f"[Rollback] Restored {restored_count} files ({failed_count} failed)")

        return failed_count == 0

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot"""
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            return False

        # Delete snapshot directory
        if snapshot.snapshot_path.exists():
            shutil.rmtree(snapshot.snapshot_path)

        # Delete from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))
        conn.commit()
        conn.close()

        print(f"[Rollback] Deleted snapshot: {snapshot_id}")
        return True

    def _cleanup_old_snapshots(self):
        """Remove old snapshots beyond max_snapshots limit"""
        snapshots = self.list_snapshots(limit=1000)  # Get all

        if len(snapshots) > self.config.max_snapshots:
            # Delete oldest snapshots
            to_delete = snapshots[self.config.max_snapshots:]
            for snapshot in to_delete:
                self.delete_snapshot(snapshot.id)


# =============================================================================
# Canary Deployment
# =============================================================================

@dataclass
class CanaryConfig:
    """Canary deployment configuration"""
    initial_traffic: float = 0.1  # Start with 10%
    increment_traffic: float = 0.2  # Increase by 20% each stage
    stage_duration_minutes: int = 30  # 30 minutes per stage
    health_check_interval: int = 60  # Check every minute
    rollback_on_error_rate: float = 0.05  # Rollback if 5% error rate
    rollback_on_latency_increase: float = 0.2  # Rollback if 20% latency increase


class CanaryDeployment:
    """
    Canary deployment with gradual traffic rollout.

    Usage:
        canary = CanaryDeployment(rollback_manager)

        # Start canary deployment
        deployment_id = canary.start(
            description="New model routing logic",
            new_config=improved_config
        )

        # Monitor and adjust traffic
        while canary.is_active(deployment_id):
            metrics = get_current_metrics()
            canary.record_metrics(deployment_id, metrics)

            if canary.should_proceed(deployment_id):
                canary.increase_traffic(deployment_id)
            elif canary.should_rollback(deployment_id):
                canary.rollback(deployment_id)

            time.sleep(60)
    """

    def __init__(
        self,
        rollback_manager: RollbackManager,
        config: Optional[CanaryConfig] = None,
    ):
        """
        Initialize canary deployment.

        Args:
            rollback_manager: Rollback manager for snapshots
            config: Canary configuration
        """
        self.rollback = rollback_manager
        self.config = config or CanaryConfig()

        # Active deployments
        self.deployments: Dict[str, Dict[str, Any]] = {}

    def start(
        self,
        description: str,
        new_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Start canary deployment.

        Args:
            description: Deployment description
            new_config: New configuration to deploy
            metadata: Optional metadata

        Returns:
            Deployment ID
        """
        # Create snapshot before deployment
        snapshot = self.rollback.create_snapshot(
            description=f"Before canary: {description}",
            metadata=metadata,
        )

        deployment_id = f"canary_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        self.deployments[deployment_id] = {
            "description": description,
            "snapshot_id": snapshot.id,
            "new_config": new_config,
            "status": DeploymentStatus.IN_PROGRESS,
            "current_traffic": self.config.initial_traffic,
            "stage": 0,
            "started_at": datetime.now(),
            "stage_started_at": datetime.now(),
            "baseline_metrics": {},
            "current_metrics": {},
            "metadata": metadata or {},
        }

        print(f"[Canary] Started deployment: {deployment_id}")
        print(f"[Canary] Initial traffic: {self.config.initial_traffic * 100}%")

        return deployment_id

    def is_active(self, deployment_id: str) -> bool:
        """Check if deployment is active"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False

        return deployment["status"] == DeploymentStatus.IN_PROGRESS

    def record_metrics(
        self,
        deployment_id: str,
        metrics: Dict[str, float],
    ):
        """
        Record current metrics for deployment.

        Args:
            deployment_id: Deployment ID
            metrics: Current metrics (error_rate, avg_latency, etc.)
        """
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return

        # Store baseline on first record
        if not deployment["baseline_metrics"]:
            deployment["baseline_metrics"] = metrics.copy()

        deployment["current_metrics"] = metrics

    def should_proceed(self, deployment_id: str) -> bool:
        """Check if deployment should proceed to next stage"""
        deployment = self.deployments.get(deployment_id)
        if not deployment or deployment["status"] != DeploymentStatus.IN_PROGRESS:
            return False

        # Check if stage duration met
        time_in_stage = datetime.now() - deployment["stage_started_at"]
        stage_duration = timedelta(minutes=self.config.stage_duration_minutes)

        if time_in_stage < stage_duration:
            return False

        # Check if metrics are healthy
        if self._metrics_degraded(deployment):
            return False

        return True

    def should_rollback(self, deployment_id: str) -> bool:
        """Check if deployment should be rolled back"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False

        return self._metrics_degraded(deployment)

    def _metrics_degraded(self, deployment: Dict[str, Any]) -> bool:
        """Check if metrics have degraded"""
        baseline = deployment["baseline_metrics"]
        current = deployment["current_metrics"]

        if not baseline or not current:
            return False

        # Check error rate
        if current.get("error_rate", 0) > self.config.rollback_on_error_rate:
            print(f"[Canary] Error rate too high: {current['error_rate']}")
            return True

        # Check latency increase
        baseline_latency = baseline.get("avg_latency", 0)
        current_latency = current.get("avg_latency", 0)

        if baseline_latency > 0:
            latency_increase = (current_latency - baseline_latency) / baseline_latency
            if latency_increase > self.config.rollback_on_latency_increase:
                print(f"[Canary] Latency increased too much: {latency_increase * 100}%")
                return True

        return False

    def increase_traffic(self, deployment_id: str) -> bool:
        """Increase traffic to canary"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False

        new_traffic = min(
            1.0,
            deployment["current_traffic"] + self.config.increment_traffic
        )

        deployment["current_traffic"] = new_traffic
        deployment["stage"] += 1
        deployment["stage_started_at"] = datetime.now()

        print(f"[Canary] Increased traffic to {new_traffic * 100}%")

        # If at 100%, deployment is complete
        if new_traffic >= 1.0:
            deployment["status"] = DeploymentStatus.HEALTHY
            print(f"[Canary] ✅ Deployment complete: {deployment_id}")

        return True

    def rollback(self, deployment_id: str) -> bool:
        """Rollback canary deployment"""
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return False

        snapshot_id = deployment["snapshot_id"]
        success = self.rollback.restore_snapshot(snapshot_id)

        if success:
            deployment["status"] = DeploymentStatus.ROLLED_BACK
            print(f"[Canary] ↩️ Rolled back deployment: {deployment_id}")
        else:
            deployment["status"] = DeploymentStatus.FAILED
            print(f"[Canary] ❌ Rollback failed: {deployment_id}")

        return success


# =============================================================================
# Utility Functions
# =============================================================================

def create_rollback_manager(
    workspace_root: Optional[Path] = None,
) -> RollbackManager:
    """
    Create rollback manager with standard configuration.

    Args:
        workspace_root: Root directory of workspace

    Returns:
        Configured RollbackManager
    """
    return RollbackManager(workspace_root=workspace_root)


def quick_snapshot(description: str) -> StateSnapshot:
    """Quick helper to create a snapshot"""
    rollback = create_rollback_manager()
    return rollback.create_snapshot(description)


def quick_restore(snapshot_id: str) -> bool:
    """Quick helper to restore a snapshot"""
    rollback = create_rollback_manager()
    return rollback.restore_snapshot(snapshot_id)
