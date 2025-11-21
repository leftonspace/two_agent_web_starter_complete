# Comprehensive Codebase Audit - JARVIS for Business

**Repository:** leftonspace/two_agent_web_starter_complete
**Purpose:** Complete system audit to verify all components are functional before Phase 8.1
**Priority:** CRITICAL - Must pass before any new development

---

## Audit Objectives

1. ✅ Verify all Python files compile without syntax errors
2. ✅ Check all imports resolve correctly (no missing modules)
3. ✅ Validate core system components are functional
4. ✅ Ensure test suites pass
5. ✅ Verify configuration files are correct
6. ✅ Check for merge artifacts and conflicts
7. ✅ Validate file structure matches documentation
8. ✅ Test critical integration points
9. ✅ Review git repository health
10. ✅ Generate comprehensive audit report

---

## Audit Tasks

### TASK 1: File Structure Validation

**Objective:** Verify repository structure is complete and matches expected layout.

**Actions:**
1. List all directories in `agent/`
2. Check for required core files:
   - `agent/orchestrator.py`
   - `agent/llm.py`
   - `agent/cost_tracker.py`
   - `agent/knowledge_graph.py`
   - `agent/domain_router.py`
   - `agent/exec_tools.py`
   - `agent/exec_safety.py`
   - `agent/exec_analysis.py`
   - `agent/exec_deps.py`
   - `agent/run_logger.py`
   - `agent/run_mode.py`
   - `agent/status_codes.py`
   - `agent/config.py`
   - `agent/core_logging.py`

3. Check for required support files:
   - `agent/prompts.py`
   - `agent/git_utils.py`
   - `agent/sandbox.py`
   - `agent/safe_io.py`

4. Verify directory structure:
   ```
   agent/
   ├── tests/
   ├── tests_sanity/
   ├── tests_e2e/
   ├── tools/
   ├── workflows/
   ├── prompts/
   ├── run_logs/
   ├── cost_logs/
   └── memory_store/
   ```

5. Check root files:
   - `.gitignore`
   - `.env.example`
   - `requirements.txt`
   - `README.md`
   - `DEVELOPER_GUIDE.md`
   - `make.py`

**Success Criteria:**
- All required core files present
- Directory structure complete
- No unexpected files in critical paths

**Output:** List of missing/unexpected files

---

### TASK 2: Python Syntax Validation

**Objective:** Ensure all Python files compile without syntax errors.

**Actions:**
1. Compile all Python files in `agent/`:
   ```bash
   python -m py_compile agent/*.py
   ```

2. Check specific critical files individually:
   ```bash
   python -m py_compile agent/orchestrator.py
   python -m py_compile agent/llm.py
   python -m py_compile agent/cost_tracker.py
   python -m py_compile agent/knowledge_graph.py
   python -m py_compile agent/domain_router.py
   python -m py_compile agent/exec_tools.py
   python -m py_compile agent/exec_safety.py
   python -m py_compile agent/run_logger.py
   python -m py_compile agent/run_mode.py
   ```

3. Check test files:
   ```bash
   python -m py_compile agent/tests/*.py
   python -m py_compile agent/tests_sanity/*.py
   ```

4. Check dev scripts:
   ```bash
   python -m py_compile dev/*.py
   ```

**Success Criteria:**
- Zero syntax errors
- All files compile successfully

**Output:** List of files with syntax errors (if any)

---

### TASK 3: Import Dependency Check

**Objective:** Verify all imports resolve correctly.

**Actions:**
1. Test imports for core modules:
   ```python
   # Test orchestrator imports
   from agent.orchestrator import run_orchestrator
   from agent.orchestrator import Orchestrator

   # Test LLM imports
   from agent.llm import chat, chat_json

   # Test cost tracker imports
   from agent.cost_tracker import CostTracker
   from agent.cost_tracker_instance import get_cost_tracker

   # Test knowledge graph imports
   from agent.knowledge_graph import KnowledgeGraph

   # Test domain router imports
   from agent.domain_router import classify_domain

   # Test execution imports
   from agent.exec_tools import get_tool_metadata
   from agent.exec_safety import run_safety_checks
   from agent.exec_analysis import analyze_code
   from agent.exec_deps import check_dependencies

   # Test logging imports
   from agent.core_logging import log_event
   from agent.run_logger import RunSummary
   from agent.run_mode import RunMode

   # Test utility imports
   from agent.prompts import load_prompts
   from agent.git_utils import commit_all
   from agent.config import Config
   from agent.status_codes import StatusCode
   ```

2. Check for circular import issues:
   ```python
   # Import orchestrator and check what it imports
   import agent.orchestrator
   # Should not cause circular import errors
   ```

3. Test cross-module dependencies:
   ```python
   # Orchestrator should be able to use all its dependencies
   from agent.orchestrator_context import OrchestratorContext
   from agent.specialists import SpecialistRegistry
   from agent.overseer import Overseer
   from agent.workflow_manager import WorkflowManager
   ```

4. Check for missing external dependencies:
   ```python
   # Third-party imports
   import openai
   import anthropic
   import pytest
   import sqlalchemy
   # etc.
   ```

**Success Criteria:**
- All imports resolve successfully
- No circular import errors
- No missing module errors

**Output:**
- List of import errors
- Circular dependency graph (if any)
- Missing external packages

---

### TASK 4: Core Component Functional Tests

**Objective:** Verify core components can be instantiated and basic operations work.

**Actions:**

1. **Test LLM Client:**
   ```python
   from agent.llm import chat

   # Test basic chat (mock if no API key)
   result = await chat("test prompt", model="gpt-4o-mini")
   assert result is not None
   ```

2. **Test Cost Tracker:**
   ```python
   from agent.cost_tracker_instance import get_cost_tracker

   tracker = get_cost_tracker()
   assert tracker is not None

   # Test tracking a call
   tracker.track_call("gpt-4o", 100, 50)
   total = tracker.get_total_cost()
   assert total > 0
   ```

3. **Test Orchestrator Initialization:**
   ```python
   from agent.orchestrator import Orchestrator
   from agent.orchestrator_context import OrchestratorContext

   context = OrchestratorContext()
   orchestrator = Orchestrator(context)
   assert orchestrator is not None
   ```

4. **Test Knowledge Graph:**
   ```python
   from agent.knowledge_graph import KnowledgeGraph

   kg = KnowledgeGraph()
   assert kg is not None

   # Test basic operations
   kg.add_mission_node("test_mission", {"status": "test"})
   ```

5. **Test Domain Router:**
   ```python
   from agent.domain_router import classify_domain

   domain = classify_domain("Build a Python web scraper")
   assert domain is not None
   assert hasattr(domain, 'value')
   ```

6. **Test Safety Checks:**
   ```python
   from agent.exec_safety import run_safety_checks

   safe = run_safety_checks("print('hello')", "python")
   assert safe is not None
   ```

7. **Test Logging:**
   ```python
   from agent.core_logging import log_event

   log_event("test_event", {"key": "value"})
   # Should not raise errors
   ```

**Success Criteria:**
- All components instantiate without errors
- Basic operations complete successfully
- No runtime exceptions

**Output:**
- List of component initialization failures
- Stack traces for errors

---

### TASK 5: Test Suite Validation

**Objective:** Run all test suites and verify they pass.

**Actions:**

1. **Run Sanity Tests:**
   ```bash
   pytest agent/tests_sanity/test_sanity.py -v --tb=short
   ```

2. **Run Unit Tests:**
   ```bash
   pytest agent/tests/ -v --tb=short
   ```

3. **Run E2E Tests (if available):**
   ```bash
   pytest agent/tests_e2e/ -v --tb=short
   ```

4. **Run Specific Component Tests:**
   ```bash
   # Test orchestrator
   pytest agent/tests/test_orchestrator.py -v

   # Test LLM
   pytest agent/tests/test_llm.py -v

   # Test cost tracker
   pytest agent/tests/test_cost_tracker.py -v

   # Test knowledge graph
   pytest agent/tests/test_knowledge_graph.py -v
   ```

5. **Check Test Coverage:**
   ```bash
   pytest agent/tests/ --cov=agent --cov-report=term-missing
   ```

**Success Criteria:**
- All tests pass (or document known failures)
- Test coverage >60% on core files
- No import errors in tests

**Output:**
- Test results summary
- Failed test details
- Coverage report

---

### TASK 6: Configuration Validation

**Objective:** Verify all configuration files are correct and complete.

**Actions:**

1. **Check `.env.example`:**
   ```bash
   cat .env.example
   ```
   - Verify it contains all required API keys
   - Check format is correct

2. **Check `requirements.txt`:**
   ```bash
   cat requirements.txt
   ```
   - Verify all dependencies listed
   - Check for version conflicts
   - Try installing: `pip install -r requirements.txt --dry-run`

3. **Check `agent/config.py`:**
   ```python
   from agent.config import Config

   config = Config()
   assert hasattr(config, 'DEFAULT_MODEL')
   assert hasattr(config, 'MAX_ITERATIONS')
   assert hasattr(config, 'ENABLE_SAFETY_CHECKS')
   ```

4. **Check `agent/project_config.json`:**
   ```bash
   python -c "import json; json.load(open('agent/project_config.json'))"
   ```

5. **Check `pytest.ini` or `pyproject.toml`:**
   - Verify pytest configuration exists
   - Check test paths are correct

**Success Criteria:**
- All config files valid
- No missing required configuration
- Dependencies installable

**Output:**
- Configuration issues
- Missing dependencies

---

### TASK 7: Merge Conflict Detection

**Objective:** Find any unresolved merge conflicts or artifacts.

**Actions:**

1. **Search for Git conflict markers:**
   ```bash
   grep -r "<<<<<<< " agent/
   grep -r "=======" agent/ | grep -v ".pyc" | grep -v "__pycache__"
   grep -r ">>>>>>> " agent/
   ```

2. **Check for duplicate function definitions:**
   ```bash
   # Look for functions defined multiple times in same file
   for file in agent/*.py; do
       echo "Checking $file"
       grep -n "^def " "$file" | awk -F: '{print $2}' | sort | uniq -d
   done
   ```

3. **Check for duplicate imports:**
   ```bash
   for file in agent/*.py; do
       echo "Checking imports in $file"
       grep "^import \|^from " "$file" | sort | uniq -d
   done
   ```

4. **Look for orphaned files:**
   ```bash
   # Find .orig or .bak files from merges
   find agent/ -name "*.orig" -o -name "*.bak" -o -name "*~"
   ```

5. **Check git status:**
   ```bash
   git status
   git diff --check
   ```

**Success Criteria:**
- No conflict markers found
- No duplicate definitions
- Git status clean

**Output:**
- List of files with conflict markers
- Duplicate definitions found
- Orphaned files

---

### TASK 8: Integration Point Testing

**Objective:** Test that major system integrations work correctly.

**Actions:**

1. **Test Orchestrator → LLM Integration:**
   ```python
   from agent.orchestrator import Orchestrator
   from agent.llm import chat

   # Verify orchestrator can call LLM
   # (with mocked LLM if no API key)
   ```

2. **Test Orchestrator → Cost Tracker Integration:**
   ```python
   from agent.orchestrator import Orchestrator
   from agent.cost_tracker_instance import get_cost_tracker

   # Verify cost tracking happens during orchestration
   ```

3. **Test Orchestrator → Knowledge Graph Integration:**
   ```python
   from agent.orchestrator import Orchestrator
   from agent.knowledge_graph import KnowledgeGraph

   # Verify missions are logged to knowledge graph
   ```

4. **Test Domain Router → Specialists Integration:**
   ```python
   from agent.domain_router import classify_domain
   from agent.specialists import SpecialistRegistry

   # Verify domain classification connects to specialists
   ```

5. **Test Execution → Safety Integration:**
   ```python
   from agent.exec_tools import execute_tool
   from agent.exec_safety import run_safety_checks

   # Verify safety checks run before execution
   ```

**Success Criteria:**
- All integrations functional
- Data flows correctly between components
- No integration errors

**Output:**
- Integration failures
- Data flow issues

---

### TASK 9: Git Repository Health

**Objective:** Verify git repository is in good state.

**Actions:**

1. **Check current branch:**
   ```bash
   git branch --show-current
   git status
   ```

2. **List all branches:**
   ```bash
   git branch -a
   ```

3. **Check for uncommitted changes:**
   ```bash
   git diff
   git diff --cached
   ```

4. **Verify no corrupted commits:**
   ```bash
   git fsck --full
   ```

5. **Check recent commit history:**
   ```bash
   git log --oneline -20
   ```

6. **Look for large files:**
   ```bash
   git ls-files -z | xargs -0 du -h | sort -hr | head -20
   ```

**Success Criteria:**
- Repository not corrupted
- No unexpected uncommitted changes
- Reasonable file sizes

**Output:**
- Git health report
- Large files list
- Uncommitted changes

---

### TASK 10: Documentation Accuracy

**Objective:** Verify documentation matches actual code state.

**Actions:**

1. **Check DEVELOPER_GUIDE.md mentions match files:**
   - Files mentioned exist
   - File purposes match descriptions

2. **Check CLEAN_BRANCH_GUIDE.md (if exists):**
   - Instructions still valid
   - File references correct

3. **Check implementation guide:**
   - `docs/IMPLEMENTATION_PROMPTS_PHASES_6_11 (1).md` exists
   - Phases described match current state

4. **Check README.md:**
   - Setup instructions accurate
   - Dependencies listed match requirements.txt

**Success Criteria:**
- Documentation accurate
- No broken references
- Setup instructions work

**Output:**
- Documentation issues
- Broken references

---

### TASK 11: Code Quality Checks

**Objective:** Check for code quality issues.

**Actions:**

1. **Check for common anti-patterns:**
   ```bash
   # Look for bare except clauses
   grep -n "except:" agent/*.py

   # Look for print statements (should use logging)
   grep -n "print(" agent/*.py | grep -v "#" | grep -v "test"

   # Look for TODO/FIXME comments
   grep -rn "TODO\|FIXME\|HACK\|XXX" agent/
   ```

2. **Check file permissions:**
   ```bash
   # Verify executable files are marked
   ls -la dev/*.py
   ls -la agent/*.py
   ```

3. **Check for unused imports:**
   ```bash
   # Would need pyflakes or similar
   python -m pyflakes agent/*.py 2>&1 | grep "imported but unused"
   ```

4. **Check for undefined names:**
   ```bash
   python -m pyflakes agent/*.py 2>&1 | grep "undefined name"
   ```

**Success Criteria:**
- Minimal anti-patterns
- No undefined names
- Appropriate permissions

**Output:**
- Code quality issues
- Anti-patterns found

---

### TASK 12: Critical Path Execution Test

**Objective:** Test that critical execution paths work end-to-end.

**Actions:**

1. **Test simple orchestrator run (dry run):**
   ```bash
   # With mocked LLM
   python dev/run_once.py --task "test task" --dry-run
   ```

2. **Test cost tracking works:**
   ```python
   from agent.cost_tracker_instance import get_cost_tracker

   tracker = get_cost_tracker()
   initial = tracker.get_total_cost()

   # Simulate some calls
   tracker.track_call("gpt-4o", 1000, 500)

   final = tracker.get_total_cost()
   assert final > initial
   ```

3. **Test logging works:**
   ```python
   from agent.core_logging import log_event
   import os

   log_event("audit_test", {"status": "testing"})

   # Verify log file created
   # Check run_logs_main/ directory
   ```

4. **Test safety checks work:**
   ```python
   from agent.exec_safety import run_safety_checks

   # Safe code
   safe = run_safety_checks("x = 1 + 1", "python")
   assert safe == True

   # Unsafe code
   unsafe = run_safety_checks("import os; os.system('rm -rf /')", "python")
   assert unsafe == False
   ```

**Success Criteria:**
- Critical paths execute
- No runtime errors
- Outputs as expected

**Output:**
- Execution results
- Error traces

---

## Comprehensive Audit Report Template

After completing all tasks, generate this report:

```markdown
# JARVIS Codebase Audit Report

**Date:** [Date]
**Repository:** leftonspace/two_agent_web_starter_complete
**Branch:** [Current Branch]
**Auditor:** [AI/Human]

---

## Executive Summary

- **Overall Status:** [PASS / FAIL / WARNINGS]
- **Critical Issues:** [Count]
- **Warnings:** [Count]
- **Tests Passing:** [X/Y]
- **Code Coverage:** [X%]

---

## Task Results

### 1. File Structure: [PASS/FAIL]
- Missing Files: [List or "None"]
- Unexpected Files: [List or "None"]
- Notes: [Any observations]

### 2. Python Syntax: [PASS/FAIL]
- Files with Errors: [Count]
- Error Details: [List or "None"]

### 3. Import Dependencies: [PASS/FAIL]
- Import Errors: [List or "None"]
- Circular Imports: [List or "None"]
- Missing Packages: [List or "None"]

### 4. Core Components: [PASS/FAIL]
- Failed Components: [List or "None"]
- Error Details: [Details]

### 5. Test Suites: [PASS/FAIL]
- Total Tests: [Count]
- Passing: [Count]
- Failing: [Count]
- Coverage: [X%]

### 6. Configuration: [PASS/FAIL]
- Config Issues: [List or "None"]

### 7. Merge Conflicts: [PASS/FAIL]
- Conflict Markers: [Count]
- Files Affected: [List or "None"]

### 8. Integration Points: [PASS/FAIL]
- Failed Integrations: [List or "None"]

### 9. Git Repository: [PASS/FAIL]
- Repository Health: [Good/Issues]
- Uncommitted Changes: [Yes/No]

### 10. Documentation: [PASS/FAIL]
- Accuracy Issues: [List or "None"]

### 11. Code Quality: [PASS/FAIL]
- Anti-patterns: [Count]
- Undefined Names: [Count]

### 12. Critical Paths: [PASS/FAIL]
- Execution Issues: [List or "None"]

---

## Critical Issues (Must Fix)

1. [Issue description]
   - **Impact:** [High/Medium/Low]
   - **Location:** [File:line]
   - **Fix:** [Recommended fix]

[Repeat for each critical issue]

---

## Warnings (Should Fix)

1. [Warning description]
   - **Impact:** [Medium/Low]
   - **Location:** [File:line]
   - **Fix:** [Recommended fix]

[Repeat for each warning]

---

## Recommendations

### Immediate Actions (Before Phase 8.1)
1. [Action]
2. [Action]

### Short-term Improvements
1. [Improvement]
2. [Improvement]

### Long-term Considerations
1. [Consideration]
2. [Consideration]

---

## Sign-off

- [ ] All critical issues resolved
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Git repository clean
- [ ] **READY FOR PHASE 8.1** [YES/NO]

---

**Audit Complete**
```

---

## How to Use This Audit

### Option 1: Manual Execution

Go through each task manually and check off items.

### Option 2: Automated Script

Create `dev/run_audit.py`:

```python
#!/usr/bin/env python3
"""
Comprehensive codebase audit script.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Run command and report result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*60)

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ FAILED: {description}")
        print(f"Error: {result.stderr}")
        return False
    else:
        print(f"✅ PASSED: {description}")
        print(result.stdout)
        return True

def main():
    """Run comprehensive audit."""
    results = {}

    # Task 1: File Structure
    results['file_structure'] = run_command(
        "ls -la agent/orchestrator.py agent/llm.py agent/cost_tracker.py",
        "Check core files exist"
    )

    # Task 2: Python Syntax
    results['python_syntax'] = run_command(
        "python -m py_compile agent/orchestrator.py",
        "Compile orchestrator.py"
    )

    # Task 3: Imports
    results['imports'] = run_command(
        "python -c 'from agent.orchestrator import run_orchestrator'",
        "Test orchestrator imports"
    )

    # Task 5: Tests
    results['tests'] = run_command(
        "pytest agent/tests_sanity/test_sanity.py -v",
        "Run sanity tests"
    )

    # Task 7: Merge conflicts
    results['conflicts'] = run_command(
        "! grep -r '<<<<<<< ' agent/",
        "Check for merge conflict markers"
    )

    # Summary
    print("\n" + "="*60)
    print("AUDIT SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for task, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{task}: {status}")

    print(f"\nTotal: {passed}/{total} passed")

    if passed == total:
        print("\n🎉 ALL CHECKS PASSED - READY FOR PHASE 8.1")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED - REVIEW ISSUES ABOVE")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

Then run:
```bash
python dev/run_audit.py
```

### Option 3: Use AI Agent

Give this entire document to an AI agent with repository access:

```
Please perform a comprehensive audit of the leftonspace/two_agent_web_starter_complete
repository following the AUDIT_PROMPT.md file. Execute all 12 tasks and generate
the comprehensive audit report. Pay special attention to:

1. Import errors
2. Merge conflict artifacts
3. Test failures
4. Integration issues

Provide the full audit report with specific file:line references for any issues found.
```

---

## Success Criteria for "Ready for Phase 8.1"

Before proceeding to Phase 8.1, the following MUST be true:

- ✅ All Python files compile without syntax errors
- ✅ All imports resolve correctly
- ✅ Core components (Orchestrator, LLM, Cost Tracker, Knowledge Graph) functional
- ✅ At least 80% of tests passing
- ✅ No merge conflict markers in code
- ✅ Git repository clean (no corrupted commits)
- ✅ Documentation matches code state
- ✅ Critical execution paths work

If ANY of these fail, STOP and fix issues before implementing Phase 8.1.

---

**End of Audit Prompt**
