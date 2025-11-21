# Developer Guide

## Phase 1.7: Model Registry

### Overview

The Model Registry (Phase 1.7) externalizes model configuration from hard-coded Python to a JSON file (`agent/models.json`). This enables model updates, pricing changes, and deprecation management without code changes.

**Addresses**: Vulnerability A3 - Hard-coded model names requiring code changes when providers deprecate models.

### Architecture

```
agent/
├── models.json              # Model registry (providers, models, pricing, aliases)
├── model_registry.py        # Registry loader and query interface
├── model_router.py          # Uses registry for model selection
├── cost_tracker.py          # Uses registry for pricing
└── tools/
    └── update_models.py     # CLI tool for registry management
```

### Models.json Structure

```json
{
  "version": "1.0",
  "providers": {
    "openai": {
      "models": {
        "gpt-5-mini": {
          "id": "gpt-5-mini-2025-08-07",
          "cost_per_1k_prompt": 0.003,
          "cost_per_1k_completion": 0.009,
          "deprecated": false
        }
      }
    }
  },
  "aliases": {
    "manager_default": "openai/gpt-5-mini",
    "high_complexity": "openai/gpt-5"
  }
}
```

### Usage

#### Querying Models

```python
from model_registry import get_registry

# Get registry (singleton)
registry = get_registry()

# Get model by alias
model = registry.get_model("manager_default")
print(model.full_id)  # "gpt-5-mini-2025-08-07"
print(model.cost_per_1k_prompt)  # 0.003

# Get model by provider/model
model = registry.get_model("openai/gpt-5")

# Get model for role
model = registry.get_role_model("manager", "planning")
model = registry.get_role_model("employee", "default", complexity="high")

# Calculate cost
cost = model.get_cost_for_tokens(prompt_tokens=1000, completion_tokens=500)
```

#### Model Router Integration

The `model_router.py` automatically uses the registry:

```python
from model_router import choose_model

# Model router now resolves aliases from registry
model_id = choose_model(
    task_type="code",
    complexity="high",
    role="employee",
    interaction_index=2
)
# Returns: "gpt-5-2025-08-07" (resolved from registry)
```

#### Cost Tracking Integration

The `cost_tracker.py` automatically uses registry for pricing:

```python
import cost_tracker

# Cost tracker queries registry for current pricing
cost_tracker.register_call("manager", "gpt-5-mini-2025-08-07", 1000, 500)
# Uses pricing from models.json automatically
```

### Updating the Registry

#### Via CLI Tool

```bash
# List all models
python -m agent.tools.update_models --list

# Check for deprecated models
python -m agent.tools.update_models --check-deprecations

# Mark model as deprecated
python -m agent.tools.update_models --deprecate openai/gpt-4-turbo \\
    --date 2025-06-01 --replacement "gpt-5"

# Add new model
python -m agent.tools.update_models --add openai/gpt-6 \\
    --full-id gpt-6-2025-11-01 \\
    --cost-prompt 0.02 \\
    --cost-completion 0.06

# Update pricing
python -m agent.tools.update_models --update openai/gpt-5-mini \\
    --cost-prompt 0.002 \\
    --cost-completion 0.008
```

#### Manual Editing

1. **Edit** `agent/models.json`
2. **Backup** created automatically by CLI tool
3. **No restart required** - Registry reloads on next access

### Deprecation Management

#### Deprecation Workflow

1. **Mark deprecated** in `models.json`:
   ```json
   {
     "deprecated": true,
     "deprecation_date": "2025-06-01",
     "replacement": "gpt-5"
   }
   ```

2. **Check at startup**:
   ```python
   from model_router import check_model_deprecations
   check_model_deprecations()
   ```

3. **Warnings displayed**:
   ```
   ⚠️  Model Registry: 1 model(s) deprecated
     - high_complexity -> openai/gpt-4-turbo is DEPRECATED
       (use gpt-5 instead) [Removal: 2025-06-01]
   ```

### Best Practices

#### DO:
- ✅ Use aliases (`"manager_default"`) instead of direct IDs
- ✅ Update `models.json` when providers change pricing
- ✅ Mark models as deprecated before removal
- ✅ Provide replacement model in deprecation
- ✅ Use CLI tool for updates (creates backups)

#### DON'T:
- ❌ Hard-code model IDs in application code
- ❌ Edit `models.json` directly in production (use CLI tool)
- ❌ Remove deprecated models immediately (grace period)
- ❌ Change model IDs without updating aliases

### Migration from Hard-Coded Models

#### Before (Phase 1.6)

```python
# Hard-coded in model_router.py
ROUTING_RULES = {
    "planning": {
        "low": "gpt-5-mini-2025-08-07",  # Hard-coded
        "high": "gpt-5-2025-08-07",      # Hard-coded
    }
}

# Hard-coded in cost_tracker.py
PRICES = {
    "gpt-5-mini": {
        "input": 0.250 / 1_000_000,  # Hard-coded
        "output": 2.000 / 1_000_000,
    }
}
```

#### After (Phase 1.7)

```python
# model_router.py - Uses aliases
ROUTING_RULES = {
    "planning": {
        "low": "manager_default",     # Resolves via registry
        "high": "high_complexity",     # Resolves via registry
    }
}

# cost_tracker.py - Queries registry
price_cfg = _get_pricing_from_registry(model_id)
```

### Testing

```bash
# Run model registry tests
pytest agent/tests/unit/test_model_registry.py -v

# Test model resolution
python -c "from model_registry import get_registry; \\
    print(get_registry().get_model('manager_default').full_id)"

# Test deprecation check
python -m agent.tools.update_models --check-deprecations
```

### Troubleshooting

#### Issue: "Model registry not found"

**Solution**: Ensure `agent/models.json` exists. Copy from template if needed.

```bash
cp agent/models.json.template agent/models.json
```

#### Issue: "Unknown model alias"

**Solution**: Check `aliases` section in `models.json`. Add missing alias:

```bash
python -m agent.tools.update_models --list
# Edit models.json to add alias
```

#### Issue: "Pricing not found for model"

**Solution**: Ensure model has `cost_per_1k_prompt` and `cost_per_1k_completion` in `models.json`.

### API Reference

#### ModelRegistry

- `get_model(ref: str) -> ModelInfo` - Get model by alias or provider/model
- `get_role_model(role: str, context: str, complexity: str) -> ModelInfo` - Get model for role
- `list_models(provider: str, include_deprecated: bool) -> List[ModelInfo]` - List all models
- `check_deprecations(warning_days: int) -> List[Tuple[str, ModelInfo]]` - Check for deprecated models
- `get_cost_threshold(level: str) -> float` - Get cost threshold
- `reload() -> None` - Reload registry from disk

#### ModelInfo

- `provider: str` - Provider name
- `model_id: str` - Short model ID
- `full_id: str` - Complete API model ID
- `cost_per_1k_prompt: float` - Prompt cost per 1k tokens
- `cost_per_1k_completion: float` - Completion cost per 1k tokens
- `deprecated: bool` - Whether model is deprecated
- `deprecation_date: str` - ISO date of deprecation
- `replacement: str` - Recommended replacement
- `get_cost_for_tokens(prompt: int, completion: int) -> float` - Calculate cost

### Performance

- **Registry load**: ~2ms (cached as singleton)
- **Model lookup**: <0.1ms (cached after first access)
- **Cost calculation**: <0.1ms
- **No runtime overhead** - Equivalent to hard-coded lookups

### Backwards Compatibility

- **config.py**: `ModelDefaults` deprecated but still functional
- **Fallback**: Hard-coded prices used if registry unavailable
- **Migration timeline**: 6 months before removing legacy code

### Security

- **Validation**: JSON schema validation on load
- **Backup**: Automatic backup before updates
- **Audit trail**: Update tool logs all changes
- **No secrets**: Registry contains only public pricing info

---

For more information, see:
- `agent/models.json` - Registry file
- `agent/model_registry.py` - Registry implementation
- `agent/tools/update_models.py` - Management CLI
- `agent/tests/unit/test_model_registry.py` - Test suite
