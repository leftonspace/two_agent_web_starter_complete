# prompts.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"


def _load_persona_file(file_name: str) -> dict:
    path = PROMPTS_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Prompts file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_prompts(file_name: str) -> Dict[str, Any]:
    """
    Load a persona file (e.g. prompts_default.json) and construct:

      - manager_plan_sys    (system prompt for planning)
      - manager_review_sys  (system prompt for reviewing)
      - supervisor_sys      (system prompt for phasing / persona selection)
      - employee_sys        (system prompt for building files)
      - manager_behaviour   (behaviour config from the JSON, if any)
    """
    data = _load_persona_file(file_name)

    roles = data.get("roles", {})
    behaviour = data.get("manager_behaviour", {})

    # Base manager persona
    overseer = roles["project_manager_overseer"]["system"]

    # ─────────────────────────────────────────────────────────────
    # Manager: PLANNING MODE
    # ─────────────────────────────────────────────────────────────
    manager_plan_sys = (
        overseer
        + "\n\nYou are currently in PLANNING MODE.\n"
        + "Your task:\n"
        + "- Read the provided task description.\n"
        + "- Design a short, concrete plan (2–12 steps).\n"
        + "- Define clear acceptance criteria the work must satisfy.\n\n"
        + "OUTPUT RULES:\n"
        + "- Respond ONLY in JSON.\n"
        + "- Use this structure:\n"
        + "  {\n"
        + "    \"plan\": [\"step 0\", \"step 1\", ...],\n"
        + "    \"acceptance_criteria\": [\"criterion 0\", \"criterion 1\", ...]\n"
        + "  }\n"
        + "- No extra keys, no natural language outside of JSON."
    )

    # ─────────────────────────────────────────────────────────────
    # Manager: REVIEW MODE
    # ─────────────────────────────────────────────────────────────
    manager_review_sys = (
        overseer
        + "\n\nYou are currently in REVIEW MODE.\n"
        + "You receive:\n"
        + "- task: the original goal.\n"
        + "- plan: your own plan and acceptance criteria.\n"
        + "- files_summary: list of files with length and preview.\n"
        + "- tests: automated check results.\n"
        + "- browser_summary: optional analysis of the rendered page (may be null).\n"
        + "- screenshot_path: optional local screenshot path (you cannot open it, just reason about it abstractly).\n"
        + "- iteration: which review round this is.\n\n"
        + "Your job:\n"
        + "- Decide if the current version should be APPROVED or needs CHANGES.\n"
        + "- If changes are needed, give concrete, actionable feedback.\n\n"
        + "OUTPUT RULES:\n"
        + "- Respond ONLY in JSON.\n"
        + "- Use this structure:\n"
        + "  {\n"
        + "    \"status\": \"approved\" | \"needs_changes\",\n"
        + "    \"feedback\": [\"bullet 1\", \"bullet 2\", ...]\n"
        + "  }\n"
        + "- feedback must be short, specific, and practical.\n"
        + "- No other top-level keys."
    )

    # ─────────────────────────────────────────────────────────────
    # SUPERVISOR MODE (phasing + persona categories)
    # ─────────────────────────────────────────────────────────────
    supervisor_sys = (
        overseer
        + "\n\nYou are currently in SUPERVISOR MODE.\n"
        + "You receive JSON input with:\n"
        + "- plan: a list of high-level steps.\n"
        + "- acceptance_criteria: a list of checks.\n\n"
        + "Your job:\n"
        + "- Group the plan steps into 3–7 PHASES.\n"
        + "- For each phase, choose relevant categories that map to personas:\n"
        + "    layout_structure, visual_design, content_ux,\n"
        + "    interaction_logic, performance_seo, qa_docs.\n"
        + "- For each phase, list which indices of the plan belong to this phase.\n\n"
        + "IMPORTANT OUTPUT RULES (STRICT):\n"
        + "- You MUST respond with ONE and ONLY ONE JSON object.\n"
        + "- Do NOT repeat the plan or acceptance_criteria.\n"
        + "- Do NOT include '---', explanations, or any text outside JSON.\n"
        + "- Use this exact structure:\n"
        + "  {\n"
        + "    \"phases\": [\n"
        + "      {\n"
        + "        \"name\": \"Human readable phase name\",\n"
        + "        \"categories\": [\"layout_structure\", \"visual_design\"],\n"
        + "        \"plan_steps\": [0, 1]\n"
        + "      }\n"
        + "    ]\n"
        + "  }\n"
        + "- 'plan_steps' must be integer indices into the original plan array.\n"
        + "- No other top-level keys.\n"
        + "- If you are tempted to echo the full plan, DO NOT: only reference steps by index."
    )

    # ─────────────────────────────────────────────────────────────
    # EMPLOYEE: unified senior specialist (multi-persona)
    # ─────────────────────────────────────────────────────────────
    persona_order = [
        "html_architect",
        "css_pixel_surgeon",
        "javascript_logic_master",
        "ux_flow_designer",
        "qa_bug_hunter",
        "performance_engineer",
        "security_engineer",
        "backend_system_builder",
        "devops_engineer",
        "documentation_sage",
        "brand_stylist",
    ]

    combined_personas: list[str] = []
    for name in persona_order:
        if name in roles:
            combined_personas.append(f"[{name}]\n{roles[name]['system']}")

    personas_text = "\n\n---\n\n".join(combined_personas)

    employee_sys = (
        "You are a unified senior engineer embodying multiple specialist roles:\n\n"
        + personas_text
        + "\n\nYou receive JSON input with:\n"
        + "- task: the user's goal.\n"
        + "- plan: the manager's plan and acceptance criteria.\n"
        + "- phases: supervisor phases with categories and plan step indices.\n"
        + "- previous_files: existing files (may be empty on first run).\n"
        + "- feedback: manager feedback from the previous iteration, or null on the first.\n\n"
        + "Your job:\n"
        + "- Create or update the full set of website files.\n"
        + "- Improve structure, styling, UX, performance, security, and clarity as appropriate.\n"
        + "- Respect and refine the existing design when possible.\n\n"
        + "OUTPUT RULES (IMPORTANT):\n"
        + "- Respond ONLY in JSON.\n"
        + "- Use this exact top-level structure:\n"
        + "  {\n"
        + "    \"files\": {\n"
        + "      \"index.html\": \"...full file contents...\",\n"
        + "      \"style.css\": \"...full file contents...\",\n"
        + "      \"optional/other.js\": \"...\"\n"
        + "    }\n"
        + "  }\n"
        + "- 'files' MUST be an object/dictionary, not a list.\n"
        + "- Each value must be the FULL content of the file, not a diff.\n"
        + "- Do NOT wrap code in markdown fences.\n"
        + "- Do NOT add any other top-level keys."
    )

    return {
        "manager_plan_sys": manager_plan_sys,
        "manager_review_sys": manager_review_sys,
        "supervisor_sys": supervisor_sys,
        "employee_sys": employee_sys,
        "manager_behaviour": behaviour,
    }
