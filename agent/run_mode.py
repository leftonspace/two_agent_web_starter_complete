# run_mode.py
from __future__ import annotations

import json
from pathlib import Path

# We import defaults just for display purposes.
try:
    from llm import (
        DEFAULT_MANAGER_MODEL,
        DEFAULT_SUPERVISOR_MODEL,
        DEFAULT_EMPLOYEE_MODEL,
    )
except ImportError:
    # Fallback labels if constants are not accessible for any reason.
    DEFAULT_MANAGER_MODEL = "gpt-5-mini"
    DEFAULT_SUPERVISOR_MODEL = "gpt-5-nano"
    DEFAULT_EMPLOYEE_MODEL = "gpt-5"


def _load_config() -> dict:
    cfg_path = Path(__file__).resolve().parent / "project_config.json"
    if not cfg_path.exists():
        raise FileNotFoundError(f"project_config.json not found at {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def _print_summary(cfg: dict) -> None:
    mode = cfg.get("mode", "3loop")
    project = cfg.get("project_subdir", "<unknown>")
    task = cfg.get("task", "").strip()
    short_task = (task[:120] + "…") if len(task) > 120 else task

    max_rounds = int(cfg.get("max_rounds", 1))
    use_visual_review = bool(cfg.get("use_visual_review", False))
    prompts_file = cfg.get("prompts_file", "prompts_default.json")

    max_cost_usd = float(cfg.get("max_cost_usd", 0.0) or 0.0)
    cost_warning_usd = float(cfg.get("cost_warning_usd", 0.0) or 0.0)
    interactive_cost_mode = cfg.get("interactive_cost_mode", "off")

    print("======================================")
    print("  Two-Agent / Multi-Agent Runner")
    print("======================================")
    print(f"Mode:             {mode}  (2loop = Manager↔Employee, 3loop = Manager↔Supervisor↔Employee)")
    print(f"Project subdir:   {project}")
    print(f"Task (short):     {short_task}")
    print(f"Max rounds:       {max_rounds}")
    print(f"Visual review:    {use_visual_review}")
    print(f"Prompts file:     {prompts_file}")
    print("--------------------------------------")
    print(f"Cost warning:     {cost_warning_usd or 0.0:.4f} USD")
    print(f"Cost cap:         {max_cost_usd or 0.0:.4f} USD")
    print(f"Interactive cost: {interactive_cost_mode!r}  (off|once)")
    print("--------------------------------------")
    print("Default models (can be overridden by env vars):")
    print(f"  Manager:   {DEFAULT_MANAGER_MODEL}")
    print(f"  Supervisor:{DEFAULT_SUPERVISOR_MODEL}")
    print(f"  Employee:  {DEFAULT_EMPLOYEE_MODEL}")
    print("======================================\n")


def main() -> None:
    cfg = _load_config()
    _print_summary(cfg)

    mode = cfg.get("mode", "3loop").lower().strip()
    if mode == "2loop":
        from orchestrator_2loop import main as main_2loop
        main_2loop()
    else:
        # Default to 3-loop if anything else
        from orchestrator import main as main_3loop
        main_3loop()


if __name__ == "__main__":
    main()
