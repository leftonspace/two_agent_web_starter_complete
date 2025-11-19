# merge_manager.py
"""
STAGE 4.1 & 4.2: Merge Manager & Semantic Git Commits

This module provides:
1. Git diff analysis and LLM-powered summarization
2. Semantic commit message generation
3. Automatic git commit functionality

KEY FEATURES:
- compute_diff: Get git diff for a repo
- summarize_diff_with_llm: LLM-powered diff analysis
- summarize_session: Generate semantic commit messages from session changes
- make_commit: Execute git commits with semantic messages
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from core_logging import log_event
from llm import chat_json


def compute_diff(repo_path: Path) -> str:
    """
    Compute git diff for the given repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Git diff as a string, or empty string if:
        - No git repo exists
        - No changes detected
        - An error occurred
    """
    try:
        repo_path = Path(repo_path)

        # Check if .git exists
        if not (repo_path / ".git").exists():
            return ""

        # Run git diff
        result = subprocess.run(
            ["git", "diff"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        if result.returncode != 0:
            # Log error but don't crash
            print(f"[MergeManager] git diff failed: {result.stderr}")
            return ""

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        print("[MergeManager] git diff timed out after 30s")
        return ""
    except Exception as e:
        print(f"[MergeManager] Error computing diff: {e}")
        return ""


def summarize_diff_with_llm(
    run_id: str,
    repo_path: Path,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Summarize git diff using LLM analysis.

    Args:
        run_id: Current run ID for logging
        repo_path: Path to the repository
        context: Optional context dict (stage info, etc.)

    Returns:
        Dict with:
        - summary: Human-readable summary
        - files_touched: List of files modified
        - risks: List of potential risks
        - suggested_followups: List of suggested next steps
    """
    diff = compute_diff(repo_path)

    # If no diff, return empty summary
    if not diff:
        result = {
            "summary": "No changes detected",
            "impact": "none",
            "files_touched": [],
            "risks": [],
            "suggested_followups": [],
        }
        log_event(run_id, "merge_manager_diff_summary", result)
        return result

    # Truncate very long diffs for LLM (keep first 8000 chars)
    diff_for_llm = diff[:8000]
    if len(diff) > 8000:
        diff_for_llm += "\n\n... (diff truncated, too long for LLM)"

    # Build prompt for LLM
    system_prompt = """You are an expert code reviewer analyzing git diffs.

Your task:
1. Summarize the changes in 2-3 sentences
2. List the files touched
3. Identify potential risks (bugs, security, performance)
4. Suggest follow-up actions (tests, documentation, etc.)

Respond in JSON format ONLY:
{
  "summary": "Brief 2-3 sentence summary",
  "impact": "low|medium|high",
  "files_touched": ["file1.py", "file2.js"],
  "risks": ["Risk 1", "Risk 2"],
  "suggested_followups": ["Action 1", "Action 2"]
}"""

    user_content = f"Analyze this git diff:\n\n```diff\n{diff_for_llm}\n```"

    # Add context if provided
    if context:
        stage = context.get("stage_name", "")
        iteration = context.get("iteration", 0)
        if stage:
            user_content += f"\n\nContext: Stage '{stage}', Iteration {iteration}"

    try:
        # Call LLM
        response = chat_json(
            role="merge_manager",
            system_prompt=system_prompt,
            user_content=user_content,
            model="gpt-5-mini",  # Use cheaper model for diff analysis
            temperature=0.1,
            expect_json=True,
        )

        # Extract analysis (handle timeout case)
        if response.get("timeout"):
            result = {
                "summary": "LLM timeout - unable to analyze diff",
                "impact": "unknown",
                "files_touched": [],
                "risks": ["LLM analysis unavailable"],
                "suggested_followups": [],
            }
        else:
            # Use response directly (should have the structure we want)
            result = {
                "summary": response.get("summary", "No summary provided"),
                "impact": response.get("impact", "unknown"),
                "files_touched": response.get("files_touched", []),
                "risks": response.get("risks", []),
                "suggested_followups": response.get("suggested_followups", []),
            }

        # Log the result
        log_event(run_id, "merge_manager_diff_summary", result)
        return result

    except Exception as e:
        print(f"[MergeManager] Error in LLM analysis: {e}")
        result = {
            "summary": f"Error analyzing diff: {e}",
            "impact": "unknown",
            "files_touched": [],
            "risks": ["Analysis failed"],
            "suggested_followups": [],
        }
        log_event(run_id, "merge_manager_diff_summary", result)
        return result


def summarize_session(
    run_id: str,
    repo_path: Path,
    task: Optional[str] = None,
) -> Dict[str, str]:
    """
    Generate semantic commit message for the entire session.

    Args:
        run_id: Current run ID for logging
        repo_path: Path to the repository
        task: Optional task description for context

    Returns:
        Dict with:
        - title: Short commit title (50 chars max)
        - body: Longer commit body with details
    """
    diff = compute_diff(repo_path)

    # If no diff, return empty commit message
    if not diff:
        result = {
            "title": "No changes to commit",
            "body": "No modifications were made during this session.",
        }
        log_event(run_id, "semantic_commit_summary", result)
        return result

    # Truncate very long diffs for LLM
    diff_for_llm = diff[:8000]
    if len(diff) > 8000:
        diff_for_llm += "\n\n... (diff truncated)"

    # Build prompt for LLM
    system_prompt = """You are an expert at writing semantic git commit messages.

Your task:
1. Analyze the git diff
2. Generate a concise commit title (max 50 chars, imperative mood)
3. Write a detailed commit body explaining:
   - What changed and why
   - Key files/features affected
   - Tests run (if applicable)
   - Any breaking changes or important notes

Follow conventional commits style.

Respond in JSON format ONLY:
{
  "title": "feat: add user authentication system",
  "body": "- Implemented JWT-based auth\\n- Added login/logout endpoints\\n- Created User model\\n- Tests: All 15 auth tests passing"
}"""

    user_content = f"Generate a semantic commit message for these changes:\n\n```diff\n{diff_for_llm}\n```"

    if task:
        user_content += f"\n\nOriginal task: {task}"

    user_content += f"\n\nRun ID: {run_id}"

    try:
        # Call LLM
        response = chat_json(
            role="merge_manager",
            system_prompt=system_prompt,
            user_content=user_content,
            model="gpt-5-mini",  # Use cheaper model for commit messages
            temperature=0.2,
            expect_json=True,
        )

        # Extract commit message (handle timeout case)
        if response.get("timeout"):
            result = {
                "title": f"Auto-commit: {run_id[:8]}",
                "body": "Changes made during automated orchestrator run.\n\nLLM analysis unavailable due to timeout.",
            }
        else:
            result = {
                "title": response.get("title", f"Auto-commit: {run_id[:8]}")[:50],  # Enforce 50 char limit
                "body": response.get("body", "Changes made during automated orchestrator run."),
            }

        # Log the result
        log_event(run_id, "semantic_commit_summary", result)
        return result

    except Exception as e:
        print(f"[MergeManager] Error generating commit message: {e}")
        result = {
            "title": f"Auto-commit: {run_id[:8]}",
            "body": f"Changes made during automated orchestrator run.\n\nError: {e}",
        }
        log_event(run_id, "semantic_commit_summary", result)
        return result


def make_commit(
    repo_path: Path,
    title: str,
    body: str,
) -> bool:
    """
    Create a git commit with the given title and body.

    Args:
        repo_path: Path to the repository
        title: Commit title (first line)
        body: Commit body (details)

    Returns:
        True if commit succeeded, False otherwise
    """
    try:
        repo_path = Path(repo_path)

        # Check if .git exists
        if not (repo_path / ".git").exists():
            print(f"[MergeManager] No git repo at {repo_path}")
            return False

        # Stage all changes
        add_result = subprocess.run(
            ["git", "add", "."],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        if add_result.returncode != 0:
            print(f"[MergeManager] git add failed: {add_result.stderr}")
            return False

        # Build commit message (title + blank line + body)
        commit_message = f"{title}\n\n{body}"

        # Create commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        output = (commit_result.stderr or commit_result.stdout or "").lower()

        # Check if nothing to commit
        if commit_result.returncode != 0:
            if "nothing to commit" in output:
                print("[MergeManager] Nothing to commit (working tree clean)")
                return False
            print(f"[MergeManager] git commit failed: {commit_result.stderr}")
            return False

        print(f"[MergeManager] Created commit: {title}")
        return True

    except subprocess.TimeoutExpired:
        print("[MergeManager] git commit timed out after 30s")
        return False
    except Exception as e:
        print(f"[MergeManager] Error creating commit: {e}")
        return False
