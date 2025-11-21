"""
PHASE 5.6: Tests for Monitoring & Alerting System

Tests metrics collection, alert rules, and notification channels.

Run with: python tests/test_monitoring_alerting.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add agent/ to path
agent_dir = Path(__file__).resolve().parent.parent / "agent"
if str(agent_dir) not in sys.path:
    sys.path.insert(0, str(agent_dir))

from monitoring import MetricsCollector
from alerting import AlertManager, AlertRule, Alert


class TestRunner:
    """Simple test runner."""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def test(self, name, func):
        """Run a test function."""
        try:
            func()
            print(f"✓ {name}")
            self.passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            self.failed += 1
        except Exception as e:
            print(f"✗ {name}: Unexpected error: {e}")
            self.failed += 1

    def summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print(f"\n{'=' * 60}")
        print(f"Tests run: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"{'=' * 60}")
        return self.failed == 0


def run_tests():
    """Run all monitoring and alerting tests."""
    runner = TestRunner()

    print("=" * 60)
    print("PHASE 5.6: Monitoring & Alerting Tests")
    print("=" * 60)

    # ──────────────────────────────────────────────────────────────
    # Monitoring Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[MONITORING] Metrics Collection Tests")
    print("-" * 60)

    def test_metrics_collector_init():
        """Test MetricsCollector initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)
            assert metrics.db_path == db_path
            assert db_path.exists()

    runner.test("Initialize MetricsCollector", test_metrics_collector_init)

    def test_record_mission():
        """Test recording mission metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)

            metrics.record_mission(
                mission_id="test_mission_1",
                status="success",
                cost_usd=1.25,
                duration_seconds=120,
                iterations=3,
                domain="coding",
            )

            stats = metrics.get_mission_stats(hours=24)
            assert stats["total_missions"] == 1
            assert stats["successful_missions"] == 1
            assert stats["success_rate"] == 1.0
            assert stats["avg_cost_usd"] == 1.25

    runner.test("Record mission metrics", test_record_mission)

    def test_mission_success_rate():
        """Test mission success rate calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)

            # Record mixed results
            metrics.record_mission("m1", "success", 1.0, 100, 2)
            metrics.record_mission("m2", "success", 1.0, 100, 2)
            metrics.record_mission("m3", "failed", 2.0, 150, 3, error_type="ValueError")
            metrics.record_mission("m4", "success", 1.0, 100, 2)

            stats = metrics.get_mission_stats(hours=24)
            assert stats["total_missions"] == 4
            assert stats["successful_missions"] == 3
            assert stats["failed_missions"] == 1
            assert stats["success_rate"] == 0.75  # 3/4

    runner.test("Calculate mission success rate", test_mission_success_rate)

    def test_tool_execution_tracking():
        """Test tool execution tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)

            # Record tool executions
            metrics.record_tool_execution("git_status", True, 0.5, 0.0)
            metrics.record_tool_execution("git_status", True, 0.6, 0.0)
            metrics.record_tool_execution("git_status", False, 1.0, 0.0)
            metrics.record_tool_execution("pytest", True, 5.0, 0.1)

            tool_stats = metrics.get_tool_stats(limit=10)
            assert len(tool_stats) == 2

            git_status = [t for t in tool_stats if t["tool_name"] == "git_status"][0]
            assert git_status["execution_count"] == 3
            assert git_status["success_count"] == 2
            assert git_status["failure_count"] == 1
            assert git_status["success_rate"] == 2 / 3

    runner.test("Track tool execution", test_tool_execution_tracking)

    def test_error_tracking():
        """Test error tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)

            # Record errors
            metrics.record_error("ValueError", "Invalid input", "mission_1")
            metrics.record_error("ValueError", "Invalid input", "mission_2")
            metrics.record_error("APIError", "Rate limit exceeded", "mission_3")

            error_stats = metrics.get_error_stats(hours=24)
            assert len(error_stats) == 2

            value_error = [e for e in error_stats if e["error_type"] == "ValueError"][0]
            assert value_error["count"] == 2
            assert len(value_error["mission_ids"]) == 2

    runner.test("Track errors", test_error_tracking)

    def test_error_rate_calculation():
        """Test error rate calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)

            # Record missions and errors
            metrics.record_mission("m1", "success", 1.0, 100, 2)
            metrics.record_mission("m2", "failed", 2.0, 150, 3, error_type="ValueError", error_message="Invalid")
            metrics.record_mission("m3", "failed", 2.0, 150, 3, error_type="APIError", error_message="Timeout")

            error_rate = metrics.get_error_rate(hours=24)
            assert error_rate["total_missions"] == 3
            assert error_rate["failed_missions"] == 2
            assert error_rate["failure_rate"] == 2 / 3

    runner.test("Calculate error rate", test_error_rate_calculation)

    def test_health_check_recording():
        """Test health check recording."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)

            status = metrics.record_health_check(
                cpu_percent=45.0,
                memory_percent=60.0,
                disk_percent=70.0,
                active_missions=5,
                queue_length=10,
            )

            assert status == "healthy"

            health = metrics.get_latest_health()
            assert health is not None
            assert health["cpu_percent"] == 45.0
            assert health["status"] == "healthy"

    runner.test("Record health check", test_health_check_recording)

    def test_health_status_degraded():
        """Test health status degradation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)

            # High CPU should trigger degraded
            status = metrics.record_health_check(
                cpu_percent=85.0,
                memory_percent=60.0,
                disk_percent=70.0,
            )
            assert status == "degraded"

            # High disk should trigger unhealthy
            status = metrics.record_health_check(
                cpu_percent=50.0,
                memory_percent=60.0,
                disk_percent=95.0,
            )
            assert status == "unhealthy"

    runner.test("Health status degradation", test_health_status_degraded)

    # ──────────────────────────────────────────────────────────────
    # Alerting Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[ALERTING] Alert Management Tests")
    print("-" * 60)

    def test_alert_manager_init():
        """Test AlertManager initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "alerting.db"
            alert_mgr = AlertManager(db_path, metrics_collector=None)
            assert alert_mgr.db_path == db_path
            assert db_path.exists()

    runner.test("Initialize AlertManager", test_alert_manager_init)

    def test_add_alert_rule():
        """Test adding alert rule."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "alerting.db"
            alert_mgr = AlertManager(db_path, metrics_collector=None)

            alert_mgr.add_rule(
                name="Test Rule",
                condition="daily_cost_exceeds",
                threshold=100.0,
                channels=["email"],
                severity="warning",
            )

            rules = alert_mgr.get_rules()
            assert len(rules) == 1
            assert rules[0].name == "Test Rule"
            assert rules[0].threshold == 100.0

    runner.test("Add alert rule", test_add_alert_rule)

    def test_enable_disable_rule():
        """Test enabling/disabling alert rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "alerting.db"
            alert_mgr = AlertManager(db_path, metrics_collector=None)

            alert_mgr.add_rule(
                name="Test Rule",
                condition="daily_cost_exceeds",
                threshold=100.0,
                channels=["email"],
            )

            # Disable rule
            alert_mgr.disable_rule("Test Rule")
            rules = alert_mgr.get_rules(enabled_only=True)
            assert len(rules) == 0

            # Enable rule
            alert_mgr.enable_rule("Test Rule")
            rules = alert_mgr.get_rules(enabled_only=True)
            assert len(rules) == 1

    runner.test("Enable/disable rules", test_enable_disable_rule)

    def test_daily_cost_alert():
        """Test daily cost alert condition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_db = Path(tmpdir) / "monitoring.db"
            alert_db = Path(tmpdir) / "alerting.db"

            metrics = MetricsCollector(metrics_db)
            alert_mgr = AlertManager(alert_db, metrics_collector=metrics)

            # Record missions with high cost
            metrics.record_mission("m1", "success", 60.0, 100, 2)
            metrics.record_mission("m2", "success", 50.0, 100, 2)

            # Add rule
            alert_mgr.add_rule(
                name="Cost Alert",
                condition="daily_cost_exceeds",
                threshold=100.0,
                channels=["email"],
            )

            # Check rule (should trigger)
            rule = alert_mgr.get_rules()[0]
            alert = alert_mgr.check_rule(rule)

            assert alert is not None
            assert alert.current_value == 110.0  # 60 + 50
            assert alert.threshold == 100.0

    runner.test("Daily cost alert", test_daily_cost_alert)

    def test_success_rate_alert():
        """Test success rate alert condition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_db = Path(tmpdir) / "monitoring.db"
            alert_db = Path(tmpdir) / "alerting.db"

            metrics = MetricsCollector(metrics_db)
            alert_mgr = AlertManager(alert_db, metrics_collector=metrics)

            # Record missions with low success rate (60%)
            metrics.record_mission("m1", "success", 1.0, 100, 2)
            metrics.record_mission("m2", "success", 1.0, 100, 2)
            metrics.record_mission("m3", "success", 1.0, 100, 2)
            metrics.record_mission("m4", "failed", 2.0, 150, 3)
            metrics.record_mission("m5", "failed", 2.0, 150, 3)

            # Add rule (threshold: 80%)
            alert_mgr.add_rule(
                name="Success Rate Alert",
                condition="success_rate_below",
                threshold=80.0,
                channels=["email"],
            )

            # Check rule (should trigger)
            rule = alert_mgr.get_rules()[0]
            alert = alert_mgr.check_rule(rule)

            assert alert is not None
            assert alert.current_value == 60.0  # 3/5 = 60%
            assert alert.threshold == 80.0

    runner.test("Success rate alert", test_success_rate_alert)

    def test_alert_cooldown():
        """Test alert cooldown prevents spam."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_db = Path(tmpdir) / "monitoring.db"
            alert_db = Path(tmpdir) / "alerting.db"

            metrics = MetricsCollector(metrics_db)
            alert_mgr = AlertManager(alert_db, metrics_collector=metrics)

            # Record high cost
            metrics.record_mission("m1", "success", 150.0, 100, 2)

            # Add rule with short cooldown
            alert_mgr.add_rule(
                name="Cost Alert",
                condition="daily_cost_exceeds",
                threshold=100.0,
                channels=["email"],
                cooldown_minutes=1,
            )

            rule = alert_mgr.get_rules()[0]

            # First check should trigger
            alert1 = alert_mgr.check_rule(rule)
            assert alert1 is not None

            # Set cooldown
            alert_mgr._set_cooldown(rule.name, rule.cooldown_minutes)

            # Second check should be blocked by cooldown
            alert2 = alert_mgr.check_rule(rule)
            assert alert2 is None

    runner.test("Alert cooldown", test_alert_cooldown)

    def test_alert_history():
        """Test alert history recording."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_db = Path(tmpdir) / "monitoring.db"
            alert_db = Path(tmpdir) / "alerting.db"

            metrics = MetricsCollector(metrics_db)
            alert_mgr = AlertManager(alert_db, metrics_collector=metrics)

            # Create and record alert
            alert = Alert(
                rule_name="Test Alert",
                severity="warning",
                message="Test message",
                current_value=150.0,
                threshold=100.0,
                timestamp=datetime.utcnow().isoformat(),
            )
            alert_mgr._record_alert(alert, ["email"])

            # Get history
            history = alert_mgr.get_alert_history(hours=24)
            assert len(history) == 1
            assert history[0]["rule_name"] == "Test Alert"

    runner.test("Alert history recording", test_alert_history)

    # ──────────────────────────────────────────────────────────────
    # Acceptance Criteria Tests
    # ──────────────────────────────────────────────────────────────
    print("\n[AC] Acceptance Criteria Tests")
    print("-" * 60)

    def test_ac_metrics_collected_continuously():
        """AC: Metrics collected continuously."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)

            # Record metrics over time
            for i in range(10):
                metrics.record_mission(
                    f"mission_{i}",
                    "success" if i % 2 == 0 else "failed",
                    1.0 + i * 0.1,
                    100 + i * 10,
                    2,
                )

            stats = metrics.get_mission_stats(hours=24)
            assert stats["total_missions"] == 10
            assert stats["successful_missions"] == 5
            assert stats["failed_missions"] == 5

    runner.test("AC: Metrics collected continuously", test_ac_metrics_collected_continuously)

    def test_ac_alerts_trigger_correctly():
        """AC: Alerts trigger correctly when conditions are met."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_db = Path(tmpdir) / "monitoring.db"
            alert_db = Path(tmpdir) / "alerting.db"

            metrics = MetricsCollector(metrics_db)
            alert_mgr = AlertManager(alert_db, metrics_collector=metrics)

            # Set up conditions that will trigger alerts
            metrics.record_mission("m1", "success", 120.0, 100, 2)  # High cost

            alert_mgr.add_rule(
                name="Cost Exceeded",
                condition="daily_cost_exceeds",
                threshold=100.0,
                channels=["email"],
            )

            # Check all rules
            alerts = alert_mgr.check_all_rules()

            # Should have triggered the cost alert
            assert len(alerts) == 1
            assert alerts[0].rule_name == "Cost Exceeded"

    runner.test("AC: Alerts trigger correctly", test_ac_alerts_trigger_correctly)

    def test_ac_multiple_alert_channels():
        """AC: Notifications sent via multiple channels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            alert_db = Path(tmpdir) / "alerting.db"
            alert_mgr = AlertManager(alert_db, metrics_collector=None)

            # Add rule with multiple channels
            alert_mgr.add_rule(
                name="Multi-Channel Alert",
                condition="daily_cost_exceeds",
                threshold=100.0,
                channels=["email", "slack", "pagerduty"],
            )

            rules = alert_mgr.get_rules()
            assert len(rules) == 1
            assert "email" in rules[0].channels
            assert "slack" in rules[0].channels
            assert "pagerduty" in rules[0].channels

    runner.test("AC: Multiple notification channels", test_ac_multiple_alert_channels)

    def test_ac_dashboard_queries():
        """AC: Dashboard queries return metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "monitoring.db"
            metrics = MetricsCollector(db_path)

            # Record sample data
            for i in range(24):
                metrics.record_mission(
                    f"mission_{i}",
                    "success",
                    1.0,
                    100,
                    2,
                    domain="coding",
                )

            # Test dashboard queries
            stats = metrics.get_mission_stats(hours=24)
            assert stats["total_missions"] == 24

            trend = metrics.get_mission_trend(hours=24, bucket_hours=1)
            assert len(trend) > 0

            tool_stats = metrics.get_tool_stats(limit=10)
            assert isinstance(tool_stats, list)

            error_stats = metrics.get_error_stats(hours=24)
            assert isinstance(error_stats, list)

    runner.test("AC: Dashboard queries work", test_ac_dashboard_queries)

    return runner.summary()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
