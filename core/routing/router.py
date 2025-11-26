"""
PHASE 7.5: Task Router

Orchestrates the full request → classify → select → execute flow.
Ties together all routing components.

Usage:
    from core.routing import TaskRouter, get_task_router

    router = get_task_router()

    # Route and execute in one call
    routing, result = await router.route_and_execute("write a python script")

    # Or route first, then execute
    routing = await router.route("write a python script")
    result = await router.execute_with_routing(routing, "write a python script")
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .classifier import DomainClassifier, ClassificationResult, get_domain_classifier

if TYPE_CHECKING:
    from core.specialists import Specialist
    from core.specialists.pool import DomainPool, SelectionMode
    from core.specialists.pool_manager import PoolManager


# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Execution Error
# ============================================================================


class ExecutionError(Exception):
    """Error during task execution."""

    def __init__(
        self,
        message: str,
        task_id: Optional[UUID] = None,
        attempts: int = 0,
    ):
        super().__init__(message)
        self.task_id = task_id
        self.attempts = attempts


# ============================================================================
# Model Selection (stub for integration)
# ============================================================================


class ModelSelection(BaseModel):
    """Model selection result from model router."""

    provider: str = Field(default="anthropic")
    model: str = Field(default="claude-sonnet-4-20250514")
    model_name: str = Field(default="sonnet")
    complexity_level: str = Field(default="medium")
    estimated_cost_cad: float = Field(default=0.0)
    fallback_chain: List[str] = Field(default_factory=list)
    reasoning: str = Field(default="")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider,
            "model": self.model,
            "model_name": self.model_name,
            "complexity": self.complexity_level,
            "estimated_cost": self.estimated_cost_cad,
            "fallbacks": self.fallback_chain,
        }


# ============================================================================
# Routing Result
# ============================================================================


class RoutingResult(BaseModel):
    """Result of routing a request."""

    task_id: UUID = Field(default_factory=uuid4)
    domain: str
    domain_confidence: float = Field(ge=0.0, le=1.0)
    classification_method: str = Field(default="keyword")

    # Specialist info
    specialist_id: Optional[UUID] = None
    specialist_name: Optional[str] = None
    specialist_generation: int = Field(default=1)

    # Model selection
    model_selection: ModelSelection = Field(default_factory=ModelSelection)

    # Selection mode used
    selection_mode: str = Field(default="weighted")

    # Timing
    classified_at: datetime = Field(default_factory=datetime.utcnow)
    routing_duration_ms: int = Field(default=0, ge=0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": str(self.task_id),
            "domain": self.domain,
            "domain_confidence": round(self.domain_confidence, 3),
            "classification_method": self.classification_method,
            "specialist": {
                "id": str(self.specialist_id) if self.specialist_id else None,
                "name": self.specialist_name,
                "generation": self.specialist_generation,
            },
            "model": self.model_selection.to_dict(),
            "selection_mode": self.selection_mode,
            "classified_at": self.classified_at.isoformat(),
            "routing_duration_ms": self.routing_duration_ms,
        }


# ============================================================================
# Task Result
# ============================================================================


class TaskResult(BaseModel):
    """Result of executing a task."""

    task_id: UUID
    specialist_id: UUID
    specialist_name: Optional[str] = None

    # Domain
    domain: str
    task_type: Optional[str] = None

    # Content
    request: str
    response: str = ""

    # Artifacts
    artifacts: List[str] = Field(default_factory=list)

    # Execution metadata
    execution_time_ms: int = Field(default=0, ge=0)
    model_used: str = Field(default="unknown")
    tokens_used: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    cost_cad: float = Field(default=0.0, ge=0.0)

    # Status
    success: bool = True
    error: Optional[str] = None
    attempts: int = Field(default=1, ge=1)

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    # Context
    context: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": str(self.task_id),
            "specialist_id": str(self.specialist_id),
            "domain": self.domain,
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "cost_cad": round(self.cost_cad, 6),
            "attempts": self.attempts,
            "error": self.error,
        }


# ============================================================================
# Router Configuration
# ============================================================================


class RouterConfig(BaseModel):
    """Configuration for task router."""

    # Specialist selection
    use_best_for_critical: bool = Field(
        default=True,
        description="Use BEST selection mode for critical complexity tasks",
    )

    # Fallback settings
    max_fallback_attempts: int = Field(
        default=3,
        ge=1,
        description="Maximum fallback attempts on failure",
    )

    # Timeout settings
    execution_timeout_seconds: float = Field(
        default=120.0,
        gt=0,
        description="Maximum execution time",
    )

    # Default model settings
    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
    )

    # Cost tracking
    record_costs: bool = Field(
        default=True,
        description="Record costs to budget controller",
    )

    # Logging
    log_routing: bool = Field(
        default=True,
        description="Log routing decisions",
    )


# ============================================================================
# Task Router
# ============================================================================


class TaskRouter:
    """
    Route tasks to domain specialist pools.

    Full flow:
    1. Classify request → domain
    2. Get domain pool
    3. Select specialist from pool
    4. Route to model based on complexity
    5. Execute
    6. Return result

    Usage:
        router = TaskRouter()

        # Full flow
        routing, result = await router.route_and_execute("write a script")

        # Just routing
        routing = await router.route("write a script")

        # Execute with existing routing
        result = await router.execute_with_routing(routing, "write a script")
    """

    def __init__(
        self,
        config: Optional[RouterConfig] = None,
        classifier: Optional[DomainClassifier] = None,
        pool_manager: Optional["PoolManager"] = None,
        model_router: Optional[Any] = None,
        budget_controller: Optional[Any] = None,
        provider_registry: Optional[Any] = None,
    ):
        """
        Initialize the router.

        Args:
            config: Router configuration
            classifier: Domain classifier
            pool_manager: Pool manager for specialist selection
            model_router: Model router for model selection
            budget_controller: Budget controller for cost tracking
            provider_registry: Provider registry for execution
        """
        self._config = config or RouterConfig()
        self._classifier = classifier
        self._pool_manager = pool_manager
        self._model_router = model_router
        self._budget_controller = budget_controller
        self._provider_registry = provider_registry

        # Statistics
        self._total_routes = 0
        self._total_executions = 0
        self._total_failures = 0
        self._initialized_at = datetime.utcnow()

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def config(self) -> RouterConfig:
        """Get configuration."""
        return self._config

    @property
    def classifier(self) -> DomainClassifier:
        """Get domain classifier (lazy load)."""
        if self._classifier is None:
            self._classifier = get_domain_classifier()
        return self._classifier

    @property
    def pool_manager(self) -> "PoolManager":
        """Get pool manager (lazy load)."""
        if self._pool_manager is None:
            from core.specialists.pool_manager import get_pool_manager
            self._pool_manager = get_pool_manager()
        return self._pool_manager

    @property
    def model_router(self) -> Any:
        """Get model router (lazy load)."""
        if self._model_router is None:
            try:
                from core.routing.model_router import get_model_router
                self._model_router = get_model_router()
            except ImportError:
                logger.warning("Model router not available")
        return self._model_router

    @property
    def budget_controller(self) -> Any:
        """Get budget controller (lazy load)."""
        if self._budget_controller is None:
            try:
                from core.budget import get_budget_controller
                self._budget_controller = get_budget_controller()
            except ImportError:
                logger.debug("Budget controller not available")
        return self._budget_controller

    # -------------------------------------------------------------------------
    # Routing
    # -------------------------------------------------------------------------

    async def route(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingResult:
        """
        Route a request to determine domain, specialist, and model.

        Args:
            request: The user request
            context: Additional context

        Returns:
            RoutingResult with routing decisions
        """
        start_time = time.time()
        self._total_routes += 1

        # 1. Classify request
        classification = await self.classifier.classify(request)

        if self._config.log_routing:
            logger.info(
                f"Classified to {classification.domain} "
                f"(confidence={classification.confidence:.2f}, method={classification.method})"
            )

        # 2. Get pool
        pool = self.pool_manager.get_pool(classification.domain)

        if pool is None:
            # Fallback to administration
            logger.warning(f"No pool for domain {classification.domain}, using administration")
            pool = self.pool_manager.get_pool("administration")
            classification.domain = "administration"

        # 3. Determine selection mode based on complexity
        selection_mode = self._determine_selection_mode(request, classification, context)

        # 4. Select specialist
        specialist = self._select_specialist(pool, selection_mode)

        # 5. Get model selection
        model_selection = self._get_model_selection(request, classification, context)

        routing_duration_ms = int((time.time() - start_time) * 1000)

        return RoutingResult(
            task_id=uuid4(),
            domain=classification.domain,
            domain_confidence=classification.confidence,
            classification_method=classification.method,
            specialist_id=specialist.id if specialist else None,
            specialist_name=specialist.name if specialist else None,
            specialist_generation=getattr(specialist, 'generation', 1) if specialist else 1,
            model_selection=model_selection,
            selection_mode=selection_mode,
            routing_duration_ms=routing_duration_ms,
        )

    def _determine_selection_mode(
        self,
        request: str,
        classification: ClassificationResult,
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Determine specialist selection mode based on complexity."""
        # Check for critical tasks
        if self._config.use_best_for_critical:
            # Use model router's complexity assessment if available
            if self.model_router:
                try:
                    if hasattr(self.model_router, 'assessor'):
                        complexity = self.model_router.assessor.assess(
                            request,
                            classification.domain,
                        )
                        if hasattr(complexity, 'level') and complexity.level.value == "critical":
                            return "best"
                except Exception:
                    pass

            # Simple heuristics for critical detection
            critical_indicators = [
                "production",
                "critical",
                "urgent",
                "security",
                "deployment",
            ]
            request_lower = request.lower()
            if any(ind in request_lower for ind in critical_indicators):
                return "best"

        # Default to weighted selection
        return "weighted"

    def _select_specialist(
        self,
        pool: "DomainPool",
        selection_mode: str,
    ) -> Optional["Specialist"]:
        """Select a specialist from the pool."""
        if pool is None:
            return None

        try:
            from core.specialists.pool import SelectionMode

            mode_map = {
                "best": SelectionMode.BEST,
                "weighted": SelectionMode.WEIGHTED,
                "round_robin": SelectionMode.ROUND_ROBIN,
            }

            mode = mode_map.get(selection_mode, SelectionMode.WEIGHTED)
            return pool.select(mode=mode)

        except Exception as e:
            logger.error(f"Failed to select specialist: {e}")
            # Return first specialist as fallback
            if pool.specialists:
                return pool.specialists[0]
            return None

    def _get_model_selection(
        self,
        request: str,
        classification: ClassificationResult,
        context: Optional[Dict[str, Any]],
    ) -> ModelSelection:
        """Get model selection from model router."""
        if self.model_router:
            try:
                selection = self.model_router.route(
                    request=request,
                    domain=classification.domain,
                    context=context,
                )
                # Convert to our ModelSelection type
                return ModelSelection(
                    provider=getattr(selection, 'provider', 'anthropic'),
                    model=getattr(selection, 'model', 'claude-sonnet-4-20250514'),
                    model_name=getattr(selection, 'model_name', 'sonnet'),
                    complexity_level=getattr(selection, 'complexity_level', 'medium'),
                    estimated_cost_cad=getattr(selection, 'estimated_cost_cad', 0.0),
                    fallback_chain=getattr(selection, 'fallback_chain', []),
                    reasoning=getattr(selection, 'reasoning', ''),
                )
            except Exception as e:
                logger.warning(f"Model routing failed: {e}")

        # Default selection
        return ModelSelection(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            model_name="sonnet",
            complexity_level="medium",
            fallback_chain=["claude-3-5-haiku-20241022"],
        )

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    async def execute(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """
        Execute a request (routes first, then executes).

        Args:
            request: The user request
            context: Additional context

        Returns:
            TaskResult with response
        """
        routing = await self.route(request, context)
        return await self.execute_with_routing(routing, request, context)

    async def execute_with_routing(
        self,
        routing: RoutingResult,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """
        Execute a request with pre-computed routing.

        Args:
            routing: Pre-computed routing result
            request: The user request
            context: Additional context

        Returns:
            TaskResult with response
        """
        self._total_executions += 1
        start_time = time.time()

        # Get specialist
        specialist = None
        if routing.specialist_id:
            pool = self.pool_manager.get_pool(routing.domain)
            if pool:
                specialist = pool.get_specialist(routing.specialist_id)

        # Execute with fallback chain
        attempts = 0
        last_error = None
        models_to_try = [routing.model_selection.model] + routing.model_selection.fallback_chain

        for model in models_to_try[:self._config.max_fallback_attempts]:
            attempts += 1
            try:
                result = await self._execute_with_model(
                    task_id=routing.task_id,
                    request=request,
                    specialist=specialist,
                    model=model,
                    provider=routing.model_selection.provider,
                    context=context,
                )
                result.attempts = attempts
                result.execution_time_ms = int((time.time() - start_time) * 1000)
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Execution failed with {model}: {e}, trying fallback")
                continue

        # All attempts failed
        self._total_failures += 1
        raise ExecutionError(
            f"All models failed after {attempts} attempts: {last_error}",
            task_id=routing.task_id,
            attempts=attempts,
        )

    async def _execute_with_model(
        self,
        task_id: UUID,
        request: str,
        specialist: Optional["Specialist"],
        model: str,
        provider: str,
        context: Optional[Dict[str, Any]],
    ) -> TaskResult:
        """Execute request with a specific model."""
        start_time = time.time()

        # Build system prompt
        system_prompt = self._build_system_prompt(specialist, context)

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request},
        ]

        # Get provider and execute
        response_content = ""
        input_tokens = 0
        output_tokens = 0
        cost_cad = 0.0

        try:
            # Try to use provider registry
            if self._provider_registry:
                provider_instance = self._provider_registry.get(provider)
                completion = await provider_instance.complete(
                    messages=messages,
                    model=model,
                    temperature=self._get_temperature(specialist),
                )
                response_content = completion.content
                input_tokens = completion.input_tokens
                output_tokens = completion.output_tokens

            else:
                # Mock execution for testing
                response_content = self._mock_execute(request, specialist)
                input_tokens = len(request.split()) * 2
                output_tokens = len(response_content.split()) * 2

            # Estimate cost
            cost_cad = self._estimate_cost(model, input_tokens, output_tokens)

            # Record cost if budget controller available
            if self._config.record_costs and self.budget_controller:
                await self._record_cost(
                    task_id=task_id,
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_cad=cost_cad,
                )

        except Exception as e:
            logger.error(f"Execution error: {e}")
            raise

        execution_time_ms = int((time.time() - start_time) * 1000)

        return TaskResult(
            task_id=task_id,
            specialist_id=specialist.id if specialist else uuid4(),
            specialist_name=specialist.name if specialist else "default",
            domain=specialist.domain if specialist else "administration",
            request=request,
            response=response_content,
            execution_time_ms=execution_time_ms,
            model_used=model,
            tokens_used=input_tokens + output_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_cad=cost_cad,
            success=True,
            completed_at=datetime.utcnow(),
            context=context or {},
        )

    def _build_system_prompt(
        self,
        specialist: Optional["Specialist"],
        context: Optional[Dict[str, Any]],
    ) -> str:
        """Build system prompt for execution."""
        if specialist and hasattr(specialist, 'config'):
            return specialist.config.system_prompt

        # Default system prompt
        return """You are a helpful AI assistant. Provide clear, accurate, and helpful responses.
Be concise but thorough. If you're unsure about something, say so."""

    def _get_temperature(self, specialist: Optional["Specialist"]) -> float:
        """Get temperature for execution."""
        if specialist and hasattr(specialist, 'config'):
            return getattr(specialist.config, 'temperature', self._config.default_temperature)
        return self._config.default_temperature

    def _mock_execute(
        self,
        request: str,
        specialist: Optional["Specialist"],
    ) -> str:
        """Mock execution for testing without providers."""
        domain = specialist.domain if specialist else "general"
        return (
            f"[Mock Response for {domain}]\n\n"
            f"Request received: {request[:100]}...\n\n"
            f"This is a mock response. In production, this would be "
            f"generated by the configured LLM provider."
        )

    def _estimate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Estimate cost in CAD."""
        # Simple cost estimation (would use actual rates in production)
        rates = {
            "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        }

        model_rates = rates.get(model, {"input": 0.003, "output": 0.015})
        usd_cost = (input_tokens / 1000 * model_rates["input"] +
                    output_tokens / 1000 * model_rates["output"])

        # Convert to CAD (rough estimate)
        return usd_cost * 1.35

    async def _record_cost(
        self,
        task_id: UUID,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_cad: float,
    ) -> None:
        """Record cost to budget controller."""
        try:
            from core.budget import SpendingRecord, BudgetCategory

            record = SpendingRecord(
                timestamp=datetime.utcnow(),
                category=BudgetCategory.PRODUCTION,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_cad=cost_cad,
                task_id=task_id,
            )

            await self.budget_controller.record_spend(record)

        except Exception as e:
            logger.warning(f"Failed to record cost: {e}")

    # -------------------------------------------------------------------------
    # Combined Flow
    # -------------------------------------------------------------------------

    async def route_and_execute(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[RoutingResult, TaskResult]:
        """
        Route and execute a request in one call.

        Args:
            request: The user request
            context: Additional context

        Returns:
            Tuple of (RoutingResult, TaskResult)
        """
        routing = await self.route(request, context)
        result = await self.execute_with_routing(routing, request, context)
        return routing, result

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "total_routes": self._total_routes,
            "total_executions": self._total_executions,
            "total_failures": self._total_failures,
            "success_rate": (
                (self._total_executions - self._total_failures) / self._total_executions
                if self._total_executions > 0
                else 1.0
            ),
            "classifier_stats": self.classifier.get_stats(),
            "initialized_at": self._initialized_at.isoformat(),
        }

    def reset_stats(self) -> None:
        """Reset router statistics."""
        self._total_routes = 0
        self._total_executions = 0
        self._total_failures = 0


# ============================================================================
# Singleton Instance
# ============================================================================


_task_router: Optional[TaskRouter] = None


def get_task_router() -> TaskRouter:
    """Get the global task router."""
    global _task_router
    if _task_router is None:
        _task_router = TaskRouter()
    return _task_router


def reset_task_router() -> None:
    """Reset the global task router (for testing)."""
    global _task_router
    _task_router = None
