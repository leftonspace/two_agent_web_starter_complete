"""
PHASE 7.4: Pool Manager

Central manager for all domain pools. Provides access to specialists
across domains and handles pool lifecycle.

Usage:
    from core.specialists import PoolManager, SelectionMode

    manager = PoolManager()

    # Get or create a pool
    pool = manager.get_pool("code_review")

    # Select from pool
    specialist = pool.select(SelectionMode.WEIGHTED)

    # Get JARVIS (best administration specialist)
    jarvis = manager.get_jarvis()
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from .pool import DomainPool, NoSpecialistsError, SelectionMode
from .specialist import Specialist, SpecialistStatus


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Singleton Instance
# ============================================================================


_pool_manager: Optional["PoolManager"] = None


def get_pool_manager() -> "PoolManager":
    """Get the global pool manager instance."""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = PoolManager()
    return _pool_manager


def reset_pool_manager() -> None:
    """Reset the global pool manager (for testing)."""
    global _pool_manager
    _pool_manager = None


# ============================================================================
# Pool Manager
# ============================================================================


class PoolManager:
    """
    Manages all domain pools in the system.

    Provides a centralized interface for:
    - Creating and retrieving pools
    - Selecting specialists across domains
    - Managing JARVIS (the administration specialist)
    - Auto-discovering domains from config files
    """

    # Default domains that should always exist
    DEFAULT_DOMAINS = [
        "administration",  # JARVIS domain
        "code_generation",
        "code_review",
        "research",
        "planning",
    ]

    # JARVIS domain name
    JARVIS_DOMAIN = "administration"

    def __init__(
        self,
        config_path: Optional[str] = None,
        use_database: bool = False,
    ):
        """
        Initialize the pool manager.

        Args:
            config_path: Path to domain configs (default: config/domains/)
            use_database: Whether to persist to database
        """
        self._pools: Dict[str, DomainPool] = {}
        self._config_path = config_path or "config/domains"
        self._use_database = use_database
        self._initialized_at = datetime.utcnow()

        # Initialize default pools
        self._ensure_default_pools()

        logger.info(f"PoolManager initialized with {len(self._pools)} pools")

    def _ensure_default_pools(self) -> None:
        """Ensure default domain pools exist."""
        for domain in self.DEFAULT_DOMAINS:
            if domain not in self._pools:
                self._pools[domain] = DomainPool(domain=domain)

    # -------------------------------------------------------------------------
    # Pool Access
    # -------------------------------------------------------------------------

    def get_pool(self, domain: str) -> DomainPool:
        """
        Get pool for a domain, creating if necessary.

        Args:
            domain: Domain name

        Returns:
            DomainPool for the domain
        """
        if domain not in self._pools:
            self._pools[domain] = DomainPool(domain=domain)
            logger.info(f"Created new pool for domain: {domain}")

        return self._pools[domain]

    def create_pool(self, domain: str, max_size: int = 3) -> DomainPool:
        """
        Create a new pool for a domain.

        Args:
            domain: Domain name
            max_size: Maximum specialists in pool

        Returns:
            New DomainPool
        """
        if domain in self._pools:
            logger.warning(f"Pool for {domain} already exists")
            return self._pools[domain]

        pool = DomainPool(domain=domain, max_size=max_size)
        self._pools[domain] = pool
        logger.info(f"Created pool for {domain} (max_size={max_size})")

        return pool

    def list_pools(self) -> List[DomainPool]:
        """List all pools."""
        return list(self._pools.values())

    def list_domains(self) -> List[str]:
        """List all domain names."""
        return list(self._pools.keys())

    def has_pool(self, domain: str) -> bool:
        """Check if pool exists for domain."""
        return domain in self._pools

    def remove_pool(self, domain: str) -> Optional[DomainPool]:
        """
        Remove a pool (specialists are not deleted).

        Args:
            domain: Domain to remove

        Returns:
            Removed pool or None if not found
        """
        if domain in self._pools:
            pool = self._pools.pop(domain)
            logger.info(f"Removed pool for {domain}")
            return pool
        return None

    # -------------------------------------------------------------------------
    # JARVIS Access
    # -------------------------------------------------------------------------

    def get_jarvis(self) -> Optional[Specialist]:
        """
        Get JARVIS - the best administration specialist.

        Returns:
            Best specialist from administration pool, or None if empty
        """
        pool = self.get_pool(self.JARVIS_DOMAIN)
        return pool.get_best()

    def get_jarvis_or_raise(self) -> Specialist:
        """
        Get JARVIS, raising if not available.

        Returns:
            JARVIS specialist

        Raises:
            NoSpecialistsError: If no JARVIS available
        """
        jarvis = self.get_jarvis()
        if jarvis is None:
            raise NoSpecialistsError(self.JARVIS_DOMAIN)
        return jarvis

    def is_jarvis(self, specialist: Specialist) -> bool:
        """Check if specialist is currently JARVIS."""
        jarvis = self.get_jarvis()
        if jarvis is None:
            return False
        return specialist.id == jarvis.id

    # -------------------------------------------------------------------------
    # Cross-Pool Operations
    # -------------------------------------------------------------------------

    def select_specialist(
        self,
        domain: str,
        mode: SelectionMode = SelectionMode.WEIGHTED,
        specialist_id: Optional[UUID] = None,
    ) -> Specialist:
        """
        Select a specialist from a domain pool.

        Args:
            domain: Domain to select from
            mode: Selection mode
            specialist_id: Specific specialist ID (for SPECIFIC mode)

        Returns:
            Selected specialist
        """
        pool = self.get_pool(domain)
        return pool.select(mode=mode, specialist_id=specialist_id)

    def get_all_specialists(
        self,
        status: Optional[SpecialistStatus] = None,
    ) -> List[Specialist]:
        """
        Get all specialists across all pools.

        Args:
            status: Filter by status (optional)

        Returns:
            List of specialists
        """
        specialists = []
        for pool in self._pools.values():
            for s in pool.specialists:
                if status is None or s.status == status:
                    specialists.append(s)
        return specialists

    def find_specialist(self, specialist_id: UUID) -> Optional[Specialist]:
        """
        Find a specialist by ID across all pools.

        Args:
            specialist_id: Specialist ID

        Returns:
            Specialist if found, None otherwise
        """
        for pool in self._pools.values():
            specialist = pool.get_specialist(specialist_id)
            if specialist:
                return specialist
        return None

    def get_specialist_pool(self, specialist_id: UUID) -> Optional[DomainPool]:
        """
        Get the pool containing a specialist.

        Args:
            specialist_id: Specialist ID

        Returns:
            DomainPool if found, None otherwise
        """
        for pool in self._pools.values():
            if pool.get_specialist(specialist_id):
                return pool
        return None

    # -------------------------------------------------------------------------
    # Pool Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics across all pools."""
        total_specialists = 0
        total_tasks = 0
        total_selections = 0
        domain_stats = []

        for pool in self._pools.values():
            pool_specialists = len(pool.specialists)
            pool_tasks = sum(s.performance.task_count for s in pool.specialists)

            total_specialists += pool_specialists
            total_tasks += pool_tasks
            total_selections += pool.selection_count

            domain_stats.append({
                "domain": pool.domain,
                "specialists": pool_specialists,
                "tasks": pool_tasks,
                "selections": pool.selection_count,
                "generation": pool.generation,
                "is_jarvis_domain": pool.is_jarvis_domain(),
            })

        return {
            "total_pools": len(self._pools),
            "total_specialists": total_specialists,
            "total_tasks": total_tasks,
            "total_selections": total_selections,
            "initialized_at": self._initialized_at.isoformat(),
            "domains": domain_stats,
        }

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top specialists across all domains.

        Args:
            limit: Maximum entries to return

        Returns:
            List of specialist summaries ordered by score
        """
        all_specialists = self.get_all_specialists(status=SpecialistStatus.ACTIVE)
        all_specialists.extend(
            self.get_all_specialists(status=SpecialistStatus.PROBATION)
        )

        # Sort by average score
        all_specialists.sort(
            key=lambda s: s.performance.avg_score,
            reverse=True,
        )

        return [
            {
                "rank": i + 1,
                "name": s.name,
                "domain": s.domain,
                "avg_score": round(s.performance.avg_score, 3),
                "task_count": s.performance.task_count,
                "status": s.status.value,
                "is_jarvis": self.is_jarvis(s),
            }
            for i, s in enumerate(all_specialists[:limit])
        ]

    # -------------------------------------------------------------------------
    # Auto-Discovery
    # -------------------------------------------------------------------------

    def auto_discover_domains(self) -> List[str]:
        """
        Auto-discover domains from config files.

        Looks for YAML files in config/domains/ directory.
        Each file represents a domain configuration.

        Returns:
            List of discovered domain names
        """
        discovered = []
        config_dir = Path(self._config_path)

        if not config_dir.exists():
            logger.debug(f"Domain config directory not found: {config_dir}")
            return discovered

        # Look for YAML files
        for config_file in config_dir.glob("*.yaml"):
            domain = config_file.stem
            if domain not in self._pools:
                self._pools[domain] = DomainPool(domain=domain)
                discovered.append(domain)
                logger.info(f"Auto-discovered domain: {domain}")

        # Also check .yml extension
        for config_file in config_dir.glob("*.yml"):
            domain = config_file.stem
            if domain not in self._pools:
                self._pools[domain] = DomainPool(domain=domain)
                discovered.append(domain)
                logger.info(f"Auto-discovered domain: {domain}")

        return discovered

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            "pools": {
                domain: pool.to_summary()
                for domain, pool in self._pools.items()
            },
            "stats": self.get_stats(),
        }

    def load_from_database(self) -> None:
        """Load pools and specialists from database."""
        if not self._use_database:
            return

        try:
            from database import get_session
            from database.models import SpecialistDB
            from database.models.domain_pool import DomainPoolDB

            with get_session() as session:
                # Load pools
                pool_rows = session.query(DomainPoolDB).all()
                for pool_row in pool_rows:
                    pool_dict = pool_row.to_dict()

                    # Load specialists for this pool
                    specialist_rows = (
                        session.query(SpecialistDB)
                        .filter(SpecialistDB.domain == pool_row.domain)
                        .filter(SpecialistDB.status.in_(["active", "probation"]))
                        .all()
                    )

                    specialists = [
                        Specialist.from_db_row(row.to_dict())
                        for row in specialist_rows
                    ]

                    pool = DomainPool.from_db_row(pool_dict, specialists)
                    self._pools[pool.domain] = pool

                logger.info(f"Loaded {len(pool_rows)} pools from database")

        except ImportError:
            logger.warning("Database models not available for loading")
        except Exception as e:
            logger.error(f"Failed to load from database: {e}")

    def save_to_database(self) -> None:
        """Save pools to database."""
        if not self._use_database:
            return

        try:
            from database import get_session
            from database.models.domain_pool import DomainPoolDB

            with get_session() as session:
                for pool in self._pools.values():
                    pool_dict = pool.to_db_dict()

                    # Upsert pool
                    existing = (
                        session.query(DomainPoolDB)
                        .filter(DomainPoolDB.domain == pool.domain)
                        .first()
                    )

                    if existing:
                        # Update
                        for key, value in pool_dict.items():
                            if key != "id":
                                setattr(existing, key, value)
                    else:
                        # Insert
                        new_pool = DomainPoolDB.from_dict(pool_dict)
                        session.add(new_pool)

                session.commit()
                logger.info(f"Saved {len(self._pools)} pools to database")

        except ImportError:
            logger.warning("Database models not available for saving")
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
