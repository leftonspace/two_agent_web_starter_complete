from pathlib import Path
import sys


# Project root and agent dir
ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "agent"

# Make sure Python can see agent/ as a module location
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

import site_tools  # type: ignore  # we only care that it imports


def test_site_tools_has_snapshot_function():
    """
    Very lightweight integration check:

    - agent/site_tools.py is importable
    - it exposes a write_iteration_snapshot helper
    """
    assert hasattr(
        site_tools, "write_iteration_snapshot"
    ), "site_tools.write_iteration_snapshot is missing"
