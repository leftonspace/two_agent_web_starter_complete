# PHASE 5.6: Monitoring & Alerting

## Overview

Comprehensive monitoring and alerting system for tracking mission metrics, tool usage, error rates, and system health with multi-channel notifications.

## Features

### Metrics Collection
- **Mission Metrics:** Success/failure rate, cost tracking, execution time, iterations
- **Tool Usage:** Execution counts, success rates, average duration, cost tracking
- **Error Tracking:** Error types, frequencies, associated missions
- **Health Checks:** CPU, memory, disk usage, queue length, system status

### Alert Rules
- **Cost Alerts:** Daily/hourly budget exceeded
- **Performance Alerts:** Success rate drops below threshold
- **Error Alerts:** Error rate increases significantly
- **Health Alerts:** System degradation or unhealthy status
- **Queue Alerts:** Queue length exceeds capacity

### Notification Channels
- **Email:** SMTP-based email notifications
- **Slack:** Webhook-based Slack messages
- **PagerDuty:** Event API integration for critical alerts
- **Extensible:** Easy to add custom channels

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Metrics Collector                     │
├─────────────────────────────────────────────────────────┤
│  - Mission metrics (success/fail/cost/duration)         │
│  - Tool usage tracking                                  │
│  - Error rate monitoring                                │
│  - Health check recording                               │
│  - Time series data storage (SQLite)                    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Alert Manager                        │
├─────────────────────────────────────────────────────────┤
│  - Rule evaluation engine                               │
│  - Condition checking (cost, success rate, errors)      │
│  - Cooldown management (prevent alert spam)             │
│  - Alert history tracking                               │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Email   │    │  Slack   │    │PagerDuty │
    │ Notifier │    │ Notifier │    │ Notifier │
    └──────────┘    └──────────┘    └──────────┘
```

## Usage

### Metrics Collection

#### Recording Mission Metrics

```python
from agent.monitoring import record_mission

# Record successful mission
record_mission(
    mission_id="mission_123",
    status="success",
    cost_usd=1.25,
    duration_seconds=120,
    iterations=3,
    domain="coding",
)

# Record failed mission
record_mission(
    mission_id="mission_124",
    status="failed",
    cost_usd=2.50,
    duration_seconds=180,
    iterations=5,
    domain="finance",
    error_type="ValueError",
    error_message="Invalid input format",
)
```

#### Recording Tool Execution

```python
from agent.monitoring import record_tool_execution

# Record successful tool execution
record_tool_execution(
    tool_name="git_status",
    success=True,
    duration_seconds=0.5,
    cost_usd=0.0,
)

# Record failed tool execution
record_tool_execution(
    tool_name="pytest",
    success=False,
    duration_seconds=5.0,
    cost_usd=0.1,
)
```

#### Recording Errors

```python
from agent.monitoring import record_error

record_error(
    error_type="APIError",
    error_message="Rate limit exceeded",
    mission_id="mission_125",
)
```

#### Recording Health Checks

```python
from agent.monitoring import record_health_check

status = record_health_check(
    cpu_percent=45.0,
    memory_percent=60.0,
    disk_percent=70.0,
    active_missions=5,
    queue_length=10,
)
# Returns: "healthy", "degraded", or "unhealthy"
```

### Querying Metrics

#### Mission Statistics

```python
from agent.monitoring import get_metrics_collector

metrics = get_metrics_collector()

# Get 24-hour statistics
stats = metrics.get_mission_stats(hours=24)
print(f"Total missions: {stats['total_missions']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Average cost: ${stats['avg_cost_usd']:.2f}")
print(f"Average duration: {stats['avg_duration_seconds']:.1f}s")

# Get statistics by domain
coding_stats = metrics.get_mission_stats(hours=24, domain="coding")
finance_stats = metrics.get_mission_stats(hours=24, domain="finance")
```

#### Mission Trends

```python
# Get hourly trend for last 24 hours
trend = metrics.get_mission_trend(hours=24, bucket_hours=1)

for bucket in trend:
    print(f"{bucket['timestamp']}: {bucket['total']} missions, "
          f"{bucket['success_rate']:.1%} success rate")
```

#### Tool Statistics

```python
# Get top 20 most-used tools
tool_stats = metrics.get_tool_stats(limit=20, order_by="execution_count")

for tool in tool_stats:
    print(f"{tool['tool_name']}: {tool['execution_count']} executions, "
          f"{tool['success_rate']:.1%} success rate")
```

#### Error Statistics

```python
# Get errors from last 24 hours
error_stats = metrics.get_error_stats(hours=24, limit=20)

for error in error_stats:
    print(f"{error['error_type']}: {error['count']} occurrences")
    print(f"  Message: {error['error_message']}")
    print(f"  Last seen: {error['last_seen']}")
```

#### Error Rate

```python
error_rate = metrics.get_error_rate(hours=24)
print(f"Failure rate: {error_rate['failure_rate']:.1%}")
print(f"Total errors: {error_rate['total_errors']}")
print(f"Unique errors: {error_rate['unique_errors']}")
```

#### Health Status

```python
# Get latest health check
health = metrics.get_latest_health()
print(f"Status: {health['status']}")
print(f"CPU: {health['cpu_percent']}%")
print(f"Memory: {health['memory_percent']}%")
print(f"Active missions: {health['active_missions']}")

# Get health trend
health_trend = metrics.get_health_trend(hours=24)
for check in health_trend:
    print(f"{check['timestamp']}: {check['status']} "
          f"(CPU: {check['cpu_percent']}%, Memory: {check['memory_percent']}%)")
```

### Alert Management

#### Adding Alert Rules

```python
from agent.alerting import get_alert_manager

alert_mgr = get_alert_manager()

# Daily cost budget alert
alert_mgr.add_rule(
    name="Daily Cost Budget",
    condition="daily_cost_exceeds",
    threshold=100.0,  # $100/day
    channels=["email", "slack"],
    severity="warning",
    cooldown_minutes=60,  # Don't re-alert for 1 hour
)

# Success rate alert
alert_mgr.add_rule(
    name="Low Success Rate",
    condition="success_rate_below",
    threshold=80.0,  # 80% success rate
    channels=["email"],
    severity="error",
)

# Error rate spike alert
alert_mgr.add_rule(
    name="Error Rate Spike",
    condition="error_rate_increases",
    threshold=2.0,  # 2x increase
    channels=["slack", "pagerduty"],
    severity="critical",
)

# Queue length alert
alert_mgr.add_rule(
    name="Queue Overload",
    condition="queue_length_exceeds",
    threshold=100,
    channels=["email"],
    severity="warning",
)
```

#### Managing Rules

```python
# Get all rules
rules = alert_mgr.get_rules(enabled_only=True)
for rule in rules:
    print(f"{rule.name}: {rule.condition} (threshold: {rule.threshold})")

# Disable a rule
alert_mgr.disable_rule("Daily Cost Budget")

# Enable a rule
alert_mgr.enable_rule("Daily Cost Budget")
```

#### Checking Alerts

```python
# Check all enabled rules
alerts = alert_mgr.check_all_rules()

for alert in alerts:
    print(f"🚨 {alert.rule_name}: {alert.message}")
    print(f"   Current: {alert.current_value:.2f}, Threshold: {alert.threshold:.2f}")
```

#### Alert History

```python
# Get alert history for last 24 hours
history = alert_mgr.get_alert_history(hours=24, limit=100)

for alert in history:
    print(f"{alert['timestamp']}: {alert['rule_name']}")
    print(f"  Severity: {alert['severity']}")
    print(f"  Message: {alert['message']}")
```

### Notification Configuration

#### Email Configuration

Set environment variables:

```bash
export ALERT_SMTP_HOST="smtp.gmail.com"
export ALERT_SMTP_PORT="587"
export ALERT_SMTP_USER="your-email@gmail.com"
export ALERT_SMTP_PASSWORD="your-app-password"
export ALERT_FROM_EMAIL="alerts@yourcompany.com"
export ALERT_TO_EMAILS="admin@yourcompany.com,oncall@yourcompany.com"
```

Or configure programmatically:

```python
from agent.alerting import EmailNotifier

email_notifier = EmailNotifier(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    smtp_user="your-email@gmail.com",
    smtp_password="your-app-password",
    from_email="alerts@yourcompany.com",
    to_emails=["admin@yourcompany.com", "oncall@yourcompany.com"],
)
```

#### Slack Configuration

Set environment variable with your Slack webhook URL:

```bash
export ALERT_SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

Create a Slack webhook:
1. Go to https://api.slack.com/apps
2. Create a new app
3. Add "Incoming Webhooks" feature
4. Create a webhook for your channel
5. Copy the webhook URL

#### PagerDuty Configuration

Set environment variable with your integration key:

```bash
export ALERT_PAGERDUTY_KEY="your-integration-key"
```

Get PagerDuty integration key:
1. Go to your PagerDuty service
2. Go to Integrations → Add Integration
3. Select "Events API V2"
4. Copy the integration key

## Built-in Alert Conditions

### 1. Daily Cost Exceeds

**Condition:** `daily_cost_exceeds`

Triggers when total mission cost in last 24 hours exceeds threshold.

```python
alert_mgr.add_rule(
    name="Daily Budget Alert",
    condition="daily_cost_exceeds",
    threshold=100.0,  # $100/day
    channels=["email", "slack"],
)
```

### 2. Success Rate Below

**Condition:** `success_rate_below`

Triggers when mission success rate drops below threshold percentage.

```python
alert_mgr.add_rule(
    name="Success Rate Alert",
    condition="success_rate_below",
    threshold=80.0,  # 80%
    channels=["email"],
)
```

### 3. Error Rate Increases

**Condition:** `error_rate_increases`

Triggers when error rate increases by threshold multiplier.

```python
alert_mgr.add_rule(
    name="Error Spike Alert",
    condition="error_rate_increases",
    threshold=2.0,  # 2x increase
    channels=["pagerduty"],
)
```

### 4. Queue Length Exceeds

**Condition:** `queue_length_exceeds`

Triggers when mission queue length exceeds threshold.

```python
alert_mgr.add_rule(
    name="Queue Overload Alert",
    condition="queue_length_exceeds",
    threshold=100,
    channels=["email"],
)
```

## Integration with Orchestrator

### Recording Mission Metrics

Add to `orchestrator.py`:

```python
from agent.monitoring import record_mission

# At end of main() function
record_mission(
    mission_id=core_run_id,
    status="success" if final_status == "approved" else "failed",
    cost_usd=final_cost_summary.get("total_usd", 0.0),
    duration_seconds=time.time() - start_time,
    iterations=max_rounds,
    domain=domain.value if domain else None,
    error_type=None,  # Extract from final_status if failed
    error_message=None,
)
```

### Recording Tool Metrics

Add to `exec_tools.py`:

```python
from agent.monitoring import record_tool_execution
import time

def call_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    start_time = time.time()
    result = _actual_tool_execution(tool_name, **kwargs)
    duration = time.time() - start_time

    # Record metrics
    record_tool_execution(
        tool_name=tool_name,
        success=(result.get("status") == "success"),
        duration_seconds=duration,
        cost_usd=result.get("cost_usd", 0.0),
    )

    return result
```

### Recording Errors

Add to error handling:

```python
from agent.monitoring import record_error

try:
    # ... mission execution ...
except Exception as e:
    record_error(
        error_type=type(e).__name__,
        error_message=str(e),
        mission_id=core_run_id,
    )
    raise
```

### Periodic Health Checks

Add health check background task:

```python
import psutil
from agent.monitoring import record_health_check

def run_health_check():
    """Run periodic health check."""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    # Get queue metrics from your queue system
    active_missions = get_active_mission_count()
    queue_length = get_queue_length()

    status = record_health_check(
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=disk,
        active_missions=active_missions,
        queue_length=queue_length,
    )

    return status

# Run every 5 minutes
import schedule
schedule.every(5).minutes.do(run_health_check)
```

### Periodic Alert Checks

Add alert check background task:

```python
from agent.alerting import get_alert_manager

def check_alerts():
    """Check all alert rules."""
    alert_mgr = get_alert_manager()
    alerts = alert_mgr.check_all_rules()

    if alerts:
        print(f"[Alerts] {len(alerts)} alert(s) triggered")
        for alert in alerts:
            print(f"  - {alert.rule_name}: {alert.message}")

    return alerts

# Run every 10 minutes
import schedule
schedule.every(10).minutes.do(check_alerts)
```

## Dashboard Queries

### Mission Dashboard

```python
from agent.monitoring import get_metrics_collector

metrics = get_metrics_collector()

# Overview statistics
stats_24h = metrics.get_mission_stats(hours=24)
stats_7d = metrics.get_mission_stats(hours=24 * 7)

dashboard = {
    "24h": {
        "total_missions": stats_24h["total_missions"],
        "success_rate": f"{stats_24h['success_rate']:.1%}",
        "total_cost": f"${stats_24h['total_cost_usd']:.2f}",
        "avg_duration": f"{stats_24h['avg_duration_seconds']:.1f}s",
    },
    "7d": {
        "total_missions": stats_7d["total_missions"],
        "success_rate": f"{stats_7d['success_rate']:.1%}",
        "total_cost": f"${stats_7d['total_cost_usd']:.2f}",
    },
}
```

### Tool Usage Dashboard

```python
# Top tools by usage
top_tools = metrics.get_tool_stats(limit=10, order_by="execution_count")

# Top tools by cost
expensive_tools = metrics.get_tool_stats(limit=10, order_by="total_cost_usd")

tool_dashboard = {
    "most_used": [
        {
            "name": t["tool_name"],
            "count": t["execution_count"],
            "success_rate": f"{t['success_rate']:.1%}",
        }
        for t in top_tools
    ],
    "most_expensive": [
        {
            "name": t["tool_name"],
            "cost": f"${t['total_cost_usd']:.2f}",
        }
        for t in expensive_tools
    ],
}
```

### Error Dashboard

```python
# Recent errors
recent_errors = metrics.get_error_stats(hours=24, limit=10)
error_rate = metrics.get_error_rate(hours=24)

error_dashboard = {
    "error_rate": f"{error_rate['failure_rate']:.1%}",
    "total_errors": error_rate["total_errors"],
    "unique_errors": error_rate["unique_errors"],
    "top_errors": [
        {
            "type": e["error_type"],
            "message": e["error_message"],
            "count": e["count"],
        }
        for e in recent_errors
    ],
}
```

### Health Dashboard

```python
# Current health
current_health = metrics.get_latest_health()

# Health trend
health_trend = metrics.get_health_trend(hours=24)

health_dashboard = {
    "current": {
        "status": current_health["status"],
        "cpu": f"{current_health['cpu_percent']}%",
        "memory": f"{current_health['memory_percent']}%",
        "disk": f"{current_health['disk_percent']}%",
        "queue": current_health["queue_length"],
    },
    "trend": [
        {
            "time": h["timestamp"],
            "status": h["status"],
            "cpu": h["cpu_percent"],
        }
        for h in health_trend
    ],
}
```

## Database Schema

### Metrics Database

**mission_metrics:**
- Mission execution records (time series)
- Tracks status, cost, duration, iterations, errors

**tool_metrics:**
- Tool usage statistics (aggregated)
- Tracks execution counts, success rates, duration, cost

**error_metrics:**
- Error occurrence tracking (aggregated)
- Tracks error types, frequencies, affected missions

**health_metrics:**
- System health checks (time series)
- Tracks CPU, memory, disk, queue metrics

### Alerting Database

**alert_rules:**
- Alert rule definitions
- Tracks conditions, thresholds, channels, cooldowns

**alert_history:**
- Historical alert records
- Tracks when alerts fired and to which channels

**alert_cooldowns:**
- Active cooldown periods
- Prevents alert spam

## Testing

Run tests:

```bash
python tests/test_monitoring_alerting.py
```

Expected output:

```
============================================================
PHASE 5.6: Monitoring & Alerting Tests
============================================================

[MONITORING] Metrics Collection Tests
------------------------------------------------------------
✓ Initialize MetricsCollector
✓ Record mission metrics
✓ Calculate mission success rate
✓ Track tool execution
✓ Track errors
✓ Calculate error rate
✓ Record health check
✓ Health status degradation

[ALERTING] Alert Management Tests
------------------------------------------------------------
✓ Initialize AlertManager
✓ Add alert rule
✓ Enable/disable rules
✓ Daily cost alert
✓ Success rate alert
✓ Alert cooldown
✓ Alert history recording

[AC] Acceptance Criteria Tests
------------------------------------------------------------
✓ AC: Metrics collected continuously
✓ AC: Alerts trigger correctly
✓ AC: Multiple notification channels
✓ AC: Dashboard queries work

============================================================
Tests run: 19
Passed: 19
Failed: 0
============================================================
```

## Acceptance Criteria

✅ **AC1: Metrics collected continuously**
- Mission metrics tracked for all executions
- Tool usage tracked automatically
- Errors logged with context
- Health checks recorded periodically

✅ **AC2: Alerts trigger correctly**
- Cost budget alerts fire when threshold exceeded
- Success rate alerts trigger on drops below threshold
- Error rate spike detection works
- Cooldown prevents alert spam

✅ **AC3: Notifications sent via email/Slack**
- Email notifications via SMTP
- Slack notifications via webhooks
- PagerDuty integration for critical alerts
- Multiple channels per rule supported

✅ **AC4: Dashboard queries available**
- Mission statistics queries
- Tool usage statistics
- Error rate tracking
- Health status monitoring
- Time series trend queries

## Production Deployment

### 1. Configure Notification Channels

```bash
# Email
export ALERT_SMTP_HOST="smtp.gmail.com"
export ALERT_SMTP_PORT="587"
export ALERT_SMTP_USER="your-email@gmail.com"
export ALERT_SMTP_PASSWORD="your-app-password"
export ALERT_TO_EMAILS="admin@yourcompany.com"

# Slack
export ALERT_SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# PagerDuty
export ALERT_PAGERDUTY_KEY="your-integration-key"
```

### 2. Add Alert Rules

```python
from agent.alerting import get_alert_manager

alert_mgr = get_alert_manager()

# Production alert rules
alert_mgr.add_rule("Daily Cost Budget", "daily_cost_exceeds", 1000.0, ["email", "slack"])
alert_mgr.add_rule("Success Rate Critical", "success_rate_below", 80.0, ["email", "pagerduty"])
alert_mgr.add_rule("Error Spike", "error_rate_increases", 3.0, ["pagerduty"])
alert_mgr.add_rule("Queue Overload", "queue_length_exceeds", 500, ["email"])
```

### 3. Set Up Background Tasks

```python
import schedule
import time
from agent.monitoring import record_health_check
from agent.alerting import get_alert_manager

def run_monitoring_loop():
    """Run monitoring and alerting loop."""
    # Health checks every 5 minutes
    schedule.every(5).minutes.do(record_health_check)

    # Alert checks every 10 minutes
    alert_mgr = get_alert_manager()
    schedule.every(10).minutes.do(alert_mgr.check_all_rules)

    while True:
        schedule.run_pending()
        time.sleep(60)

# Run in background thread
import threading
monitor_thread = threading.Thread(target=run_monitoring_loop, daemon=True)
monitor_thread.start()
```

## Best Practices

### 1. Alert Tuning

- **Start Conservative:** Begin with higher thresholds and adjust down
- **Use Cooldowns:** Prevent alert fatigue with appropriate cooldown periods
- **Severity Levels:** Reserve "critical" for truly urgent issues
- **Test Notifications:** Test each channel before going live

### 2. Metrics Collection

- **Consistent Recording:** Record metrics for all missions, not just failures
- **Rich Context:** Include domain, error types, and metadata
- **Periodic Health Checks:** Run health checks on a regular schedule
- **Clean Old Data:** Archive or delete old metrics periodically

### 3. Dashboard Design

- **Real-Time Views:** Show current status prominently
- **Trend Analysis:** Include historical trends for pattern detection
- **Actionable Metrics:** Focus on metrics that drive decisions
- **Response Time:** Optimize queries for fast dashboard loading

## Troubleshooting

### No Alerts Firing

1. Check that rules are enabled: `alert_mgr.get_rules(enabled_only=True)`
2. Verify metrics are being collected: `metrics.get_mission_stats(hours=24)`
3. Check cooldown status: Alert may be in cooldown period
4. Verify notification channels are configured (environment variables)

### Email Notifications Not Sending

1. Check SMTP configuration: `echo $ALERT_SMTP_HOST`
2. Verify credentials are correct
3. Check firewall/network allows SMTP connections
4. Use app-specific password (not account password) for Gmail
5. Check spam folder for received emails

### Slack Notifications Not Sending

1. Verify webhook URL: `echo $ALERT_SLACK_WEBHOOK`
2. Test webhook with curl:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test alert"}' \
     $ALERT_SLACK_WEBHOOK
   ```
3. Check Slack app permissions
4. Verify webhook hasn't been revoked

### High Database Size

1. Archive old metrics to separate database
2. Delete metrics older than retention period
3. Use VACUUM to reclaim space
4. Consider time-series database for long-term storage

## Future Enhancements

1. **Grafana Integration:** Export metrics to Grafana for advanced visualization
2. **Prometheus Metrics:** Expose metrics in Prometheus format
3. **Custom Alert Conditions:** Allow user-defined alert conditions
4. **Alert Grouping:** Group related alerts to reduce notification volume
5. **Alert Escalation:** Escalate alerts if not acknowledged
6. **Anomaly Detection:** ML-based anomaly detection for metrics
7. **SLA Tracking:** Track and alert on SLA violations

## Related Files

- `agent/monitoring.py` - Metrics collection implementation
- `agent/alerting.py` - Alert management implementation
- `tests/test_monitoring_alerting.py` - Comprehensive test suite
- `data/monitoring.db` - Metrics database
- `data/alerting.db` - Alerting database

## Summary

Phase 5.6 delivers a **production-ready monitoring and alerting system**:

- ✅ Comprehensive metrics collection
- ✅ Flexible alert rules with multiple conditions
- ✅ Multi-channel notifications (email, Slack, PagerDuty)
- ✅ Dashboard-ready queries
- ✅ 19/19 tests passing (100%)
- ✅ Production-ready with configuration examples

The system provides visibility into mission performance, tool usage, error rates, and system health, with proactive alerting to catch issues before they become critical.
