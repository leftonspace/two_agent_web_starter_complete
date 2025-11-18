#!/usr/bin/env python3
# dev/profile_run.py
"""
Profile an orchestrator run for performance analysis.

Measures:
- Wall-clock runtime
- CPU time
- Memory footprint (if psutil available)
- Token usage from cost tracker

Outputs a JSON profile next to the run logs.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Add agent directory to path
agent_dir = Path(__file__).resolve().parent.parent / "agent"
sys.path.insert(0, str(agent_dir))


def get_memory_info() -> dict:
    """Get current memory usage. Requires psutil if available."""
    try:
        import psutil

        process = psutil.Process()
        mem_info = process.memory_info()
        return {
            "rss_mb": mem_info.rss / 1024 / 1024,  # Resident set size
            "vms_mb": mem_info.vms / 1024 / 1024,  # Virtual memory size
            "available": True,
        }
    except ImportError:
        return {"available": False, "note": "psutil not installed"}


def main() -> None:
    """Run and profile an orchestrator run."""
    print("\n" + "=" * 70)
    print("  DEV TOOL: Profile Run")
    print("=" * 70 + "\n")

    # Check for psutil
    try:
        import psutil

        print("✓ psutil available - full memory profiling enabled")
    except ImportError:
        print("⚠️  psutil not installed - memory profiling limited")
        print("   Install with: pip install psutil\n")

    # Start profiling
    start_time = time.time()
    start_cpu = time.process_time()
    start_memory = get_memory_info()

    print("📊 Starting profiled run...\n")
    print("=" * 70)

    # Run the orchestrator
    run_id = None
    exception_occurred = None

    try:
        from run_mode import main as run_main

        run_main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Run interrupted by user")
        exception_occurred = "KeyboardInterrupt"
    except Exception as e:
        print(f"\n\n❌ Run failed: {e}")
        exception_occurred = str(e)

    # End profiling
    end_time = time.time()
    end_cpu = time.process_time()
    end_memory = get_memory_info()

    wall_time = end_time - start_time
    cpu_time = end_cpu - start_cpu

    print("\n" + "=" * 70)
    print("  📊 Profiling Results")
    print("=" * 70 + "\n")

    # Build profile
    profile = {
        "wall_time_seconds": round(wall_time, 3),
        "cpu_time_seconds": round(cpu_time, 3),
        "wall_time_formatted": format_duration(wall_time),
        "cpu_time_formatted": format_duration(cpu_time),
    }

    # Add memory info if available
    if start_memory.get("available") and end_memory.get("available"):
        peak_rss = end_memory["rss_mb"]
        delta_rss = end_memory["rss_mb"] - start_memory["rss_mb"]
        profile["memory"] = {
            "peak_rss_mb": round(peak_rss, 2),
            "delta_rss_mb": round(delta_rss, 2),
            "start_rss_mb": round(start_memory["rss_mb"], 2),
            "end_rss_mb": round(end_memory["rss_mb"], 2),
        }
        print(f"⏱️  Wall time:    {profile['wall_time_formatted']}")
        print(f"⚙️  CPU time:     {profile['cpu_time_formatted']}")
        print(f"💾 Peak memory:  {peak_rss:.2f} MB")
        print(f"📈 Memory delta: {delta_rss:+.2f} MB")
    else:
        profile["memory"] = start_memory
        print(f"⏱️  Wall time:    {profile['wall_time_formatted']}")
        print(f"⚙️  CPU time:     {profile['cpu_time_formatted']}")
        print(f"💾 Memory:       (not available)")

    # Try to get cost tracker info
    try:
        import cost_tracker

        cost_summary = cost_tracker.get_summary()
        profile["cost"] = cost_summary
        print(f"💰 Total cost:   ${cost_summary.get('total_usd', 0.0):.4f}")
        print(f"🔢 Total tokens: {cost_summary.get('total_tokens', 0):,}")
    except Exception:
        pass

    if exception_occurred:
        profile["exception"] = exception_occurred

    # Try to find the latest run and save profile alongside it
    try:
        run_logs_dir = agent_dir.parent / "run_logs"
        if run_logs_dir.exists():
            run_dirs = sorted(
                [d for d in run_logs_dir.iterdir() if d.is_dir()],
                key=lambda d: d.stat().st_mtime,
                reverse=True,
            )

            if run_dirs:
                latest_run_dir = run_dirs[0]
                run_id = latest_run_dir.name

                # Save profile
                profile_file = latest_run_dir / "profile.json"
                profile_file.write_text(json.dumps(profile, indent=2), encoding="utf-8")

                print(f"\n📄 Profile saved:  {profile_file}")
                print(f"📁 Run ID:         {run_id}")
    except Exception as e:
        print(f"\n⚠️  Could not save profile: {e}")

        # Fallback: save to current directory
        fallback_file = Path("profile.json")
        fallback_file.write_text(json.dumps(profile, indent=2), encoding="utf-8")
        print(f"📄 Profile saved to: {fallback_file}")

    print()


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


if __name__ == "__main__":
    main()
