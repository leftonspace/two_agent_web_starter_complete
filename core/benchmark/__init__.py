"""
PHASE 7.5: Benchmark System

Load and execute benchmark test suites for evaluating specialists.

Usage:
    from core.benchmark import (
        # Loader
        BenchmarkLoader,
        get_benchmark_loader,
        Benchmark,
        BenchmarkTask,

        # Executor
        BenchmarkExecutor,
        get_benchmark_executor,
        BenchmarkRun,
        BenchmarkProgress,

        # Verifier
        Verifier,
        get_verifier,
        VerificationResult,
    )

    # Load and run a benchmark
    loader = get_benchmark_loader()
    benchmark = loader.load("benchmarks/code_generation/basic_functions.yaml")

    executor = get_benchmark_executor()
    run = await executor.run(benchmark)
    print(f"Score: {run.avg_score:.2f}")
"""

from .loader import (
    # Models
    VerificationRule,
    BenchmarkTask,
    Benchmark,
    # Loader
    BenchmarkLoader,
    get_benchmark_loader,
    reset_benchmark_loader,
)

from .verifier import (
    # Results
    VerificationResult,
    VerificationSummary,
    # Base
    BaseChecker,
    # Checkers
    SyntaxValidChecker,
    HasErrorHandlingChecker,
    HasDocstringsChecker,
    HasTypeHintsChecker,
    ContainsChecker,
    NotContainsChecker,
    MinLengthChecker,
    RegexMatchChecker,
    FormatValidChecker,
    # Verifier
    Verifier,
    get_verifier,
    reset_verifier,
)

from .executor import (
    # Results
    BenchmarkTaskResult,
    BenchmarkRun,
    BenchmarkProgress,
    # Config
    ExecutorConfig,
    # Executor
    BenchmarkExecutor,
    get_benchmark_executor,
    reset_benchmark_executor,
)


__all__ = [
    # Loader models
    "VerificationRule",
    "BenchmarkTask",
    "Benchmark",
    # Loader
    "BenchmarkLoader",
    "get_benchmark_loader",
    "reset_benchmark_loader",
    # Verifier results
    "VerificationResult",
    "VerificationSummary",
    # Verifier base
    "BaseChecker",
    # Checkers
    "SyntaxValidChecker",
    "HasErrorHandlingChecker",
    "HasDocstringsChecker",
    "HasTypeHintsChecker",
    "ContainsChecker",
    "NotContainsChecker",
    "MinLengthChecker",
    "RegexMatchChecker",
    "FormatValidChecker",
    # Verifier
    "Verifier",
    "get_verifier",
    "reset_verifier",
    # Executor results
    "BenchmarkTaskResult",
    "BenchmarkRun",
    "BenchmarkProgress",
    # Executor config
    "ExecutorConfig",
    # Executor
    "BenchmarkExecutor",
    "get_benchmark_executor",
    "reset_benchmark_executor",
]
