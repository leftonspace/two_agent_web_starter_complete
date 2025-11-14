import os
from pathlib import Path
import importlib

import cost_tracker

# We import orchestrator via importlib so pytest doesn't auto-run it.
orchestrator = importlib.import_module("orchestrator")


def test_smoke_run_hello_kevin(tmp_path: Path) -> None:
    """
    Very small end-to-end smoke test.

    WARNING: This will call the OpenAI API.
    Only run when you actually want to test the full pipeline.
    """

    if not os.getenv("OPENAI_API_KEY"):
        # Skip if no key set
        import pytest

        pytest.skip("OPENAI_API_KEY not set; skipping real E2E test.")

    # Prepare a tiny project folder under tmp_path
    project_dir = tmp_path / "hello_kevin_e2e"
    project_dir.mkdir(parents=True, exist_ok=True)

    # Minimal config for this run
    config = {
        "project_root": str(project_dir),
        "task": "Create a minimal landing page that says 'Hello Kevin'.",
        "prompts_file": "prompts_default.json",
        "mode": "3loop",
        "max_rounds": 1,
        "use_visual_review": False,
        "use_git": False,
        "git_repo_root": None,
        "git_auto_commit": False,
    }

    # Reset cost
    cost_tracker.reset()

    # Run orchestrator.main with our custom config
    orchestrator.main(config_override=config)

    # Check files exist
    index_file = project_dir / "index.html"
    assert index_file.exists()
    html = index_file.read_text(encoding="utf-8")
    assert "Hello Kevin" in html

    # Ensure some cost was tracked
    assert cost_tracker.get_total_cost_usd() > 0.0
