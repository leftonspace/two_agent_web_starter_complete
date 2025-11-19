# Logging System Migration Guide - Phase 1.6

**Status**: 🚧 In Progress
**Target Completion**: Phase 1.6
**Deprecation Timeline**: run_logger.py will be removed in Version 2.0 (6 months)

---

## Table of Contents

1. [Overview](#overview)
2. [Migration Strategy](#migration-strategy)
3. [API Mapping](#api-mapping)
4. [Migration Steps](#migration-steps)
5. [Breaking Changes](#breaking-changes)
6. [Migration Tool](#migration-tool)
7. [Timeline](#timeline)

---

## Overview

### Problem Statement

**Vulnerability A2**: Dual logging systems cause duplication, wasted resources, and inconsistencies.

The codebase currently maintains two parallel logging systems:

1. **run_logger.py** (Legacy, 436 lines)
   - Dict-based API
   - Writes to `agent/run_logs/<project>_<mode>.jsonl`
   - Append-based high-level run summaries
   - Used for backward compatibility

2. **core_logging.py** (Modern, 748 lines)
   - Event-based structured logging
   - Writes to `agent/run_logs_main/<run_id>.jsonl`
   - Granular event tracking
   - STAGE 2+ system with rich event types

### Why Migrate?

❌ **Problems with Dual System**:
- Duplicated logging logic (violation of DRY principle)
- Inconsistent data formats between systems
- Wasted CPU cycles and disk I/O
- Maintenance burden (updates needed in two places)
- Confusion for developers (which system to use?)
- Risk of data loss (events logged in one but not the other)

✅ **Benefits of core_logging Only**:
- Single source of truth for all events
- Consistent structured format (JSONL event stream)
- Rich event types for detailed analysis
- Better performance (no duplicate writes)
- Easier to maintain and extend
- Unified query interface

---

## Migration Strategy

### Phase 1.5 Foundation

✅ **Already Complete**: In Phase 1.5, we implemented dependency injection with `OrchestratorContext`. The orchestrator now uses:
- `context.logger` → points to `core_logging` (modern)
- `context.run_logger` → points to `run_logger` (legacy)

This means **most** logging already uses core_logging! Only a few legacy calls remain.

### Phase 1.6 Plan

1. **Remove Legacy Calls**: Eliminate remaining `context.run_logger` calls from orchestrator
2. **Add Deprecation Warnings**: Mark all run_logger functions as deprecated
3. **Keep for Compatibility**: run_logger.py stays in codebase (deprecated) for 6 months
4. **Provide Migration Tool**: Tool to convert old JSONL files to new format
5. **Update Documentation**: Clear migration guide for users

### What Gets Deprecated

The following functions in `run_logger.py` are deprecated:

```python
# Legacy dict-based API
- start_run_legacy(config, mode, out_dir) → Dict
- log_iteration_legacy(run_record, iteration_data) → None
- finish_run_legacy(run_record, final_status, cost_summary, out_dir) → None

# STAGE 2 dataclass API (also deprecated)
- start_run(config) → RunSummary
- log_iteration(run_summary, iteration) → None
- finalize_run(run_summary, final_status) → None

# Session APIs (also deprecated)
- start_session(...) → SessionSummary
- log_session_run(...) → None
- finalize_session(...) → None
```

All these are replaced by `core_logging` event-based logging.

---

## API Mapping

### Legacy run_logger → core_logging Equivalents

| run_logger Function | core_logging Equivalent | Notes |
|---------------------|------------------------|-------|
| `start_run_legacy(cfg, mode, dir)` | `log_start(run_id, folder, task, config)` | core_logging uses run_id from `new_run_id()` |
| `log_iteration_legacy(rec, data)` | `log_iteration_begin()` + `log_iteration_end()` | Split into begin/end events |
| `finish_run_legacy(rec, status, cost, dir)` | `log_final_status(run_id, status, ...)` | Final status event |
| `RunSummary` dataclass | `get_run_summary(run_id)` | Query aggregated summary |
| `log_iteration(summary, iteration)` | `log_event(run_id, 'iteration', ...)` | Generic event log |

### Event Types in core_logging

core_logging provides these specific event types:

```python
# Run lifecycle
log_start(run_id, ...)
log_final_status(run_id, status, ...)

# Iteration lifecycle
log_iteration_begin(run_id, iteration, ...)
log_iteration_end(run_id, iteration, status, ...)

# LLM calls
log_llm_call(run_id, role, model, ...)

# File operations
log_file_write(run_id, files, ...)

# Safety
log_safety_check(run_id, status, errors, warnings, ...)

# Cost tracking
log_cost_checkpoint(run_id, checkpoint, total_cost, ...)

# Workflow (STAGE 3)
log_workflow_initialized(run_id, ...)
log_stage_started(run_id, stage_id, ...)
log_stage_completed(run_id, stage_id, ...)

# Generic
log_event(run_id, event_type, payload)
```

---

## Migration Steps

### For Application Code

#### Before (using run_logger):

```python
from run_logger import start_run, log_iteration, finalize_run

# Start run
run_summary = start_run(config)

# Log iteration
iteration_log = IterationLog(
    index=1,
    role="manager",
    status="ok",
    notes="Planning complete"
)
log_iteration(run_summary, iteration_log)

# Finalize
finalize_run(run_summary, "approved")
```

#### After (using core_logging):

```python
import core_logging

# Start run
run_id = core_logging.new_run_id()
core_logging.log_start(
    run_id,
    project_folder="/path/to/project",
    task_description="Build landing page",
    config={"max_rounds": 3}
)

# Log iteration
core_logging.log_iteration_begin(run_id, iteration=1, mode="3loop", max_rounds=3)
# ... do work ...
core_logging.log_iteration_end(run_id, iteration=1, status="ok", tests_all_passed=True)

# Finalize
core_logging.log_final_status(
    run_id,
    status="approved",
    reason="All iterations passed",
    iterations=3,
    total_cost_usd=0.25
)
```

### For orchestrator.py

**Phase 1.5 already completed most of this!** Only 4 legacy calls remain:

#### Remaining Legacy Calls to Remove:

```python
# Line 761: Remove this
run_record = context.run_logger.start_run(cfg, mode, out_dir)
# Already have: core_run_id = context.logger.new_run_id() (line 505)
# Already have: context.logger.log_start(...) (line 764)

# Lines 854, 967, 1665: Remove these
context.run_logger.finish_run_legacy(run_record, final_status, final_cost_summary, out_dir)
# Already have: context.logger.log_final_status(...) (line 1744)

# Line 1479: Remove this
context.run_logger.log_iteration_legacy(run_record, {...})
# Already have: context.logger.log_iteration_begin/end()

# Lines 830, 1510: These are okay (use new API)
context.run_logger.log_iteration(run_summary, ...)
# But can be removed if run_summary is not needed
```

---

## Breaking Changes

### What's Changing

1. **run_logger.py functions are deprecated** (but still work with warnings)
2. **Different log file locations**:
   - Old: `agent/run_logs/<project>_<mode>.jsonl`
   - New: `agent/run_logs_main/<run_id>.jsonl`
3. **Different log formats**:
   - Old: Appended run summaries (one JSON object per run)
   - New: Event stream (one event per line)

### What's NOT Changing

- Existing log files are preserved (nothing is deleted)
- run_logger.py stays in codebase for 6 months
- Deprecation warnings only (no errors)
- Migration tool available for converting old logs

### Compatibility

```python
# OLD CODE (still works, but shows warning)
from run_logger import start_run, finalize_run
run = start_run(config)  # ⚠️ DeprecationWarning
finalize_run(run, "ok")   # ⚠️ DeprecationWarning

# NEW CODE (recommended)
import core_logging
run_id = core_logging.new_run_id()
core_logging.log_start(run_id, ...)
core_logging.log_final_status(run_id, ...)
```

---

## Migration Tool

### Using the Migration Tool

Convert old run_logger JSONL files to core_logging format:

```bash
# Convert a single file
python -m agent.tools.migrate_logs \
    --source agent/run_logs/my_project_3loop.jsonl \
    --dest agent/run_logs_main/

# Convert entire directory
python -m agent.tools.migrate_logs \
    --source agent/run_logs/ \
    --dest agent/run_logs_main/ \
    --recursive

# Dry run (show what would happen)
python -m agent.tools.migrate_logs \
    --source agent/run_logs/ \
    --dest agent/run_logs_main/ \
    --dry-run
```

### What It Does

1. Reads old JSONL file (one run summary per line)
2. Extracts events from run summary structure
3. Converts to core_logging event format
4. Writes new JSONL file with `<run_id>.jsonl` naming
5. Validates integrity (checksums, event counts)
6. Reports conversion statistics

### Event Conversion

Old run summary → Multiple new events:

```python
# Old format (1 line in run_logs):
{
  "run_id": "2025-01-15T10:30:00.000Z_3loop",
  "started_at": "2025-01-15T10:30:00.000Z",
  "finished_at": "2025-01-15T10:35:00.000Z",
  "final_status": "approved",
  "iterations": [
    {"index": 1, "role": "manager", "status": "ok", ...},
    {"index": 2, "role": "employee", "status": "ok", ...},
  ],
  "cost_summary": {"total_usd": 0.25, ...}
}

# New format (multiple lines in run_logs_main/<run_id>.jsonl):
{"timestamp": "2025-01-15T10:30:00.000Z", "event_type": "run_start", ...}
{"timestamp": "2025-01-15T10:31:00.000Z", "event_type": "iteration_begin", "iteration": 1, ...}
{"timestamp": "2025-01-15T10:32:00.000Z", "event_type": "iteration_end", "iteration": 1, ...}
{"timestamp": "2025-01-15T10:34:00.000Z", "event_type": "cost_checkpoint", ...}
{"timestamp": "2025-01-15T10:35:00.000Z", "event_type": "final_status", "status": "approved", ...}
```

---

## Timeline

### Phase 1.6 (Current - Week 1)

- ✅ Audit run_logger usage
- ✅ Create migration plan
- 🚧 Remove legacy calls from orchestrator.py
- 🚧 Add deprecation warnings to run_logger.py
- 🚧 Create migration tool
- 🚧 Update documentation

### Phase 1.7-2.0 (6 Months)

- **Months 1-5**: Deprecation period
  - run_logger.py exists with warnings
  - Users can migrate at their own pace
  - Migration tool available
  - Support for questions

- **Month 6 (Version 2.0)**: Final Removal
  - run_logger.py deleted from codebase
  - Only core_logging remains
  - Old JSONL files archived (not deleted)
  - Final migration reminder

### Migration Deadlines

| Date | Milestone |
|------|-----------|
| 2025-01-XX | Phase 1.6 complete, deprecation begins |
| 2025-02-XX | First deprecation reminder |
| 2025-04-XX | Second deprecation reminder |
| 2025-06-XX | Final deprecation reminder |
| 2025-07-XX | run_logger.py removed (Version 2.0) |

---

## FAQ

**Q: Will my existing code break?**
A: No! run_logger.py stays in the codebase for 6 months with deprecation warnings only.

**Q: Do I need to migrate my old log files?**
A: No, old logs are preserved. Migration tool is optional for analysis/querying.

**Q: Can I still query run summaries?**
A: Yes! Use `core_logging.get_run_summary(run_id)` to get aggregated summaries.

**Q: What if I use RunSummary dataclass?**
A: The dataclass stays for 6 months. Migrate to dict-based summaries from `get_run_summary()`.

**Q: Will this affect my tests?**
A: Tests may show deprecation warnings. Update to core_logging to silence them.

**Q: Can I use both systems during transition?**
A: Yes, but avoid duplicate logging. Prefer core_logging for new code.

---

## Getting Help

- **Documentation**: See this guide
- **Issues**: File GitHub issue with `[logging-migration]` tag
- **Examples**: See `agent/tests/unit/test_core_logging.py`
- **Migration Tool**: `python -m agent.tools.migrate_logs --help`

---

## Related Documentation

- [core_logging API Reference](./CORE_LOGGING_API.md)
- [Phase 1.5: Dependency Injection](./DEPENDENCY_INJECTION.md)
- [Phase 1.6 Implementation Guide](./IMPLEMENTATION_GUIDE.md)
- [CHANGELOG.md](../CHANGELOG.md)

---

**Status**: Phase 1.6 migration in progress. Target completion: Week 1.
