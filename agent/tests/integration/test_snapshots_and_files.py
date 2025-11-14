import sys
from pathlib import Path

# Test file path: .../agent/tests/integration/test_snapshots_and_files.py
# parents[0] = .../agent/tests/integration
# parents[1] = .../agent/tests
# parents[2] = .../agent
# parents[3] = .../two_agent_web_starter (project root)
ROOT = Path(__file__).resolve().parents[3]
AGENT_DIR = ROOT / "agent"

if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

import site_tools  # type: ignore  # noqa: E402  # we only care that it imports


def test_site_tools_imports():
    """
    Lightweight integration check:
    - agent/site_tools.py is importable
    """
    assert hasattr(site_tools, "__file__")
