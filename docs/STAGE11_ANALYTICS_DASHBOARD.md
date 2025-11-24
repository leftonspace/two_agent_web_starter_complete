# STAGE 11: Analytics & Insights Dashboard

**Status**: ✅ Implemented

**Purpose**: Provide comprehensive analytics, metrics, and insights across all orchestrator runs and jobs, enabling data-driven optimization and cost tracking.

---

## Overview

Stage 11 adds a complete analytics layer that aggregates data from all runs and jobs to provide:

- **Overall KPIs**: Total runs, tokens, costs, and performance metrics
- **Per-Project Analytics**: Breakdown by project with QA pass rates
- **Per-Model Analytics**: Token usage and cost by AI model
- **Time-Series Trends**: Daily aggregates for cost and run volume
- **QA Metrics**: Pass rates and quality distributions
- **Budget Tracking**: Monthly budget monitoring with progress visualization
- **Data Export**: Download analytics as JSON or CSV for external analysis

The analytics system operates on existing persisted data (run_logs, jobs_state.json) and requires no external database.

---

## Quick Start

### 1. Enable Analytics

Analytics is enabled by default. Configure in `agent/project_config.json`:

```json
{
  "analytics": {
    "enabled": true,
    "monthly_budget": 50.0,
    "timeseries_days": 30
  }
}
```

### 2. Access the Dashboard

Start the web server:

```bash
python -m agent.webapp.app
```

Navigate to:
```
http://127.0.0.1:8000/analytics
```

### 3. View Metrics

The dashboard displays:
- **KPI Cards**: Key metrics at a glance
- **Budget Progress**: Monthly spend tracking
- **Time-Series Charts**: Cost and run trends over time
- **QA Distribution**: Quality check status breakdown
- **Project Table**: Per-project analytics
- **Model Table**: Per-model cost breakdown

### 4. Export Data

Click the export buttons to download:
- **JSON**: Complete analytics data structure
- **CSV**: Tabular data for spreadsheet analysis

---

## Architecture

### Core Components

1. **`agent/analytics.py`** - Analytics engine with aggregation logic
2. **`agent/webapp/app.py`** - API endpoints for analytics
3. **`agent/webapp/templates/analytics.html`** - Dashboard UI
4. **`agent/project_config.json`** - Configuration

### Data Models

#### `AnalyticsSummary`
Complete analytics overview:
```python
@dataclass
class AnalyticsSummary:
    total_runs: int
    total_jobs: int
    total_tokens: int
    total_cost: float
    avg_cost_per_run: float
    avg_duration_seconds: float
    jobs_completed: int
    jobs_failed: int
    jobs_cancelled: int
    jobs_running: int
    jobs_queued: int
    runs_2loop: int
    runs_3loop: int
    qa_summary: QASummary
    monthly_budget: Optional[float]
    current_month_cost: float
    budget_remaining: Optional[float]
    generated_at: str
```

#### `ProjectSummary`
Analytics for a single project:
```python
@dataclass
class ProjectSummary:
    project_name: str
    runs_count: int
    last_run_time: Optional[str]
    total_tokens: int
    total_cost: float
    avg_duration_seconds: float
    qa_passed: int
    qa_warning: int
    qa_failed: int
    qa_not_run: int
```

#### `ModelSummary`
Analytics for a single AI model:
```python
@dataclass
class ModelSummary:
    model_name: str
    total_tokens: int
    total_cost: float
    usage_count: int
```

#### `TimeSeriesPoint`
Daily aggregate data point:
```python
@dataclass
class TimeSeriesPoint:
    date: str  # YYYY-MM-DD
    runs: int
    tokens: int
    cost: float
    qa_passed: int
    qa_warning: int
    qa_failed: int
```

#### `QASummary`
QA metrics across all runs:
```python
@dataclass
class QASummary:
    total_qa_runs: int
    qa_passed: int
    qa_warning: int
    qa_failed: int
    qa_error: int
    qa_not_run: int
    pass_rate: float
```

---

## Metrics Tracked

### Overall Metrics

- **Total Runs**: Count of all orchestrator runs
- **Total Jobs**: Count of all background jobs
- **Total Tokens**: Sum of all tokens used across all models
- **Total Cost**: Sum of all API costs in USD
- **Average Cost Per Run**: Mean cost across all runs
- **Average Duration**: Mean execution time in seconds
- **Mode Distribution**: Count of 2-loop vs 3-loop runs

### Job Metrics

- **Jobs Completed**: Successfully finished jobs
- **Jobs Failed**: Jobs that encountered errors
- **Jobs Cancelled**: User-cancelled jobs
- **Jobs Running**: Currently executing jobs
- **Jobs Queued**: Jobs waiting to start

### QA Metrics

- **Total QA Runs**: Number of runs with QA executed
- **QA Passed**: Runs passing all quality checks
- **QA Warning**: Runs with non-critical issues
- **QA Failed**: Runs with critical quality issues
- **QA Error**: Runs where QA execution failed
- **QA Not Run**: Runs without QA checks
- **Pass Rate**: Percentage of passed / (passed + warning + failed)

### Budget Metrics

- **Monthly Budget**: Configured spending limit
- **Current Month Cost**: Total cost for current calendar month
- **Budget Remaining**: Budget - Current Month Cost
- **Budget Progress**: Visual percentage indicator

### Time-Series Metrics

Daily aggregates over configurable window (default 30 days):
- **Runs per day**: Count of runs each day
- **Cost per day**: Total cost each day
- **Tokens per day**: Total tokens each day
- **QA statuses per day**: Distribution of QA results

### Per-Project Metrics

For each project:
- **Runs Count**: Number of runs for this project
- **Last Run Time**: Timestamp of most recent run
- **Total Tokens**: Sum of tokens for this project
- **Total Cost**: Sum of costs for this project
- **Average Duration**: Mean run time for this project
- **QA Pass Rate**: Percentage of runs passing QA

### Per-Model Metrics

For each AI model:
- **Total Tokens**: Sum of tokens consumed by this model
- **Total Cost**: Sum of costs for this model
- **Usage Count**: Number of runs using this model
- **Cost Share**: Percentage of total cost

---

## Web Dashboard

### KPI Cards

Six key metric cards at the top:

1. **Total Runs** - Shows 2-loop/3-loop breakdown
2. **Total Tokens** - Formatted with thousands separators
3. **Total Cost** - USD with average per run
4. **Average Duration** - Seconds with decimal precision
5. **QA Pass Rate** - Percentage with passed/total counts
6. **Jobs** - Total with completed/failed breakdown

### Budget Progress Bar

If `monthly_budget` is configured:
- Shows current month cost vs budget
- Color-coded:
  - Green: 0-69% of budget
  - Yellow: 70-89% of budget
  - Red: 90-100%+ of budget
- Displays remaining budget amount

### Time-Series Charts

Two canvas-based line charts:

1. **Cost Over Time**
   - Daily cost aggregates
   - Purple gradient line
   - X-axis: Dates (MM-DD format)
   - Y-axis: Cost in USD

2. **Runs Over Time**
   - Daily run counts
   - Green gradient line
   - X-axis: Dates (MM-DD format)
   - Y-axis: Number of runs

Charts use lightweight vanilla JavaScript with HTML5 Canvas (no external libraries).

### QA Distribution

Four colored stat boxes:
- **Passed** (green): Count of passed runs
- **Warning** (yellow): Count of runs with warnings
- **Failed** (red): Count of failed runs
- **Not Run** (gray): Count of runs without QA

### Per-Project Table

Sortable table with columns:
- **Project**: Project name
- **Runs**: Total run count
- **Last Run**: Timestamp (truncated to 19 chars)
- **Total Tokens**: Formatted number
- **Total Cost**: USD to 2 decimals
- **Avg Duration**: Seconds to 1 decimal
- **QA Pass Rate**: Percentage with color coding
  - Green: ≥80%
  - Yellow: 50-79%
  - Red: <50%

### Per-Model Table

Table with columns:
- **Model**: AI model name
- **Total Tokens**: Formatted number
- **Total Cost**: USD to 4 decimals
- **Usage Count**: Number of runs
- **Cost Share**: Percentage of total cost

### Export Buttons

Two download buttons:
- **📥 Download JSON**: Complete analytics data structure
- **📄 Download CSV**: Tabular format for Excel/Sheets

---

## API Endpoints

### GET `/analytics`

Analytics dashboard page (HTML).

**Response**: Rendered HTML template with analytics data

**Query Parameters**: None

---

### GET `/api/analytics/summary`

Overall analytics summary.

**Response**:
```json
{
  "total_runs": 42,
  "total_jobs": 38,
  "total_tokens": 523000,
  "total_cost": 15.43,
  "avg_cost_per_run": 0.367,
  "avg_duration_seconds": 245.6,
  "jobs_completed": 35,
  "jobs_failed": 2,
  "jobs_cancelled": 1,
  "jobs_running": 0,
  "jobs_queued": 0,
  "runs_2loop": 18,
  "runs_3loop": 24,
  "qa_summary": {
    "total_qa_runs": 40,
    "qa_passed": 32,
    "qa_warning": 6,
    "qa_failed": 2,
    "qa_error": 0,
    "qa_not_run": 2,
    "pass_rate": 0.8
  },
  "monthly_budget": 50.0,
  "current_month_cost": 12.34,
  "budget_remaining": 37.66,
  "generated_at": "2025-11-18T10:30:00.000Z"
}
```

---

### GET `/api/analytics/projects`

Per-project analytics breakdown.

**Response**:
```json
[
  {
    "project_name": "contafuel_marketing",
    "runs_count": 15,
    "last_run_time": "2025-11-18T09:30:00.000Z",
    "total_tokens": 245000,
    "total_cost": 7.21,
    "avg_duration_seconds": 223.5,
    "qa_passed": 12,
    "qa_warning": 2,
    "qa_failed": 1,
    "qa_not_run": 0
  },
  ...
]
```

---

### GET `/api/analytics/models`

Per-model analytics breakdown.

**Response**:
```json
[
  {
    "model_name": "gpt-4o",
    "total_tokens": 320000,
    "total_cost": 11.2,
    "usage_count": 42
  },
  {
    "model_name": "gpt-4o-mini",
    "total_tokens": 180000,
    "total_cost": 3.6,
    "usage_count": 42
  },
  ...
]
```

---

### GET `/api/analytics/timeseries`

Time-series daily aggregates.

**Query Parameters**:
- None (uses `timeseries_days` from config)

**Response**:
```json
{
  "daily": [
    {
      "date": "2025-10-19",
      "runs": 0,
      "tokens": 0,
      "cost": 0.0,
      "qa_passed": 0,
      "qa_warning": 0,
      "qa_failed": 0
    },
    {
      "date": "2025-10-20",
      "runs": 3,
      "tokens": 42000,
      "cost": 1.23,
      "qa_passed": 2,
      "qa_warning": 1,
      "qa_failed": 0
    },
    ...
  ]
}
```

---

### GET `/api/analytics/qa`

QA-specific analytics.

**Response**:
```json
{
  "total_qa_runs": 40,
  "qa_passed": 32,
  "qa_warning": 6,
  "qa_failed": 2,
  "qa_error": 0,
  "qa_not_run": 2,
  "pass_rate": 0.8
}
```

---

### GET `/api/analytics/export/json`

Export complete analytics as JSON file.

**Response**: File download with `Content-Disposition: attachment`

**Content**:
```json
{
  "summary": { ... },
  "projects": [ ... ],
  "models": [ ... ],
  "timeseries": [ ... ]
}
```

---

### GET `/api/analytics/export/csv`

Export analytics as CSV file.

**Response**: File download with `Content-Disposition: attachment`

**Content**:
```csv
OVERALL SUMMARY
Metric,Value
Total Runs,42
Total Jobs,38
Total Tokens,523000
...

PER-PROJECT SUMMARY
Project,Runs,Last Run,Total Tokens,Total Cost (USD),Avg Duration (s),...
contafuel_marketing,15,2025-11-18T09:30:00.000Z,245000,7.21,223.5,...
...

PER-MODEL SUMMARY
Model,Total Tokens,Total Cost (USD),Usage Count
gpt-4o,320000,11.2,42
...
```

---

## Configuration Reference

### Complete Analytics Configuration

In `agent/project_config.json`:

```json
{
  "analytics": {
    // Enable/disable analytics dashboard
    "enabled": true,

    // Optional monthly budget in USD (null to disable budget tracking)
    "monthly_budget": 50.0,

    // Number of days to include in time-series charts
    "timeseries_days": 30
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable/disable analytics dashboard |
| `monthly_budget` | float or null | `null` | Monthly spending limit in USD (null = no budget) |
| `timeseries_days` | integer | `30` | Number of days for time-series charts |

---

## Programmatic Usage

### Get Complete Analytics

```python
from analytics import get_analytics

# Get all analytics data
data = get_analytics()

print(f"Total runs: {data['summary']['total_runs']}")
print(f"Total cost: ${data['summary']['total_cost']:.2f}")

# Access per-project data
for project in data['projects']:
    print(f"{project['project_name']}: {project['runs_count']} runs")
```

### Load Runs and Jobs

```python
from analytics import load_all_runs, load_all_jobs

runs = load_all_runs()
jobs = load_all_jobs()

print(f"Loaded {len(runs)} runs and {len(jobs)} jobs")
```

### Compute Specific Summaries

```python
from analytics import (
    compute_overall_summary,
    compute_project_summaries,
    compute_model_summaries,
    compute_timeseries,
)

runs = load_all_runs()
jobs = load_all_jobs()

# Overall summary
summary = compute_overall_summary(runs, jobs)
print(f"Average cost per run: ${summary.avg_cost_per_run:.4f}")

# Per-project
projects = compute_project_summaries(runs)
for proj in projects:
    print(f"{proj.project_name}: {proj.runs_count} runs")

# Per-model
models = compute_model_summaries(runs)
for model in models:
    print(f"{model.model_name}: {model.total_tokens:,} tokens")

# Time-series (last 7 days)
timeseries = compute_timeseries(runs, days=7)
for point in timeseries:
    print(f"{point.date}: {point.runs} runs, ${point.cost:.2f}")
```

### Export Analytics

```python
from analytics import export_analytics_json, export_analytics_csv

# Export to JSON
json_str = export_analytics_json(summary, projects, models, timeseries)
with open("analytics.json", "w") as f:
    f.write(json_str)

# Export to CSV
csv_str = export_analytics_csv(summary, projects, models)
with open("analytics.csv", "w") as f:
    f.write(csv_str)
```

---

## Testing

### Run Analytics Tests

```bash
cd agent/
pytest tests_stage11/ -v
```

### Test Coverage

- ✓ Data loading (runs and jobs)
- ✓ Overall summary computation
- ✓ Per-project aggregation
- ✓ Per-model aggregation
- ✓ Time-series generation
- ✓ QA analytics
- ✓ Current month cost tracking
- ✓ JSON export
- ✓ CSV export
- ✓ Missing data handling
- ✓ Empty data handling

---

## Troubleshooting

### Dashboard Shows "Disabled"

**Cause**: Analytics disabled in configuration

**Solution**: Set `analytics.enabled = true` in `project_config.json`

---

### No Data Displayed

**Cause**: No runs or jobs in system

**Solution**:
1. Run at least one project through the orchestrator
2. Check that `run_logs/` directory exists and contains run data
3. Verify `agent/jobs_state.json` exists

---

### Budget Not Showing

**Cause**: `monthly_budget` not configured

**Solution**: Add `monthly_budget` to analytics config:
```json
{
  "analytics": {
    "monthly_budget": 50.0
  }
}
```

---

### Charts Not Rendering

**Cause**: JavaScript error or missing data

**Solution**:
1. Check browser console for errors
2. Verify time-series data has runs
3. Ensure runs have valid timestamps

---

### Export Download Fails

**Cause**: File write permissions or data serialization error

**Solution**:
1. Check browser downloads folder permissions
2. Verify analytics data is JSON-serializable
3. Check server logs for errors

---

## Performance Considerations

### Data Loading

- Analytics loads all runs from `run_logs/*/run_summary.json`
- With 1000+ runs, initial load may take 1-2 seconds
- Consider archiving old runs if performance degrades

### Caching

- Current implementation recomputes on every request
- For large datasets, consider adding caching layer
- Cache invalidation can trigger on new run completion

### Optimization Tips

1. **Archive old runs**: Move runs older than 6 months to separate directory
2. **Limit history**: Adjust `timeseries_days` to reduce data processed
3. **Add indexes**: If migrating to database, add indexes on `started_at`, `project_dir`

---

## Future Enhancements

Potential improvements for future stages:

1. **Advanced Filtering**
   - Filter by date range
   - Filter by project, model, or QA status
   - Search and sort capabilities

2. **More Charts**
   - Token usage trends
   - Cost breakdown pie chart
   - QA pass rate over time
   - Model usage distribution

3. **Comparison Views**
   - Week-over-week comparisons
   - Month-over-month trends
   - Project vs project benchmarking

4. **Alerts & Notifications**
   - Budget threshold alerts
   - QA failure notifications
   - Cost spike detection

5. **Custom Dashboards**
   - User-configurable widgets
   - Save custom views
   - Team-level analytics

6. **Advanced Exports**
   - PDF reports
   - Excel workbooks with multiple sheets
   - Automated email reports

7. **Real-Time Updates**
   - WebSocket live updates
   - Auto-refresh on job completion
   - Live cost tracking

---

## Summary

Stage 11 provides a complete analytics and insights dashboard that:

- ✅ Aggregates data from all runs and jobs
- ✅ Provides comprehensive metrics and KPIs
- ✅ Tracks costs and budgets
- ✅ Monitors QA quality over time
- ✅ Enables data-driven optimization
- ✅ Supports data export for external analysis
- ✅ Requires no external database
- ✅ Integrates seamlessly with existing web UI

The analytics system helps teams understand their AI development costs, optimize model usage, and maintain quality standards across projects.

---

For questions or issues, see the main README or create an issue on GitHub.
