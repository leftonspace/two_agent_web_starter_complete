from pathlib import Path
import importlib.util
import json

# Test file path: .../agent/tests/e2e/test_smoke_hello_kevin.py
# parents[0] = .../agent/tests/e2e
# parents[1] = .../agent/tests
# parents[2] = .../agent
# parents[3] = .../two_agent_web_starter (project root)
ROOT = Path(__file__).resolve().parents[3]
AGENT_DIR = ROOT / "agent"


def _load_orchestrator_module():
    """Load agent/orchestrator.py directly from the agent folder."""
    orch_path = AGENT_DIR / "orchestrator.py"
    assert orch_path.exists(), f"orchestrator.py not found at {orch_path}"

    spec = importlib.util.spec_from_file_location("agent_orchestrator", orch_path)
    assert spec and spec.loader, "Could not create import spec for orchestrator.py"

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_project_config_loads_and_has_basic_keys():
    cfg_path = AGENT_DIR / "project_config.json"
    assert cfg_path.exists(), f"project_config.json not found at {cfg_path}"

    data = json.loads(cfg_path.read_text(encoding="utf-8"))

    # Keep this robust and aligned with your current schema:
    # We just sanity-check that these fundamental knobs exist.
    required_keys = ("task", "mode", "max_rounds", "max_cost_usd")
    for key in required_keys:
        assert key in data, f"Expected key '{key}' missing in project_config.json"


def test_orchestrator_module_imports_and_has_main():
    orch = _load_orchestrator_module()
    assert hasattr(orch, "main"), "orchestrator.main is missing"
