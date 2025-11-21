# llm.py
from __future__ import annotations

import json
import os
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
            "manager": os.getenv("DEFAULT_MANAGER_MODEL", "gpt-5-mini-2025-08-07"),
            "supervisor": os.getenv("DEFAULT_SUPERVISOR_MODEL", "gpt-5-nano"),
            "employee": os.getenv("DEFAULT_EMPLOYEE_MODEL", "gpt-5-2025-08-07"),
        }


# Cache default models at module load
_DEFAULT_MODELS = _get_default_models()
DEFAULT_MANAGER_MODEL = _DEFAULT_MODELS["manager"]
DEFAULT_SUPERVISOR_MODEL = _DEFAULT_MODELS["supervisor"]
DEFAULT_EMPLOYEE_MODEL = _DEFAULT_MODELS["employee"]


def _post(payload: dict) -> dict:
    """
    Low-level helper to call the OpenAI Chat Completions endpoint.

    - PHASE 3 (future): Checks for simulation mode and returns stub if enabled
    - Retries up to 3 times.
    - On success: returns the full JSON response.
    - On repeated failure: returns a *stub* dict with `timeout=True`
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
    is_timeout = False

    for attempt in range(1, 4):
        try:
            resp = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=180,
            )

            # If the API returns an HTTP error, show the body so we can debug.
            # PHASE 1.2: Sanitize error body to prevent API key leakage
            if resp.status_code != 200:
                print("=== OpenAI error body ===")
                sanitized_error = log_sanitizer.sanitize_error_message(resp.text)
                print(sanitized_error)
                resp.raise_for_status()

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
            # PHASE 1.2: Sanitize exception message to prevent sensitive data leakage
            sanitized_exc_msg = log_sanitizer.sanitize_error_message(str(exc))
            print(
                f"[LLM] HTTP/connection error on attempt {attempt}/3: {sanitized_exc_msg}. "
                "Retrying..." if attempt < 3 else "[LLM] Giving up after 3 failed attempts."
            )

    # If we get here, all retries failed. Return a stub object with the
    # shape our orchestrator expects, so it won't crash.
    reason = str(last_error) if last_error is not None else "Unknown error"
    # PHASE 1.2: Sanitize reason to prevent sensitive data in return values
    sanitized_reason = log_sanitizer.sanitize_error_message(reason)

    return {
        "timeout": True,
        "is_timeout": is_timeout,  # PHASE 4.3 (R3): Flag for fallback logic
        "reason": sanitized_reason,
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
    # STAGE 5: New parameters for model routing
    task_type: Optional[str] = None,
    complexity: Optional[str] = None,
    interaction_index: int = 1,
    is_very_important: bool = False,
    run_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    # STAGE 5.2: Cost cap enforcement
    max_cost_usd: float = 0.0,
) -> Dict[str, Any]:
    """
    High-level helper that:
    - Selects a model (manager / supervisor / employee) if not provided.
    - Uses intelligent routing (Stage 5) when task_type is provided.
    - Calls `_post` and records usage via `cost_tracker`.
    - Returns parsed JSON (default) or raw text if `expect_json=False`.

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
            if "gpt-5-pro" in chosen_model or "gpt-5-2025" in chosen_model or "gpt-5" in chosen_model:
                fallback_model = "gpt-5-mini-2025-08-07"
            elif "gpt-5-mini" in chosen_model:
                fallback_model = "gpt-5-nano"
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

    # SAFE FALLBACK: If _post() returned a stub due to timeout/error,
    # return a minimal safe dict instead of crashing the orchestrator.
    if data.get("timeout"):
        print(f"[LLM] Detected timeout stub from _post(). Reason: {data.get('reason', 'unknown')}")
        return {
            "plan": [],
            "notes": f"LLM failure — safe stub returned. Reason: {data.get('reason', 'unknown')}",
            "status": "timeout",
            "files": {},
            "acceptance_criteria": [],
            "phases": [],
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
