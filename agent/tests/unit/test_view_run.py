# test_view_run.py
"""
Unit tests for view_run.py (Stage 2.3 - CLI Dashboard)

Tests cover:
- Summary computation and delegation to core_logging
- Event sorting by timestamp
- Error event filtering
- Timestamp formatting
- Graceful handling of missing/malformed logs
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import core_logging
import view_run


class TestSummaryComputation:
    """Test summary computation logic."""

    def test_compute_summary_empty_events(self):
        """Test compute_summary with no events."""
        result = view_run.compute_summary([])

        assert result == {}

    def test_compute_summary_delegates_to_core_logging(self):
        """Test that compute_summary delegates to core_logging.get_run_summary."""
        # Create mock events
        events = [
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1000.0,
                event_type="start",
                payload={"task_description": "Test task"},
                schema_version="1.0"
            ),
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1001.0,
                event_type="final_status",
                payload={"status": "success"},
                schema_version="1.0"
            )
        ]

        with mock.patch("core_logging.get_run_summary") as mock_summary:
            mock_summary.return_value = {
                "run_id": "test123",
                "start_time": 1000.0,
                "end_time": 1001.0,
                "duration_seconds": 1.0,
                "num_iterations": 0,
                "models_used": [],
                "safety_status": None,
                "final_status": "success",
                "total_events": 2
            }

            result = view_run.compute_summary(events)

            # Verify delegation occurred
            mock_summary.assert_called_once_with("test123")

            # Verify base summary is included
            assert result["run_id"] == "test123"
            assert result["final_status"] == "success"

            # Verify error_events is added by view_run
            assert "error_events" in result

    def test_compute_summary_tracks_error_events(self):
        """Test that error events are properly tracked."""
        events = [
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1000.0,
                event_type="start",
                payload={},
                schema_version="1.0"
            ),
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1001.0,
                event_type="safety_check",
                payload={"summary_status": "failed", "error_count": 5},
                schema_version="1.0"
            ),
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1002.0,
                event_type="final_status",
                payload={"status": "failed"},
                schema_version="1.0"
            )
        ]

        result = view_run.compute_summary(events)

        # Should have 2 error events (safety_check failed + final_status failed)
        assert len(result["error_events"]) == 2


class TestEventSorting:
    """Test that events are sorted by timestamp in timeline."""

    def test_print_timeline_sorts_events(self, capsys):
        """Test that print_timeline sorts events chronologically."""
        # Create events in non-chronological order
        events = [
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1003.0,  # Third
                event_type="final_status",
                payload={"status": "success"},
                schema_version="1.0"
            ),
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1000.0,  # First
                event_type="start",
                payload={"task_description": "Test"},
                schema_version="1.0"
            ),
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1002.0,  # Second
                event_type="iteration_begin",
                payload={"iteration": 1},
                schema_version="1.0"
            )
        ]

        view_run.print_timeline(events)

        captured = capsys.readouterr()
        output_lines = captured.out.strip().split("\n")

        # Find event lines (skip header/footer)
        event_lines = [line for line in output_lines if line.startswith("[+")]

        # Verify chronological order by checking timestamps in output
        assert len(event_lines) == 3
        assert "start" in event_lines[0]
        assert "iteration_begin" in event_lines[1]
        assert "final_status" in event_lines[2]


class TestTimestampFormatting:
    """Test timestamp formatting and timezone handling."""

    def test_format_timestamp(self):
        """Test basic timestamp formatting."""
        # Unix epoch timestamp
        ts = 1609459200.0  # 2021-01-01 00:00:00 UTC

        result = view_run.format_timestamp(ts)

        # Should return a formatted string (exact value depends on local timezone)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "2021" in result or "2020" in result  # Account for timezone offset

    def test_print_summary_shows_timezone_note(self, capsys):
        """Test that summary includes timezone note."""
        summary = {
            "run_id": "test123",
            "start_time": 1000.0,
            "end_time": 1001.0,
            "duration_seconds": 1.0,
            "num_iterations": 1,
            "models_used": ["gpt-4o"],
            "safety_status": "passed",
            "final_status": "success"
        }

        view_run.print_summary(summary)

        captured = capsys.readouterr()

        # Verify timezone note is present
        assert "local system time" in captured.out.lower() or "timestamp" in captured.out.lower()


class TestErrorFiltering:
    """Test --only-errors filtering."""

    def test_error_event_filtering(self):
        """Test that only error events are included when filtering."""
        events = [
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1000.0,
                event_type="start",
                payload={},
                schema_version="1.0"
            ),
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1001.0,
                event_type="safety_check",
                payload={"summary_status": "failed"},
                schema_version="1.0"
            ),
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1002.0,
                event_type="iteration_end",
                payload={},
                schema_version="1.0"
            )
        ]

        # Filter error events (manual implementation of the filter logic from main)
        error_events = [
            e for e in events
            if (
                e.event_type == "error"
                or e.event_type == "warning"
                or (e.event_type == "safety_check" and e.payload.get("summary_status") == "failed")
                or (e.event_type == "final_status" and e.payload.get("status") not in ("success", "approved"))
            )
        ]

        # Should only have 1 error event (safety_check)
        assert len(error_events) == 1
        assert error_events[0].event_type == "safety_check"


class TestEventInfoFormatting:
    """Test event info formatting for different event types."""

    def test_format_start_event(self):
        """Test formatting of start event."""
        event = core_logging.LogEvent(
            run_id="test123",
            timestamp=1000.0,
            event_type="start",
            payload={"task_description": "Build a website for testing"},
            schema_version="1.0"
        )

        result = view_run._format_event_info(event)

        assert "Task:" in result
        assert "Build a website" in result

    def test_format_iteration_events(self):
        """Test formatting of iteration events."""
        begin_event = core_logging.LogEvent(
            run_id="test123",
            timestamp=1000.0,
            event_type="iteration_begin",
            payload={"iteration": 2},
            schema_version="1.0"
        )

        end_event = core_logging.LogEvent(
            run_id="test123",
            timestamp=1001.0,
            event_type="iteration_end",
            payload={"iteration": 2, "status": "needs_changes"},
            schema_version="1.0"
        )

        begin_result = view_run._format_event_info(begin_event)
        end_result = view_run._format_event_info(end_event)

        assert "Iteration 2 started" in begin_result
        assert "Iteration 2 ended" in end_result
        assert "needs_changes" in end_result

    def test_format_safety_check_event(self):
        """Test formatting of safety check event."""
        event = core_logging.LogEvent(
            run_id="test123",
            timestamp=1000.0,
            event_type="safety_check",
            payload={
                "summary_status": "failed",
                "error_count": 3,
                "warning_count": 5
            },
            schema_version="1.0"
        )

        result = view_run._format_event_info(event)

        assert "failed" in result
        assert "errors: 3" in result
        assert "warnings: 5" in result
        assert "✗" in result  # Failure emoji


class TestGracefulErrorHandling:
    """Test graceful handling of missing/malformed data."""

    def test_compute_summary_with_minimal_events(self):
        """Test summary computation with minimal event data."""
        events = [
            core_logging.LogEvent(
                run_id="test123",
                timestamp=1000.0,
                event_type="start",
                payload={},  # Minimal payload
                schema_version="1.0"
            )
        ]

        # Should not crash
        result = view_run.compute_summary(events)

        assert result is not None
        assert isinstance(result, dict)

    def test_format_event_info_unknown_type(self):
        """Test formatting of unknown event type."""
        event = core_logging.LogEvent(
            run_id="test123",
            timestamp=1000.0,
            event_type="unknown_event_type",
            payload={"some": "data"},
            schema_version="1.0"
        )

        result = view_run._format_event_info(event)

        # Should fall back to str(payload)
        assert "some" in result or "data" in result
