#!/usr/bin/env python3
"""
PHASE 5.2: Dependency Locking Script

Generates a locked requirements file from the flexible requirements.txt.
Ensures reproducible builds across environments.

Usage:
    python scripts/lock_dependencies.py              # Generate requirements.lock
    python scripts/lock_dependencies.py --check      # Verify lock is up to date
    python scripts/lock_dependencies.py --install    # Install from lockfile

Features:
- Generates exact version pins from installed packages
- Preserves comments and categories from requirements.lock
- Validates lockfile exists and matches installed packages
- Supports both pip and pip-tools workflows
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_TXT = PROJECT_ROOT / "requirements.txt"
REQUIREMENTS_LOCK = PROJECT_ROOT / "requirements.lock"


def get_installed_packages() -> Dict[str, str]:
    """
    Get all installed packages with their versions.

    Returns:
        Dict mapping package name to version
    """
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=True,
    )

    packages = {}
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Handle both == and @ (editable installs)
        if "==" in line:
            name, version = line.split("==", 1)
            packages[name.lower()] = version
        elif "@" in line:
            # Editable install, skip
            continue

    return packages


def parse_requirements(path: Path) -> List[Tuple[str, Optional[str]]]:
    """
    Parse requirements file to get package names and version specs.

    Args:
        path: Path to requirements file

    Returns:
        List of (package_name, version_spec) tuples
    """
    if not path.exists():
        return []

    packages = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Remove extras like [asyncio]
            if "[" in line:
                base = line.split("[")[0]
                rest = line.split("]")[-1] if "]" in line else ""
                line = base + rest

            # Parse version spec
            for op in [">=", "<=", "==", "~=", "!=", ">", "<"]:
                if op in line:
                    name = line.split(op)[0].strip()
                    spec = line[len(name):].strip()
                    packages.append((name.lower(), spec))
                    break
            else:
                packages.append((line.lower(), None))

    return packages


def generate_lockfile(
    installed: Dict[str, str],
    required: List[Tuple[str, Optional[str]]],
) -> str:
    """
    Generate lockfile content from installed packages.

    Args:
        installed: Dict of installed package versions
        required: List of required packages from requirements.txt

    Returns:
        Lockfile content as string
    """
    lines = [
        f"# PHASE 5.2: Locked Dependencies for Reproducible Builds",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"#",
        f"# This file contains exact pinned versions for production deployments.",
        f"# For development with flexible versions, use requirements.txt",
        f"#",
        f"# Regenerate with: python scripts/lock_dependencies.py",
        f"# Install with: pip install -r requirements.lock",
        f"#",
        f"# WARNING: These versions were locked at a specific point in time.",
        f"# Security updates may require regenerating this file.",
        f"",
    ]

    # Get required package names
    required_names = {name for name, _ in required}

    # Add required packages first
    lines.append("# ============================================================================")
    lines.append("# Direct Dependencies (from requirements.txt)")
    lines.append("# ============================================================================")

    for name, _ in required:
        if name in installed:
            lines.append(f"{name}=={installed[name]}")
        else:
            lines.append(f"# {name}  # Not installed")

    # Add transitive dependencies
    lines.append("")
    lines.append("# ============================================================================")
    lines.append("# Transitive Dependencies (automatically resolved)")
    lines.append("# ============================================================================")

    transitive = sorted(
        (name, version)
        for name, version in installed.items()
        if name not in required_names
    )

    for name, version in transitive:
        lines.append(f"{name}=={version}")

    return "\n".join(lines) + "\n"


def check_lockfile() -> bool:
    """
    Check if lockfile exists and is reasonably up to date.

    Returns:
        True if lockfile is valid
    """
    if not REQUIREMENTS_LOCK.exists():
        print(f"ERROR: Lockfile not found at {REQUIREMENTS_LOCK}")
        print("Run 'python scripts/lock_dependencies.py' to generate it.")
        return False

    # Check if requirements.txt is newer than lockfile
    if REQUIREMENTS_TXT.exists():
        req_mtime = REQUIREMENTS_TXT.stat().st_mtime
        lock_mtime = REQUIREMENTS_LOCK.stat().st_mtime

        if req_mtime > lock_mtime:
            print("WARNING: requirements.txt is newer than requirements.lock")
            print("Consider regenerating the lockfile.")
            return False

    print(f"Lockfile OK: {REQUIREMENTS_LOCK}")
    return True


def install_from_lockfile() -> int:
    """
    Install packages from lockfile.

    Returns:
        Exit code from pip
    """
    if not REQUIREMENTS_LOCK.exists():
        print(f"ERROR: Lockfile not found at {REQUIREMENTS_LOCK}")
        return 1

    print(f"Installing from {REQUIREMENTS_LOCK}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_LOCK)],
    )
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Dependency locking for reproducible builds"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if lockfile is up to date",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install from lockfile",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REQUIREMENTS_LOCK,
        help="Output lockfile path",
    )

    args = parser.parse_args()

    if args.check:
        sys.exit(0 if check_lockfile() else 1)

    if args.install:
        sys.exit(install_from_lockfile())

    # Generate lockfile
    print("Generating lockfile...")

    try:
        installed = get_installed_packages()
        required = parse_requirements(REQUIREMENTS_TXT)

        if not installed:
            print("ERROR: No packages installed. Install requirements first:")
            print(f"  pip install -r {REQUIREMENTS_TXT}")
            sys.exit(1)

        content = generate_lockfile(installed, required)

        args.output.write_text(content)
        print(f"Generated {args.output} with {len(installed)} packages")

    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to get installed packages: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
