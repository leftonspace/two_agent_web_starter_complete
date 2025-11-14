"""
Root shim so tests and tools can import `site_tools` from the project root.

All public functions from `agent.site_tools` (including write_iteration_snapshot)
are re-exported here.
"""

from agent import site_tools as _impl

# Re-export all public names from agent.site_tools
for _name in dir(_impl):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_impl, _name)

# Optional: keep a reference to the underlying module if needed
impl = _impl
