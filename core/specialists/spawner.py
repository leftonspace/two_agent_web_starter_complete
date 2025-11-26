"""
PHASE 7.4: Specialist Spawner

Creates new specialists with optional mutations and learnings from the graveyard.
Specialists inherit lessons from failed predecessors to avoid repeating mistakes.

Usage:
    from core.specialists import Spawner, get_spawner

    spawner = get_spawner()

    # Create from domain template
    specialist = spawner.spawn_initial("code_generation")

    # Create with graveyard learnings
    learnings = get_graveyard_learnings("code_generation")
    specialist = spawner.spawn_with_learnings("code_generation", learnings)

    # Clone best performer with mutations
    specialist = spawner.spawn_from_best("code_generation")
"""

from __future__ import annotations

import logging
import random
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .specialist import (
    Specialist,
    SpecialistConfig,
    SpecialistStatus,
)
from .domain_config import (
    DomainConfig,
    DomainConfigLoader,
    get_domain_loader,
)
from .pool import DomainPool
from .pool_manager import PoolManager, get_pool_manager


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Models
# ============================================================================


class MutationType(str, Enum):
    """Types of mutations that can be applied to specialist configs."""
    TEMPERATURE = "temperature"
    PROMPT_ADDITION = "prompt_addition"
    PROMPT_EMPHASIS = "prompt_emphasis"
    TOOL_ADJUSTMENT = "tool_adjustment"
    RETRY_ADJUSTMENT = "retry_adjustment"


class LearningType(str, Enum):
    """Types of learnings from the graveyard."""
    AVOIDANCE = "avoidance"      # Things to NOT do
    ENHANCEMENT = "enhancement"  # Things to ALWAYS do
    TECHNIQUE = "technique"      # Specific techniques that worked


class Learning(BaseModel):
    """A learning extracted from graveyard specialists."""

    type: LearningType = Field(
        ...,
        description="Type of learning",
    )
    instruction: str = Field(
        ...,
        min_length=1,
        description="The learning instruction",
    )
    source_specialist_id: Optional[str] = Field(
        default=None,
        description="ID of specialist this came from",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence in this learning (based on evidence)",
    )
    domain: str = Field(
        default="",
        description="Domain this learning applies to",
    )

    @classmethod
    def avoidance(cls, instruction: str, **kwargs) -> "Learning":
        """Create an avoidance learning."""
        return cls(type=LearningType.AVOIDANCE, instruction=instruction, **kwargs)

    @classmethod
    def enhancement(cls, instruction: str, **kwargs) -> "Learning":
        """Create an enhancement learning."""
        return cls(type=LearningType.ENHANCEMENT, instruction=instruction, **kwargs)

    @classmethod
    def technique(cls, instruction: str, **kwargs) -> "Learning":
        """Create a technique learning."""
        return cls(type=LearningType.TECHNIQUE, instruction=instruction, **kwargs)


class Mutation(BaseModel):
    """A mutation to apply to a specialist config."""

    type: MutationType = Field(
        ...,
        description="Type of mutation",
    )
    description: str = Field(
        default="",
        description="Human-readable description",
    )
    value: Any = Field(
        default=None,
        description="Mutation-specific value",
    )
    applied: bool = Field(
        default=False,
        description="Whether mutation was applied",
    )


# ============================================================================
# Spawner
# ============================================================================


class Spawner:
    """
    Create new specialists with optional mutations and learnings.

    The spawner is responsible for:
    - Creating initial specialists from domain templates
    - Cloning high performers with minor mutations
    - Injecting learnings from the graveyard
    - Generating appropriate names

    Usage:
        spawner = Spawner()

        # From template
        spec = spawner.spawn_initial("code_generation")

        # With learnings
        spec = spawner.spawn_with_learnings("code_generation", learnings)

        # Clone best with mutations
        spec = spawner.spawn_from_best("code_generation")
    """

    # Default name prefixes for domains
    DOMAIN_PREFIXES = {
        "administration": "Admin",
        "code_generation": "Code",
        "code_review": "Review",
        "business_documents": "Docs",
        "research": "Research",
        "planning": "Plan",
    }

    def __init__(
        self,
        config_loader: Optional[DomainConfigLoader] = None,
        pool_manager: Optional[PoolManager] = None,
    ):
        """
        Initialize the spawner.

        Args:
            config_loader: Domain config loader (uses global if not provided)
            pool_manager: Pool manager (uses global if not provided)
        """
        self._config_loader = config_loader
        self._pool_manager = pool_manager

    @property
    def config_loader(self) -> DomainConfigLoader:
        """Get the config loader."""
        if self._config_loader is None:
            self._config_loader = get_domain_loader()
        return self._config_loader

    @property
    def pool_manager(self) -> PoolManager:
        """Get the pool manager."""
        if self._pool_manager is None:
            self._pool_manager = get_pool_manager()
        return self._pool_manager

    # -------------------------------------------------------------------------
    # Spawning Methods
    # -------------------------------------------------------------------------

    def spawn_initial(self, domain: str) -> Specialist:
        """
        Create a specialist from domain template.

        Args:
            domain: Domain to create specialist for

        Returns:
            New Specialist in PROBATION status
        """
        # Load domain config
        domain_config = self.config_loader.load(domain)

        # Generate name
        name = self._generate_name(domain, generation=1)

        # Create specialist config from domain defaults
        spec_config = domain_config.create_specialist_config()

        # Create specialist
        specialist = Specialist(
            domain=domain,
            name=name,
            config=spec_config,
            generation=1,
            status=SpecialistStatus.PROBATION,
        )

        logger.info(f"Spawned initial specialist: {name} for domain {domain}")
        return specialist

    def spawn_with_learnings(
        self,
        domain: str,
        learnings: List[Learning],
    ) -> Specialist:
        """
        Create a specialist with graveyard learnings injected.

        Args:
            domain: Domain to create specialist for
            learnings: Learnings from graveyard to inject

        Returns:
            New Specialist with learnings in config
        """
        # Start with initial specialist
        specialist = self.spawn_initial(domain)

        # Get pool generation for naming
        pool = self.pool_manager.get_pool(domain)
        new_generation = pool.generation + 1

        # Inject learnings
        if learnings:
            specialist.config = self.inject_learnings(specialist.config, learnings)

        # Update generation and name
        specialist.generation = new_generation
        specialist.name = self._generate_name(domain, new_generation)

        logger.info(
            f"Spawned specialist with {len(learnings)} learnings: "
            f"{specialist.name} (gen {new_generation})"
        )
        return specialist

    def spawn_from_best(
        self,
        domain: str,
        pool: Optional[DomainPool] = None,
        mutations: Optional[List[Mutation]] = None,
        auto_mutate: bool = True,
    ) -> Specialist:
        """
        Clone the best performer with optional mutations.

        Args:
            domain: Domain to spawn for
            pool: Pool to get best from (uses manager if not provided)
            mutations: Specific mutations to apply
            auto_mutate: Whether to apply automatic mutations

        Returns:
            New Specialist evolved from best performer
        """
        # Get pool
        if pool is None:
            pool = self.pool_manager.get_pool(domain)

        # Get best specialist
        best = pool.get_best()
        if best is None:
            # No specialists in pool, spawn initial
            logger.warning(f"No specialists in {domain} pool, spawning initial")
            return self.spawn_initial(domain)

        # Clone config
        new_config = self._clone_config(best.config)

        # Apply mutations
        applied_mutations = []
        if mutations:
            for mutation in mutations:
                new_config = self.apply_mutation(new_config, mutation)
                applied_mutations.append(mutation)

        if auto_mutate:
            auto_mutation = self._generate_auto_mutation(best)
            if auto_mutation:
                new_config = self.apply_mutation(new_config, auto_mutation)
                applied_mutations.append(auto_mutation)

        # Create new specialist
        new_generation = best.generation + 1
        name = self._generate_name(domain, new_generation)

        specialist = Specialist(
            domain=domain,
            name=name,
            config=new_config,
            generation=new_generation,
            parent_id=best.id,
            status=SpecialistStatus.PROBATION,
        )

        mutation_desc = ", ".join(m.description for m in applied_mutations if m.applied)
        logger.info(
            f"Spawned from best ({best.name}): {name} "
            f"with mutations: {mutation_desc or 'none'}"
        )

        return specialist

    def spawn_population(
        self,
        domain: str,
        count: int = 3,
        learnings: Optional[List[Learning]] = None,
    ) -> List[Specialist]:
        """
        Spawn multiple specialists for initial pool population.

        Args:
            domain: Domain to populate
            count: Number of specialists to create
            learnings: Optional learnings to inject

        Returns:
            List of new specialists with varied configs
        """
        specialists = []

        for i in range(count):
            if i == 0:
                # First one is baseline from template
                spec = self.spawn_initial(domain)
            else:
                # Others get mutations for diversity
                spec = self.spawn_initial(domain)
                mutation = self._generate_diversity_mutation(i)
                spec.config = self.apply_mutation(spec.config, mutation)
                spec.name = self._generate_name(domain, 1, variant=chr(ord('a') + i))

            # Inject learnings if provided
            if learnings:
                spec.config = self.inject_learnings(spec.config, learnings)

            specialists.append(spec)

        logger.info(f"Spawned population of {count} specialists for {domain}")
        return specialists

    # -------------------------------------------------------------------------
    # Learning Injection
    # -------------------------------------------------------------------------

    def inject_learnings(
        self,
        config: SpecialistConfig,
        learnings: List[Learning],
    ) -> SpecialistConfig:
        """
        Add learnings to specialist config.

        Learnings are added to the system prompt and avoid_patterns list.

        Args:
            config: Config to modify
            learnings: Learnings to inject

        Returns:
            New config with learnings
        """
        # Separate by type
        avoidances = [l for l in learnings if l.type == LearningType.AVOIDANCE]
        enhancements = [l for l in learnings if l.type == LearningType.ENHANCEMENT]
        techniques = [l for l in learnings if l.type == LearningType.TECHNIQUE]

        if not avoidances and not enhancements and not techniques:
            return config

        # Clone config
        new_config = self._clone_config(config)

        # Build prompt addition
        addition = "\n\n## Learnings from Previous Specialists\n\n"

        if avoidances:
            addition += "AVOID these patterns (caused failures):\n"
            for learning in avoidances:
                addition += f"- {learning.instruction}\n"
            addition += "\n"

        if enhancements:
            addition += "ALWAYS follow these practices:\n"
            for learning in enhancements:
                addition += f"- {learning.instruction}\n"
            addition += "\n"

        if techniques:
            addition += "Proven techniques:\n"
            for learning in techniques:
                addition += f"- {learning.instruction}\n"

        # Update config
        new_config.system_prompt = new_config.system_prompt + addition

        # Add avoidances to avoid_patterns list
        new_config.avoid_patterns = list(new_config.avoid_patterns) + [
            l.instruction for l in avoidances
        ]

        # Add techniques to learned_techniques list
        new_config.learned_techniques = list(new_config.learned_techniques) + [
            l.instruction for l in techniques
        ]

        return new_config

    # -------------------------------------------------------------------------
    # Mutation Methods
    # -------------------------------------------------------------------------

    def apply_mutation(
        self,
        config: SpecialistConfig,
        mutation: Mutation,
    ) -> SpecialistConfig:
        """
        Apply a mutation to a specialist config.

        Args:
            config: Config to mutate
            mutation: Mutation to apply

        Returns:
            New config with mutation applied
        """
        # Clone to avoid mutating original
        new_config = self._clone_config(config)

        if mutation.type == MutationType.TEMPERATURE:
            # Adjust temperature
            delta = mutation.value if mutation.value else random.uniform(-0.1, 0.1)
            new_temp = max(0.0, min(2.0, new_config.temperature + delta))
            new_config.temperature = new_temp
            mutation.applied = True
            mutation.description = f"Temperature {config.temperature:.2f} -> {new_temp:.2f}"

        elif mutation.type == MutationType.PROMPT_ADDITION:
            # Add text to prompt
            if mutation.value:
                new_config.system_prompt = new_config.system_prompt + f"\n\n{mutation.value}"
                mutation.applied = True
                mutation.description = f"Added: {mutation.value[:50]}..."

        elif mutation.type == MutationType.PROMPT_EMPHASIS:
            # Add emphasis to existing instruction
            if mutation.value:
                emphasis = f"\n\nIMPORTANT: {mutation.value}"
                new_config.system_prompt = new_config.system_prompt + emphasis
                mutation.applied = True
                mutation.description = f"Emphasized: {mutation.value[:50]}..."

        elif mutation.type == MutationType.TOOL_ADJUSTMENT:
            # Add or remove tools
            if isinstance(mutation.value, dict):
                if "add" in mutation.value:
                    new_config.tools_enabled = list(
                        set(new_config.tools_enabled) | set(mutation.value["add"])
                    )
                if "remove" in mutation.value:
                    new_config.tools_enabled = [
                        t for t in new_config.tools_enabled
                        if t not in mutation.value["remove"]
                    ]
                mutation.applied = True
                mutation.description = f"Tools adjusted"

        elif mutation.type == MutationType.RETRY_ADJUSTMENT:
            # Adjust retry count
            delta = mutation.value if mutation.value else random.choice([-1, 1])
            new_retries = max(0, min(5, new_config.max_retries + delta))
            new_config.max_retries = new_retries
            mutation.applied = True
            mutation.description = f"Retries {config.max_retries} -> {new_retries}"

        return new_config

    def _generate_auto_mutation(self, parent: Specialist) -> Optional[Mutation]:
        """Generate automatic mutation based on parent performance."""
        perf = parent.performance

        # If declining, try lower temperature for more consistency
        if perf.trend.value == "declining":
            return Mutation(
                type=MutationType.TEMPERATURE,
                value=-0.05,
                description="Lower temperature (parent declining)",
            )

        # If improving, try slightly higher temperature for exploration
        if perf.trend.value == "improving" and perf.avg_score > 0.8:
            return Mutation(
                type=MutationType.TEMPERATURE,
                value=0.05,
                description="Higher temperature (parent improving)",
            )

        # Random small temperature adjustment
        return Mutation(
            type=MutationType.TEMPERATURE,
            value=random.uniform(-0.05, 0.05),
            description="Random temperature adjustment",
        )

    def _generate_diversity_mutation(self, index: int) -> Mutation:
        """Generate mutation for population diversity."""
        # Different temperature for each variant
        temp_offsets = [0.0, -0.1, 0.1, -0.2, 0.2]
        offset = temp_offsets[index % len(temp_offsets)]

        return Mutation(
            type=MutationType.TEMPERATURE,
            value=offset,
            description=f"Diversity temperature offset {offset:+.1f}",
        )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _generate_name(
        self,
        domain: str,
        generation: int,
        variant: str = "",
    ) -> str:
        """
        Generate specialist name.

        Format: {Prefix}_v{generation}{variant}
        Examples: Code_v1, Admin_v3, Docs_v2b

        Args:
            domain: Domain name
            generation: Generation number
            variant: Optional variant suffix (a, b, c, etc.)

        Returns:
            Generated name
        """
        # Get prefix for domain
        prefix = self.DOMAIN_PREFIXES.get(
            domain,
            domain.title().replace("_", "")[:6]
        )

        name = f"{prefix}_v{generation}"
        if variant:
            name += variant

        return name

    def _clone_config(self, config: SpecialistConfig) -> SpecialistConfig:
        """Create a deep copy of a specialist config."""
        return SpecialistConfig(
            system_prompt=config.system_prompt,
            temperature=config.temperature,
            tools_enabled=list(config.tools_enabled),
            tools_required=list(config.tools_required),
            avoid_patterns=list(config.avoid_patterns),
            learned_techniques=list(config.learned_techniques),
            preferred_model_tier=config.preferred_model_tier,
            min_model_tier=config.min_model_tier,
            max_retries=config.max_retries,
            retry_temperature_bump=config.retry_temperature_bump,
            max_response_tokens=config.max_response_tokens,
        )


# ============================================================================
# Singleton Instance
# ============================================================================


_spawner: Optional[Spawner] = None


def get_spawner() -> Spawner:
    """Get the global spawner instance."""
    global _spawner
    if _spawner is None:
        _spawner = Spawner()
    return _spawner


def reset_spawner() -> None:
    """Reset the global spawner (for testing)."""
    global _spawner
    _spawner = None
