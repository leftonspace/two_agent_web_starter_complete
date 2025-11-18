# llm.py
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import requests

import cost_tracker

# OpenAI Chat Completions endpoint
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Default model labels – can be overridden via env vars.
DEFAULT_MANAGER_MODEL = os.getenv("DEFAULT_MANAGER_MODEL", "gpt-5-mini-2025-08-07")
DEFAULT_SUPERVISOR_MODEL = os.getenv("DEFAULT_SUPERVISOR_MODEL", "gpt-5-nano")
DEFAULT_EMPLOYEE_MODEL = os.getenv("DEFAULT_EMPLOYEE_MODEL", "gpt-5-2025-08-07")


def _post(payload: dict) -> dict:
    """
    Low-level helper to call the OpenAI Chat Completions endpoint.

    - Retries up to 3 times.
    - On success: returns the full JSON response.
    - On repeated failure: returns a *stub* dict with `timeout=True`
      instead of raising, so the caller can handle it gracefully.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None

    for attempt in range(1, 4):
        try:
            resp = requests.post(
                OPENAI_URL,
                headers=headers,
                json=payload,
                timeout=180,
            )

            # If the API returns an HTTP error, show the body so we can debug.
            if resp.status_code != 200:
                print("=== OpenAI error body ===")
                print(resp.text)
                resp.raise_for_status()

            return resp.json()

        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(
                f"[LLM] HTTP/connection error on attempt {attempt}/3: {exc}. "
                "Retrying..." if attempt < 3 else "[LLM] Giving up after 3 failed attempts."
            )

    # If we get here, all retries failed. Return a stub object with the
    # shape our orchestrator expects, so it won't crash.
    reason = str(last_error) if last_error is not None else "Unknown error"

    return {
        "timeout": True,
        "reason": reason,
        "plan": [],
        "acceptance_criteria": [],
        "phases": [],
        # IMPORTANT: must be a dict, not a list, so the orchestrator's
        # `files_dict = emp.get("files", {})` + `isinstance(files_dict, dict)` checks
        # do not explode.
        "files": {},
        "notes": "Step skipped due to upstream API error. "
        "Safe stub returned by llm._post.",
        "analysis": {"status": "timeout"},
        "status": "timeout",
    }


def chat_json(
    role: str,
    system_prompt: Optional[str] = None,
    user_content: str = "",
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.2,
    expect_json: bool = True,
) -> Dict[str, Any]:
    """
    High-level helper that:
    - Selects a model (manager / supervisor / employee) if not provided.
    - Calls `_post` and records usage via `cost_tracker`.
    - Returns parsed JSON (default) or raw text if `expect_json=False`.

    `system_prompt` is the original parameter name.
    `system` is an alias used by some callers (e.g. code_review_bot).
    If both are provided, `system` wins.
    """
    if model is None:
        if role == "manager":
            chosen_model = DEFAULT_MANAGER_MODEL
        elif role == "supervisor":
            chosen_model = DEFAULT_SUPERVISOR_MODEL
        else:
            chosen_model = DEFAULT_EMPLOYEE_MODEL
    else:
        chosen_model = model

    # Choose which system message to use
    effective_system = system if system is not None else (system_prompt or "")

    messages = [
        {"role": "system", "content": effective_system},
        {"role": "user", "content": user_content},
    ]

    payload: Dict[str, Any] = {
        "model": chosen_model,
        "messages": messages,
        "temperature": temperature,
    }

    data = _post(payload)

    # Cost tracking – best-effort, non-fatal on failure.
    try:
        usage = data.get("usage")
        if usage:
            prompt_tokens = int(usage.get("prompt_tokens", 0))
            completion_tokens = int(usage.get("completion_tokens", 0))

            # Register this call in the in-memory cost state.
            cost_tracker.register_call(
                role=role,
                model=chosen_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

            # Optional: persist a simple history record to disk.
            cost_tracker.append_history(
                total_usd=cost_tracker.get_total_cost_usd(),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model=chosen_model,
            )

    except Exception as e:  # noqa: BLE001
        print(f"[CostTracker] Failed to record usage: {e}")

    # If caller wants raw text, don't try to parse it.
    if not data.get("choices"):
        if expect_json:
            raise RuntimeError("Model returned no choices; cannot parse JSON.")
        return {"raw": ""}

    content = data["choices"][0]["message"]["content"]

    if not expect_json:
        return {"raw": content}

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:  # pragma: no cover
        raise RuntimeError(
            "Model response was not valid JSON.\n"
            f"Role: {role}\n"
            f"Model: {chosen_model}\n"
            f"Content:\n{content}"
        ) from e
