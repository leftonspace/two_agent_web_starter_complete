# git_utils.py
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

# PHASE 1.4: Import secret scanner for pre-commit checks
try:
    import git_secret_scanner
    SECRET_SCANNER_AVAILABLE = True
except ImportError:
    SECRET_SCANNER_AVAILABLE = False


def _run_git(args: list[str], cwd: Path):
    """
    Run a git command in the given directory, capturing output.
    Never raises; returns the CompletedProcess.
    """
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )


def _git_available() -> bool:
    """
    Return True if `git` is available on PATH, False otherwise.
    """
    try:
        proc = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode == 0
    except Exception:
        return False


def ensure_repo(root: Path) -> bool:
    """
    Ensure there is a Git repo at `root`.

    - If Git is not installed, returns False and prints a message.
    - If `.git` exists, returns True.
    - Otherwise tries `git init` and returns True on success.
    - Never raises; on failure returns False and prints a short reason.
    """
    try:
        root = Path(root)

        if not root.exists():
            print(f"[Git] Directory does not exist: {root}")
            return False

        if not _git_available():
            print("[Git] git is not available on PATH; skipping Git integration.")
            return False

        git_dir = root / ".git"
        if git_dir.exists():
            print(f"[Git] Existing repository detected in {root}")
            return True

        proc = _run_git(["init"], cwd=root)
        if proc.returncode != 0:
            msg = (proc.stderr or proc.stdout or "").strip()
            print(f"[Git] Failed to initialize repository in {root}: {msg}")
            return False

        print(f"[Git] Initialized new repository in {root}")
        return True
    except Exception as e:
        print(f"[Git] Error while preparing repository in {root}: {e}")
        return False


def pre_commit_check(
    root: Path,
    secret_scanning_enabled: bool = True,
) -> Tuple[bool, Optional[str]]:
    """
    PHASE 1.4: Run pre-commit checks including secret scanning.

    Args:
        root: Repository root directory
        secret_scanning_enabled: Whether to run secret scanning (default: True)

    Returns:
        (passed, error_message) tuple
        - passed: True if all checks passed, False if commit should be blocked
        - error_message: Human-readable error message if checks failed, None otherwise

    Examples:
        >>> passed, error = pre_commit_check(Path("sites/my_project"))
        >>> if not passed:
        ...     print(f"Pre-commit check failed: {error}")
    """
    # Skip secret scanning if disabled
    if not secret_scanning_enabled:
        return (True, None)

    # Skip if secret scanner not available
    if not SECRET_SCANNER_AVAILABLE:
        print("[Git] Secret scanner not available - skipping pre-commit checks")
        return (True, None)

    try:
        root = Path(root)

        # Get list of modified/new files from git status
        status_proc = _run_git(["status", "--porcelain"], cwd=root)
        if status_proc.returncode != 0:
            # Can't get status, allow commit but warn
            print("[Git] Warning: Could not get git status for secret scanning")
            return (True, None)

        # Parse git status output
        files_to_scan = []
        for line in status_proc.stdout.splitlines():
            if len(line) < 3:
                continue
            # Git status format: "XY filename"
            # X = staged, Y = unstaged
            status_code = line[:2]
            filename = line[3:].strip()

            # Skip deleted files
            if "D" in status_code:
                continue

            file_path = root / filename
            if file_path.exists():
                files_to_scan.append(file_path)

        if not files_to_scan:
            # No files to scan
            return (True, None)

        # Scan files for secrets
        print(f"[Git] Scanning {len(files_to_scan)} file(s) for secrets...")
        findings = git_secret_scanner.scan_files_for_secrets(files_to_scan)

        if not findings:
            print("[Git] ✅ No secrets detected")
            return (True, None)

        # Secrets detected - block commit
        print(f"[Git] 🚨 Found {len(findings)} potential secret(s)")

        # Format detailed error report
        error_report = git_secret_scanner.format_findings_report(findings)

        return (False, error_report)

    except Exception as e:
        print(f"[Git] Warning: Secret scanning failed: {e}")
        # Fail-open: Allow commit if scanner errors
        return (True, None)


def commit_all(
    root: Path,
    message: str,
    secret_scanning_enabled: bool = True,
) -> bool:
    """
    Stage all changes and create a commit with the given message.

    PHASE 1.4: Now includes pre-commit secret scanning.

    - If `.git` is missing, does nothing.
    - If there is nothing to commit, prints a friendly message.
    - If secrets are detected, blocks commit and prints error report.
    - Never raises; logs any errors and continues.

    Args:
        root: Repository root directory
        message: Commit message
        secret_scanning_enabled: Whether to run secret scanning (default: True)

    Returns:
        True if commit succeeded, False otherwise
    """
    try:
        root = Path(root)
        if not (root / ".git").exists():
            # No repo, silently ignore
            return False

        # PHASE 1.4: Run pre-commit secret scanning
        passed, error_message = pre_commit_check(root, secret_scanning_enabled)
        if not passed:
            print("\n" + "="*70)
            print(error_message)
            print("="*70 + "\n")
            print("[Git] ❌ Commit BLOCKED due to secret scanning failure")
            return False

        add_proc = _run_git(["add", "."], cwd=root)
        if add_proc.returncode != 0:
            msg = (add_proc.stderr or add_proc.stdout or "").strip()
            print(f"[Git] git add failed: {msg}")
            return False

        commit_proc = _run_git(["commit", "-m", message], cwd=root)
        output = (commit_proc.stderr or commit_proc.stdout or "").lower()

        if commit_proc.returncode != 0:
            if "nothing to commit" in output:
                print("[Git] Nothing new to commit.")
                return True  # Not an error, just nothing to commit
            msg = (commit_proc.stderr or commit_proc.stdout or "").strip()
            print(f"[Git] git commit failed: {msg}")
            return False

        print(f"[Git] Created commit: {message}")
        return True
    except Exception as e:
        print(f"[Git] Error during commit in {root}: {e}")
        return False
