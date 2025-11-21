"""
Tests for brain module functionality.

STAGE 12: Tests project profiling, recommendations, and auto-tuning.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(agent_dir))

import brain  # noqa: E402


@pytest.fixture
def sample_runs():
    """Create sample run data for testing."""
    now = datetime.utcnow()
    runs = []

    # Project A - 3loop performs better
    for i in range(8):
        run_date = now - timedelta(days=i)
        mode = "3loop" if i % 2 == 0 else "2loop"
        cost = 0.8 if mode == "3loop" else 1.2  # 3loop cheaper
        qa_status = "passed" if mode == "3loop" else ("passed" if i % 3 == 0 else "warning")

        run = {
            "run_id": f"run_a_{i}",
            "started_at": run_date.isoformat() + "Z",
            "finished_at": (run_date + timedelta(minutes=5)).isoformat() + "Z",
            "mode": mode,
            "project_dir": "/sites/project_a",
            "rounds_completed": 2,
            "max_rounds": 5,
            "cost_summary": {
                "total_cost_usd": cost,
                "by_role": {
                    "manager": {"total_tokens": 1000, "total_cost_usd": cost * 0.2},
                    "employee": {"total_tokens": 3000, "total_cost_usd": cost * 0.8},
                }
            },
            "qa_status": qa_status,
            "config": {"prompt_strategy": "baseline"}
        }
        runs.append(run)

    return runs


def test_build_project_profile(sample_runs, monkeypatch):
    """Test project profile building."""
    # Mock load_all_runs to return our sample data
    def mock_load_runs():
        return sample_runs

    monkeypatch.setattr(brain.analytics, "load_all_runs", mock_load_runs)

    profile = brain.build_project_profile("project_a")

    assert profile.project_id == "project_a"
    assert profile.runs_count == 8
    assert profile.avg_cost > 0
    assert "3loop" in profile.modes
    assert "2loop" in profile.modes
    assert profile.avg_rounds_used > 0


def test_mode_stats_computation(sample_runs, monkeypatch):
    """Test per-mode statistics computation."""
    monkeypatch.setattr(brain.analytics, "load_all_runs", lambda: sample_runs)

    profile = brain.build_project_profile("project_a")

    # Should have stats for both modes
    assert "3loop" in profile.modes
    assert "2loop" in profile.modes

    mode_3loop = profile.modes["3loop"]
    mode_2loop = profile.modes["2loop"]

    # 3loop should have better (lower) cost
    assert mode_3loop.avg_cost < mode_2loop.avg_cost

    # 3loop should have better QA pass rate
    assert mode_3loop.qa_pass_rate > mode_2loop.qa_pass_rate


def test_preferred_mode_selection(sample_runs, monkeypatch):
    """Test that preferred mode is selected correctly."""
    monkeypatch.setattr(brain.analytics, "load_all_runs", lambda: sample_runs)

    profile = brain.build_project_profile("project_a")

    # 3loop should be preferred (better QA and lower cost)
    assert profile.preferred_mode == "3loop"


def test_recommend_mode_change():
    """Test mode change recommendation logic."""
    # Create mock profile where 3loop is clearly better
    profile = brain.ProjectProfile(project_id="test")
    profile.runs_count = 10
    profile.sufficient_data = True

    profile.modes["3loop"] = brain.ModeStats(
        mode="3loop",
        runs_count=5,
        median_cost=0.8,
        qa_pass_rate=1.0,
        avg_cost=0.8
    )

    profile.modes["2loop"] = brain.ModeStats(
        mode="2loop",
        runs_count=5,
        median_cost=1.2,
        qa_pass_rate=0.8,
        avg_cost=1.2
    )

    profile.preferred_mode = "3loop"

    # Current config uses 2loop
    current_config = {"mode": "2loop"}

    rec = brain._recommend_mode(profile, current_config)

    assert rec is not None
    assert rec.category == "mode"
    assert rec.current_value == "2loop"
    assert rec.recommended_value == "3loop"
    assert rec.confidence in ["high", "medium"]


def test_recommend_max_rounds():
    """Test max_rounds recommendation logic."""
    profile = brain.ProjectProfile(project_id="test")
    profile.runs_count = 10
    profile.sufficient_data = True

    # Most runs complete by round 2
    profile.rounds_distribution = {1: 2, 2: 6, 3: 2}
    profile.max_rounds_completed = 3
    profile.overall_qa_pass_rate = 0.9

    # Current config has max_rounds=5
    current_config = {"max_rounds": 5}

    rec = brain._recommend_max_rounds(profile, current_config)

    assert rec is not None
    assert rec.category == "rounds"
    assert rec.current_value == 5
    assert rec.recommended_value < 5  # Should recommend lower


def test_generate_recommendations(sample_runs, monkeypatch):
    """Test full recommendation generation."""
    monkeypatch.setattr(brain.analytics, "load_all_runs", lambda: sample_runs)

    profile = brain.build_project_profile("project_a")
    current_config = {
        "mode": "2loop",
        "max_rounds": 5,
        "max_cost_usd": 2.0
    }

    recommendations = brain.generate_recommendations(profile, current_config)

    # Should have at least one recommendation (mode change)
    assert len(recommendations) > 0

    # Should recommend switching to 3loop
    mode_recs = [r for r in recommendations if r.category == "mode"]
    if mode_recs:
        assert mode_recs[0].recommended_value == "3loop"


def test_apply_auto_tune():
    """Test auto-tune application."""
    config = {
        "mode": "2loop",
        "max_rounds": 5,
        "max_cost_usd": 1.5
    }

    recommendations = [
        brain.Recommendation(
            category="mode",
            current_value="2loop",
            recommended_value="3loop",
            explanation="3loop is better",
            confidence="high",
            estimated_impact="20% cost reduction"
        ),
        brain.Recommendation(
            category="rounds",
            current_value=5,
            recommended_value=3,
            explanation="Most runs finish by round 3",
            confidence="high",
            estimated_impact="Faster completion"
        )
    ]

    tuning_config = brain.TuningConfig(enabled=True, apply_safely=True)

    tuned_config = brain.apply_auto_tune(config, recommendations, tuning_config)

    # Should have applied recommendations
    assert tuned_config["mode"] == "3loop"
    assert tuned_config["max_rounds"] == 3
    assert tuned_config["_auto_tuned"] is True
    assert "mode=3loop" in tuned_config["_tuned_fields"]


def test_apply_auto_tune_skip_low_confidence():
    """Test that low-confidence recommendations are skipped in safe mode."""
    config = {"mode": "2loop"}

    recommendations = [
        brain.Recommendation(
            category="mode",
            current_value="2loop",
            recommended_value="3loop",
            explanation="Maybe better",
            confidence="low",
            estimated_impact="Unknown"
        )
    ]

    tuning_config = brain.TuningConfig(enabled=True, apply_safely=True)

    tuned_config = brain.apply_auto_tune(config, recommendations, tuning_config)

    # Should NOT have applied low-confidence recommendation in safe mode
    assert tuned_config["mode"] == "2loop"


def test_insufficient_data_handling(monkeypatch):
    """Test that insufficient data prevents recommendations."""
    # Only 2 runs - below threshold of 5
    runs = [
        {
            "run_id": "run_1",
            "started_at": "2024-01-01T10:00:00Z",
            "finished_at": "2024-01-01T10:05:00Z",
            "mode": "3loop",
            "project_dir": "/sites/test_proj",
            "rounds_completed": 2,
            "cost_summary": {"total_cost_usd": 1.0, "by_role": {}},
            "qa_status": "passed",
            "config": {"prompt_strategy": "baseline"}
        },
        {
            "run_id": "run_2",
            "started_at": "2024-01-02T10:00:00Z",
            "finished_at": "2024-01-02T10:05:00Z",
            "mode": "2loop",
            "project_dir": "/sites/test_proj",
            "rounds_completed": 2,
            "cost_summary": {"total_cost_usd": 1.2, "by_role": {}},
            "qa_status": "passed",
            "config": {"prompt_strategy": "baseline"}
        }
    ]

    monkeypatch.setattr(brain.analytics, "load_all_runs", lambda: runs)

    profile = brain.build_project_profile("test_proj")

    # Should have insufficient_data flag set
    assert profile.sufficient_data is False
    assert profile.runs_count < 5

    # Recommendations should be empty
    recommendations = brain.generate_recommendations(profile, {"mode": "2loop"})
    assert len(recommendations) == 0


def test_tuning_config_defaults():
    """Test tuning config loading with defaults."""
    config = brain.load_tuning_config()

    assert isinstance(config, brain.TuningConfig)
    assert config.min_runs_for_recommendations == 5
    assert config.apply_safely is True


def test_get_available_strategies():
    """Test loading available prompt strategies."""
    strategies = brain.get_available_strategies()

    assert isinstance(strategies, dict)
    assert "baseline" in strategies


def test_get_tuning_analysis(sample_runs, monkeypatch):
    """Test complete tuning analysis API."""
    monkeypatch.setattr(brain.analytics, "load_all_runs", lambda: sample_runs)

    current_config = {
        "mode": "2loop",
        "max_rounds": 5
    }

    analysis = brain.get_tuning_analysis("project_a", current_config)

    # Should have all expected keys
    assert "profile" in analysis
    assert "recommendations" in analysis
    assert "tuning_config" in analysis
    assert "available_strategies" in analysis

    # Profile should have data
    assert analysis["profile"]["runs_count"] == 8
    assert analysis["profile"]["project_id"] == "project_a"


def test_strategy_stats_computation():
    """Test per-strategy statistics."""
    runs = [
        {
            "run_id": "run_1",
            "started_at": "2024-01-01T10:00:00Z",
            "finished_at": "2024-01-01T10:05:00Z",
            "mode": "3loop",
            "project_dir": "/sites/test",
            "rounds_completed": 2,
            "cost_summary": {"total_cost_usd": 0.8, "by_role": {}},
            "qa_status": "passed",
            "config": {"prompt_strategy": "baseline"}
        },
        {
            "run_id": "run_2",
            "started_at": "2024-01-02T10:00:00Z",
            "finished_at": "2024-01-02T10:05:00Z",
            "mode": "3loop",
            "project_dir": "/sites/test",
            "rounds_completed": 2,
            "cost_summary": {"total_cost_usd": 1.5, "by_role": {}},
            "qa_status": "passed",
            "config": {"prompt_strategy": "fast_iter"}
        }
    ]

    stats = brain._compute_strategy_stats("baseline", [runs[0]])

    assert stats.strategy == "baseline"
    assert stats.runs_count == 1
    assert stats.avg_cost == 0.8
    assert stats.qa_pass_rate == 1.0
