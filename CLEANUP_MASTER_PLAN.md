# JARVIS Codebase Cleanup Master Plan

**Created:** 2024-11-26
**Status:** Draft - Awaiting Approval
**Total Phases:** 10
**Estimated Files to Review:** 200+

---

## Executive Summary

This document outlines a systematic cleanup of the JARVIS codebase to:
1. Remove obsolete/duplicate dashboards and files
2. Consolidate scattered code
3. Verify all code for errors and inconsistencies
4. Establish a clean, maintainable architecture

**Priority Order:** Critical → High → Medium → Low

---

## Phase 1: Dashboard Cleanup (CRITICAL)

### 1.1 Remove Orchestrator Dashboard (`/dashboard`)

**Goal:** Remove the orchestrator dashboard route completely.

**Files to Modify/Delete:**

| File | Action | Notes |
|------|--------|-------|
| `agent/webapp/app.py` | MODIFY | Remove `/dashboard` route definition |
| `agent/webapp/templates/dashboard.html` | DELETE | 78KB legacy template |
| `agent/webapp/static/css/design-system.css` | REVIEW | Check if dashboard-specific styles can be removed |

**Verification Steps:**
- [ ] Confirm `/dashboard` returns 404 after removal
- [ ] Confirm React `/ui` still works
- [ ] Confirm legacy `/jarvis-dashboard` still works (if keeping)
- [ ] No console errors on remaining dashboards

---

### 1.2 Evaluate Legacy Dashboard (`/jarvis-dashboard`)

**Decision Required:** Keep or Remove?

**If KEEPING:**
| File | Action |
|------|--------|
| `agent/webapp/templates/jarvis.html` | KEEP (72KB) |
| Related CSS in `design-system.css` | KEEP |

**If REMOVING:**
| File | Action |
|------|--------|
| `agent/webapp/templates/jarvis.html` | DELETE |
| `agent/webapp/app.py` | MODIFY - Remove route |

---

### 1.3 Update Startup Banner

**File:** `agent/webapp/app.py`

**Current Output:**
```
Dashboard (React):   http://127.0.0.1:8000/ui
Dashboard (Legacy):  http://127.0.0.1:8000/jarvis-dashboard
Chat Interface:      http://127.0.0.1:8000/jarvis
Orchestrator:        http://127.0.0.1:8000/dashboard  ← REMOVE THIS LINE
```

**After Cleanup:**
```
Dashboard:           http://127.0.0.1:8000/ui
Chat Interface:      http://127.0.0.1:8000/jarvis
```

---

## Phase 2: Template Files Cleanup (HIGH)

### 2.1 Audit All HTML Templates

**Location:** `agent/webapp/templates/`

| File | Size | Status | Action |
|------|------|--------|--------|
| `dashboard.html` | 78KB | OBSOLETE | DELETE (Phase 1) |
| `jarvis.html` | 72KB | REVIEW | Keep if legacy dashboard stays |
| `base.html` | 24KB | ACTIVE | VERIFY - base template for others |
| `approvals.html` | 21KB | REVIEW | Check if used |
| `integrations.html` | 21KB | REVIEW | Check if used |
| `project_detail.html` | 16KB | REVIEW | Check if used |
| `analytics.html` | 14KB | REVIEW | Check if used |
| `job_detail.html` | 13KB | REVIEW | Check if used |
| `chat.html` | 13KB | REVIEW | Check if used |
| `tuning.html` | 10KB | REVIEW | Check if used |
| `jobs.html` | 8KB | REVIEW | Check if used |
| `run_detail.html` | 7KB | REVIEW | Check if used |
| `index.html` | 6KB | REVIEW | Check if used |
| `projects.html` | 2KB | REVIEW | Check if used |

**Verification Steps:**
- [ ] Search `app.py` for each template reference
- [ ] Test each route that uses templates
- [ ] Document which templates are actively used
- [ ] Mark unused templates for deletion

---

### 2.2 Template Route Mapping

**Task:** Create mapping of routes → templates → usage

```
Route               → Template              → Used By
/dashboard          → dashboard.html        → TO BE REMOVED
/jarvis-dashboard   → jarvis.html          → TBD
/jarvis             → chat.html?           → VERIFY
/analytics          → analytics.html       → VERIFY
/tuning             → tuning.html          → VERIFY
/approvals          → approvals.html       → VERIFY
/integrations       → integrations.html    → VERIFY
/jobs               → jobs.html            → VERIFY
/projects           → projects.html        → VERIFY
```

---

## Phase 3: Static Files Cleanup (MEDIUM)

### 3.1 CSS Audit

**File:** `agent/webapp/static/css/design-system.css` (117KB)

**Tasks:**
- [ ] Identify CSS classes used only by deleted templates
- [ ] Remove unused CSS rules
- [ ] Document remaining CSS dependencies

### 3.2 Static Assets Inventory

**Location:** `agent/webapp/static/`

- [ ] List all files in static folder
- [ ] Cross-reference with templates
- [ ] Remove orphaned assets (images, JS, etc.)

---

## Phase 4: API Routes Cleanup (HIGH)

### 4.1 Audit API Route Files

**Location:** `api/routes/`

| File | Purpose | Action |
|------|---------|--------|
| `dashboard.py` | Dashboard data API | VERIFY endpoints used |
| `tasks.py` | Task management | VERIFY |
| `benchmark.py` | Benchmark execution | VERIFY |
| `evaluation.py` | Evaluation metrics | VERIFY |

**Location:** `agent/webapp/`

| File | Size | Action |
|------|------|--------|
| `app.py` | 83KB | AUDIT - Large monolith |
| `admin_api.py` | 26KB | VERIFY |
| `finance_api.py` | 21KB | VERIFY |
| `api_keys.py` | 13KB | VERIFY |
| `code_api.py` | 10KB | VERIFY |
| `auth_routes.py` | 9KB | VERIFY |
| `auth.py` | 12KB | VERIFY |
| `chat_api.py` | 7KB | VERIFY |

### 4.2 Remove Unused Endpoints

**Task:** For each API file:
- [ ] List all endpoints defined
- [ ] Check if endpoint is called by React UI
- [ ] Check if endpoint is called by legacy templates
- [ ] Mark unused endpoints for removal

---

## Phase 5: Orchestrator Consolidation (HIGH)

### 5.1 Current Orchestrator Files

| File | Lines | Purpose | Action |
|------|-------|---------|--------|
| `orchestrator.py` (root) | 8 | STUB | DELETE |
| `agent/orchestrator.py` | 2,155 | MAIN | KEEP |
| `agent/orchestrator_2loop.py` | 446 | Alternative | REVIEW |
| `agent/orchestrator_context.py` | 682 | Context mgmt | REVIEW |
| `agent/orchestrator_integration.py` | 402 | Integration | REVIEW |
| `agent/orchestrator_selector.py` | 306 | Selection | REVIEW |
| `agent/council/orchestrator.py` | ? | Council pattern | REVIEW |

**Reference:** See `ORCHESTRATOR_CONSOLIDATION_PLAN.md` for detailed plan.

### 5.2 Consolidation Tasks

- [ ] Verify which orchestrator files are actively imported
- [ ] Identify dead code in each file
- [ ] Merge common functionality
- [ ] Update all imports after consolidation
- [ ] Run full test suite

---

## Phase 6: Configuration Cleanup (MEDIUM)

### 6.1 Configuration Locations

| Location | Contents | Action |
|----------|----------|--------|
| `/config/domains/` | Domain configs | AUDIT |
| `/config/models/` | Model configs | AUDIT |
| `/config/routing/` | Routing rules | AUDIT |
| `/config/security/` | Security settings | AUDIT |
| `config.yaml` (root) | Main config | VERIFY |
| `.env` files | Environment vars | VERIFY |

### 6.2 Configuration Tasks

- [ ] List all config files
- [ ] Check for duplicate settings
- [ ] Remove obsolete configurations
- [ ] Centralize scattered configs

---

## Phase 7: Documentation Cleanup (LOW)

### 7.1 Root-Level Documentation (30 files)

| File | Action |
|------|--------|
| `CLEANUP_MASTER_PLAN.md` | NEW - This file |
| `DASHBOARD_FIX_PLAN.md` | ARCHIVE after cleanup |
| `ORCHESTRATOR_CONSOLIDATION_PLAN.md` | ARCHIVE after cleanup |
| `README.md` | UPDATE |
| Other MD files | AUDIT for relevance |

### 7.2 Documentation Tasks

- [ ] Review each MD file for accuracy
- [ ] Archive completed plans
- [ ] Update README with current architecture
- [ ] Remove obsolete documentation

---

## Phase 8: React UI Code Verification (HIGH)

### 8.1 Component Audit

**Location:** `ui/src/components/`

| Directory | Files | Action |
|-----------|-------|--------|
| `dashboard/` | Multiple | VERIFY all components |
| `charts/` | Multiple | VERIFY |
| `common/` | Multiple | VERIFY |
| `layout/` | Multiple | VERIFY |
| `modals/` | Multiple | VERIFY |

### 8.2 Page Audit

**Location:** `ui/src/pages/`

| File | Action |
|------|--------|
| `Dashboard.tsx` | VERIFY - Main dashboard |
| `CostLogPage.tsx` | VERIFY |
| `DomainDetailPage.tsx` | VERIFY |
| `GraveyardPage.tsx` | VERIFY |
| `SettingsPage.tsx` | VERIFY |

### 8.3 Code Quality Checks

- [ ] Run `npm run lint` - fix all errors
- [ ] Run `npm run build` - verify no build errors
- [ ] Check for console errors in browser
- [ ] Verify all API calls have error handling
- [ ] Check for any remaining `toFixed` issues
- [ ] Verify TypeScript types are correct

---

## Phase 9: Python Code Verification (HIGH)

### 9.1 Syntax & Import Verification

**For each Python file:**
- [ ] Run `python -m py_compile <file>`
- [ ] Check for circular imports
- [ ] Verify all imports resolve

### 9.2 Code Quality Checks

- [ ] Run `ruff check .` or `flake8 .`
- [ ] Check for unused imports
- [ ] Check for undefined variables
- [ ] Verify exception handling

### 9.3 Test Suite

- [ ] Run `pytest` - all tests pass
- [ ] Check test coverage
- [ ] Remove tests for deleted code

---

## Phase 10: Final Verification & Cleanup (CRITICAL)

### 10.1 Full System Test

- [ ] Start server: `python -m agent.webapp.app`
- [ ] Test React dashboard: `http://localhost:8000/ui`
- [ ] Test all API endpoints
- [ ] Verify no console errors
- [ ] Verify no server errors

### 10.2 Git Cleanup

- [ ] Review all changes with `git diff`
- [ ] Create meaningful commits per phase
- [ ] Update `.gitignore` if needed
- [ ] Remove any accidentally committed files

### 10.3 Documentation Update

- [ ] Update README.md with final architecture
- [ ] Document removed features
- [ ] Archive old planning documents

---

## Execution Checklist

### Before Starting Each Phase:
1. [ ] Create git branch: `git checkout -b cleanup/phase-X`
2. [ ] Read phase requirements completely
3. [ ] Identify all affected files

### After Each Phase:
1. [ ] Run full test suite
2. [ ] Test affected functionality manually
3. [ ] Commit with descriptive message
4. [ ] Document any issues found

### After All Phases:
1. [ ] Merge all cleanup branches
2. [ ] Full system test
3. [ ] Update this document with completion status
4. [ ] Archive planning documents

---

## Files Summary

### Confirmed for DELETION:
1. `agent/webapp/templates/dashboard.html` (78KB)
2. `orchestrator.py` (root - 8 line stub)

### Pending Review:
- 13 other HTML templates
- 6 orchestrator variant files
- Multiple config files
- 30 documentation files

### Must KEEP:
- `ui/` - React dashboard (entire folder)
- `agent/webapp/app.py` - Main application
- `agent/orchestrator.py` - Main orchestrator
- `api/` - API routes

---

## Approval

**Phase 1 Ready for Execution:** YES / NO

**Approved By:** ________________
**Date:** ________________

---

## Progress Tracking

| Phase | Status | Date Started | Date Completed |
|-------|--------|--------------|----------------|
| 1 | NOT STARTED | | |
| 2 | NOT STARTED | | |
| 3 | NOT STARTED | | |
| 4 | NOT STARTED | | |
| 5 | NOT STARTED | | |
| 6 | NOT STARTED | | |
| 7 | NOT STARTED | | |
| 8 | NOT STARTED | | |
| 9 | NOT STARTED | | |
| 10 | NOT STARTED | | |

