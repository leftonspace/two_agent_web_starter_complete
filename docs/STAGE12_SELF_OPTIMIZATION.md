# STAGE 12: Self-Optimization & Auto-Tuning Layer ("Brain")

**Status**: ✅ Implemented

**Purpose**: Enable the orchestrator to learn from historical runs and automatically optimize settings for cost efficiency, quality, and performance.

---

## Overview

Stage 12 adds a self-learning "brain" that analyzes past performance and intelligently recommends better settings:

- **Project Profiling**: Historical behavior summaries per project
- **Intelligent Recommendations**: Data-driven suggestions for mode, rounds, cost limits, and prompt strategies
- **Prompt Strategies**: Named prompt sets with A/B testing and performance tracking
- **Auto-Tuning**: Optional automatic application of recommendations
- **Confidence Scoring**: High/medium/low confidence levels for each recommendation
- **Safety Mechanisms**: Minimum data requirements, safe mode, manual overrides
- **Web Dashboard**: UI for viewing recommendations and controlling auto-tune

The brain operates on existing run data and uses simple heuristics (no external ML frameworks required).

---

## Quick Start

### 1. Enable Auto-Tuning

Configure in `agent/project_config.json`:

```json
{
  "auto_tune": {
    "enabled": false,
    "apply_safely": true,
    "min_runs_for_recommendations": 5,
    "confidence_threshold": "medium"
  }
}
```

### 2. Access the Tuning Dashboard

Start the web server:

```bash
python -m agent.webapp.app
```

Navigate to:
```
http://127.0.0.1:8000/tuning
```

### 3. View Recommendations

The dashboard displays:
- **Project Profile**: Historical statistics and trends
- **Recommendations**: Specific suggested changes with explanations
- **Auto-Tune Toggle**: Enable/disable automatic application
- **Confidence Badges**: High/medium/low confidence indicators

### 4. Enable Auto-Tuning (Optional)

Toggle auto-tune in the UI or update config:

```json
{
  "auto_tune": {
    "enabled": true
  }
}
```

When enabled, recommendations are automatically applied before each run.

---

## Key Concepts

### Project Profiles

A **Project Profile** is a statistical summary of a project's historical behavior:

- **Mode Performance**: 2-loop vs 3-loop cost, QA pass rate, duration
- **Cost Distribution**: Min, median, max, and average costs
- **Rounds Usage**: Distribution of rounds completed, typical max_rounds needed
- **Strategy Performance**: Per-strategy cost and QA metrics
- **QA Trends**: Overall pass rate and status distribution
- **Preferred Settings**: Statistically best mode and strategy

Profiles require minimum 5 runs for reliability.

### Prompt Strategies

**Prompt Strategies** are named sets of prompts that can be A/B tested:

```json
{
  "prompts": {
    "default_strategy": "baseline",
    "strategies": {
      "baseline": {
        "file": "prompts_default.json",
        "description": "Default balanced prompts for quality and cost"
      },
      "aggressive_refactor": {
        "file": "prompts_aggressive.json",
        "description": "Aggressive refactoring and optimization"
      },
      "fast_iter": {
        "file": "prompts_fast.json",
        "description": "Fast iteration with minimal validation"
      }
    }
  }
}
```

Each strategy's performance is tracked independently, enabling data-driven selection.

### Recommendations

A **Recommendation** suggests a specific configuration change:

```python
@dataclass
class Recommendation:
    category: str              # "mode", "rounds", "cost", "strategy"
    current_value: Any         # Current configuration value
    recommended_value: Any     # Suggested new value
    explanation: str           # Why this change is suggested
    confidence: str            # "high", "medium", "low"
    estimated_impact: str      # Expected benefit
```

Recommendations are generated based on:
- **Statistical significance**: Minimum sample sizes per mode/strategy
- **Quality priority**: QA pass rate weighted 70%, cost weighted 30%
- **Threshold requirements**: Changes must show >15% improvement
- **Confidence levels**: Based on sample size and variance

### Auto-Tuning

**Auto-Tuning** automatically applies recommendations before runs:

1. Load project profile from historical data
2. Generate recommendations based on current config
3. Apply recommendations with confidence filtering
4. Mark config with `_auto_tuned` flag
5. Track which fields were tuned in `_tuned_fields`

Safety features:
- **Opt-in**: Disabled by default
- **Safe Mode**: Skip low-confidence recommendations
- **Graceful Fallback**: Errors don't block runs
- **Manual Override**: User can always override settings
- **Reversible**: Original config preserved

---

## Architecture

### Core Components

1. **`agent/brain.py`** (753 lines) - Self-optimization engine
2. **`agent/project_config.json`** - Configuration with prompts and auto-tune sections
3. **`agent/runner.py`** - Integration point for applying tuning
4. **`agent/webapp/app.py`** - API endpoints for tuning
5. **`agent/webapp/templates/tuning.html`** - Tuning dashboard UI

### Data Models

#### `ProjectProfile`

Complete historical profile for a project:

```python
@dataclass
class ProjectProfile:
    project_id: str
    runs_count: int
    modes: Dict[str, ModeStats]
    preferred_mode: Optional[str]
    min_cost: float
    median_cost: float
    max_cost: float
    avg_cost: float
    avg_rounds_used: float
    max_rounds_completed: int
    rounds_distribution: Dict[int, int]
    strategies: Dict[str, StrategyStats]
    preferred_strategy: Optional[str]
    overall_qa_pass_rate: float
    sufficient_data: bool
```

#### `ModeStats`

Statistics for a single mode (2-loop or 3-loop):

```python
@dataclass
class ModeStats:
    mode: str
    runs_count: int
    avg_cost: float
    median_cost: float
    min_cost: float
    max_cost: float
    avg_duration: float
    qa_pass_rate: float
    qa_passed: int
    qa_warning: int
    qa_failed: int
```

#### `StrategyStats`

Statistics for a prompt strategy:

```python
@dataclass
class StrategyStats:
    strategy: str
    runs_count: int
    avg_cost: float
    median_cost: float
    qa_pass_rate: float
    avg_duration: float
```

#### `Recommendation`

Single tuning suggestion:

```python
@dataclass
class Recommendation:
    category: str              # "mode", "rounds", "cost", "strategy"
    current_value: Any
    recommended_value: Any
    explanation: str
    confidence: str            # "high", "medium", "low"
    estimated_impact: str
```

#### `TuningConfig`

Auto-tuning behavior configuration:

```python
@dataclass
class TuningConfig:
    enabled: bool
    apply_safely: bool
    min_runs_for_recommendations: int
    confidence_threshold: str
```

---

## Recommendation Logic

### Mode Recommendation

Recommends switching between 2-loop and 3-loop:

**Criteria**:
- Minimum 3 runs per mode
- Preferred mode has similar or better QA pass rate (within 5%)
- Preferred mode costs >15% less
- Current config uses non-preferred mode

**Confidence**:
- **High**: 5+ runs per mode, QA difference <2%, cost savings >20%
- **Medium**: 3+ runs per mode, QA difference <5%, cost savings >15%
- **Low**: Otherwise

**Example**:
```
Current: 2loop
Recommended: 3loop
Explanation: 3loop has similar QA pass rate (95% vs 97%) but costs 23% less ($0.80 vs $1.04)
Confidence: high
Impact: ~$0.24 savings per run
```

### Max Rounds Recommendation

Recommends adjusting `max_rounds` based on actual usage:

**Recommend Lower** when:
- 95%+ of runs complete before reaching max_rounds
- Current max_rounds is >2 rounds higher than typical usage
- Overall QA pass rate >80% (quality is good)

**Recommend Higher** when:
- 20%+ of runs hit max_rounds limit
- Likely incomplete work due to round limit

**Confidence**:
- **High**: 10+ runs with consistent pattern
- **Medium**: 5-9 runs with clear trend
- **Low**: <5 runs or high variance

**Example**:
```
Current: max_rounds=5
Recommended: max_rounds=3
Explanation: 95% of runs complete by round 3, QA pass rate is 92%
Confidence: high
Impact: Faster completion, clearer expectations
```

### Cost Limit Recommendation

Recommends adjusting `max_cost_usd` to match actual needs:

**Recommend Increase** when:
- Historical max cost exceeds current limit
- Suggest: historical_max * 1.2 (20% buffer)

**Recommend Decrease** when:
- Current limit is >30% higher than historical max
- Suggest: historical_max * 1.2 (appropriate buffer)

**Confidence**:
- **High**: 10+ runs, stable cost pattern
- **Medium**: 5-9 runs
- **Low**: <5 runs

**Example**:
```
Current: max_cost_usd=2.0
Recommended: max_cost_usd=1.2
Explanation: Historical max cost is $0.95. Current limit is 110% higher than needed.
Confidence: medium
Impact: Better cost control without restricting runs
```

### Strategy Recommendation

Recommends switching prompt strategies:

**Criteria**:
- Minimum 3 runs per strategy
- Alternative strategy has better weighted score:
  - Score = (QA_rate * 0.7) + (1/cost * 0.3)
- Score difference >10%

**Confidence**:
- **High**: 5+ runs per strategy, QA both >85%
- **Medium**: 3+ runs per strategy, QA both >70%
- **Low**: Otherwise

**Example**:
```
Current: baseline
Recommended: fast_iter
Explanation: fast_iter has similar QA (93% vs 95%) but 18% lower cost
Confidence: high
Impact: ~$0.15 savings per run
```

---

## Web Dashboard

### Profile Statistics

Six key metric cards:

1. **Total Runs** - Historical run count for this project
2. **Average Cost** - Mean cost with min-max range
3. **QA Pass Rate** - Percentage with color coding
4. **Avg Rounds Used** - Typical rounds completed
5. **Preferred Mode** - Best performing mode (2loop/3loop)
6. **Preferred Strategy** - Best performing prompt strategy

### Recommendations Display

Each recommendation shown with:
- **Category Badge**: mode / rounds / cost / strategy
- **Confidence Badge**: Color-coded (green=high, yellow=medium, gray=low)
- **Change Visualization**: `current_value → recommended_value`
- **Explanation**: Why this change is suggested
- **Estimated Impact**: Expected benefit

### Auto-Tune Toggle

Interactive toggle switch:
- **Enabled**: Recommendations automatically applied before runs
- **Disabled**: Recommendations shown but not applied
- Updates backend config via POST request
- Shows current state with smooth animations

### Insufficient Data Warning

Displayed when `runs_count < min_runs_for_recommendations`:
```
⚠️ Insufficient data for recommendations.
Need 5 runs, currently have 2 runs.
```

### How Auto-Tune Works

Explanatory section covering:
- Data analysis process
- Recommendation generation
- Automatic application (when enabled)
- Safety mechanisms
- Manual override capability

---

## API Endpoints

### GET `/tuning`

Tuning dashboard page (HTML).

**Response**: Rendered HTML template with profile, recommendations, and config

---

### GET `/api/projects/{project_id}/profile`

Get complete tuning analysis for a project.

**Path Parameters**:
- `project_id`: Project directory name

**Response**:
```json
{
  "profile": {
    "project_id": "contafuel_marketing",
    "runs_count": 12,
    "sufficient_data": true,
    "modes": {
      "3loop": {
        "mode": "3loop",
        "runs_count": 7,
        "avg_cost": 0.82,
        "median_cost": 0.80,
        "qa_pass_rate": 0.95
      },
      "2loop": {
        "mode": "2loop",
        "runs_count": 5,
        "avg_cost": 1.15,
        "median_cost": 1.12,
        "qa_pass_rate": 0.90
      }
    },
    "preferred_mode": "3loop",
    "avg_cost": 0.95,
    "median_cost": 0.92,
    "min_cost": 0.65,
    "max_cost": 1.45,
    "avg_rounds_used": 2.3,
    "max_rounds_completed": 3,
    "rounds_distribution": {"1": 1, "2": 7, "3": 4},
    "overall_qa_pass_rate": 0.92
  },
  "recommendations": [
    {
      "category": "mode",
      "current_value": "2loop",
      "recommended_value": "3loop",
      "explanation": "3loop has similar QA pass rate (95% vs 90%) but costs 29% less",
      "confidence": "high",
      "estimated_impact": "~$0.33 savings per run"
    }
  ],
  "tuning_config": {
    "enabled": false,
    "apply_safely": true,
    "min_runs_for_recommendations": 5,
    "confidence_threshold": "medium"
  },
  "available_strategies": {
    "baseline": {
      "file": "prompts_default.json",
      "description": "Default balanced prompts for quality and cost"
    }
  }
}
```

---

### GET `/api/projects/{project_id}/recommendations`

Get only recommendations for a project.

**Path Parameters**:
- `project_id`: Project directory name

**Query Parameters**:
- `current_config`: JSON string of current configuration (optional)

**Response**:
```json
{
  "recommendations": [
    {
      "category": "rounds",
      "current_value": 5,
      "recommended_value": 3,
      "explanation": "95% of runs complete by round 3, QA pass rate is 92%",
      "confidence": "high",
      "estimated_impact": "Faster completion, clearer expectations"
    }
  ],
  "profile_summary": {
    "runs_count": 12,
    "sufficient_data": true
  }
}
```

---

### POST `/api/auto-tune/toggle`

Enable or disable auto-tuning globally.

**Form Data**:
- `enabled`: boolean (true/false)

**Response**:
```json
{
  "success": true,
  "enabled": true,
  "message": "Auto-tune enabled"
}
```

---

### GET `/api/strategies`

Get available prompt strategies.

**Response**:
```json
{
  "default_strategy": "baseline",
  "strategies": {
    "baseline": {
      "file": "prompts_default.json",
      "description": "Default balanced prompts for quality and cost"
    },
    "aggressive_refactor": {
      "file": "prompts_aggressive.json",
      "description": "Aggressive refactoring and optimization"
    }
  }
}
```

---

## Configuration Reference

### Complete Auto-Tune Configuration

In `agent/project_config.json`:

```json
{
  "prompts": {
    "default_strategy": "baseline",
    "strategies": {
      "baseline": {
        "file": "prompts_default.json",
        "description": "Default balanced prompts for quality and cost"
      },
      "aggressive_refactor": {
        "file": "prompts_aggressive.json",
        "description": "Aggressive refactoring and optimization"
      },
      "fast_iter": {
        "file": "prompts_fast.json",
        "description": "Fast iteration with minimal validation"
      }
    }
  },
  "auto_tune": {
    // Enable/disable automatic application of recommendations
    "enabled": false,

    // Skip low-confidence recommendations in safe mode
    "apply_safely": true,

    // Minimum runs required before generating recommendations
    "min_runs_for_recommendations": 5,

    // Minimum confidence level to apply ("high", "medium", "low")
    "confidence_threshold": "medium"
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `prompts.default_strategy` | string | `"baseline"` | Default prompt strategy to use |
| `prompts.strategies` | object | `{}` | Named prompt strategies with file and description |
| `auto_tune.enabled` | boolean | `false` | Enable automatic application of recommendations |
| `auto_tune.apply_safely` | boolean | `true` | Skip low-confidence recommendations |
| `auto_tune.min_runs_for_recommendations` | integer | `5` | Minimum runs needed for recommendations |
| `auto_tune.confidence_threshold` | string | `"medium"` | Minimum confidence level to apply |

---

## Programmatic Usage

### Build Project Profile

```python
from brain import build_project_profile

# Build profile from historical data
profile = build_project_profile("contafuel_marketing")

print(f"Total runs: {profile.runs_count}")
print(f"Preferred mode: {profile.preferred_mode}")
print(f"Average cost: ${profile.avg_cost:.2f}")
print(f"QA pass rate: {profile.overall_qa_pass_rate:.1%}")

# Check mode performance
if "3loop" in profile.modes:
    mode_3loop = profile.modes["3loop"]
    print(f"3loop: {mode_3loop.runs_count} runs, ${mode_3loop.avg_cost:.2f}, {mode_3loop.qa_pass_rate:.1%} QA")
```

### Generate Recommendations

```python
from brain import generate_recommendations

current_config = {
    "mode": "2loop",
    "max_rounds": 5,
    "max_cost_usd": 2.0
}

recommendations = generate_recommendations(profile, current_config)

for rec in recommendations:
    print(f"\n{rec.category.upper()} ({rec.confidence} confidence)")
    print(f"  Current: {rec.current_value}")
    print(f"  Recommended: {rec.recommended_value}")
    print(f"  Reason: {rec.explanation}")
    print(f"  Impact: {rec.estimated_impact}")
```

### Apply Auto-Tuning

```python
from brain import apply_auto_tune, load_tuning_config

tuning_config = load_tuning_config()

if tuning_config.enabled:
    tuned_config = apply_auto_tune(config, recommendations, tuning_config)

    if tuned_config.get("_auto_tuned"):
        print("Auto-tuning applied:")
        for field in tuned_config.get("_tuned_fields", []):
            print(f"  - {field}")
```

### Get Complete Analysis

```python
from brain import get_tuning_analysis

analysis = get_tuning_analysis("contafuel_marketing", current_config)

print(f"Profile: {analysis['profile']['runs_count']} runs")
print(f"Recommendations: {len(analysis['recommendations'])}")
print(f"Auto-tune enabled: {analysis['tuning_config']['enabled']}")
```

### Load Available Strategies

```python
from brain import get_available_strategies

strategies = get_available_strategies()

print(f"Default strategy: {strategies['default_strategy']}")
for name, info in strategies['strategies'].items():
    print(f"  {name}: {info['description']}")
```

---

## Integration with Runner

The runner automatically applies auto-tuning before each run:

```python
# In agent/runner.py

# STAGE 12: Apply auto-tuning if enabled
original_config = config.copy()
project_subdir = config.get("project_subdir")

try:
    tuning_config = brain.load_tuning_config()
    if tuning_config.enabled and not config.get("_skip_auto_tune", False):
        # Build project profile
        profile = brain.build_project_profile(project_subdir)

        # Generate recommendations
        recommendations = brain.generate_recommendations(profile, config)

        # Apply recommendations if sufficient data
        if recommendations:
            config = brain.apply_auto_tune(config, recommendations, tuning_config)
            print(f"[BRAIN] Auto-tune applied {len(recommendations)} recommendations")
            for rec in recommendations:
                print(f"  - {rec.category}: {rec.current_value} → {rec.recommended_value}")
except Exception as e:
    # Auto-tune failures should not block runs
    print(f"[BRAIN] Auto-tune failed (continuing with original config): {e}")
    config = original_config
```

Run metadata tracks auto-tuning:

```python
run_config["prompt_strategy"] = prompt_strategy
run_config["auto_tuned"] = config.get("_auto_tuned", False)
if config.get("_tuned_fields"):
    run_config["tuned_fields"] = config.get("_tuned_fields")
```

---

## Testing

### Run Brain Tests

```bash
cd agent/
pytest tests_stage12/ -v
```

### Test Coverage

- ✓ Project profile building
- ✓ Mode statistics computation
- ✓ Preferred mode selection (70/30 QA/cost weighting)
- ✓ Mode recommendation logic
- ✓ Max rounds recommendation logic
- ✓ Cost limit recommendation logic
- ✓ Strategy recommendation logic
- ✓ Full recommendation generation
- ✓ Auto-tune application
- ✓ Safe mode (skip low-confidence)
- ✓ Insufficient data handling
- ✓ Configuration loading
- ✓ Strategy listing
- ✓ Complete tuning analysis API

### Example Test

```python
def test_recommend_mode_change():
    """Test mode change recommendation logic."""
    profile = brain.ProjectProfile(project_id="test")
    profile.runs_count = 10
    profile.sufficient_data = True

    # 3loop performs better
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
```

---

## Troubleshooting

### No Recommendations Shown

**Cause**: Insufficient run history

**Solution**:
1. Check `runs_count >= min_runs_for_recommendations` (default 5)
2. Run more projects to build historical data
3. Verify `run_logs/` contains run summaries
4. Check that runs belong to the same project

---

### Auto-Tune Not Applying

**Cause**: Auto-tune disabled or safe mode filtering

**Solution**:
1. Verify `auto_tune.enabled = true` in config
2. Check recommendations have sufficient confidence
3. If `apply_safely = true`, only high/medium confidence applied
4. Review runner logs for `[BRAIN]` messages

---

### Recommendations Seem Wrong

**Cause**: Insufficient data or skewed sample

**Solution**:
1. Check sample size per mode/strategy (need 3+ runs each)
2. Look for outliers affecting averages
3. Verify QA data is accurate
4. Check if recent runs are representative

---

### Strategy Not Tracked

**Cause**: Strategy not defined or not selected

**Solution**:
1. Add strategy to `prompts.strategies` in config
2. Set `prompts.default_strategy` or specify at runtime
3. Verify strategy name matches config exactly
4. Check run metadata includes `prompt_strategy` field

---

### Dashboard Shows Old Data

**Cause**: Cache or stale run data

**Solution**:
1. Refresh browser page (F5)
2. Check `run_logs/` for recent run summaries
3. Verify run timestamps are current
4. Look for errors in server logs

---

## Safety Mechanisms

### Minimum Data Requirements

- **Overall**: 5 runs minimum before any recommendations
- **Per-Mode**: 3 runs per mode for mode comparisons
- **Per-Strategy**: 3 runs per strategy for strategy comparisons

### Confidence Filtering

In safe mode (`apply_safely = true`):
- **High confidence**: Always applied
- **Medium confidence**: Applied if threshold = "medium" or "low"
- **Low confidence**: Skipped unless threshold = "low"

### Graceful Degradation

Auto-tune failures never block runs:
```python
try:
    config = brain.apply_auto_tune(...)
except Exception as e:
    print(f"[BRAIN] Auto-tune failed: {e}")
    config = original_config  # Fallback to original
```

### Manual Override

Users can always override auto-tuned settings:
- Modify `project_config.json`
- Pass explicit parameters to runner
- Disable auto-tune temporarily with `_skip_auto_tune = true`

### Reversibility

Original configuration preserved:
- Auto-tuned config marked with `_auto_tuned = true`
- Tuned fields tracked in `_tuned_fields` list
- Original values remain in run logs
- Can disable auto-tune anytime

---

## Performance Considerations

### Data Loading

- Loads all runs via `analytics.load_all_runs()`
- Filters by project for profile building
- With 1000+ runs, profile building takes 1-2 seconds
- Consider archiving old runs if performance degrades

### Recommendation Generation

- Lightweight statistical computations
- No external ML libraries or models
- Near-instant generation (<100ms)
- Scales to hundreds of runs without issues

### Caching Opportunities

Current implementation recomputes on every request. Future optimizations:
1. Cache profiles for 5 minutes
2. Invalidate cache on new run completion
3. Pre-compute profiles for common projects

---

## Best Practices

### Getting Started

1. **Collect Baseline Data**: Run 5-10 projects with default settings
2. **Review Recommendations**: Check tuning dashboard for suggestions
3. **Enable Manually First**: Apply recommendations manually to verify
4. **Enable Auto-Tune**: Once confident, enable automatic application
5. **Monitor Results**: Watch analytics for cost/quality trends

### A/B Testing Strategies

1. **Define Strategies**: Create 2-3 prompt variants
2. **Alternate Manually**: Run each strategy 3-5 times
3. **Review Stats**: Compare cost and QA pass rates
4. **Select Winner**: Update `default_strategy` to best performer
5. **Continue Testing**: Try new variants over time

### Cost Optimization

1. **Start with 3-loop**: Generally more cost-efficient
2. **Monitor QA**: Ensure quality doesn't degrade
3. **Adjust Rounds**: Lower max_rounds if runs finish early
4. **Refine Prompts**: Test leaner prompt strategies
5. **Track Savings**: Use analytics to measure improvements

### Quality Assurance

1. **Weight QA Highly**: Brain uses 70/30 QA/cost weighting
2. **Set QA Baselines**: Aim for >85% pass rate
3. **Investigate Failures**: Review failed runs before auto-tuning
4. **Safe Mode On**: Keep `apply_safely = true` until confident
5. **Gradual Rollout**: Test on one project before enabling globally

---

## Future Enhancements

Potential improvements for future iterations:

1. **Advanced Scoring**
   - Multi-objective optimization
   - Pareto frontier analysis
   - Custom weighting per user

2. **Time-Aware Recommendations**
   - Weight recent runs more heavily
   - Detect regime changes
   - Seasonal adjustment

3. **Strategy Auto-Generation**
   - Automatically create prompt variants
   - Genetic algorithm for prompt evolution
   - A/B test framework

4. **Predictive Modeling**
   - Estimate run cost before execution
   - Predict QA pass likelihood
   - Anomaly detection

5. **Multi-Project Learning**
   - Transfer learning across projects
   - Cross-project benchmarking
   - Shared strategy library

6. **Advanced UI**
   - Interactive recommendation tuning
   - Custom confidence thresholds
   - What-if analysis
   - Historical recommendation tracking

7. **Integration**
   - Slack/email notifications for recommendations
   - CI/CD pipeline integration
   - API for external optimization tools

---

## Summary

Stage 12 provides a self-optimizing "brain" that:

- ✅ Learns from historical run data
- ✅ Generates intelligent recommendations with explanations
- ✅ Supports A/B testing of prompt strategies
- ✅ Automatically applies tuning when enabled
- ✅ Prioritizes quality (70%) over cost (30%)
- ✅ Requires minimum data before recommending
- ✅ Filters by confidence in safe mode
- ✅ Never blocks runs (graceful degradation)
- ✅ Supports manual overrides anytime
- ✅ Provides comprehensive web dashboard

The brain helps teams continuously improve their AI development workflow, reducing costs while maintaining quality standards.

---

For questions or issues, see the main README or create an issue on GitHub.
