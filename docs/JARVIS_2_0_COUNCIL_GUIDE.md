# JARVIS 2.0 Council System Tuning Guide

**Version:** 2.0.0
**Date:** November 23, 2025

The Council System is JARVIS 2.0's unique gamified meta-orchestration layer. This guide covers tuning and optimization for optimal performance.

---

## Table of Contents

1. [Council System Overview](#council-system-overview)
2. [Core Concepts](#core-concepts)
3. [Councillor Configuration](#councillor-configuration)
4. [Vote Weight Tuning](#vote-weight-tuning)
5. [Happiness System](#happiness-system)
6. [Performance Metrics](#performance-metrics)
7. [Fire/Spawn Mechanics](#firespawn-mechanics)
8. [Tuning Strategies](#tuning-strategies)
9. [Monitoring & Debugging](#monitoring--debugging)
10. [Advanced Configurations](#advanced-configurations)

---

## Council System Overview

The Council System transforms agent coordination into a gamified system where AI "councillors" vote on decisions, earn rewards, and can be fired for poor performance.

```
                    ┌────────────────────────────────────┐
                    │         Council Leader             │
                    │    (JARVIS - Meta-Orchestrator)    │
                    └─────────────────┬──────────────────┘
                                      │
                                      ▼
                    ┌────────────────────────────────────┐
                    │         Voting Session             │
                    │  "How should we approach this?"    │
                    └─────────────────┬──────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
   ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
   │    Ada      │           │    Bob      │           │   Charlie   │
   │  (Coding)   │           │  (Design)   │           │  (Testing)  │
   │             │           │             │           │             │
   │ Perf: 92%   │           │ Perf: 78%   │           │ Perf: 85%   │
   │ Happy: 80   │           │ Happy: 65   │           │ Happy: 72   │
   │ Weight: 1.84│           │ Weight: 1.0 │           │ Weight: 1.36│
   └─────────────┘           └─────────────┘           └─────────────┘
          │                           │                           │
          │        Vote: Complex      │     Vote: Standard        │
          │        Conf: 0.9          │     Conf: 0.7             │
          │                           │     Vote: Complex         │
          │                           │     Conf: 0.8             │
          ▼                           ▼                           ▼
                    ┌────────────────────────────────────┐
                    │    Weighted Tally → Winner         │
                    │    Complex: 1.84×0.9 + 1.36×0.8   │
                    │    Standard: 1.0×0.7              │
                    │    Result: Complex wins           │
                    └────────────────────────────────────┘
```

### Key Benefits

- **Incentive Alignment**: Councillors motivated by performance metrics
- **Democratic Decisions**: Weighted voting prevents single-point failures
- **Self-Healing**: Underperformers automatically replaced
- **Adaptability**: Council composition evolves with task needs

---

## Core Concepts

### Councillor

A specialized AI agent with:

| Attribute | Description | Range |
|-----------|-------------|-------|
| `id` | Unique identifier | string |
| `name` | Display name | string |
| `specialization` | Domain expertise | enum |
| `performance` | Performance metrics | 0.0-1.0 |
| `happiness` | Mood/satisfaction | 0-100 |
| `vote_weight` | Influence in votes | 0.0-2.0+ |
| `status` | active, probation, suspended | enum |

### Vote Weight Formula

```
vote_weight = base_weight × performance_coefficient × happiness_modifier × specialization_bonus

Where:
- base_weight = 1.0
- performance_coefficient = 0.5 + (performance × 1.5)  # Range: 0.5-2.0
- happiness_modifier = 0.8 + (happiness/100 × 0.4)     # Range: 0.8-1.2
- specialization_bonus = 1.0-1.5 based on task match
```

### Performance Metrics

```python
@dataclass
class PerformanceMetrics:
    quality_score: float     # Output quality (0-1)
    speed_score: float       # Completion speed (0-1)
    feedback_score: float    # Review feedback (0-1)
    success_rate: float      # Task completion rate (0-1)

    @property
    def overall(self) -> float:
        """Weighted average of all metrics."""
        return (
            self.quality_score * 0.4 +
            self.speed_score * 0.2 +
            self.feedback_score * 0.2 +
            self.success_rate * 0.2
        )
```

---

## Councillor Configuration

### Basic Setup

```yaml
# config/council.yaml
council:
  enabled: true
  min_councillors: 3
  max_councillors: 10

  # Initial councillor pool
  councillors:
    - id: ada_001
      name: "Ada"
      specialization: coding
      initial_performance: 0.8
      initial_happiness: 70

    - id: bob_002
      name: "Bob"
      specialization: design
      initial_performance: 0.75
      initial_happiness: 70

    - id: charlie_003
      name: "Charlie"
      specialization: testing
      initial_performance: 0.82
      initial_happiness: 70
```

### Specialization Configuration

```yaml
specializations:
  coding:
    description: "Software development and debugging"
    weight_bonus: 1.3
    required_count: 2
    task_types:
      - code_generation
      - debugging
      - refactoring

  design:
    description: "UI/UX and system design"
    weight_bonus: 1.2
    required_count: 1
    task_types:
      - ui_design
      - architecture
      - prototyping

  testing:
    description: "Quality assurance and testing"
    weight_bonus: 1.1
    required_count: 1
    task_types:
      - unit_testing
      - integration_testing
      - code_review

  review:
    description: "Code review and quality gates"
    weight_bonus: 1.2
    required_count: 1
    task_types:
      - code_review
      - security_review
      - documentation_review

  architecture:
    description: "System architecture and planning"
    weight_bonus: 1.4
    required_count: 1
    task_types:
      - system_design
      - technical_planning
      - infrastructure
```

---

## Vote Weight Tuning

### Understanding Vote Weights

```
Example Councillor: Ada
- Performance: 92% (0.92)
- Happiness: 80
- Specialization: coding (bonus: 1.3)
- Task type: code_generation (matches specialization)

Calculation:
- base_weight = 1.0
- performance_coefficient = 0.5 + (0.92 × 1.5) = 1.88
- happiness_modifier = 0.8 + (80/100 × 0.4) = 1.12
- specialization_bonus = 1.3 (task matches)

Final: 1.0 × 1.88 × 1.12 × 1.3 = 2.74
```

### Tuning Parameters

```yaml
voting:
  # Weight calculation parameters
  weights:
    base: 1.0
    performance:
      min_coefficient: 0.5    # Floor for poor performers
      max_coefficient: 2.0    # Ceiling for top performers
      scaling_factor: 1.5     # How much performance matters
    happiness:
      min_modifier: 0.8       # Unhappy penalty
      max_modifier: 1.2       # Happy bonus
      scaling_factor: 0.4     # How much happiness matters
    specialization:
      coding: 1.3
      design: 1.2
      testing: 1.1
      review: 1.2
      architecture: 1.4
```

### Impact Analysis

| Performance | Happiness | Specialization Match | Vote Weight |
|-------------|-----------|---------------------|-------------|
| 100% | 100 | Yes (1.3) | 3.12 |
| 100% | 100 | No (1.0) | 2.40 |
| 80% | 70 | Yes (1.3) | 2.16 |
| 80% | 70 | No (1.0) | 1.66 |
| 50% | 50 | Yes (1.3) | 1.30 |
| 50% | 50 | No (1.0) | 1.00 |
| 40% | 30 | No (1.0) | 0.74 |

### Balancing Strategies

**High-Stakes Decisions (Conservative):**
```yaml
voting:
  weights:
    performance:
      scaling_factor: 2.0    # Performance matters more
    specialization:
      coding: 1.5            # Experts weighted higher
```

**Collaborative Environment (Balanced):**
```yaml
voting:
  weights:
    performance:
      min_coefficient: 0.7   # Less penalty for low performers
      scaling_factor: 1.0    # Performance matters less
    happiness:
      scaling_factor: 0.6    # Happiness matters more
```

---

## Happiness System

### Happiness Events

```yaml
happiness:
  initial_value: 70
  min_value: 0
  max_value: 100

  events:
    # Positive events
    task_success: 5
    bonus_received: 15
    praise: 8
    vote_won: 3
    new_colleague: 2
    vacation: 20
    promotion: 25
    streak_bonus: 10       # 5+ successful tasks

    # Negative events
    task_failure: -8
    criticism: -10
    overworked: -12        # >3 tasks without break
    vote_ignored: -5
    colleague_fired: -8
    deadline_missed: -15
    bug_in_production: -20

  # Decay over time
  decay:
    enabled: true
    rate: 0.02             # 2% per day
    min_threshold: 50      # Don't decay below 50
```

### Happiness Effects

```yaml
happiness:
  effects:
    # Work quality modifier based on happiness
    quality_modifiers:
      0-20:   0.7          # Very unhappy: 30% quality reduction
      21-40:  0.85         # Unhappy: 15% reduction
      41-60:  0.95         # Neutral: 5% reduction
      61-80:  1.0          # Happy: Normal
      81-100: 1.1          # Very happy: 10% bonus

    # Burnout risk thresholds
    burnout:
      threshold: 25        # Below this, burnout risk
      effects:
        - reduced_output
        - increased_errors
        - slower_response

    # Voluntary leave risk
    leave_risk:
      threshold: 15        # Below this, may "quit"
      probability: 0.1     # 10% chance per evaluation
```

### Managing Happiness

**Boosting Happiness:**
```python
# Give praise after good work
await happiness_manager.apply_event(
    councillor=ada,
    event=HappinessEvent.PRAISE,
    reason="Excellent code quality in last PR"
)

# Award bonuses
await happiness_manager.apply_event(
    councillor=ada,
    event=HappinessEvent.BONUS_RECEIVED,
    reason="Top performer this sprint"
)

# Grant vacation (reset happiness to 90)
await happiness_manager.grant_vacation(councillor=ada)
```

**Preventing Burnout:**
```python
# Check workload before assignment
workload = await council.get_workload(councillor=ada)
if workload.tasks_since_break > 3:
    # Assign to someone else or give break
    await happiness_manager.apply_event(
        councillor=ada,
        event=HappinessEvent.OVERWORKED
    )
```

---

## Performance Metrics

### Metric Collection

```yaml
performance:
  metrics:
    quality:
      weight: 0.4
      sources:
        - code_review_scores
        - test_pass_rates
        - bug_reports
      decay: 0.1           # 10% weight to older measurements

    speed:
      weight: 0.2
      sources:
        - task_completion_time
        - response_latency
      baseline_ms: 30000   # 30 second baseline

    feedback:
      weight: 0.2
      sources:
        - peer_reviews
        - user_satisfaction
      scale: 1-5

    success_rate:
      weight: 0.2
      window: 20           # Last 20 tasks
      threshold: 0.8       # 80% success expected
```

### Performance Evaluation

```python
# Automatic evaluation after each task
async def evaluate_performance(councillor: Councillor, task_result: TaskResult):
    metrics = councillor.performance

    # Update quality score
    if task_result.review_score:
        metrics.quality_score = (
            metrics.quality_score * 0.9 +
            task_result.review_score * 0.1
        )

    # Update speed score
    expected_time = get_expected_time(task_result.task_type)
    actual_time = task_result.completion_time
    speed_ratio = min(expected_time / actual_time, 1.5)
    metrics.speed_score = (
        metrics.speed_score * 0.9 +
        (speed_ratio / 1.5) * 0.1
    )

    # Update success rate
    metrics.success_rate = councillor.success_count / councillor.task_count

    # Recalculate overall
    councillor.performance = metrics
    councillor.vote_weight = calculate_vote_weight(councillor)
```

### Performance Thresholds

```yaml
performance:
  thresholds:
    excellent: 0.9         # Top performer status
    good: 0.7              # Normal performance
    warning: 0.5           # Performance improvement needed
    critical: 0.4          # Fire consideration

  actions:
    excellent:
      - bonus_eligible
      - promotion_eligible
      - increased_responsibility

    warning:
      - performance_review
      - reduced_task_complexity
      - mentorship_assigned

    critical:
      - final_warning
      - probation_period
      - fire_consideration
```

---

## Fire/Spawn Mechanics

### Firing Conditions

```yaml
council:
  firing:
    conditions:
      # Any of these triggers firing consideration
      - performance_below: 0.4
      - consecutive_failures: 5
      - happiness_below: 20
      - prolonged_probation: 30  # days on probation

    process:
      warning_first: true        # Issue warning before firing
      warning_period_days: 7     # Time to improve
      require_replacement: true  # Must spawn replacement
      morale_impact: -8          # Other councillors' happiness
```

### Firing Process

```python
async def evaluate_councillor(councillor: Councillor):
    """Periodic evaluation of councillor status."""

    # Check firing conditions
    if (
        councillor.performance.overall < 0.4 or
        councillor.consecutive_failures >= 5 or
        councillor.happiness < 20
    ):
        if councillor.warning_issued:
            # Already warned, proceed with firing
            await fire_councillor(councillor)
        else:
            # Issue warning first
            await issue_warning(councillor)
            councillor.warning_issued = True
            councillor.warning_date = datetime.now()

async def fire_councillor(councillor: Councillor):
    """Remove a councillor from the council."""

    # Notify other councillors (affects morale)
    for other in council.councillors:
        if other.id != councillor.id:
            await happiness_manager.apply_event(
                councillor=other,
                event=HappinessEvent.COLLEAGUE_FIRED
            )

    # Remove from council
    council.remove(councillor)

    # Spawn replacement if needed
    if len(council.councillors) < council.min_councillors:
        await spawn_councillor(specialization=councillor.specialization)
```

### Spawning New Councillors

```yaml
council:
  spawning:
    # When to spawn new councillors
    triggers:
      - below_minimum: true
      - workload_exceeded: 0.9   # >90% capacity
      - specialization_gap: true  # Missing required spec

    # New councillor settings
    initial_status: probation
    probation_period_days: 14
    probation_tasks: 10          # Tasks to prove themselves

    # Performance initialization
    initial_performance:
      quality_score: 0.7         # Start at 70%
      speed_score: 0.7
      feedback_score: 0.7
      success_rate: 0.7

    initial_happiness: 80        # New hires are optimistic
```

### Spawn Process

```python
async def spawn_councillor(
    specialization: Specialization,
    reason: str = "replacement"
) -> Councillor:
    """Create a new councillor."""

    # Generate unique identity
    new_councillor = Councillor(
        id=generate_id(),
        name=generate_name(),
        specialization=specialization,
        performance=PerformanceMetrics(
            quality_score=0.7,
            speed_score=0.7,
            feedback_score=0.7,
            success_rate=0.7
        ),
        happiness=80,
        status=CouncillorStatus.PROBATION
    )

    # Add to council
    council.add(new_councillor)

    # Notify team (slight morale boost)
    for other in council.councillors:
        await happiness_manager.apply_event(
            councillor=other,
            event=HappinessEvent.NEW_COLLEAGUE
        )

    return new_councillor
```

### Probation Management

```yaml
council:
  probation:
    duration_days: 14
    required_tasks: 10
    minimum_performance: 0.6
    graduation_threshold: 0.7

    # What happens at end of probation
    graduation:
      success:
        happiness_bonus: 15
        full_vote_weight: true
      failure:
        action: fire
        no_warning: true
```

---

## Tuning Strategies

### Strategy 1: High-Performance Team

Maximize quality output at the cost of councillor turnover.

```yaml
council:
  # Strict performance requirements
  firing:
    conditions:
      performance_below: 0.6     # Higher threshold
      consecutive_failures: 3    # Less tolerance

  # Performance-weighted voting
  voting:
    weights:
      performance:
        scaling_factor: 2.0      # Performance dominates

  # Less concern for happiness
  happiness:
    effects:
      quality_modifiers:
        0-20: 0.85               # Less penalty
```

### Strategy 2: Stable Team

Prioritize team stability and morale over raw performance.

```yaml
council:
  # Lenient firing
  firing:
    conditions:
      performance_below: 0.3     # Very low threshold
      consecutive_failures: 10   # High tolerance
    process:
      warning_period_days: 14    # Longer improvement window

  # Happiness-focused
  happiness:
    events:
      praise: 12                 # More impact
      bonus_received: 20
    effects:
      quality_modifiers:
        0-20: 0.6                # Bigger happiness impact
```

### Strategy 3: Specialist Team

Emphasize expertise over generalization.

```yaml
council:
  # Specialization bonuses
  voting:
    weights:
      specialization:
        coding: 1.8              # High expert bonus
        architecture: 2.0
        testing: 1.5

  # Required specialists
  specializations:
    coding:
      required_count: 3
    architecture:
      required_count: 2
```

### Strategy 4: Democratic Team

Equal voice for all councillors.

```yaml
council:
  voting:
    weights:
      base: 1.0
      performance:
        min_coefficient: 0.9     # Near-equal weights
        max_coefficient: 1.1
      happiness:
        min_modifier: 0.95
        max_modifier: 1.05
      specialization:
        coding: 1.0              # No specialist bonus
        design: 1.0
        testing: 1.0
```

---

## Monitoring & Debugging

### Council Dashboard

```python
# Get council status
status = council.get_status()

print(f"Active Councillors: {status['active_count']}")
print(f"On Probation: {status['probation_count']}")
print(f"Average Performance: {status['avg_performance']:.1%}")
print(f"Average Happiness: {status['avg_happiness']:.0f}")
print(f"Total Tasks Completed: {status['total_tasks']}")

# Individual councillor stats
for c in council.councillors:
    print(f"\n{c.name} ({c.specialization}):")
    print(f"  Performance: {c.performance.overall:.1%}")
    print(f"  Happiness: {c.happiness}")
    print(f"  Vote Weight: {c.vote_weight:.2f}")
    print(f"  Tasks: {c.task_count} (Success: {c.success_rate:.1%})")
```

### Voting Analysis

```python
# Analyze recent votes
votes = council.get_voting_history(limit=10)

for vote in votes:
    print(f"\nVote: {vote.question}")
    print(f"Winner: {vote.winner}")
    for ballot in vote.ballots:
        print(f"  {ballot.councillor}: {ballot.choice} "
              f"(conf: {ballot.confidence:.1f}, weight: {ballot.weight:.2f})")
```

### Performance Trends

```python
# Track performance over time
trends = council.get_performance_trends(days=30)

for councillor_id, trend in trends.items():
    print(f"\n{councillor_id}:")
    print(f"  Start: {trend['start']:.1%}")
    print(f"  End: {trend['end']:.1%}")
    print(f"  Change: {trend['change']:+.1%}")
    print(f"  Trend: {'↑' if trend['improving'] else '↓'}")
```

### Alerts

```yaml
monitoring:
  alerts:
    - name: low_council_morale
      condition: avg_happiness < 50
      action: notify_admin

    - name: mass_firing_risk
      condition: councillors_below_threshold > 2
      action: pause_evaluations

    - name: vote_weight_imbalance
      condition: max_weight / min_weight > 5
      action: rebalance_consideration

    - name: performance_decline
      condition: avg_performance_change < -0.1
      action: investigate
```

---

## Advanced Configurations

### Multi-Council Setup

```yaml
# Separate councils for different domains
councils:
  engineering:
    min_councillors: 5
    specializations: [coding, testing, architecture]
    voting:
      quorum_percentage: 0.6

  design:
    min_councillors: 3
    specializations: [ui_design, ux_research]
    voting:
      quorum_percentage: 0.5

# Cross-council coordination
coordination:
  joint_votes:
    enabled: true
    requires: [engineering, design]
    for_task_types: [full_product_design]
```

### Dynamic Weight Adjustment

```yaml
council:
  dynamic_weights:
    enabled: true
    adjustment_period: weekly

    rules:
      # Boost underrepresented specialists
      - condition: "specialization_ratio < 0.2"
        adjustment: "+0.2 to underrepresented"

      # Balance extreme performers
      - condition: "vote_weight > 3.0"
        adjustment: "cap at 3.0"
```

### Integration with Patterns

```yaml
# Council votes on pattern selection
patterns:
  selection:
    method: council_vote
    options:
      - sequential
      - hierarchical
      - auto_select
    fallback_on_tie: auto_select
```

---

## Quick Reference

### Optimal Starting Values

| Parameter | Conservative | Balanced | Aggressive |
|-----------|-------------|----------|------------|
| `min_councillors` | 5 | 4 | 3 |
| `performance_fire_threshold` | 0.3 | 0.4 | 0.5 |
| `consecutive_failures_limit` | 7 | 5 | 3 |
| `happiness_fire_threshold` | 15 | 20 | 30 |
| `warning_period_days` | 14 | 7 | 3 |
| `performance_scaling` | 1.0 | 1.5 | 2.0 |
| `happiness_scaling` | 0.6 | 0.4 | 0.2 |

### Common Issues

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| All votes tie | Equal weights | Increase performance scaling |
| One councillor dominates | Extreme performance gap | Cap max weight |
| Rapid turnover | Strict thresholds | Lower fire threshold |
| Low morale | Too many negative events | Increase praise/bonus |
| Stagnant performance | No incentives | Add streak bonuses |

---

*Council System Tuning Guide - JARVIS 2.0*
