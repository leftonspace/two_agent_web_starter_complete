# Orchestrator Consolidation Plan

**Status**: Deferred from P1 to P2
**Priority**: Medium-High
**Estimated Effort**: 3-5 days
**Risk Level**: High (affects core execution flow)
**Created**: 2025-11-24

---

## Executive Summary

JARVIS currently has **6 orchestrator files** with overlapping functionality, inconsistent naming, and complex interdependencies. This technical debt creates confusion, maintenance burden, and risk of bugs. A systematic consolidation is required to:

1. Merge redundant orchestrator implementations
2. Fix file header mismatches
3. Create clear version hierarchy
4. Update all import references
5. Comprehensive testing to prevent regressions

**Current State**: 6 orchestrator files (~200KB total code)
**Desired State**: 1-2 orchestrator files with clear versioning
**Impact**: Core execution flow, multi-agent coordination, stage management

---

## Problem Statement

### Current Issues

1. **Multiple Orchestrator Files** (6 total):
   - `orchestrator.py` (83KB)
   - `orchestrator_2loop.py` (16KB)
   - `orchestrator_3loop_legacy.py` (35KB)
   - `orchestrator_phase3.py` (32KB)
   - `orchestrator_context.py` (19KB)
   - `orchestrator_integration.py` (13KB)

2. **File Header Mismatches**:
   - `orchestrator.py` header says "orchestrator_phase3.py"
   - Unclear which is the "current" version
   - Comments reference wrong filenames

3. **Unclear Ownership**:
   - Multiple files claim to be "Phase 3"
   - Legacy markers not consistent
   - No clear deprecation path

4. **Maintenance Burden**:
   - Bug fixes need to be applied to multiple files
   - Feature additions unclear where to implement
   - Import confusion across codebase

5. **Testing Gaps**:
   - No integration tests comparing orchestrators
   - Unclear which tests cover which orchestrator
   - Risk of silent breakage

---

## Current File Analysis

### 1. `orchestrator.py` (83,332 bytes)

**Header Claims**: "orchestrator_phase3.py"

**Purpose** (from header):
```python
"""
PHASE 3: Adaptive Multi-Agent Orchestrator

This orchestrator implements the full Phase 3 architecture with:
- Dynamic roadmap management (merge, split, reorder, skip, reopen stages)
- Adaptive stage flow (auto-advance on 0 findings, intelligent fix cycles)
- Horizontal agent communication (inter-agent bus)
- Stage-level persistent memory
- Regression detection and automatic stage reopening
- Comprehensive Phase 3 logging
"""
```

**Key Features**:
- Dynamic roadmap management
- Adaptive stage flow
- Inter-agent bus integration
- Stage-level memory
- Regression detection
- Phase 3 logging

**Import Dependencies**:
- `core_logging`
- `cost_tracker`
- `exec_tools`
- `git_utils`
- `inter_agent_bus`
- `llm`
- `memory_store`
- `prompts`
- `run_logger`

**Status**: ✅ Most feature-complete, appears to be the "current" version

---

### 2. `orchestrator_phase3.py` (32,059 bytes)

**Purpose**: Unknown (needs analysis)

**Relationship to orchestrator.py**: Unclear - same name in header but different file

**Status**: ⚠️ Potentially redundant or older version

**Action Required**: Compare with orchestrator.py line-by-line

---

### 3. `orchestrator_3loop_legacy.py` (34,786 bytes)

**Purpose**: 3-loop orchestration (Plan → Execute → Review)

**Key Features**:
- JARVIS → Supervisor → Employee hierarchy
- 3-loop pattern
- Legacy Stage 1-2 features

**Marked as**: "legacy" in filename

**Status**: ⚠️ Should be deprecated or archived

**Action Required**: Verify no unique features needed, then deprecate

---

### 4. `orchestrator_2loop.py` (16,461 bytes)

**Purpose**: 2-loop orchestration (Execute → Review)

**Key Features**:
- Simplified 2-loop pattern
- Lighter weight than 3-loop

**Status**: ⚠️ Potentially useful for simple tasks, or redundant

**Action Required**: Evaluate if use cases justify keeping

---

### 5. `orchestrator_context.py` (19,102 bytes)

**Purpose**: Context-aware orchestration

**Key Features**:
- Context management
- Session state tracking

**Status**: ⚠️ Should be merged into main orchestrator or extracted as utility

**Action Required**: Extract context management to separate module

---

### 6. `orchestrator_integration.py` (13,134 bytes)

**Purpose**: Integration orchestration (unclear)

**Status**: ⚠️ Unclear purpose, potentially test/integration harness

**Action Required**: Analyze usage, potentially move to tests/

---

## Dependency Analysis

### Files That Import Orchestrators

Need to search codebase for:
```bash
from orchestrator import
from orchestrator_2loop import
from orchestrator_3loop_legacy import
from orchestrator_phase3 import
from orchestrator_context import
from orchestrator_integration import
```

**Action Required**: Run comprehensive grep to find all imports

### Common Dependencies

All orchestrators depend on:
- `core_logging` - Logging infrastructure
- `cost_tracker` - Cost tracking
- `llm` - LLM calls
- `run_logger` - Run tracking
- `prompts` - Prompt management
- `git_utils` - Git operations

**Strategy**: These can remain external dependencies

### Unique Dependencies

Each orchestrator may have unique dependencies that need consolidation:
- `inter_agent_bus` (Phase 3 only?)
- `memory_store` (Phase 3 only?)
- Different prompt templates

**Action Required**: Catalog unique dependencies per orchestrator

---

## Consolidation Strategy

### Option 1: Single Unified Orchestrator (Recommended)

**Approach**: Merge all functionality into one orchestrator with modes

```python
class JarvisOrchestrator:
    """
    Unified orchestrator with multiple execution modes.

    Modes:
    - PHASE3: Full adaptive multi-agent (default)
    - LEGACY_3LOOP: 3-loop pattern for compatibility
    - SIMPLE_2LOOP: Lightweight 2-loop
    - CONTEXT_AWARE: Context-based routing
    """

    def __init__(self, mode: OrchestratorMode = OrchestratorMode.PHASE3):
        self.mode = mode
        # Initialize based on mode
```

**Pros**:
- Single source of truth
- Easy to maintain
- Clear versioning
- Shared code for common functionality

**Cons**:
- Large file size
- More complex initialization
- Risk of mode-specific bugs

---

### Option 2: Hierarchical Architecture

**Approach**: Base class with specialized subclasses

```python
class BaseOrchestrator:
    """Base orchestrator with core functionality"""
    # Common code: cost tracking, logging, git ops

class Phase3Orchestrator(BaseOrchestrator):
    """Phase 3 adaptive orchestrator"""
    # Phase 3 specific: roadmap management, inter-agent bus

class LegacyOrchestrator(BaseOrchestrator):
    """Legacy 3-loop orchestrator (deprecated)"""
    # Legacy code for backward compatibility
```

**Pros**:
- Clear inheritance hierarchy
- Easier to test individual variants
- Gradual deprecation path

**Cons**:
- Multiple files to maintain
- Shared code in base class can become bloated
- Import complexity

---

### Option 3: Modular Composition (Best Practice)

**Approach**: Extract functionality into composable modules

```python
# Core modules
from .stages import StageManager
from .agents import AgentCoordinator
from .memory import OrchestratorMemory
from .roadmap import RoadmapManager

class JarvisOrchestrator:
    """
    Orchestrator composed of modular components.

    Components:
    - StageManager: Stage flow and transitions
    - AgentCoordinator: Multi-agent coordination
    - OrchestratorMemory: Stage and session memory
    - RoadmapManager: Dynamic roadmap management
    """

    def __init__(self):
        self.stages = StageManager()
        self.agents = AgentCoordinator()
        self.memory = OrchestratorMemory()
        self.roadmap = RoadmapManager()
```

**Pros**:
- Best separation of concerns
- Highly testable
- Easy to extend
- Clear module boundaries

**Cons**:
- Most refactoring work
- Requires careful interface design
- Initial complexity

**Recommendation**: Option 3 (Modular Composition) for long-term maintainability

---

## Implementation Plan

### Phase 1: Analysis & Inventory (Day 1)

**Tasks**:
1. **Compare Files Line-by-Line**
   - Run diff between orchestrator.py and orchestrator_phase3.py
   - Identify unique code in each file
   - Document feature matrix

2. **Map Dependencies**
   - Grep all imports of orchestrator files
   - Create dependency graph
   - Identify breaking change risks

3. **Review Test Coverage**
   - Find all tests for each orchestrator
   - Identify gaps in test coverage
   - Document test scenarios needed

4. **User Impact Analysis**
   - Which orchestrator is used in production?
   - Are multiple orchestrators actively used?
   - Migration path for existing users

**Deliverables**:
- Feature comparison matrix
- Dependency graph diagram
- Test coverage report
- User impact assessment

---

### Phase 2: Design Consolidation (Day 2)

**Tasks**:
1. **Design Module Architecture**
   - Define module boundaries
   - Design interfaces
   - Create UML diagrams

2. **Plan Data Migration**
   - Identify state/config differences
   - Design migration scripts
   - Backward compatibility strategy

3. **Define Testing Strategy**
   - Unit tests per module
   - Integration tests for orchestrator
   - Regression test suite
   - Performance benchmarks

4. **Create Rollback Plan**
   - Snapshot current state
   - Document rollback procedure
   - Identify rollback triggers

**Deliverables**:
- Architecture design document
- Module interface specifications
- Testing plan
- Rollback procedure

---

### Phase 3: Extract Common Code (Day 3)

**Tasks**:
1. **Create Base Modules**
   ```
   agent/orchestration/
   ├── __init__.py
   ├── base.py           # Base orchestrator
   ├── stages.py         # Stage management
   ├── agents.py         # Agent coordination
   ├── memory.py         # Orchestrator memory
   ├── roadmap.py        # Roadmap management
   └── loops.py          # Loop patterns (2-loop, 3-loop)
   ```

2. **Extract Common Code**
   - Cost tracking
   - Logging infrastructure
   - Git operations
   - LLM call wrappers
   - State management

3. **Write Unit Tests**
   - Test each module independently
   - Mock external dependencies
   - Cover edge cases

**Deliverables**:
- `agent/orchestration/` directory
- Common code extracted
- Unit tests for each module

---

### Phase 4: Consolidate Main Orchestrator (Day 4)

**Tasks**:
1. **Create Unified Orchestrator**
   - Combine Phase 3 features
   - Add mode selection
   - Integrate all modules

2. **Migrate Unique Features**
   - From orchestrator_2loop.py
   - From orchestrator_3loop_legacy.py
   - From orchestrator_context.py
   - From orchestrator_integration.py

3. **Update Imports**
   - Replace old imports across codebase
   - Add deprecation warnings to old files
   - Update documentation

4. **Write Integration Tests**
   - Test full orchestration flows
   - Test mode switching
   - Test backward compatibility

**Deliverables**:
- `agent/orchestration/orchestrator.py` (consolidated)
- Deprecated old orchestrator files
- Updated imports
- Integration tests

---

### Phase 5: Testing & Validation (Day 5)

**Tasks**:
1. **Comprehensive Testing**
   - Run full test suite
   - Execute integration tests
   - Performance benchmarks
   - Memory leak checks

2. **Manual Testing**
   - Test common workflows
   - Test edge cases
   - Test error handling
   - Test rollback scenarios

3. **Code Review**
   - Review all changes
   - Check for security issues
   - Verify best practices
   - Documentation review

4. **Performance Validation**
   - Compare with baseline
   - Check memory usage
   - Verify no regressions

**Deliverables**:
- Test results report
- Performance comparison
- Code review sign-off
- Go/no-go decision

---

## Testing Requirements

### Unit Tests

**For Each Module**:
```python
# test_stages.py
def test_stage_transition()
def test_stage_validation()
def test_stage_memory()

# test_agents.py
def test_agent_assignment()
def test_agent_communication()
def test_agent_coordination()

# test_roadmap.py
def test_roadmap_creation()
def test_roadmap_modification()
def test_stage_merging()
```

**Coverage Target**: 80%+ for each module

---

### Integration Tests

**Critical Workflows**:
1. Simple task execution (2-loop)
2. Complex task with supervision (3-loop)
3. Multi-stage project (Phase 3)
4. Context-aware routing
5. Error recovery and retry
6. Cost tracking throughout
7. Git operations integration
8. Inter-agent communication

**Test Matrix**:
| Test Case | Mode | Expected Result |
|-----------|------|-----------------|
| Simple query | SIMPLE_2LOOP | Execute → Review → Done |
| Code generation | LEGACY_3LOOP | Plan → Execute → Review → Done |
| Multi-stage project | PHASE3 | Dynamic stages, agent coordination |
| Error handling | All | Graceful recovery, proper logging |

---

### Regression Tests

**Compare Against Baseline**:
- Run same tasks on old vs new orchestrator
- Compare outputs
- Compare costs
- Compare execution time
- Compare memory usage

**Regression Suite**:
```bash
# Run regression tests
pytest tests/regression/test_orchestrator_compatibility.py -v

# Compare outputs
diff old_output.json new_output.json

# Performance comparison
python scripts/benchmark_orchestrators.py
```

---

### Performance Benchmarks

**Metrics to Track**:
- Task execution time
- Memory usage
- API call count
- Cost per task
- Agent spawn time
- Stage transition time

**Baseline Targets**:
- No more than 5% performance regression
- Memory usage within 10% of baseline
- Same or fewer API calls
- Cost within 2% of baseline

---

## Risk Assessment

### High Risks

1. **Breaking Production Workflows** (Severity: Critical)
   - **Impact**: Users unable to execute tasks
   - **Mitigation**: Comprehensive testing, gradual rollout, keep old files temporarily
   - **Rollback**: Revert to old orchestrators immediately

2. **Import Chain Breakage** (Severity: High)
   - **Impact**: Module import errors across codebase
   - **Mitigation**: Automated import scanning, IDE refactoring tools
   - **Rollback**: Restore old imports

3. **Performance Regression** (Severity: High)
   - **Impact**: Slower execution, higher costs
   - **Mitigation**: Performance benchmarks, load testing
   - **Rollback**: Revert if >10% regression

### Medium Risks

4. **Test Coverage Gaps** (Severity: Medium)
   - **Impact**: Undetected bugs in production
   - **Mitigation**: Comprehensive test suite, manual testing
   - **Rollback**: N/A (fix bugs as found)

5. **Documentation Drift** (Severity: Medium)
   - **Impact**: Confusion for developers
   - **Mitigation**: Update docs alongside code
   - **Rollback**: Update docs to reflect revert

6. **Config Migration Issues** (Severity: Medium)
   - **Impact**: Existing configs may not work
   - **Mitigation**: Migration scripts, backward compatibility
   - **Rollback**: Restore old configs

### Low Risks

7. **Learning Curve** (Severity: Low)
   - **Impact**: Developers need time to learn new structure
   - **Mitigation**: Documentation, examples, migration guide
   - **Rollback**: N/A

---

## Migration Guide for Users

### For Developers

**Before Consolidation**:
```python
from orchestrator import run_agent
from orchestrator_3loop_legacy import ThreeLoopOrchestrator
```

**After Consolidation**:
```python
from agent.orchestration import JarvisOrchestrator, OrchestratorMode

# Default (Phase 3)
orchestrator = JarvisOrchestrator()

# Legacy 3-loop mode
orchestrator = JarvisOrchestrator(mode=OrchestratorMode.LEGACY_3LOOP)
```

---

### Configuration Changes

**Before**:
```yaml
orchestrator:
  type: phase3
  loops: 3
```

**After**:
```yaml
orchestrator:
  mode: PHASE3  # or LEGACY_3LOOP, SIMPLE_2LOOP
  config:
    # Mode-specific config
```

---

### Import Updates

**Automated Script**:
```bash
# Run import migration script
python scripts/migrate_orchestrator_imports.py

# Verify changes
git diff
```

**Manual Updates**:
```python
# Old
from orchestrator import execute_task
from orchestrator_phase3 import Phase3Orchestrator

# New
from agent.orchestration import JarvisOrchestrator
```

---

## Success Criteria

### Must Have (P0)

- ✅ All 6 orchestrators consolidated into 1-2 files
- ✅ File headers match actual filenames
- ✅ All imports updated across codebase
- ✅ 80%+ test coverage
- ✅ Zero critical bugs
- ✅ All integration tests pass
- ✅ Documentation updated

### Should Have (P1)

- ✅ Performance within 5% of baseline
- ✅ Modular architecture implemented
- ✅ Backward compatibility for 1 version
- ✅ Migration guide complete
- ✅ Deprecation warnings on old files

### Nice to Have (P2)

- ✅ Performance improvements
- ✅ Reduced code duplication
- ✅ Better error messages
- ✅ Enhanced logging

---

## Timeline

### Aggressive (3 days)

**Risk**: High
**Suitable for**: Small codebase, simple consolidation

| Day | Phase | Tasks |
|-----|-------|-------|
| 1 | Analysis | Compare files, map dependencies |
| 1 | Design | Module architecture, interfaces |
| 2 | Implementation | Extract common code, consolidate |
| 2-3 | Testing | Unit tests, integration tests |
| 3 | Validation | Performance testing, code review |

---

### Recommended (5 days)

**Risk**: Medium
**Suitable for**: Production codebase, thorough testing

| Day | Phase | Tasks |
|-----|-------|-------|
| 1 | Analysis & Inventory | Deep analysis of all 6 files |
| 2 | Design Consolidation | Architecture design, planning |
| 3 | Extract Common Code | Module extraction, unit tests |
| 4 | Consolidate Main | Unified orchestrator, integration tests |
| 5 | Testing & Validation | Comprehensive testing, validation |

---

### Conservative (7-10 days)

**Risk**: Low
**Suitable for**: Critical production system, extensive testing

| Days | Phase | Tasks |
|------|-------|-------|
| 1-2 | Analysis | Thorough comparison, dependency mapping |
| 2-3 | Design | Detailed design, multiple review rounds |
| 3-5 | Implementation | Incremental consolidation, continuous testing |
| 5-7 | Testing | Full test suite, performance benchmarks |
| 7-8 | Validation | Manual testing, code review, security audit |
| 9-10 | Deployment | Gradual rollout, monitoring, documentation |

**Recommendation**: 5-day timeline for JARVIS consolidation

---

## Rollback Plan

### Triggers for Rollback

1. **Critical Bug Discovered**
   - Data loss
   - Execution failure >10% of tasks
   - Security vulnerability

2. **Performance Regression**
   - >10% slower execution
   - >20% memory increase
   - >5% cost increase

3. **Breaking Changes**
   - Existing configs broken
   - Import errors across codebase
   - Test failures >20%

---

### Rollback Procedure

**Step 1: Immediate Actions** (5 minutes)
```bash
# 1. Stop deployment
git checkout main

# 2. Restore old orchestrators
git revert <consolidation-commit-sha>

# 3. Redeploy
git push origin main
```

**Step 2: Verification** (15 minutes)
```bash
# 1. Run smoke tests
pytest tests/smoke/ -v

# 2. Verify imports work
python -c "from orchestrator import execute_task"

# 3. Test sample workflow
python scripts/test_workflow.py
```

**Step 3: Communication** (30 minutes)
- Notify team of rollback
- Document issues encountered
- Plan remediation

---

### Snapshot Before Consolidation

**Create Comprehensive Snapshot**:
```bash
# Use rollback manager
python scripts/create_consolidation_snapshot.py

# Manual backup
cp -r agent/orchestrator*.py .backups/orchestrators/
cp -r tests/test_orchestrator*.py .backups/tests/
```

---

## Appendix

### A. File Comparison Commands

```bash
# Compare main orchestrators
diff -u orchestrator.py orchestrator_phase3.py > orchestrator_diff.txt

# Find unique functions
grep "^def " orchestrator.py | sort > orch1_functions.txt
grep "^def " orchestrator_phase3.py | sort > orch2_functions.txt
diff orch1_functions.txt orch2_functions.txt

# Count lines per file
wc -l orchestrator*.py
```

---

### B. Dependency Graph Generation

```bash
# Install dependency analyzer
pip install pydeps

# Generate dependency graph
pydeps orchestrator.py --max-bacon=2 -o orchestrator_deps.svg

# Or use grep to find imports
grep -r "from orchestrator" agent/ | sort | uniq > orchestrator_imports.txt
```

---

### C. Test Coverage Commands

```bash
# Run with coverage
pytest --cov=agent.orchestration --cov-report=html tests/

# View coverage report
open htmlcov/index.html

# Coverage per module
pytest --cov=agent.orchestration --cov-report=term-missing
```

---

### D. Performance Benchmark Script

```python
# scripts/benchmark_orchestrators.py
import time
from orchestrator import execute_task as old_execute
from agent.orchestration import JarvisOrchestrator

def benchmark():
    tasks = load_test_tasks()

    # Benchmark old
    start = time.time()
    for task in tasks:
        old_execute(task)
    old_time = time.time() - start

    # Benchmark new
    orch = JarvisOrchestrator()
    start = time.time()
    for task in tasks:
        orch.execute(task)
    new_time = time.time() - start

    print(f"Old: {old_time:.2f}s")
    print(f"New: {new_time:.2f}s")
    print(f"Difference: {((new_time - old_time) / old_time * 100):.1f}%")
```

---

### E. Import Migration Script

```python
# scripts/migrate_orchestrator_imports.py
import os
import re
from pathlib import Path

OLD_IMPORTS = [
    "from orchestrator import",
    "from orchestrator_phase3 import",
    "from orchestrator_3loop_legacy import",
    "from orchestrator_2loop import",
]

NEW_IMPORT = "from agent.orchestration import"

def migrate_file(file_path):
    content = file_path.read_text()
    original = content

    for old_import in OLD_IMPORTS:
        content = content.replace(old_import, NEW_IMPORT)

    if content != original:
        file_path.write_text(content)
        print(f"Updated: {file_path}")

# Run on all Python files
for py_file in Path("agent").rglob("*.py"):
    migrate_file(py_file)
```

---

## Conclusion

Orchestrator consolidation is a **significant refactoring effort** requiring:

- **5 days minimum** for safe implementation
- **Comprehensive testing** to prevent regressions
- **Careful migration** of existing code
- **Clear rollback plan** for safety

**Recommendation**: Schedule as dedicated P2 task with proper planning, testing resources, and rollback capability.

**Priority**: Medium-High (technical debt reduction, but not blocking current functionality)

**Next Steps**:
1. Review this plan with team
2. Allocate dedicated time (no interruptions)
3. Set up comprehensive test environment
4. Execute Phase 1 (Analysis & Inventory)
5. Go/no-go decision after Phase 1 complete

---

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Author**: JARVIS AGI Team
**Status**: Planning Phase
