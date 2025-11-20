"""
PHASE 4.3: Instance-Based Cost Tracker (R5)

Provides per-run cost tracking instances to prevent race conditions
in concurrent job scenarios.

Problem: Original cost_tracker.py uses global singleton state (_GLOBAL_STATE).
When multiple jobs run concurrently, they share the same cost state, causing
misattributed costs and potential data loss on reset().

Solution: CostTrackerInstance class that creates isolated cost tracking
per orchestrator run.

Usage:
    # Create instance for this run
    tracker = CostTrackerInstance(run_id="abc123")

    # Register calls
    tracker.register_call("manager", "gpt-5-mini", 1000, 500)

    # Get summary
    summary = tracker.get_summary()
    total_cost = tracker.get_total_cost_usd()

    # Save to run metadata
    tracker.save_to_file(Path("run_logs/abc123/costs.json"))

Backward Compatibility:
The original cost_tracker.py module is preserved for legacy code.
New code should use CostTrackerInstance for isolated tracking.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import pricing logic from original cost_tracker
try:
    from cost_tracker import CallRecord, CostState, _get_pricing_fallback
    COST_TRACKER_AVAILABLE = True
except ImportError:
    COST_TRACKER_AVAILABLE = False
    # Fallback if cost_tracker not available
    from dataclasses import dataclass, field

    @dataclass
    class CallRecord:
        role: str
        model: str
        prompt_tokens: int
        completion_tokens: int
        input_cost_usd: float
        output_cost_usd: float
        total_cost_usd: float

    @dataclass
    class CostState:
        calls: List[CallRecord] = field(default_factory=list)

        def add_call(self, role: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
            # Simplified fallback pricing
            FALLBACK_PRICES = {
                "input": 0.25 / 1_000_000,
                "output": 2.0 / 1_000_000,
            }
            input_cost = prompt_tokens * FALLBACK_PRICES["input"]
            output_cost = completion_tokens * FALLBACK_PRICES["output"]
            total_cost = input_cost + output_cost

            self.calls.append(
                CallRecord(
                    role=role,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    input_cost_usd=input_cost,
                    output_cost_usd=output_cost,
                    total_cost_usd=total_cost,
                )
            )

        def summary(self) -> Dict[str, Any]:
            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0.0

            by_role: Dict[str, Dict[str, Any]] = {}
            by_model: Dict[str, Dict[str, Any]] = {}

            for c in self.calls:
                total_input_tokens += c.prompt_tokens
                total_output_tokens += c.completion_tokens
                total_cost += c.total_cost_usd

                # by_role
                r = by_role.setdefault(
                    c.role,
                    {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_usd": 0.0,
                        "num_calls": 0,
                    },
                )
                r["prompt_tokens"] += c.prompt_tokens
                r["completion_tokens"] += c.completion_tokens
                r["total_usd"] += c.total_cost_usd
                r["num_calls"] += 1

                # by_model
                m = by_model.setdefault(
                    c.model,
                    {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_usd": 0.0,
                        "num_calls": 0,
                    },
                )
                m["prompt_tokens"] += c.prompt_tokens
                m["completion_tokens"] += c.completion_tokens
                m["total_usd"] += c.total_cost_usd
                m["num_calls"] += 1

            return {
                "num_calls": len(self.calls),
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_usd": round(total_cost, 6),
                "by_role": {
                    role: {
                        **vals,
                        "total_usd": round(vals["total_usd"], 6),
                    }
                    for role, vals in by_role.items()
                },
                "by_model": {
                    model: {
                        **vals,
                        "total_usd": round(vals["total_usd"], 6),
                    }
                    for model, vals in by_model.items()
                },
            }

    def _get_pricing_fallback(model_key: str) -> Dict[str, float]:
        return {
            "input": 0.25 / 1_000_000,
            "output": 2.0 / 1_000_000,
        }


class CostTrackerInstance:
    """
    Per-run cost tracker instance.

    PHASE 4.3 (R5): Isolated cost tracking to prevent race conditions
    in concurrent job scenarios.
    """

    def __init__(self, run_id: str):
        """
        Initialize cost tracker for a specific run.

        Args:
            run_id: Unique run identifier
        """
        self.run_id = run_id
        self.state = CostState()
        self.created_at = datetime.utcnow().isoformat() + "Z"

    def register_call(
        self, role: str, model: str, prompt_tokens: int, completion_tokens: int
    ) -> None:
        """
        Register an LLM API call.

        Args:
            role: Agent role (manager, supervisor, employee)
            model: Model identifier
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        """
        try:
            self.state.add_call(role, model, prompt_tokens, completion_tokens)
        except Exception as e:
            print(f"[CostTrackerInstance] Failed to register call: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get cost summary for this run.

        Returns:
            Dict with token counts, costs by role/model, total cost
        """
        summary = self.state.summary()
        summary["run_id"] = self.run_id
        summary["created_at"] = self.created_at
        return summary

    def get_total_cost_usd(self) -> float:
        """
        Get total cost in USD for this run.

        Returns:
            Total cost in USD
        """
        try:
            return self.state.summary()["total_usd"]
        except Exception:
            return 0.0

    def check_cost_cap(
        self,
        max_cost_usd: float,
        estimated_tokens: int = 5000,
        model: str = "gpt-5-mini",
    ) -> tuple[bool, float, str]:
        """
        Check if making another LLM call would exceed the cost cap.

        Args:
            max_cost_usd: Maximum allowed cost in USD
            estimated_tokens: Rough estimate of tokens for next call
            model: Model that will be used

        Returns:
            Tuple of (would_exceed, current_cost, message)
        """
        if max_cost_usd <= 0:
            return (False, 0.0, "No cost cap configured")

        current_cost = self.get_total_cost_usd()

        # Estimate cost of next call
        price_cfg = _get_pricing_fallback(model)
        estimated_call_cost = estimated_tokens * price_cfg["output"]  # Conservative: assume all output

        projected_cost = current_cost + estimated_call_cost

        if projected_cost > max_cost_usd:
            message = (
                f"Cost cap would be exceeded: current=${current_cost:.4f}, "
                f"estimated next call=${estimated_call_cost:.4f}, "
                f"projected total=${projected_cost:.4f}, "
                f"cap=${max_cost_usd:.4f}"
            )
            return (True, current_cost, message)

        remaining = max_cost_usd - current_cost
        message = (
            f"Within budget: current=${current_cost:.4f}, "
            f"remaining=${remaining:.4f}, "
            f"cap=${max_cost_usd:.4f}"
        )
        return (False, current_cost, message)

    def save_to_file(self, file_path: Path) -> None:
        """
        Save cost summary to JSON file.

        Args:
            file_path: Path to save JSON file
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            summary = self.get_summary()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CostTrackerInstance] Failed to save to file: {e}")

    def append_history(
        self,
        log_file: Optional[Path] = None,
        project_name: Optional[str] = None,
        task: Optional[str] = None,
        status: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Append history record to log file.

        Args:
            log_file: Log file path
            project_name: Project name
            task: Task description
            status: Run status
            extra: Additional metadata
        """
        if log_file is None:
            return

        try:
            summary = self.get_summary()
            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "run_id": self.run_id,
                "project": project_name,
                "task": task,
                "status": status,
                "total_usd": summary.get("total_usd"),
                "prompt_tokens": summary.get("total_input_tokens"),
                "completion_tokens": summary.get("total_output_tokens"),
            }

            if extra:
                record.update(extra)

            log_file.parent.mkdir(parents=True, exist_ok=True)
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")

        except Exception as e:
            print(f"[CostTrackerInstance] Failed to append history: {e}")
