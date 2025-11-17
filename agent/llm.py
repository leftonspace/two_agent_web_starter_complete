# llm.py
import json
import os
from typing import Optional

import requests

import cost_tracker

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE = os.getenv("OPENAI_BASE", "https://api.openai.com/v1")

# Default models per role (can be overridden by env vars)
DEFAULT_MANAGER_MODEL = os.getenv("OPENAI_MODEL_MANAGER", "gpt-5-mini")
DEFAULT_SUPERVISOR_MODEL = os.getenv("OPENAI_MODEL_SUPERVISOR", "gpt-5-nano")
DEFAULT_EMPLOYEE_MODEL = os.getenv("OPENAI_MODEL_EMPLOYEE", "gpt-5")


def _post(payload: dict) -> dict:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment.")

    url = f"{OPENAI_BASE}/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None

    # Try up to 3 times on transient network issues / timeouts
    for attempt in range(1, 4):
        try:
            print(f"[LLM] POST attempt {attempt}/3 to {url} (model={payload.get('model')})")
            r = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=180,  # 3 minutes per attempt
            )
            if r.status_code >= 400:
                try:
                    body = r.json()
                except Exception:
                    body = r.text
                raise RuntimeError(
                    f"API error: {r.status_code}\n"
                    f"Response body: {json.dumps(body, indent=2) if isinstance(body, dict) else body}"
                )

            try:
                return r.json()
            except Exception as e:
                raise RuntimeError(f"Failed to parse JSON from OpenAI response: {e}") from e

        except requests.exceptions.ReadTimeout as e:
            last_error = e
            print(f"[LLM] Read timeout on attempt {attempt}/3. Retrying...")
            continue
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error talking to OpenAI API: {e}") from e

    raise RuntimeError(f"Error talking to OpenAI API after 3 attempts: {last_error}")


def chat_json(role: str, system: str, user_content: str, model: Optional[str] = None, expect_json: bool = True) -> dict:
    """
    Call the OpenAI Chat Completion API and parse a STRICT JSON reply.

    role: 'manager', 'supervisor', or 'employee'
    system: system prompt
    user_content: user message (we expect the model to respond with JSON)
    model: optional override model name
    """
    role_lower = (role or "unknown").lower()

    if model is None:
        if role_lower == "manager":
            model = DEFAULT_MANAGER_MODEL
        elif role_lower == "supervisor":
            model = DEFAULT_SUPERVISOR_MODEL
        else:
            model = DEFAULT_EMPLOYEE_MODEL

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        # No temperature override here to avoid unsupported value errors.
    }

    data = _post(payload)

    # Cost tracking (if usage is present)
    usage = data.get("usage")
    if usage:
        prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
        completion_tokens = int(usage.get("completion_tokens", 0) or 0)
        cost_tracker.register_call(
            role=role_lower,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    # Extract message content
    try:
        msg = data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Unexpected OpenAI response format: {e}\nFull data: {data}") from e

    msg = msg.strip()

    # Try direct JSON parse
    try:
        return json.loads(msg)
    except Exception:
        # Try to salvage the first {...} block
        start = msg.find("{")
        end = msg.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(msg[start : end + 1])
            except Exception:
                pass

    raise RuntimeError(
        "Model response was not valid JSON.\n"
        f"Role: {role_lower}\n"
        f"Model: {model}\n"
        f"Content:\n{msg}"
    )
