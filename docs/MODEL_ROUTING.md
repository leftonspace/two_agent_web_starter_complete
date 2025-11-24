# Model Routing & Cost Controls (Stage 5.2)

This document describes the intelligent model routing and cost control features implemented in Stage 5.2.

## Table of Contents

1. [Overview](#overview)
2. [Model Routing](#model-routing)
3. [GPT-4o Gating Rules](#gpt-4o-gating-rules)
4. [Cost Tracking](#cost-tracking)
5. [Cost Caps](#cost-caps)
6. [Configuration](#configuration)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Stage 5.2 introduces **centralized, intelligent model selection** and **hard cost controls** to the multi-agent orchestrator. Instead of using fixed models for each role, the system now:

- **Dynamically selects models** based on task complexity, role, and iteration
- **Enforces intelligent gating** to prevent expensive model usage on simple tasks
- **Tracks costs** in real-time with detailed breakdowns
- **Enforces cost caps** to prevent budget overruns
- **Logs cost checkpoints** at key stages of execution

---

## Model Routing

### How It Works

All LLM calls in the orchestrator flow through `model_router.choose_model()`, which selects the appropriate model based on:

- **Role**: `manager`, `supervisor`, `employee`, `merge_manager`
- **Task Type**: `planning`, `code`, `review`, `docs`, `analysis`
- **Complexity**: `low` or `high` (estimated from task characteristics)
- **Interaction Index**: Which iteration we're on (1-indexed)
- **Importance**: Whether the stage is marked as "very important"

### Model Selection Logic

```python
from model_router import choose_model

model = choose_model(
    task_type="code",
    complexity="high",
    role="employee",
    interaction_index=2,  # Second iteration
    is_very_important=False,
    config=cfg,
)
# Returns: "gpt-4o" (gpt-4o allowed on 2nd iteration with high complexity)
```

### Complexity Estimation

Complexity is estimated using multiple factors:

1. **File Count**: More files = higher complexity
2. **Stage Keywords**: Keywords like "complex", "advanced", "integration" increase complexity
3. **Previous Failures**: Tasks that failed before are considered more complex
4. **Task Type**: Code generation is more complex than documentation

See `model_router.estimate_complexity()` for implementation details.

---

## GPT-4o Gating Rules

**GPT-4o is expensive** and should only be used when necessary. The system enforces strict gating:

### Rule 1: Interaction Index Restriction

**GPT-4o can ONLY be used on the 2nd or 3rd interaction**

- ❌ First iteration: Always uses cheaper models (`gpt-4o-mini`)
- ✅ Second iteration: gpt-4o allowed if complexity is high OR stage is very important
- ✅ Third iteration: Same as second
- ❌ Fourth+ iterations: Falls back to cheaper models

**Rationale**: First iterations are exploratory; expensive models aren't justified until we've gathered context.

### Rule 2: Complexity/Importance Requirement

**GPT-4o requires high complexity OR very important flag**

- **High Complexity**: Tasks with many files, complex keywords, or previous failures
- **Very Important**: Stages explicitly marked in `llm_very_important_stages` config

### Example Scenarios

| Iteration | Complexity | Important | Model Used |
|-----------|------------|-----------|------------|
| 1 | high | ✅ | `gpt-4o-mini` (first iteration rule) |
| 2 | high | ❌ | `gpt-4o` ✅ |
| 2 | low | ✅ | `gpt-4o` ✅ |
| 2 | low | ❌ | `gpt-4o-mini` (no justification) |
| 4 | high | ✅ | `gpt-4o-mini` (past 3rd iteration) |

---

## Cost Tracking

### Real-Time Tracking

The `cost_tracker` module tracks every LLM call:

- **Tokens**: Input and output tokens per call
- **Costs**: USD cost based on model pricing
- **Breakdown**: Per-role and per-model aggregation

```python
import cost_tracker

# After orchestrator run
summary = cost_tracker.get_summary()
print(f"Total cost: ${summary['total_usd']:.4f}")
print(f"Total calls: {summary['num_calls']}")
print(f"By role: {summary['by_role']}")
print(f"By model: {summary['by_model']}")
```

### Cost Checkpoints

Cost checkpoints are logged at key stages:

1. **After Planning**: Manager creates initial plan
2. **After Each Iteration**: Employee completes work, manager reviews
3. **Final**: Before finishing the run

Checkpoints include:
- Current total cost
- Remaining budget
- Percentage of cap used
- Full cost breakdown

Logs are written to `run_logs_main/<run_id>.jsonl`:

```json
{
  "event_type": "cost_checkpoint",
  "payload": {
    "checkpoint": "iteration_1",
    "total_cost_usd": 0.1234,
    "max_cost_usd": 1.0,
    "remaining_budget_usd": 0.8766,
    "percent_of_cap": 12.34,
    "cost_summary": { ... }
  }
}
```

---

## Cost Caps

### Hard Cap Enforcement

When `max_cost_usd` is set, the system enforces a **hard cap** before each LLM call.

**How it works:**

1. Before calling the LLM, `llm.chat_json()` calls `cost_tracker.check_cost_cap()`
2. The function estimates the next call's cost (conservatively assumes all tokens are output)
3. If `current_cost + estimated_call_cost > max_cost_usd`, the call is **blocked**
4. A graceful error stub is returned instead of crashing

```python
# Example: Call blocked due to cost cap
result = chat_json(
    role="manager",
    system_prompt="...",
    user_content="...",
    max_cost_usd=0.50,  # Very low cap
)

if result.get("cost_cap_hit"):
    print(f"Cost cap exceeded: {result['notes']}")
    print(f"Current cost: ${result['current_cost_usd']:.4f}")
    # Orchestrator can gracefully abort or retry
```

### Warning Threshold

Set `cost_warning_usd` to get **warnings** before hitting the cap:

```json
{
  "max_cost_usd": 10.0,
  "cost_warning_usd": 8.0
}
```

When cost exceeds 8.0 USD, a warning is printed (once):

```
⚠️  [Cost] WARNING: total cost ~$8.12 exceeds warning threshold $8.00
```

---

## Configuration

### Config File (`project_config.json`)

```json
{
  "max_cost_usd": 5.0,
  "cost_warning_usd": 4.0,
  "interactive_cost_mode": "off",

  "llm_default_complexity": "low",
  "llm_very_important_stages": ["final_review", "deployment"],

  "manager_model": null,
  "supervisor_model": null,
  "employee_model": null
}
```

### Config Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_cost_usd` | float | 0.0 | Hard cost cap in USD. 0 = no cap. |
| `cost_warning_usd` | float | 0.0 | Warning threshold in USD. 0 = no warning. |
| `interactive_cost_mode` | string | `"off"` | `"off"`, `"once"`, or `"always"`. Prompts user before continuing. |
| `llm_default_complexity` | string | `"low"` | Default complexity if estimation fails. |
| `llm_very_important_stages` | list | `[]` | Stage names that justify gpt-4o usage. |
| `manager_model` | string\|null | `null` | Override model for manager (bypasses router if set). |
| `supervisor_model` | string\|null | `null` | Override model for supervisor (bypasses router if set). |
| `employee_model` | string\|null | `null` | Override model for employee (bypasses router if set). |

**⚠️ Warning**: Setting explicit model overrides (`manager_model`, etc.) bypasses the intelligent router. Only use for debugging.

### Environment Variables

```bash
export DEFAULT_MANAGER_MODEL="gpt-4o-mini"
export DEFAULT_SUPERVISOR_MODEL="gpt-4o-mini"
export DEFAULT_EMPLOYEE_MODEL="gpt-4o"
```

These are fallback defaults used by legacy code paths. **Recommended**: Leave unset and let the router decide.

---

## Examples

### Example 1: Running with Cost Cap

```bash
# Edit project_config.json
{
  "task": "Build a user authentication system",
  "max_rounds": 3,
  "max_cost_usd": 2.0
}

# Run orchestrator
python orchestrator.py
```

**Output:**
```
[Config] Cost configuration validated successfully.
[Cost] After planning: ~$0.12 USD
[Cost] After iteration 1: ~$0.89 USD
[Cost] After iteration 2: ~$1.78 USD
[CostCap] Cost cap would be exceeded: current=$1.78, estimated next call=$0.35, projected total=$2.13, cap=$2.00
[CostCap] Aborting LLM call to stay within budget.
[Orchestrator] Run aborted due to cost cap.
```

### Example 2: Marking Important Stages

```json
{
  "llm_very_important_stages": ["security_audit", "final_validation"]
}
```

When the orchestrator processes a phase named "security_audit", GPT-5 will be allowed even on 2nd iteration with low complexity.

### Example 3: Checking Cost Summary

```python
import cost_tracker

# After a run
summary = cost_tracker.get_summary()

print(f"📊 Run Summary:")
print(f"  Total calls: {summary['num_calls']}")
print(f"  Total cost: ${summary['total_usd']:.4f} USD")
print(f"\n💰 By Role:")
for role, stats in summary['by_role'].items():
    print(f"  {role}: {stats['num_calls']} calls, ${stats['total_usd']:.4f}")
print(f"\n🤖 By Model:")
for model, stats in summary['by_model'].items():
    print(f"  {model}: {stats['num_calls']} calls, ${stats['total_usd']:.4f}")
```

---

## Troubleshooting

### Issue: "Cost cap exceeded" but cap is not set

**Solution**: Check that `max_cost_usd` in `project_config.json` is either:
- Not present (no cap)
- Set to `0.0` (no cap)
- Set to a high value like `100.0`

### Issue: GPT-5 not being used even with high complexity

**Possible causes:**
1. **First iteration**: GPT-5 is never used on first iteration
2. **4th+ iteration**: GPT-5 gating only allows 2nd/3rd iterations
3. **Complexity too low**: Check `estimate_complexity()` output
4. **Not marked important**: Add stage to `llm_very_important_stages`

**Debug:**
```python
from model_router import estimate_complexity, is_stage_important

complexity = estimate_complexity(
    stage={"name": "my_stage", "categories": ["complex", "integration"]},
    previous_failures=0,
    files_count=5,
)
print(f"Estimated complexity: {complexity}")  # Should be > 0.5 for "high"

important = is_stage_important(stage={"name": "my_stage"}, config=cfg)
print(f"Is important: {important}")
```

### Issue: Cost tracking shows $0.00

**Possible causes:**
1. **No calls made yet**: `cost_tracker.reset()` clears all data
2. **Stub responses**: Timeout/error stubs don't consume tokens
3. **Tracking disabled**: Check that `register_call()` is being called

**Solution**: Verify LLM calls are succeeding and returning valid usage data.

### Issue: "max_cost_usd must be a valid number" error

**Solution**: Ensure `max_cost_usd` is a number, not a string:

```json
// ❌ Wrong
{"max_cost_usd": "5.0"}

// ✅ Correct
{"max_cost_usd": 5.0}
```

---

## Testing

### Unit Tests

```bash
# Test model routing logic
pytest tests/unit/test_model_router.py

# Test cost tracking
pytest tests/unit/test_cost_tracker.py
```

### Integration Tests

```bash
# Test end-to-end cost caps and summaries
pytest tests/integration/test_stage5_integration.py
```

---

## Implementation Details

### Files Involved

- `agent/model_router.py`: Central routing logic and GPT-5 gating
- `agent/cost_tracker.py`: Cost tracking and cap enforcement
- `agent/llm.py`: LLM call wrapper with cost cap checks
- `agent/orchestrator.py`: Integration of routing and cost controls
- `agent/core_logging.py`: Cost checkpoint logging

### Key Functions

| Function | Module | Purpose |
|----------|--------|---------|
| `choose_model()` | `model_router` | Select model based on task characteristics |
| `estimate_complexity()` | `model_router` | Estimate task complexity (low/high) |
| `is_stage_important()` | `model_router` | Check if stage is marked important |
| `check_cost_cap()` | `cost_tracker` | Predict if next call exceeds cap |
| `get_summary()` | `cost_tracker` | Get cost breakdown |
| `log_cost_checkpoint()` | `core_logging` | Log cost at key stages |

---

## Future Enhancements

Potential improvements for future stages:

1. **Model Fallback on Errors**: Automatically retry with cheaper model on timeout/error
2. **Dynamic Complexity Tuning**: Learn complexity thresholds from historical runs
3. **Per-Stage Cost Budgets**: Allocate budget per phase instead of global cap
4. **Cost Prediction**: Show estimated total cost before starting run
5. **Model Performance Tracking**: Track which models produce best results per task type

---

## Summary

Stage 5.2 provides **production-ready cost controls** for the multi-agent orchestrator:

✅ **Centralized Model Routing**: All calls go through intelligent router
✅ **GPT-5 Gating**: Expensive models only used when justified
✅ **Real-Time Cost Tracking**: Detailed breakdowns by role and model
✅ **Hard Cost Caps**: Enforce budget limits before calls
✅ **Comprehensive Logging**: Cost checkpoints at key stages
✅ **Configurable Policies**: Control behavior via config file
✅ **Thoroughly Tested**: Unit and integration test coverage

For questions or issues, refer to the [Troubleshooting](#troubleshooting) section or check the implementation in `agent/model_router.py`.
