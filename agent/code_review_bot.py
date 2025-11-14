"""
Simple local "code review bot" for your agent project.

- Runs Ruff (lint) and MyPy (types) on the agent folder.
- Optionally asks an LLM to summarize the findings if USE_AI_CODE_REVIEW=1.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List

import llm  # your existing module

BASE_DIR = Path(__file__).resolve().parent


def _run_cmd(cmd: List[str]) -> str:
    """Run a subprocess and return combined stdout/stderr as a string."""
    try:
        result = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return result.stdout
    except Exception as e:
        return f"[code_review_bot] Failed to run {cmd!r}: {e}"


def run_static_checks() -> dict:
    """Run Ruff + MyPy and return their raw outputs."""

    print("[code_review_bot] Running Ruff (lint)...")
    ruff_output = _run_cmd(["ruff", "check", "."])

    print("[code_review_bot] Running MyPy (type checking)...")
    mypy_output = _run_cmd(["mypy", "."])

    print("\n===== Ruff output =====")
    print(ruff_output or "(no output)")

    print("\n===== MyPy output =====")
    print(mypy_output or "(no output)")

    return {
        "ruff": ruff_output,
        "mypy": mypy_output,
    }


def ask_ai_for_review(outputs: dict) -> None:
    """Optionally ask the LLM to summarize lint/type issues and suggest fixes."""
    if not os.getenv("OPENAI_API_KEY"):
        print("[code_review_bot] OPENAI_API_KEY not set; skipping AI review.")
        return

    # Concise system prompt for the reviewer
    system_prompt = (
        "You are a senior Python reviewer for a multi-agent dev tool.\n"
        "You are given the outputs of static analysis tools (Ruff + MyPy).\n"
        "Goal: summarize the most important issues and give short, actionable suggestions.\n"
        "Focus on correctness, clarity, and maintainability. Be brief and practical."
    )

    # User content = tool outputs (truncated if huge)
    combined = (
        "Ruff output:\n"
        + outputs.get("ruff", "")
        + "\n\nMyPy output:\n"
        + outputs.get("mypy", "")
    )

    # Hard safety guard: don't send absurdly huge payloads
    if len(combined) > 40_000:
        combined = combined[:40_000] + "\n\n[Truncated output due to length.]"

    print("\n[code_review_bot] Asking AI for a short review (if allowed by your config)...\n")

    # We reuse your existing chat_json helper.
    # Reviewer role is "manager" but you could create a dedicated "reviewer" role if you like.
    review = llm.chat_json(
        role="manager",
        system=system_prompt,
        user_content=combined,
        expect_json=False,  # we just want plain text feedback
    )

    print("===== AI Review =====")
    print(review)


def main() -> None:
    outputs = run_static_checks()

    use_ai = os.getenv("USE_AI_CODE_REVIEW", "0")
    if use_ai == "1":
        ask_ai_for_review(outputs)
    else:
        print(
            "\n[code_review_bot] Static checks done. "
            "Set USE_AI_CODE_REVIEW=1 to get an AI summary of issues."
        )


if __name__ == "__main__":
    main()
