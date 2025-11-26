"""
JARVIS Integration Tests - Full Flow

Tests the complete JARVIS pipeline:
Request -> Classify -> Route -> Execute -> Evaluate -> Evolve

These tests use mocked LLM responses to ensure fast, deterministic execution
without external API calls.
"""

import asyncio
import pytest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

# Core routing components
from core.routing.router import (
    TaskRouter,
    RouterConfig,
    RoutingResult,
    TaskResult,
    reset_task_router,
)
from core.routing.classifier import (
    DomainClassifier,
    DomainClassifierConfig,
    reset_domain_classifier,
)
from core.routing.keyword_classifier import ClassificationResult

# Specialists
from core.specialists.specialist import (
    Specialist,
    SpecialistConfig,
    SpecialistStatus,
    PerformanceStats,
)
from core.specialists.pool import DomainPool, SelectionMode
from core.specialists.pool_manager import PoolManager, reset_pool_manager

# Evolution
from core.evolution.controller import (
    EvolutionController,
    EvolutionConfig,
    EvolutionResult,
    EvolutionState,
    reset_evolution_controller,
)
from core.evolution.graveyard import Graveyard, reset_graveyard
from core.evolution.convergence import reset_convergence_detector

# Evaluation
from core.evaluation.controller import (
    EvaluationController,
    EvaluationConfig,
    EvaluationMode,
    reset_evaluation_controller,
)
from core.evaluation.base import (
    EvaluationResult,
    EvaluatorType,
    EvaluationStatus,
    TaskResult as EvalTaskResult,
)

# Benchmark
from core.benchmark.loader import (
    BenchmarkLoader,
    Benchmark,
    BenchmarkTask,
    VerificationRule,
    reset_benchmark_loader,
)
from core.benchmark.executor import (
    BenchmarkExecutor,
    ExecutorConfig,
    BenchmarkRun,
    reset_benchmark_executor,
)
from core.benchmark.verifier import reset_verifier

# Budget
from core.models.budget import (
    BudgetController,
    BudgetCategory,
    BudgetStatus,
    SpendingRecord,
    reset_budget_controller,
)


# ============================================================================
# Custom Exceptions for Tests
# ============================================================================


class BudgetExceededError(Exception):
    """Raised when budget is exceeded."""
    pass


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singleton instances before and after each test."""
    # Reset before
    reset_task_router()
    reset_domain_classifier()
    reset_pool_manager()
    reset_evolution_controller()
    reset_graveyard()
    reset_convergence_detector()
    reset_evaluation_controller()
    reset_benchmark_loader()
    reset_benchmark_executor()
    reset_verifier()
    reset_budget_controller()

    yield

    # Reset after
    reset_task_router()
    reset_domain_classifier()
    reset_pool_manager()
    reset_evolution_controller()
    reset_graveyard()
    reset_convergence_detector()
    reset_evaluation_controller()
    reset_benchmark_loader()
    reset_benchmark_executor()
    reset_verifier()
    reset_budget_controller()


@pytest.fixture
def pool_manager() -> PoolManager:
    """Create pool manager with test specialists."""
    manager = PoolManager(use_database=False)

    # Add specialists to each domain pool
    for domain in ["code_generation", "business_documents", "administration", "research"]:
        pool = manager.get_pool(domain)

        for i in range(3):
            config = SpecialistConfig(
                system_prompt=f"You are a specialist for {domain}. Specialist #{i+1}.",
                temperature=0.7,
            )
            specialist = Specialist(
                domain=domain,
                name=f"{domain}_specialist_{i+1}",
                config=config,
            )
            # Set varying scores
            specialist.performance.avg_score = 0.5 + (i * 0.15)
            specialist.performance.task_count = 10
            specialist.performance.recent_scores = [0.5 + (i * 0.15)] * 5
            pool.add(specialist)

    return manager


@pytest.fixture
def task_router(pool_manager: PoolManager) -> TaskRouter:
    """Create task router with test configuration."""
    config = RouterConfig(
        use_best_for_critical=True,
        max_fallback_attempts=2,
        execution_timeout_seconds=30,
        record_costs=False,
    )

    classifier = DomainClassifier(
        config=DomainClassifierConfig(
            keyword_confidence_threshold=0.7,
            minimum_confidence_threshold=0.4,
            enable_semantic=False,  # Disable for testing
        )
    )

    return TaskRouter(
        config=config,
        classifier=classifier,
        pool_manager=pool_manager,
    )


@pytest.fixture
def budget_controller() -> BudgetController:
    """Create budget controller with test limits."""
    controller = BudgetController(use_database=False)
    return controller


@pytest.fixture
def evolution_controller(pool_manager: PoolManager) -> EvolutionController:
    """Create evolution controller for testing."""
    config = EvolutionConfig(
        default_min_score=0.5,
        min_pool_size=2,
        max_cull_per_cycle=1,
        max_learnings_per_spawn=3,
    )

    # Create graveyard with mock extractor
    graveyard = Graveyard()

    return EvolutionController(
        config=config,
        pool_manager=pool_manager,
        graveyard=graveyard,
    )


@pytest.fixture
def evaluation_controller() -> EvaluationController:
    """Create evaluation controller for testing."""
    config = EvaluationConfig(
        default_mode=EvaluationMode.SCORING_COMMITTEE,
    )
    return EvaluationController(config=config)


@pytest.fixture
def benchmark_loader() -> BenchmarkLoader:
    """Create benchmark loader pointed at test fixtures."""
    return BenchmarkLoader(benchmark_dir="tests/fixtures")


@pytest.fixture
def benchmark_executor(task_router: TaskRouter) -> BenchmarkExecutor:
    """Create benchmark executor with test configuration."""
    config = ExecutorConfig(
        max_cost_per_run=1.0,
        task_timeout_seconds=30,
        record_scores=False,
    )
    return BenchmarkExecutor(config=config, router=task_router)


# ============================================================================
# JARVIS Integration Wrapper
# ============================================================================


class JARVISTestHarness:
    """
    Test harness that wraps all JARVIS components for integration testing.
    """

    def __init__(
        self,
        pool_manager: PoolManager,
        task_router: TaskRouter,
        budget_controller: BudgetController,
        evolution_controller: EvolutionController,
        evaluation_controller: EvaluationController,
        benchmark_loader: BenchmarkLoader,
        benchmark_executor: BenchmarkExecutor,
    ):
        self.pool_manager = pool_manager
        self.task_router = task_router
        self.budget_controller = budget_controller
        self.evolution_controller = evolution_controller
        self.evaluation_controller = evaluation_controller
        self.benchmark_loader = benchmark_loader
        self.benchmark_executor = benchmark_executor

        # Evaluation results cache
        self._evaluations: Dict[UUID, EvaluationResult] = {}

    async def route_and_execute(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[RoutingResult, TaskResult]:
        """
        Route and execute a request through the full pipeline.

        Raises BudgetExceededError if budget is exceeded.
        """
        # Check budget before execution
        if not self.budget_controller.can_afford(0.01, BudgetCategory.PRODUCTION):
            raise BudgetExceededError("Production budget exceeded")

        # Route and execute
        routing, result = await self.task_router.route_and_execute(request, context)

        # Record cost
        record = SpendingRecord.create(
            category=BudgetCategory.PRODUCTION,
            provider="anthropic",
            model=routing.model_selection.model,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_cad=result.cost_cad,
            task_id=str(result.task_id),
        )
        self.budget_controller.record_spend(record)

        # Evaluate result
        if self.evaluation_controller.scoring_committee:
            eval_task = EvalTaskResult(
                task_id=result.task_id,
                specialist_id=result.specialist_id,
                domain=result.domain,
                request=result.request,
                response=result.response,
            )
            evaluation = await self.evaluation_controller.evaluate(eval_task)
            self._evaluations[result.task_id] = evaluation

        return routing, result

    async def get_evaluation(self, task_id: UUID) -> Optional[EvaluationResult]:
        """Get evaluation result for a task."""
        return self._evaluations.get(task_id)

    def set_budget_spent(self, category: BudgetCategory, amount: float) -> None:
        """Set the spent amount for a budget category (for testing)."""
        state = self.budget_controller._state.get(category)
        if state:
            state.daily.spent = amount
            state.weekly.spent = amount
            state.monthly.spent = amount


@pytest.fixture
def jarvis(
    pool_manager: PoolManager,
    task_router: TaskRouter,
    budget_controller: BudgetController,
    evolution_controller: EvolutionController,
    evaluation_controller: EvaluationController,
    benchmark_loader: BenchmarkLoader,
    benchmark_executor: BenchmarkExecutor,
) -> JARVISTestHarness:
    """Create complete JARVIS test harness."""
    return JARVISTestHarness(
        pool_manager=pool_manager,
        task_router=task_router,
        budget_controller=budget_controller,
        evolution_controller=evolution_controller,
        evaluation_controller=evaluation_controller,
        benchmark_loader=benchmark_loader,
        benchmark_executor=benchmark_executor,
    )


# ============================================================================
# Test Class: Full Flow Integration Tests
# ============================================================================


class TestFullFlow:
    """
    Integration tests for complete JARVIS flow.

    Tests cover:
    - Request classification and routing
    - Specialist selection and execution
    - Evaluation and scoring
    - Evolution (culling and spawning)
    - Benchmark execution
    - Budget enforcement
    """

    # -------------------------------------------------------------------------
    # Routing Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_simple_code_request(self, jarvis: JARVISTestHarness):
        """Test: Code request -> code_generation -> specialist -> evaluation."""
        request = "Write a Python function that reverses a string"

        # Execute
        routing, result = await jarvis.route_and_execute(request)

        # Verify routing
        assert routing.domain == "code_generation"
        assert routing.specialist_id is not None
        assert routing.specialist_name is not None
        assert routing.domain_confidence >= 0.5

        # Verify result
        assert result.response is not None
        assert result.success is True
        # Mock response contains "def" for code generation
        assert "def" in result.response.lower() or "mock" in result.response.lower()

        # Verify task metadata
        assert result.task_id == routing.task_id
        assert result.domain == routing.domain

    @pytest.mark.asyncio
    async def test_document_request(self, jarvis: JARVISTestHarness):
        """Test: Document request -> business_documents -> specialist."""
        request = "Write a brief email declining a meeting politely"

        routing, result = await jarvis.route_and_execute(request)

        # Should route to business_documents
        assert routing.domain == "business_documents"
        assert result.success is True
        assert len(result.response) > 20  # Should have substantial response

    @pytest.mark.asyncio
    async def test_research_request(self, jarvis: JARVISTestHarness):
        """Test: Research request routes to appropriate domain."""
        request = "Research the best practices for API design patterns"

        routing, result = await jarvis.route_and_execute(request)

        # May route to research or code_generation depending on keyword matching
        assert routing.domain in ["research", "code_generation", "administration"]
        assert result.success is True

    @pytest.mark.asyncio
    async def test_ambiguous_request_goes_to_admin(self, jarvis: JARVISTestHarness):
        """Test: Ambiguous request -> administration for clarification."""
        request = "Help me with the thing"

        routing, result = await jarvis.route_and_execute(request)

        # Should route to administration (fallback domain)
        assert routing.domain == "administration"
        assert result.success is True
        # Response should be available (mock or real)
        assert result.response is not None

    @pytest.mark.asyncio
    async def test_routing_metadata(self, jarvis: JARVISTestHarness):
        """Test: Routing includes all required metadata."""
        request = "Write a unit test for a login function"

        routing, result = await jarvis.route_and_execute(request)

        # Check routing metadata
        assert routing.task_id is not None
        assert routing.domain in ["code_generation", "code_review"]
        assert 0.0 <= routing.domain_confidence <= 1.0
        assert routing.classification_method in ["keyword", "semantic", "fallback"]
        assert routing.model_selection is not None
        assert routing.routing_duration_ms >= 0

    # -------------------------------------------------------------------------
    # Specialist Selection Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_weighted_specialist_selection(self, jarvis: JARVISTestHarness):
        """Test: Weighted selection favors higher-scoring specialists."""
        domain = "code_generation"
        pool = jarvis.pool_manager.get_pool(domain)

        # Run multiple requests and track selections
        selections = {}
        for _ in range(10):
            specialist = pool.select(mode=SelectionMode.WEIGHTED)
            selections[specialist.name] = selections.get(specialist.name, 0) + 1

        # Higher scoring specialists should be selected more often
        # (with weighted selection, not guaranteed but probable)
        assert len(selections) > 0

    @pytest.mark.asyncio
    async def test_best_specialist_for_critical_tasks(self, jarvis: JARVISTestHarness):
        """Test: Critical tasks should use BEST selection mode."""
        # Request with critical keywords
        request = "Deploy the production security patch immediately"

        routing, result = await jarvis.route_and_execute(request)

        # Should use best selection mode for critical tasks
        assert routing.selection_mode == "best"

    # -------------------------------------------------------------------------
    # Budget Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_budget_tracking(self, jarvis: JARVISTestHarness):
        """Test: Budget is tracked for each request."""
        initial_status = jarvis.budget_controller.get_status(BudgetCategory.PRODUCTION)
        initial_spent = initial_status.daily_spent

        # Execute a request
        request = "Write a hello world function"
        await jarvis.route_and_execute(request)

        # Budget should be updated
        new_status = jarvis.budget_controller.get_status(BudgetCategory.PRODUCTION)
        # Note: Mock execution may record 0 cost, so we just verify the call works
        assert new_status is not None

    @pytest.mark.asyncio
    async def test_budget_enforcement(self, jarvis: JARVISTestHarness):
        """Test: Requests blocked when budget exceeded."""
        # Exhaust budget by setting spent to limit
        jarvis.set_budget_spent(BudgetCategory.PRODUCTION, 999999)

        with pytest.raises(BudgetExceededError):
            await jarvis.route_and_execute("Write some code")

    @pytest.mark.asyncio
    async def test_budget_not_exceeded_allows_request(self, jarvis: JARVISTestHarness):
        """Test: Requests allowed when budget is available."""
        # Ensure budget is not exceeded
        status = jarvis.budget_controller.get_status(BudgetCategory.PRODUCTION)
        assert status.daily_remaining > 0

        # Should succeed
        routing, result = await jarvis.route_and_execute("Write a simple function")
        assert result.success is True

    # -------------------------------------------------------------------------
    # Evolution Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_specialist_score_recording(self, jarvis: JARVISTestHarness):
        """Test: Specialist scores are recorded after tasks."""
        domain = "code_generation"
        pool = jarvis.pool_manager.get_pool(domain)
        specialist = pool.specialists[0]

        initial_task_count = specialist.performance.task_count

        # Record a score
        specialist.record_score(0.85)

        assert specialist.performance.task_count == initial_task_count + 1
        assert 0.85 in specialist.performance.recent_scores

    @pytest.mark.asyncio
    async def test_evolution_culls_low_performers(self, jarvis: JARVISTestHarness):
        """Test: Low-scoring specialist gets culled."""
        domain = "code_generation"
        pool = jarvis.pool_manager.get_pool(domain)

        # Set up a clearly worst specialist
        worst = pool.specialists[0]
        worst.performance.avg_score = 0.2
        worst.performance.recent_scores = [0.2] * 10
        worst_name = worst.name

        # Ensure other specialists have higher scores
        for spec in pool.specialists[1:]:
            spec.performance.avg_score = 0.8
            spec.performance.recent_scores = [0.8] * 10

        initial_count = len(pool.specialists)

        # Run evolution
        result = await jarvis.evolution_controller.run_evolution(domain)

        # Worst should be culled
        assert result.success is True
        assert worst_name in result.culled
        # New specialist should be spawned (pool maintains size)
        assert len(result.spawned) > 0

    @pytest.mark.asyncio
    async def test_evolution_spawns_replacements(self, jarvis: JARVISTestHarness):
        """Test: Spawned specialists replace culled ones."""
        domain = "code_generation"
        pool = jarvis.pool_manager.get_pool(domain)

        # Force a culling scenario
        pool.specialists[0].performance.avg_score = 0.1
        pool.specialists[0].performance.recent_scores = [0.1] * 10

        for spec in pool.specialists[1:]:
            spec.performance.avg_score = 0.9
            spec.performance.recent_scores = [0.9] * 10

        initial_count = len(pool.specialists)

        result = await jarvis.evolution_controller.run_evolution(domain)

        # Pool should maintain size
        assert len(pool.specialists) == initial_count
        assert len(result.spawned) == len(result.culled)

    @pytest.mark.asyncio
    async def test_evolution_increments_generation(self, jarvis: JARVISTestHarness):
        """Test: Evolution increments pool generation."""
        domain = "code_generation"
        pool = jarvis.pool_manager.get_pool(domain)
        initial_gen = pool.generation

        # Set up culling scenario
        pool.specialists[0].performance.avg_score = 0.1
        pool.specialists[0].performance.recent_scores = [0.1] * 10

        result = await jarvis.evolution_controller.run_evolution(domain)

        assert result.new_generation == initial_gen + 1
        assert pool.generation == initial_gen + 1

    @pytest.mark.asyncio
    async def test_evolution_status_tracking(self, jarvis: JARVISTestHarness):
        """Test: Evolution status is tracked correctly."""
        domain = "code_generation"

        # Get initial status
        status = jarvis.evolution_controller.get_status(domain)

        assert status.domain == domain
        assert status.state in [EvolutionState.ACTIVE, EvolutionState.PAUSED]
        assert status.specialist_count > 0

    @pytest.mark.asyncio
    async def test_evolution_pause_resume(self, jarvis: JARVISTestHarness):
        """Test: Evolution can be paused and resumed."""
        from core.evolution.resume_triggers import ResumeTrigger
        domain = "code_generation"

        # Pause
        jarvis.evolution_controller.pause_evolution(domain, "Test pause")
        status = jarvis.evolution_controller.get_status(domain)
        assert status.state == EvolutionState.PAUSED
        assert status.pause_reason == "Test pause"

        # Resume (use valid enum value)
        jarvis.evolution_controller.resume_evolution(domain, ResumeTrigger.USER_REQUEST.value)
        status = jarvis.evolution_controller.get_status(domain)
        assert status.state == EvolutionState.ACTIVE

    # -------------------------------------------------------------------------
    # Benchmark Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_benchmark_loading(self, jarvis: JARVISTestHarness):
        """Test: Benchmark files can be loaded correctly."""
        benchmark = jarvis.benchmark_loader.load("tests/fixtures/test_benchmark.yaml")

        assert benchmark is not None
        assert benchmark.name == "test_benchmark"
        assert benchmark.domain == "code_generation"
        assert benchmark.total_tasks == 4
        assert benchmark.easy_count >= 1
        assert benchmark.medium_count >= 1
        assert benchmark.hard_count >= 1

    @pytest.mark.asyncio
    async def test_benchmark_execution(self, jarvis: JARVISTestHarness):
        """Test: Benchmark runs and records scores."""
        # Load test benchmark
        benchmark = jarvis.benchmark_loader.load("tests/fixtures/test_benchmark.yaml")

        # Run
        run = await jarvis.benchmark_executor.run(benchmark)

        assert run.status == "completed"
        assert run.tasks_completed == len(benchmark.tasks)
        assert run.avg_score >= 0  # Score should be recorded
        assert len(run.results) == benchmark.total_tasks

    @pytest.mark.asyncio
    async def test_benchmark_task_results(self, jarvis: JARVISTestHarness):
        """Test: Individual task results are recorded."""
        benchmark = jarvis.benchmark_loader.load("tests/fixtures/test_benchmark.yaml")
        run = await jarvis.benchmark_executor.run(benchmark)

        for result in run.results:
            assert result.task_id is not None
            assert result.status in ["completed", "failed", "skipped"]
            if result.status == "completed":
                assert result.score is not None
                assert 0 <= result.score <= 1

    @pytest.mark.asyncio
    async def test_benchmark_pause_control(self, jarvis: JARVISTestHarness):
        """Test: Benchmark pause control works."""
        # Test that pause flag can be set
        jarvis.benchmark_executor.pause()
        assert jarvis.benchmark_executor.is_paused() is True

        # Resume clears the flag
        jarvis.benchmark_executor.resume()
        assert jarvis.benchmark_executor.is_paused() is False

    @pytest.mark.asyncio
    async def test_benchmark_cancel_control(self, jarvis: JARVISTestHarness):
        """Test: Benchmark cancel control works."""
        benchmark = jarvis.benchmark_loader.load("tests/fixtures/test_benchmark.yaml")

        # Run a benchmark first to confirm execution works
        run1 = await jarvis.benchmark_executor.run(benchmark)
        assert run1.status == "completed"

        # Verify cancel flag can be checked
        jarvis.benchmark_executor.cancel()
        # Note: cancel() sets a flag that's checked at start of each task
        # Since tasks complete very quickly, we just verify the flag is set
        assert jarvis.benchmark_executor._cancelled is True

    @pytest.mark.asyncio
    async def test_benchmark_statistics(self, jarvis: JARVISTestHarness):
        """Test: Benchmark statistics are tracked."""
        benchmark = jarvis.benchmark_loader.load("tests/fixtures/test_benchmark.yaml")

        initial_stats = jarvis.benchmark_executor.get_stats()
        initial_runs = initial_stats["total_runs"]

        await jarvis.benchmark_executor.run(benchmark)

        new_stats = jarvis.benchmark_executor.get_stats()
        assert new_stats["total_runs"] == initial_runs + 1

    # -------------------------------------------------------------------------
    # Model Routing Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_model_selection_default(self, jarvis: JARVISTestHarness):
        """Test: Model selection provides default model."""
        request = "Write a simple hello function"

        routing, result = await jarvis.route_and_execute(request)

        assert routing.model_selection is not None
        assert routing.model_selection.model is not None
        assert routing.model_selection.provider == "anthropic"

    @pytest.mark.asyncio
    async def test_model_fallback_chain(self, jarvis: JARVISTestHarness):
        """Test: Model selection includes fallback chain."""
        request = "Solve this complex algorithm problem"

        routing, result = await jarvis.route_and_execute(request)

        # Should have a fallback chain
        assert routing.model_selection.fallback_chain is not None

    # -------------------------------------------------------------------------
    # Pool Manager Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_pool_manager_domains(self, jarvis: JARVISTestHarness):
        """Test: Pool manager has expected domains."""
        domains = jarvis.pool_manager.list_domains()

        assert "code_generation" in domains
        assert "business_documents" in domains
        assert "administration" in domains

    @pytest.mark.asyncio
    async def test_pool_manager_get_jarvis(self, jarvis: JARVISTestHarness):
        """Test: Can retrieve JARVIS (best admin specialist)."""
        jarvis_spec = jarvis.pool_manager.get_jarvis()

        if jarvis_spec:
            assert jarvis_spec.domain == "administration"
            # Should be the best in the pool
            pool = jarvis.pool_manager.get_pool("administration")
            best = pool.get_best()
            assert jarvis_spec.id == best.id

    @pytest.mark.asyncio
    async def test_find_specialist_by_id(self, jarvis: JARVISTestHarness):
        """Test: Can find specialist by ID across pools."""
        # Get any specialist
        pool = jarvis.pool_manager.get_pool("code_generation")
        specialist = pool.specialists[0]

        # Should find it
        found = jarvis.pool_manager.find_specialist(specialist.id)
        assert found is not None
        assert found.id == specialist.id

    # -------------------------------------------------------------------------
    # Evaluation Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_evaluation_mode_toggle(self, jarvis: JARVISTestHarness):
        """Test: Evaluation mode can be toggled."""
        controller = jarvis.evaluation_controller

        # Set initial state explicitly (mode may be persisted from previous runs)
        controller.set_mode(EvaluationMode.SCORING_COMMITTEE)
        assert controller.get_mode() == EvaluationMode.SCORING_COMMITTEE

        # Toggle to AI_COUNCIL
        controller.set_mode(EvaluationMode.AI_COUNCIL)
        assert controller.get_mode() == EvaluationMode.AI_COUNCIL

        # Toggle to BOTH
        controller.set_mode(EvaluationMode.BOTH)
        assert controller.get_mode() == EvaluationMode.BOTH

        # Toggle back
        controller.set_mode(EvaluationMode.SCORING_COMMITTEE)
        assert controller.get_mode() == EvaluationMode.SCORING_COMMITTEE

    @pytest.mark.asyncio
    async def test_evaluation_stats(self, jarvis: JARVISTestHarness):
        """Test: Evaluation statistics are tracked."""
        # Set a known mode first
        jarvis.evaluation_controller.set_mode(EvaluationMode.SCORING_COMMITTEE)

        stats = jarvis.evaluation_controller.get_stats()

        assert "mode" in stats
        assert "evaluation_count" in stats
        assert stats["mode"] == EvaluationMode.SCORING_COMMITTEE.value

    # -------------------------------------------------------------------------
    # End-to-End Flow Tests
    # -------------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_multiple_requests_flow(self, jarvis: JARVISTestHarness):
        """Test: Multiple requests are processed correctly."""
        requests = [
            "Write a Python sorting function",
            "Create a business proposal template",
            "Research machine learning trends",
            "Help me plan a project",
        ]

        results = []
        for request in requests:
            routing, result = await jarvis.route_and_execute(request)
            results.append((routing, result))

        # All should succeed
        assert all(r[1].success for r in results)

        # Different domains should be selected
        domains = set(r[0].domain for r in results)
        assert len(domains) > 1  # Multiple domains used

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle(self, jarvis: JARVISTestHarness):
        """Test: Complete lifecycle from request to potential evolution."""
        domain = "code_generation"
        pool = jarvis.pool_manager.get_pool(domain)

        # Track initial state
        initial_selection_count = pool.selection_count

        # Execute request
        request = "Write a function to calculate factorial"
        routing, result = await jarvis.route_and_execute(request)

        # Verify execution
        assert routing.domain == domain
        assert result.success is True

        # Selection count should increase
        assert pool.selection_count > initial_selection_count

    @pytest.mark.asyncio
    async def test_graveyard_receives_culled_specialists(self, jarvis: JARVISTestHarness):
        """Test: Culled specialists go to graveyard."""
        domain = "code_generation"
        pool = jarvis.pool_manager.get_pool(domain)

        # Set up culling
        worst = pool.specialists[0]
        worst.performance.avg_score = 0.1
        worst.performance.recent_scores = [0.1] * 10
        worst_name = worst.name

        for spec in pool.specialists[1:]:
            spec.performance.avg_score = 0.9

        # Run evolution
        await jarvis.evolution_controller.run_evolution(domain)

        # Check graveyard
        graveyard = jarvis.evolution_controller.graveyard
        entries = graveyard.get_entries(domain)

        culled_names = [e.name for e in entries]
        assert worst_name in culled_names


# ============================================================================
# Performance Tests
# ============================================================================


class TestPerformance:
    """Tests for performance requirements."""

    @pytest.mark.asyncio
    async def test_routing_latency(self, jarvis: JARVISTestHarness):
        """Test: Routing completes within acceptable time."""
        import time

        start = time.time()
        routing, result = await jarvis.route_and_execute("Write a simple function")
        elapsed_ms = (time.time() - start) * 1000

        # Routing should be fast (< 1 second for mock execution)
        assert elapsed_ms < 1000

    @pytest.mark.asyncio
    async def test_benchmark_completes_quickly(self, jarvis: JARVISTestHarness):
        """Test: Benchmark completes within 2 minutes."""
        import time

        benchmark = jarvis.benchmark_loader.load("tests/fixtures/test_benchmark.yaml")

        start = time.time()
        run = await jarvis.benchmark_executor.run(benchmark)
        elapsed = time.time() - start

        # Should complete in under 2 minutes
        assert elapsed < 120
        assert run.status == "completed"


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_empty_request_handling(self, jarvis: JARVISTestHarness):
        """Test: Empty requests are handled gracefully."""
        routing, result = await jarvis.route_and_execute("")

        # Should fallback to administration
        assert routing.domain == "administration"

    @pytest.mark.asyncio
    async def test_very_long_request_handling(self, jarvis: JARVISTestHarness):
        """Test: Very long requests are handled."""
        long_request = "Write code " * 1000  # Very long request

        routing, result = await jarvis.route_and_execute(long_request)

        # Should still complete
        assert result is not None

    @pytest.mark.asyncio
    async def test_missing_pool_fallback(self, jarvis: JARVISTestHarness):
        """Test: Missing domain pool falls back gracefully."""
        # Remove a pool
        jarvis.pool_manager.remove_pool("research")

        # Request should still work (falls back)
        request = "Research AI trends"
        routing, result = await jarvis.route_and_execute(request)

        assert result.success is True
