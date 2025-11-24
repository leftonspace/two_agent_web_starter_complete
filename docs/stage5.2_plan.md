# Stage 5.2 Implementation Plan

**Goal**: Enhance Stage 5.1 (Model Router & Cost Intelligence) with production-ready cost controls, error handling, and comprehensive testing.

## Stage 5.1 Status (Already Implemented)

✅ Central model router (`model_router.py`)
- `choose_model()` with GPT-5 gating rules
- Complexity estimation based on keywords and failures
- Importance checking from config

✅ Cost tracking (`cost_tracker.py`)
- Per-call tracking with tokens and costs
- Summaries by role and model
- History logging to JSONL

✅ Integration into orchestrator
- `_choose_model_for_agent()` helper function
- Model selection for manager, supervisor, employee
- Cost cap check after planning phase

✅ Basic tests
- Unit tests for `model_router.py`
- Unit tests for `cost_tracker.py`

## Stage 5.2 Enhancements (10 Sections)

### 1. **Pre-LLM Cost Cap Enforcement**
**Status**: Partially implemented (only checked after planning)
**Gap**: Cost caps should be checked BEFORE each LLM call, not just after planning
**Implementation**:
- Add `_check_cost_cap()` helper that raises/returns error before exceeding budget
- Integrate into `llm.chat_json()` before calling `_post()`
- Return graceful error instead of making call when cap would be exceeded

**Files**: `llm.py`, `orchestrator.py`

---

### 2. **Model Fallback on Errors**
**Status**: Not implemented
**Gap**: When LLM call times out or fails, should retry with cheaper model
**Implementation**:
- Add `_retry_with_fallback()` in `llm.py`
- On timeout/error, downgrade from gpt-4o → gpt-4o-mini
- Log fallback attempts
- Max 2 retries with cheaper models

**Files**: `llm.py`

---

### 3. **Enhanced Complexity Estimation**
**Status**: Partially implemented (files_count hardcoded to 0)
**Gap**: Should count actual files being modified
**Implementation**:
- In orchestrator, track files written per phase
- Pass actual `files_count` to `estimate_complexity()`
- Consider cumulative files across all phases

**Files**: `orchestrator.py`, `model_router.py`

---

### 4. **Run-Level Cost Summaries**
**Status**: Cost tracking exists but not in run logs
**Gap**: Run logs should include detailed cost breakdown
**Implementation**:
- Add cost summary to `run_summary.json`
- Include breakdown by role, model, phase
- Log to core_logging as "cost_summary" event

**Files**: `run_logger.py`, `orchestrator.py`

---

### 5. **Consistent Model Router Usage**
**Status**: Partially implemented (some calls use legacy role-based)
**Gap**: All `chat_json()` calls should use intelligent routing
**Implementation**:
- Audit all `chat_json()` calls in codebase
- Ensure `task_type`, `complexity`, `interaction_index` passed
- Remove legacy fallback path in `llm.py`

**Files**: `llm.py`, `orchestrator.py`, `merge_manager.py`, any other modules calling LLM

---

### 6. **Config Validation**
**Status**: Not implemented
**Gap**: Should validate cost-related config on startup
**Implementation**:
- Add `_validate_cost_config()` in `orchestrator.py`
- Check `max_cost_usd`, `cost_warning_usd` are valid floats
- Warn if `llm_very_important_stages` references non-existent stages
- Check model names in routing rules exist in pricing table

**Files**: `orchestrator.py`, `cost_tracker.py`

---

### 7. **Better Cost Logging**
**Status**: Basic logging exists
**Gap**: Should log routing decisions and cost checkpoints
**Implementation**:
- Log model selection reasoning (why gpt-4o vs gpt-4o-mini)
- Log cost at each iteration
- Log when approaching warning threshold
- Add "cost_checkpoint" event type to core_logging

**Files**: `core_logging.py`, `llm.py`, `orchestrator.py`

---

### 8. **Integration Tests**
**Status**: Only unit tests exist
**Gap**: Need end-to-end tests verifying cost caps work
**Implementation**:
- Test: Cost cap enforcement stops run when exceeded
- Test: GPT-5 not used on first iteration
- Test: Model fallback on errors
- Test: Very important stages get appropriate models
- Test: Cost summary appears in run logs

**Files**: `agent/tests/integration/test_stage5_integration.py` (new file)

---

### 9. **Documentation**
**Status**: Minimal comments
**Gap**: Need comprehensive docs explaining model routing
**Implementation**:
- Create `docs/MODEL_ROUTING.md` explaining:
  - How model selection works
  - GPT-5 gating rules
  - Cost cap configuration
  - Complexity estimation
- Update `DEVELOPER_GUIDE.md` with Stage 5.2 changes
- Add docstrings to all public functions

**Files**: `docs/MODEL_ROUTING.md` (new), `DEVELOPER_GUIDE.md`, code files

---

### 10. **Error Messages & UX**
**Status**: Basic error handling
**Gap**: Better user-facing messages when cost limits hit
**Implementation**:
- Clear message when cost cap prevents LLM call
- Suggestion to increase `max_cost_usd` in config
- Warning when approaching cost limit (e.g., 80% of cap)
- Log estimated remaining budget

**Files**: `llm.py`, `orchestrator.py`

---

## Implementation Order

1. ✅ **RECON**: Analyze existing code (COMPLETED)
2. ✅ **PLAN**: Create this document (COMPLETED)
3. **IMPLEMENT** (in this order):
   - Section 6: Config validation (foundation)
   - Section 1: Pre-LLM cost cap enforcement
   - Section 3: Enhanced complexity estimation
   - Section 7: Better cost logging
   - Section 4: Run-level cost summaries
   - Section 2: Model fallback on errors
   - Section 5: Consistent model router usage
   - Section 10: Better error messages
4. **TEST**:
   - Section 8: Integration tests
   - Run ruff, mypy, pytest
5. **DOCUMENT**:
   - Section 9: Documentation updates
6. **SUMMARY**: Create final summary of changes

## Key Principles

- **Backwards compatible**: Don't break existing behavior
- **Fail gracefully**: Cost overruns should not crash the system
- **Testable**: All new logic has unit or integration tests
- **Observable**: Log all important decisions for debugging
- **Configurable**: Allow users to control cost behavior via config

## Expected Outcomes

After Stage 5.2:
- ✅ Cost caps are enforced BEFORE exceeding budget
- ✅ LLM errors trigger fallback to cheaper models
- ✅ Complexity estimation uses real file counts
- ✅ Run logs include detailed cost breakdowns
- ✅ All LLM calls use intelligent model routing
- ✅ Config is validated on startup
- ✅ Comprehensive tests verify the system works
- ✅ Clear documentation explains the behavior
- ✅ Users get helpful messages about cost limits
