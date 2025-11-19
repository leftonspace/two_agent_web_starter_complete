# llm.py
from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

import cost_tracker

# OpenAI Chat Completions endpoint
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# Default model labels – can be overridden via env vars.
DEFAULT_MANAGER_MODEL = os.getenv("DEFAULT_MANAGER_MODEL", "gpt-5-mini-2025-08-07")
DEFAULT_SUPERVISOR_MODEL = os.getenv("DEFAULT_SUPERVISOR_MODEL", "gpt-5-nano")
DEFAULT_EMPLOYEE_MODEL = os.getenv("DEFAULT_EMPLOYEE_MODEL", "gpt-5-2025-08-07")


# STAGE 3.3: Load LLM resilience config from project_config.json
def _load_llm_config() -> Dict[str, Any]:
    """
    Load LLM resilience configuration from project_config.json.

    STAGE 3.3: Reads config values with fallback to environment variables
    and hardcoded defaults.

    Returns:
        Dict with max_retries, timeout_seconds, initial_backoff, max_backoff, fallback_model
    """
    config_path = Path(__file__).resolve().parent / "project_config.json"

    # Default values (fallback)
    defaults = {
        "max_retries": 5,
        "timeout_seconds": 180,
        "initial_backoff": 2.0,
        "max_backoff": 60.0,
        "fallback_model": None,
    }

    try:
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                cfg = json.load(f)
                llm_resilience = cfg.get("llm_resilience", {})

                return {
                    "max_retries": llm_resilience.get("max_retries", defaults["max_retries"]),
                    "timeout_seconds": llm_resilience.get("timeout_seconds", defaults["timeout_seconds"]),
                    "initial_backoff": llm_resilience.get("initial_backoff", defaults["initial_backoff"]),
                    "max_backoff": llm_resilience.get("max_backoff", defaults["max_backoff"]),
                    "fallback_model": llm_resilience.get("fallback_model", defaults["fallback_model"]),
                }
    except Exception as e:
        print(f"[LLM] Warning: Failed to load config from {config_path}: {e}")
        print("[LLM] Using default configuration")

    # Return defaults if config file not found or failed to load
    return defaults


# Load config at module level (cached)
_llm_config = _load_llm_config()

# STAGE 3.3: Retry and timeout configuration (from config or env vars)
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", str(_llm_config["max_retries"])))
REQUEST_TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECONDS", str(_llm_config["timeout_seconds"])))
INITIAL_BACKOFF = float(os.getenv("LLM_INITIAL_BACKOFF", str(_llm_config["initial_backoff"])))
MAX_BACKOFF = float(os.getenv("LLM_MAX_BACKOFF", str(_llm_config["max_backoff"])))
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", _llm_config.get("fallback_model") or "")


def validate_api_connectivity() -> tuple[bool, Optional[str]]:
    """
    STAGE 3.3: Validate OpenAI API connectivity before starting work.

    Returns:
        (is_valid, error_message): True if API is accessible, False otherwise.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, "OPENAI_API_KEY environment variable is not set"

    if api_key.startswith("sk-") and len(api_key) < 20:
        return False, "OPENAI_API_KEY appears to be invalid (too short)"

    # Try a minimal API call to verify connectivity
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Use a very simple prompt to test connectivity
        test_payload = {
            "model": "gpt-3.5-turbo",  # Use cheapest model for validation
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5,
        }

        resp = requests.post(
            OPENAI_URL,
            headers=headers,
            json=test_payload,
            timeout=30,  # Short timeout for validation
        )

        if resp.status_code == 200:
            return True, None
        elif resp.status_code == 401:
            return False, "Invalid API key (401 Unauthorized)"
        elif resp.status_code == 429:
            return False, "Rate limit exceeded (429). Wait and retry later"
        elif resp.status_code == 503:
            return False, "OpenAI service unavailable (503). Try again later"
        else:
            return False, f"API returned HTTP {resp.status_code}: {resp.text[:200]}"

    except requests.exceptions.Timeout:
        return False, "Connection timeout - cannot reach api.openai.com"
    except requests.exceptions.ConnectionError as e:
        return False, f"Network error - cannot connect to OpenAI API: {e}"
    except Exception as e:
        return False, f"Unexpected error during API validation: {e}"


def _post(payload: dict) -> dict:
    """
    Low-level helper to call the OpenAI Chat Completions endpoint.

    STAGE 3.3 improvements:
    - Retries up to MAX_RETRIES times (default 5, configurable via LLM_MAX_RETRIES)
    - Implements exponential backoff with jitter to avoid thundering herd
    - Configurable timeout via LLM_TIMEOUT_SECONDS
    - On success: returns the full JSON response.
    - On repeated failure: returns a *stub* dict with `llm_failure=True`
      instead of raising, so the caller can handle it gracefully.
    """
    # Ensure OPENAI_URL is always in scope (defensive coding)
    api_url = OPENAI_URL

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    last_status_code: Optional[int] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            last_status_code = resp.status_code

            # If the API returns an HTTP error, show the body so we can debug.
            if resp.status_code != 200:
                error_body = resp.text[:500]  # Limit error body length
                print(f"[LLM] OpenAI API error (HTTP {resp.status_code})")
                print(f"[LLM] Error body (truncated): {error_body}")

                # Don't retry on authentication errors (will always fail)
                if resp.status_code == 401:
                    print("[LLM] Authentication error - check your OPENAI_API_KEY")
                    raise RuntimeError("Invalid API key (401 Unauthorized)")

                resp.raise_for_status()

            # Success!
            return resp.json()

        except Exception as exc:  # noqa: BLE001
            last_error = exc

            # Determine if we should retry
            is_last_attempt = (attempt >= MAX_RETRIES)

            # Calculate backoff with exponential increase and jitter
            if not is_last_attempt:
                # Exponential backoff: 2, 4, 8, 16... seconds (capped at MAX_BACKOFF)
                base_delay = min(INITIAL_BACKOFF * (2 ** (attempt - 1)), MAX_BACKOFF)
                # Add jitter: random value between 0 and base_delay
                jitter = random.uniform(0, base_delay * 0.5)
                delay = base_delay + jitter

                print(
                    f"[LLM] HTTP/connection error on attempt {attempt}/{MAX_RETRIES}: {exc}"
                )
                print(f"[LLM] Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
            else:
                print(
                    f"[LLM] HTTP/connection error on attempt {attempt}/{MAX_RETRIES}: {exc}"
                )
                print(f"[LLM] Giving up after {MAX_RETRIES} failed attempts.")

    # If we get here, all retries failed. Return a stub object with the
    # shape our orchestrator expects, so it won't crash.
    reason = str(last_error) if last_error is not None else "Unknown error"

    if last_status_code:
        reason = f"HTTP {last_status_code}: {reason}"

    print("[LLM] ⚠️  RETURNING STUB RESPONSE - ALL API CALLS FAILED")
    print(f"[LLM] Failure reason: {reason}")

    return {
        "llm_failure": True,  # STAGE 3.3: Changed from "timeout" to be more explicit
        "timeout": True,  # Keep for backward compatibility
        "reason": reason,
        "plan": [],
        "acceptance_criteria": [],
        "phases": [],
        # IMPORTANT: must be a dict, not a list, so the orchestrator's
        # `files_dict = emp.get("files", {})` + `isinstance(files_dict, dict)` checks
        # do not explode.
        "files": {},
        "notes": f"⚠️  LLM API FAILURE - This is a stub response. Reason: {reason}",
        "analysis": {"status": "llm_failure", "reason": reason},
        "status": "llm_failure",
        "findings": [],  # STAGE 3.3: Add empty findings to prevent auto-advance on failures
    }


def chat_json(
    role: str,
    system_prompt: Optional[str] = None,
    user_content: str = "",
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,  # <-- changed: now Optional and default None
    expect_json: bool = True,
    _fallback_attempt: bool = False,  # STAGE 3.3: Internal flag for fallback retry
) -> Dict[str, Any]:
    """
    High-level helper that:
    - Selects a model (manager / supervisor / employee) if not provided.
    - Calls `_post` and records usage via `cost_tracker`.
    - Returns parsed JSON (default) or raw text if `expect_json=False`.
    - STAGE 3.3: On failure, retries with fallback model if configured.

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

    # STAGE 3.3: Store original model for fallback logic
    original_model = chosen_model

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

    # STAGE 3.3: SAFE FALLBACK - If _post() returned a stub due to timeout/error,
    # try fallback model if configured and not already tried.
    # The stub now includes llm_failure=True to help orchestrator detect issues.
    if data.get("llm_failure") or data.get("timeout"):
        reason = data.get('reason', 'unknown')
        print(f"[LLM] ⚠️  DETECTED LLM FAILURE STUB from _post()")
        print(f"[LLM] Role: {role}, Model: {chosen_model}, Reason: {reason}")

        # STAGE 3.3: Try fallback model if configured and not already tried
        if FALLBACK_MODEL and not _fallback_attempt and chosen_model != FALLBACK_MODEL:
            print(f"[LLM] 🔄 ATTEMPTING FALLBACK to model: {FALLBACK_MODEL}")
            print(f"[LLM] Original model '{chosen_model}' failed, trying fallback...")

            # Recursive call with fallback model
            try:
                fallback_result = chat_json(
                    role=role,
                    system_prompt=system_prompt,
                    user_content=user_content,
                    system=system,
                    model=FALLBACK_MODEL,  # Force fallback model
                    temperature=temperature,
                    expect_json=expect_json,
                    _fallback_attempt=True,  # Prevent infinite fallback loop
                )

                # If fallback succeeded, add metadata and return
                if not fallback_result.get("llm_failure"):
                    print(f"[LLM] ✅ FALLBACK SUCCEEDED with model: {FALLBACK_MODEL}")
                    fallback_result["_fallback_used"] = True
                    fallback_result["_original_model"] = original_model
                    fallback_result["_fallback_model"] = FALLBACK_MODEL
                    return fallback_result
                else:
                    print(f"[LLM] ❌ FALLBACK ALSO FAILED with model: {FALLBACK_MODEL}")
                    # Fall through to return failure
            except Exception as fallback_error:
                print(f"[LLM] ❌ FALLBACK EXCEPTION: {fallback_error}")
                # Fall through to return failure

        print("[LLM] This stage will produce no meaningful output.")

        return {
            "llm_failure": True,
            "plan": [],
            "notes": f"⚠️  LLM API FAILURE ({role}) - Safe stub returned. Reason: {reason}",
            "status": "llm_failure",
            "files": {},
            "acceptance_criteria": [],
            "phases": [],
            "findings": [],  # Return empty findings but mark as failure
            "reason": reason,
            "original_model": original_model,  # Track which model failed
        }

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
