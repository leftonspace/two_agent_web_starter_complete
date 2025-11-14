# cost_tracker.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import json


# USD per token, based on your pricing snippet
# (prices are per 1M tokens, so we divide by 1_000_000)
PRICES_USD_PER_TOKEN: Dict[str, Dict[str, float]] = {
    "gpt-5": {
        "input": 1.250 / 1_000_000,
        "output": 10.000 / 1_000_000,
    },
    "gpt-5-mini": {
        "input": 0.250 / 1_000_000,
        "output": 2.000 / 1_000_000,
    },
    "gpt-5-nano": {
        "input": 0.050 / 1_000_000,
        "output": 0.400 / 1_000_000,
    },
    "gpt-5-pro": {
        "input": 15.00 / 1_000_000,
        "output": 120.00 / 1_000_000,
    },
}

FALLBACK_MODEL = "gpt-5-mini"  # if we don't know a model name, use this as a safe-ish default


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
        model_key = model or FALLBACK_MODEL
        price_cfg = PRICES_USD_PER_TOKEN.get(model_key, PRICES_USD_PER_TOKEN[FALLBACK_MODEL])

        input_cost = prompt_tokens * price_cfg["input"]
        output_cost = completion_tokens * price_cfg["output"]
        total_cost = input_cost + output_cost

        self.calls.append(
            CallRecord(
                role=role,
                model=model_key,
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


_GLOBAL_STATE = CostState()


def reset() -> None:
    """Reset the global cost tracking state for a new run."""
    _GLOBAL_STATE.calls.clear()


def register_call(role: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    """Register a single API call for cost accounting."""
    try:
        _GLOBAL_STATE.add_call(role, model, prompt_tokens, completion_tokens)
    except Exception as e:
        # We don't want cost-tracking errors to kill the main flow
        print(f"[CostTracker] Failed to register call: {e}")


def get_summary() -> Dict[str, Any]:
    """Get a structured summary of costs and tokens for the current run."""
    return _GLOBAL_STATE.summary()


def get_total_cost_usd() -> float:
    """Return the estimated total cost in USD for the current run."""
    try:
        return _GLOBAL_STATE.summary()["total_usd"]
    except Exception:
        return 0.0


def append_history(
    log_file: Path,
    project_name: str,
    task: str,
    status: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Append a JSON line to a history file with timestamp, project, task, status, and cost summary.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    payload: Dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "project": project_name,
        "task": task,
        "status": status,
        "cost_summary": get_summary(),
    }
    if extra:
        payload["extra"] = extra

    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[CostTracker] Failed to write history to {log_file}: {e}")
