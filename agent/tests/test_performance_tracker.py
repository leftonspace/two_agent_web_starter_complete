"""
PHASE 9.3: Performance Tracker Tests

Tests for LLM performance tracking and analytics.
"""

import tempfile
import time
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm.performance_tracker import PerformanceTracker, PerformanceMetric, ModelStats


@pytest.fixture
def temp_storage():
    """Create temporary storage file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def tracker(temp_storage):
    """Create performance tracker with temporary storage."""
    return PerformanceTracker(storage_path=temp_storage)


@pytest.mark.asyncio
async def test_tracker_initialization(temp_storage):
    """Test tracker initialization."""
    tracker = PerformanceTracker(storage_path=temp_storage)
    assert tracker.storage_path == temp_storage
    assert len(tracker.metrics) == 0


@pytest.mark.asyncio
async def test_record_call_success(tracker):
    """Test recording successful call."""
    await tracker.record_call(
        model="gpt-4o",
        latency_ms=1200.5,
        cost_usd=0.05,
        success=True,
        prompt_tokens=100,
        completion_tokens=50,
        task_type="code",
    )

    assert len(tracker.metrics) == 1
    metric = tracker.metrics[0]

    assert metric.model == "gpt-4o"
    assert metric.latency_ms == 1200.5
    assert metric.cost_usd == 0.05
    assert metric.success is True
    assert metric.prompt_tokens == 100
    assert metric.completion_tokens == 50
    assert metric.task_type == "code"


@pytest.mark.asyncio
async def test_record_call_failure(tracker):
    """Test recording failed call."""
    await tracker.record_call(
        model="llama3",
        latency_ms=0,
        cost_usd=0.0,
        success=False,
    )

    assert len(tracker.metrics) == 1
    metric = tracker.metrics[0]

    assert metric.success is False


@pytest.mark.asyncio
async def test_multiple_calls_aggregation(tracker):
    """Test aggregation of multiple calls."""
    # Record multiple calls for same model
    await tracker.record_call("gpt-4o", 1000, 0.05, True, prompt_tokens=100, completion_tokens=50)
    await tracker.record_call("gpt-4o", 1200, 0.06, True, prompt_tokens=120, completion_tokens=60)
    await tracker.record_call("gpt-4o", 0, 0.0, False)  # Failure

    stats = tracker.get_model_stats("gpt-4o")

    assert stats is not None
    assert stats.total_calls == 3
    assert stats.successful_calls == 2
    assert stats.failed_calls == 1
    assert stats.success_rate == pytest.approx(2/3)
    assert stats.avg_latency_ms == pytest.approx(1100.0)  # (1000 + 1200) / 2
    assert stats.total_cost_usd == pytest.approx(0.11)


@pytest.mark.asyncio
async def test_get_model_stats(tracker):
    """Test getting stats for specific model."""
    await tracker.record_call("llama3", 500, 0.0, True)
    await tracker.record_call("gpt-4o", 1000, 0.05, True)

    llama_stats = tracker.get_model_stats("llama3")
    gpt_stats = tracker.get_model_stats("gpt-4o")

    assert llama_stats is not None
    assert llama_stats.model == "llama3"
    assert llama_stats.total_calls == 1

    assert gpt_stats is not None
    assert gpt_stats.model == "gpt-4o"
    assert gpt_stats.total_calls == 1


@pytest.mark.asyncio
async def test_get_all_stats(tracker):
    """Test getting all model statistics."""
    await tracker.record_call("llama3", 500, 0.0, True)
    await tracker.record_call("gpt-4o", 1000, 0.05, True)
    await tracker.record_call("mistral", 600, 0.0, True)

    all_stats = tracker.get_all_stats()

    assert len(all_stats) == 3
    assert "llama3" in all_stats
    assert "gpt-4o" in all_stats
    assert "mistral" in all_stats


@pytest.mark.asyncio
async def test_best_model_for_latency(tracker):
    """Test finding best model for latency."""
    await tracker.record_call("llama3", 2000, 0.0, True)
    await tracker.record_call("gpt-4o-mini", 800, 0.001, True)
    await tracker.record_call("gpt-4o", 1200, 0.05, True)

    best = tracker.get_best_model_for_latency()

    assert best == "gpt-4o-mini"  # Lowest latency


@pytest.mark.asyncio
async def test_best_model_for_cost(tracker):
    """Test finding best model for cost."""
    await tracker.record_call("llama3", 500, 0.0, True)
    await tracker.record_call("gpt-4o-mini", 800, 0.001, True)
    await tracker.record_call("gpt-4o", 1200, 0.05, True)

    best = tracker.get_best_model_for_cost()

    assert best == "llama3"  # Zero cost


@pytest.mark.asyncio
async def test_best_model_for_reliability(tracker):
    """Test finding best model for reliability."""
    # llama3: 2 successes, 0 failures (but < 5 calls, won't be selected)
    await tracker.record_call("llama3", 500, 0.0, True)
    await tracker.record_call("llama3", 600, 0.0, True)

    # gpt-4o: 5 successes, 0 failures (100% success rate)
    for _ in range(5):
        await tracker.record_call("gpt-4o", 1000, 0.05, True)

    # mistral: 6 successes, 2 failures (75% success rate)
    for _ in range(6):
        await tracker.record_call("mistral", 700, 0.0, True)
    for _ in range(2):
        await tracker.record_call("mistral", 0, 0.0, False)

    best = tracker.get_best_model_for_reliability()

    # gpt-4o has 100% success rate with >= 5 calls
    assert best == "gpt-4o"


@pytest.mark.asyncio
async def test_get_metrics_by_time_range(tracker):
    """Test filtering metrics by time range."""
    start = time.time()

    await tracker.record_call("model1", 100, 0.01, True)
    time.sleep(0.1)
    mid = time.time()
    time.sleep(0.1)
    await tracker.record_call("model2", 200, 0.02, True)
    end = time.time()

    # Get all metrics
    all_metrics = tracker.get_metrics_by_time_range(start, end)
    assert len(all_metrics) == 2

    # Get only first metric
    early_metrics = tracker.get_metrics_by_time_range(start, mid)
    assert len(early_metrics) == 1
    assert early_metrics[0].model == "model1"


@pytest.mark.asyncio
async def test_get_recent_metrics(tracker):
    """Test getting recent metrics."""
    # Add 10 metrics
    for i in range(10):
        await tracker.record_call(f"model{i}", 100, 0.01, True)

    # Get last 5
    recent = tracker.get_recent_metrics(count=5)

    assert len(recent) == 5
    assert recent[0].model == "model5"
    assert recent[-1].model == "model9"


@pytest.mark.asyncio
async def test_summary_report(tracker):
    """Test comprehensive summary report."""
    await tracker.record_call("llama3", 500, 0.0, True, quality_score=0.8, prompt_tokens=100, completion_tokens=50)
    await tracker.record_call("gpt-4o", 1200, 0.05, True, quality_score=0.9, prompt_tokens=200, completion_tokens=100)
    await tracker.record_call("gpt-4o", 0, 0.0, False)

    report = tracker.get_summary_report()

    assert report["total_calls"] == 3
    assert report["successful_calls"] == 2
    assert report["success_rate"] == pytest.approx(2/3)
    assert report["total_cost_usd"] == pytest.approx(0.05)
    assert report["total_tokens"] == 450  # 100+50+200+100
    assert report["avg_quality_score"] == pytest.approx(0.85)  # (0.8 + 0.9) / 2

    # Check model breakdown
    assert "llama3" in report["models"]
    assert "gpt-4o" in report["models"]

    # Check best models
    assert report["best_for_cost"] == "llama3"


@pytest.mark.asyncio
async def test_persistence(temp_storage):
    """Test metrics persistence to disk."""
    # Create tracker and add metrics
    tracker1 = PerformanceTracker(storage_path=temp_storage)
    await tracker1.record_call("llama3", 500, 0.0, True)
    await tracker1.record_call("gpt-4o", 1200, 0.05, True)

    # Create new tracker instance - should load existing metrics
    tracker2 = PerformanceTracker(storage_path=temp_storage)

    assert len(tracker2.metrics) == 2
    assert tracker2.get_model_stats("llama3") is not None
    assert tracker2.get_model_stats("gpt-4o") is not None


@pytest.mark.asyncio
async def test_export_to_csv(tracker, temp_storage):
    """Test CSV export."""
    await tracker.record_call("llama3", 500, 0.0, True, prompt_tokens=100, completion_tokens=50, task_type="code")
    await tracker.record_call("gpt-4o", 1200, 0.05, True, prompt_tokens=200, completion_tokens=100)

    csv_path = temp_storage.with_suffix(".csv")
    tracker.export_to_csv(csv_path)

    assert csv_path.exists()

    # Read and verify CSV
    with open(csv_path, "r") as f:
        lines = f.readlines()

    assert len(lines) == 3  # Header + 2 data rows
    assert "timestamp,datetime,model" in lines[0]
    assert "llama3" in lines[1]
    assert "gpt-4o" in lines[2]

    # Cleanup
    csv_path.unlink()


def test_model_stats_properties():
    """Test ModelStats calculated properties."""
    stats = ModelStats(
        model="test",
        total_calls=10,
        successful_calls=8,
        failed_calls=2,
        total_latency_ms=8000.0,
        total_cost_usd=0.50,
        total_tokens=5000,
    )

    assert stats.success_rate == 0.8
    assert stats.avg_latency_ms == 1000.0  # 8000 / 8 successful
    assert stats.avg_cost_per_call == 0.05  # 0.50 / 10


def test_performance_metric_serialization():
    """Test PerformanceMetric serialization."""
    metric = PerformanceMetric(
        timestamp=time.time(),
        model="test",
        latency_ms=100.5,
        cost_usd=0.01,
        success=True,
        quality_score=0.9,
        prompt_tokens=50,
        completion_tokens=25,
        task_type="code",
    )

    # To dict
    data = metric.to_dict()
    assert data["model"] == "test"
    assert data["latency_ms"] == 100.5

    # From dict
    metric2 = PerformanceMetric.from_dict(data)
    assert metric2.model == metric.model
    assert metric2.latency_ms == metric.latency_ms
