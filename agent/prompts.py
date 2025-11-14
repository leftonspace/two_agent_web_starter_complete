# prompts.py
import json
from pathlib import Path
from typing import Dict, Any

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

      - manager_plan_sys   (system prompt for planning)
      - manager_review_sys (system prompt for reviewing)
      - employee_sys       (system prompt for building files)
      - manager_behaviour  (behaviour config from the JSON, if any)
      - roles              (raw roles from JSON, for advanced routing)
    """
    data = _load_persona_file(file_name)

    roles = data.get("roles", {})
    behaviour = data.get("manager_behaviour", {})

    if "project_manager_overseer" not in roles:
        raise KeyError("prompts file must define 'project_manager_overseer' in roles")

    overseer = roles["project_manager_overseer"]["system"]

    # --- Manager: planning mode ---
    manager_plan_sys = (
        overseer
        + "\n\nYou are currently in PLANNING MODE.\n"
        + "Your task:\n"
        + "- Read the provided task description.\n"
        + "- Design a short, concrete plan (2–10 steps).\n"
        + "- Define clear acceptance criteria the work must satisfy.\n\n"
        + "OUTPUT RULES:\n"
        + "- Respond ONLY in JSON.\n"
        + "- Use this structure:\n"
        + "  {\n"
        + "    \"plan\": [\"step 1\", \"step 2\", ...],\n"
        + "    \"acceptance_criteria\": [\"criterion 1\", \"criterion 2\", ...]\n"
        + "  }\n"
        + "- No extra keys, no natural language outside of JSON."
    )

    # --- Manager: review mode ---
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

    # --- Employee: combined senior specialist (default all-in-one mode) ---
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

    combined_personas = []
    for name in persona_order:
        if name in roles:
            combined_personas.append(f"[{name}]\n{roles[name]['system']}")

    if not combined_personas:
        raise RuntimeError("No employee personas found in prompts file.")

    personas_text = "\n\n---\n\n".join(combined_personas)

    employee_sys = (
        "You are a unified senior engineer embodying multiple specialist roles:\n\n"
        + personas_text
        + "\n\nYou receive JSON input with:\n"
        + "- task: the user's goal.\n"
        + "- plan: the manager's plan and acceptance criteria.\n"
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
        "employee_sys": employee_sys,
        "manager_behaviour": behaviour,
        "roles": roles
    }
