# Changelog

All notable changes to the Multi-Agent Orchestrator System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Phase 8 - Root Level Audit & Cleanup (2025-11-25)

**Status**: ✅ In Progress
**Addresses**: Technical debt and documentation cleanup

#### Removed

- Deleted obsolete documentation files (AUDIT_REPORT.md, AUDIT_PROMPT.md, README.txt, etc.)
- Removed shim files (cost_tracker.py, site_tools.py root-level re-exports)
- Removed one-time utility scripts (add_sqlite_integration.py, check_hr_db.py)

#### Updated

- Fixed placeholder dates in CHANGELOG.md
- Updated tool name references in documentation (file_read → read)
- Added missing dependencies to requirements.txt
- Marked completed items in roadmap documentation
- Updated orchestrator consolidation plan status

---

### Phase 1.6 - Deprecate Dual Logging System (2025-11-20)

**Status**: ✅ Completed
**Addresses**: Vulnerability A2 - Dual logging systems causing duplication and wasted resources

#### Deprecated

- **run_logger.py** - Complete module deprecated in favor of core_logging.py
  - `start_run_legacy()` → Use `core_logging.new_run_id()` and `log_start()`
  - `log_iteration_legacy()` → Use `core_logging.log_iteration_begin()` and `log_iteration_end()`
  - `finish_run_legacy()` → Use `core_logging.log_final_status()`
  - `start_run()` (STAGE 2) → Use core_logging equivalent
  - `log_iteration()` (STAGE 2) → Use core_logging equivalent
  - `finalize_run()` (STAGE 2) → Use core_logging equivalent
- All deprecated functions now emit `DeprecationWarning` when called
- **Removal timeline**: run_logger.py will be removed in v2.0 (6 months from now)

#### Changed

- **orchestrator.py** - Refactored to use only core_logging
  - Removed all `run_logger.start_run()`, `log_iteration_legacy()`, and `finish_run_legacy()` calls
  - Now uses `core_logging.log_start()`, `log_iteration_begin()`, `log_iteration_end()`, and `log_final_status()`
  - Commented out legacy calls with migration notes
  - Removed unused legacy imports

- **orchestrator_2loop.py** - Refactored to use core_logging
  - Added core_logging infrastructure (`core_run_id`, `log_start()`)
  - Replaced all run_logger calls with core_logging equivalents
  - Added iteration begin/end logging
  - Added final status logging for all exit paths

#### Added

- **docs/MIGRATION_LOGGING.md** - Comprehensive migration guide (450+ lines)
  - API mapping table (run_logger → core_logging)
  - Step-by-step migration instructions
  - Breaking changes documentation
  - Timeline and deprecation schedule
  - FAQ section with common migration scenarios
  - Performance comparison (before/after metrics)

#### Migration Guide

See [docs/MIGRATION_LOGGING.md](./docs/MIGRATION_LOGGING.md) for complete migration instructions.

**Key Benefits**:
- ✅ **Single Source of Truth**: One logging system eliminates duplication
- ✅ **Event-Based Architecture**: JSONL event streams provide better granularity
- ✅ **Reduced Disk Usage**: No duplicate log files
- ✅ **Better Observability**: Structured events enable better analysis
- ✅ **Cleaner Codebase**: Removes 436 lines of legacy code (eventually)

**Migration Timeline**:
- **Now (Phase 1.6)**: Deprecation warnings active, both systems work
- **Months 1-5**: Grace period for migration
- **Month 6 (v2.0)**: run_logger.py removed entirely

---

## Previous Releases

### Phase 1.5 - Dependency Injection (2025-11-18)

**Status**: ✅ Completed
**Addresses**: Vulnerability A1 - Tight coupling to 12+ modules

#### Added

- **orchestrator_context.py** - Dependency injection container
  - 19 Protocol definitions for all dependencies
  - `OrchestratorContext` dataclass with core and optional services
  - `create_default()` factory for production use
  - `is_feature_available()` method for optional feature detection

- **tests/mocks.py** - Mock implementations for testing
  - `MockLLMProvider` with configurable responses
  - `MockCostTracker` with simulated cost tracking
  - 16+ additional mock providers
  - `create_mock_context()` factory for test use

- **docs/DEPENDENCY_INJECTION.md** - Complete DI documentation
  - Architecture overview
  - Usage examples (production, testing, partial mocking)
  - API reference
  - Migration guide
  - 14 unit tests with <1s execution time

#### Changed

- **orchestrator.py** - Refactored to use dependency injection
  - `main()` now accepts optional `OrchestratorContext` parameter
  - All dependencies accessed through `context.*` instead of direct imports
  - 100% backward compatible with existing code

- **orchestrator_2loop.py** - Added DI support
  - `main()` accepts optional context parameter
  - Uses `OrchestratorContext.create_default()` if no context provided

#### Migration Impact

- ✅ **100% Backward Compatible**: Existing code works without changes
- ✅ **Fast Unit Tests**: 14 tests run in <1s (no real LLM calls)
- ✅ **Zero Cost Testing**: Mocks eliminate $0.10-$0.50 per test
- ✅ **Loose Coupling**: Modules can evolve independently

---

### Phase 1.4 - Git Secret Scanning (2025-11-15)

**Status**: ✅ Completed
**Addresses**: Security vulnerability - Accidental secret commits

#### Added

- **git_secret_scanner.py** - Pre-commit secret detection
  - Pattern-based scanning for 20+ secret types
  - AWS keys, API tokens, passwords, private keys, etc.
  - Configurable sensitivity levels
  - False positive filtering

- **docs/SECURITY_GIT_SECRET_SCANNING.md** - Security documentation
  - Threat model and detection methodology
  - Configuration guide
  - Performance metrics (<200ms for typical commits)

#### Changed

- **git_utils.py** - Integrated secret scanning
  - `commit_all()` now scans for secrets before committing
  - Blocks commits containing high-risk secrets
  - Configurable via `git_secret_scanning_enabled` flag

---

### Phase 1.3 - Prompt Security (2025-11-12)

**Status**: ✅ Completed
**Addresses**: Prompt injection vulnerabilities

#### Added

- **prompt_security.py** - Injection detection and sanitization
  - Pattern-based detection for 15+ injection types
  - Task sanitization with configurable blocking
  - Security event logging

---

### Phase 1.2 - Log Sanitization (2025-11-10)

**Status**: ✅ Completed
**Addresses**: Sensitive data leakage in logs

#### Added

- **log_sanitizer.py** - Automatic PII/secret redaction
  - Redacts API keys, passwords, emails, credit cards
  - Integrated with all logging systems

---

## [1.0.0] - Initial Release

- Multi-agent orchestration system (Manager, Supervisor, Employee)
- Cost tracking and management
- Git integration
- Visual review capabilities
- Model routing based on task complexity
