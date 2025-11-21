# llm.py
from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

import core_logging
import cost_tracker
import log_sanitizer  # PHASE 1.2: Sanitize error messages
from model_router import choose_model as router_choose_model

# PHASE 5.2: LLM response caching for cost reduction
try:
    from llm_cache import get_llm_cache
    LLM_CACHE_AVAILABLE = True
except ImportError:
    LLM_CACHE_AVAILABLE = False

# PHASE 0.3: Import config module for centralized defaults
try:
    import config as config_module
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# OpenAI Chat Completions endpoint
OPENAI_URL = "https://api.openai.com/v1/chat/completions"


def _sanitize_json_escapes(content: str) -> str:
    """
    Sanitize invalid JSON escape sequences from LLM responses.

    LLMs sometimes generate invalid escape sequences like \\@ (for @media in CSS)
    which are not valid JSON escapes. This function fixes them by:
    1. Identifying invalid escape sequences (e.g., \\@, \\#, \\!, etc.)
    2. Removing the backslash before characters that don't need escaping

    Valid JSON escapes are: \" \\\\ \\/ \\b \\f \\n \\r \\t \\uXXXX

    Args:
        content: The raw LLM response content

    Returns:
        Sanitized content with valid JSON escape sequences
    """
    # Valid JSON escape characters after backslash
    valid_escapes = set('"\\bfnrtu/')

    result = []
    i = 0
    while i < len(content):
        if content[i] == '\\' and i + 1 < len(content):
            next_char = content[i + 1]
            # Check if this is a valid escape sequence
            if next_char in valid_escapes:
                # Valid escape, keep as-is
                result.append(content[i])
                result.append(next_char)
                i += 2
            else:
                # Invalid escape like \@ - remove the backslash
                # Just skip the backslash, keep the next character
                result.append(next_char)
                i += 2
        else:
            result.append(content[i])
            i += 1

    return ''.join(result)


def _get_default_models() -> Dict[str, str]:
    """
    PHASE 0.3: Get default models from config.py if available, else from environment variables.

    Returns:
        Dict with keys: manager, supervisor, employee
    """
    if CONFIG_AVAILABLE:
        cfg = config_module.get_config()
        return {
            "manager": cfg.models.manager,
            "supervisor": cfg.models.supervisor,
            "employee": cfg.models.employee,
        }
    else:
        # Legacy: Read from environment variables
        return {
            "manager": os.getenv("DEFAULT_MANAGER_MODEL", "gpt-4o-mini"),
            "supervisor": os.getenv("DEFAULT_SUPERVISOR_MODEL", "gpt-4o-mini"),
            "employee": os.getenv("DEFAULT_EMPLOYEE_MODEL", "gpt-4o-mini"),
        }


# Cache default models at module load
_DEFAULT_MODELS = _get_default_models()
DEFAULT_MANAGER_MODEL = _DEFAULT_MODELS["manager"]
DEFAULT_SUPERVISOR_MODEL = _DEFAULT_MODELS["supervisor"]
DEFAULT_EMPLOYEE_MODEL = _DEFAULT_MODELS["employee"]


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
    # PHASE 3 (infrastructure): Check for simulation mode
    if CONFIG_AVAILABLE:
        cfg = config_module.get_config()
        if cfg.simulation.value != "off":
            # Simulation mode enabled - return stub response without API call
            print(f"[LLM] Simulation mode ({cfg.simulation.value}) - returning stub response")
            return {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "plan": ["Simulated plan step 1", "Simulated plan step 2"],
                            "acceptance_criteria": ["Simulated criterion 1"],
                            "phases": [{"name": "Simulated phase", "categories": ["layout_structure"]}],
                            "files": {"index.html": "<html><body>Simulated content</body></html>"},
                            "status": "approved",
                            "feedback": [],
                            "notes": "This is a simulated response for testing",
                        })
                    }
                }],
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                },
                "simulated": True,
            }

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
            # PHASE 1.2: Sanitize error body to prevent API key leakage
            if resp.status_code != 200:
                print("=== OpenAI error body ===")
                sanitized_error = log_sanitizer.sanitize_error_message(resp.text)
                print(sanitized_error)
                resp.raise_for_status()

            # Success!
            return resp.json()

        except requests.exceptions.Timeout as exc:
            # PHASE 4.3 (R3): Track timeout explicitly for fallback logic
            last_error = exc
            is_timeout = True
            sanitized_exc_msg = log_sanitizer.sanitize_error_message(str(exc))
            print(
                f"[LLM] Timeout on attempt {attempt}/3: {sanitized_exc_msg}. "
                "Retrying..." if attempt < 3 else "[LLM] Giving up after 3 timeouts."
            )

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
    # PHASE 1.2: Sanitize reason to prevent sensitive data in return values
    sanitized_reason = log_sanitizer.sanitize_error_message(reason)

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
    # STAGE 5: Intelligent routing parameters
    task_type: Optional[str] = None,
    complexity: Optional[str] = None,
    interaction_index: int = 0,
    is_very_important: bool = False,
    config: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
    # STAGE 5.2: Cost cap enforcement
    max_cost_usd: float = 0.0,
) -> Dict[str, Any]:
    """
    High-level helper that:
    - Selects a model (manager / supervisor / employee) if not provided.
    - Uses intelligent routing (Stage 5) when task_type is provided.
    - Calls `_post` and records usage via `cost_tracker`.
    - Returns parsed JSON (default) or raw text if `expect_json=False`.
    - STAGE 3.3: On failure, retries with fallback model if configured.

    `system_prompt` is the original parameter name.
    `system` is an alias used by some callers (e.g. code_review_bot).
    If both are provided, `system` wins.

    STAGE 5 Model Routing:
    - If `model` is explicitly provided, use it (bypass router)
    - If `task_type` is provided, use intelligent routing
    - Otherwise, fall back to legacy role-based selection

    STAGE 5.2 Cost Cap Enforcement:
    - If `max_cost_usd` > 0, checks before making LLM call
    - Returns error stub if cost would be exceeded
    """
    if model is None:
        # STAGE 5: Use intelligent routing if task_type provided
        if task_type is not None:
            # Infer task_type from role if not provided
            effective_task_type = task_type
            effective_complexity = complexity or "low"

            chosen_model = router_choose_model(
                task_type=effective_task_type,
                complexity=effective_complexity,
                role=role,
                interaction_index=interaction_index,
                is_very_important=is_very_important,
                config=config,
            )

            # Log model selection
            if run_id:
                core_logging.log_event(run_id, "model_selected", {
                    "role": role,
                    "task_type": effective_task_type,
                    "complexity": effective_complexity,
                    "interaction_index": interaction_index,
                    "is_very_important": is_very_important,
                    "model_chosen": chosen_model,
                })
        else:
            # Legacy role-based selection
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

    # PHASE 5.2: LLM Response Caching - Check cache before API call
    cache_key = None
    cached_response = None
    estimated_cost = 0.0

    if LLM_CACHE_AVAILABLE:
        try:
            cache = get_llm_cache()

            # Generate cache key
            cache_key = cache.generate_key(
                role=role,
                system_prompt=effective_system,
                user_content=user_content,
                model=chosen_model,
                temperature=temperature,
            )

            # Estimate cost for cache hit tracking
            prompt_chars = len(effective_system) + len(user_content)
            estimated_tokens = (prompt_chars // 4) + 2000
            price_cfg = cost_tracker._get_pricing_fallback(chosen_model)
            estimated_cost = estimated_tokens * price_cfg["output"]  # Conservative estimate

            # Check cache
            cached_response = cache.get(cache_key, estimated_cost=estimated_cost)

            if cached_response:
                print(f"[LLMCache] Cache HIT - Saved ~${estimated_cost:.4f}")
                if run_id:
                    core_logging.log_event(run_id, "llm_cache_hit", {
                        "role": role,
                        "model": chosen_model,
                        "cost_saved_usd": estimated_cost,
                    })
                return cached_response

        except Exception as e:
            print(f"[LLMCache] Cache lookup error (will proceed with API call): {e}")

    # STAGE 5.2: Check cost cap before making the call
    if max_cost_usd > 0:
        # Estimate prompt size (rough heuristic: 4 chars per token)
        prompt_chars = len(effective_system) + len(user_content)
        estimated_tokens = (prompt_chars // 4) + 2000  # Add buffer for output

        would_exceed, current_cost, cap_message = cost_tracker.check_cost_cap(
            max_cost_usd=max_cost_usd,
            estimated_tokens=estimated_tokens,
            model=chosen_model,
        )

        if would_exceed:
            print(f"[CostCap] {cap_message}")
            print("[CostCap] Aborting LLM call to stay within budget.")

            # Return a stub indicating cost cap was hit
            return {
                "plan": [],
                "notes": f"LLM call skipped: cost cap would be exceeded. {cap_message}",
                "status": "cost_cap_exceeded",
                "files": {},
                "acceptance_criteria": [],
                "phases": [],
                "cost_cap_hit": True,
                "current_cost_usd": current_cost,
                "max_cost_usd": max_cost_usd,
            }

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

    # PHASE 4.3 (R3): LLM Timeout Fallback to Cheaper Model
    # If the primary model times out, try once with a cheaper/faster model
    if data.get("timeout") and data.get("is_timeout"):
        # Get fallback model from config or use hardcoded fallback
        fallback_model = None
        if CONFIG_AVAILABLE:
            cfg = config_module.get_config()
            fallback_model = cfg.models.llm_fallback_model if hasattr(cfg.models, 'llm_fallback_model') else None

        # Default fallback: use cheaper model based on role
        if not fallback_model:
            if "gpt-4o" in chosen_model and "mini" not in chosen_model:
                fallback_model = "gpt-4o-mini"
            elif "gpt-4" in chosen_model:
                fallback_model = "gpt-3.5-turbo"
            else:
                fallback_model = None  # Already using cheapest model

        if fallback_model and fallback_model != chosen_model:
            print(f"[LLM] Timeout detected - retrying with fallback model: {fallback_model}")

            # Log fallback attempt
            if run_id:
                core_logging.log_event(run_id, "llm_fallback", {
                    "original_model": chosen_model,
                    "fallback_model": fallback_model,
                    "reason": "timeout",
                })

            # Retry with fallback model
            fallback_payload = payload.copy()
            fallback_payload["model"] = fallback_model
            data = _post(fallback_payload)
            chosen_model = fallback_model  # Update for cost tracking

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
        print("[LLM] ⚠️  DETECTED LLM FAILURE STUB from _post()")
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
        parsed_response = json.loads(content)

        # PHASE 5.2: Store successful response in cache
        if LLM_CACHE_AVAILABLE and cache_key:
            try:
                cache = get_llm_cache()
                cache.set(cache_key, parsed_response)
            except Exception as e:
                print(f"[LLMCache] Cache storage error: {e}")

        return parsed_response

    except json.JSONDecodeError as e:  # pragma: no cover
        # Attempt to fix common invalid escape sequences (e.g., \@ in CSS @media)
        # This is a common issue with LLMs generating invalid JSON escapes
        try:
            sanitized_content = _sanitize_json_escapes(content)
            parsed_response = json.loads(sanitized_content)
            print(f"[LLM] Warning: Fixed invalid JSON escape sequences in {role} response")

            # PHASE 5.2: Store sanitized response in cache
            if LLM_CACHE_AVAILABLE and cache_key:
                try:
                    cache = get_llm_cache()
                    cache.set(cache_key, parsed_response)
                except Exception as cache_e:
                    print(f"[LLMCache] Cache storage error: {cache_e}")

            return parsed_response

        except json.JSONDecodeError:
            # If sanitization didn't help, raise the original error
            raise RuntimeError(
                "Model response was not valid JSON.\n"
                f"Role: {role}\n"
                f"Model: {chosen_model}\n"
                f"Content:\n{content}"
            ) from e


def chat(
    role: str = "employee",
    system_prompt: Optional[str] = None,
    user_content: str = "",
    *,
    system: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    **kwargs
) -> str:
    """
    PHASE 7.1: Simple text chat wrapper around chat_json.

    Returns plain text response instead of JSON.
    Useful for conversational interactions where JSON parsing is not needed.

    Args:
        role: Agent role (manager, supervisor, employee)
        system_prompt: System message
        user_content: User message
        system: Alternative system message parameter
        model: Optional model override
        temperature: Sampling temperature (default 0.7 for conversations)
        **kwargs: Additional parameters passed to chat_json

    Returns:
        Plain text response from LLM
    """
    # Call chat_json with expect_json=False
    response = chat_json(
        role=role,
        system_prompt=system_prompt,
        user_content=user_content,
        system=system,
        model=model,
        temperature=temperature,
        expect_json=False,
        **kwargs
    )

    # Extract raw text from response
    return response.get("raw", "")
