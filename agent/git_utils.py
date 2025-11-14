# git_utils.py
from __future__ import annotations

import subprocess
from pathlib import Path


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


def commit_all(root: Path, message: str) -> None:
    """
    Stage all changes and create a commit with the given message.

    - If `.git` is missing, does nothing.
    - If there is nothing to commit, prints a friendly message.
    - Never raises; logs any errors and continues.
    """
    try:
        root = Path(root)
        if not (root / ".git").exists():
            # No repo, silently ignore
            return

        add_proc = _run_git(["add", "."], cwd=root)
        if add_proc.returncode != 0:
            msg = (add_proc.stderr or add_proc.stdout or "").strip()
            print(f"[Git] git add failed: {msg}")
            return

        commit_proc = _run_git(["commit", "-m", message], cwd=root)
        output = (commit_proc.stderr or commit_proc.stdout or "").lower()

        if commit_proc.returncode != 0:
            if "nothing to commit" in output:
                print("[Git] Nothing new to commit.")
                return
            msg = (commit_proc.stderr or commit_proc.stdout or "").strip()
            print(f"[Git] git commit failed: {msg}")
            return

        print(f"[Git] Created commit: {message}")
    except Exception as e:
        print(f"[Git] Error during commit in {root}: {e}")
