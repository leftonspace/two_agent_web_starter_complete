#!/usr/bin/env python3
"""
PHASE 1.7: Model Registry Update Tool

CLI tool for updating agent/models.json without code changes.

Usage:
    # Mark a model as deprecated
    python -m agent.tools.update_models --deprecate openai/gpt-4 --date 2025-06-01

    # Add a new model
    python -m agent.tools.update_models --add openai/gpt-6 \\
        --full-id gpt-6-2025-11-01 \\
        --cost-prompt 0.02 \\
        --cost-completion 0.06

    # Update model pricing
    python -m agent.tools.update_models --update openai/gpt-4o-mini \\
        --cost-prompt 0.002 \\
        --cost-completion 0.008

    # List all models
    python -m agent.tools.update_models --list

    # Check for deprecated models
    python -m agent.tools.update_models --check-deprecations
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def load_registry(registry_path: Path) -> Dict[str, Any]:
    """Load models.json"""
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(registry_path: Path, registry: Dict[str, Any]) -> None:
    """Save models.json with backup"""
    # Create backup
    backup_path = registry_path.with_suffix(".json.bak")
    if registry_path.exists():
        shutil.copy2(registry_path, backup_path)
        print(f"✅ Backup created: {backup_path}")

    # Save updated registry
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    print(f"✅ Registry updated: {registry_path}")


def mark_deprecated(
    registry: Dict[str, Any],
    provider: str,
    model_id: str,
    deprecation_date: str,
    replacement: Optional[str] = None,
) -> Dict[str, Any]:
    """Mark a model as deprecated"""
    if provider not in registry["providers"]:
        raise ValueError(f"Unknown provider: {provider}")

    if model_id not in registry["providers"][provider]["models"]:
        raise ValueError(f"Unknown model: {model_id} for provider {provider}")

    model = registry["providers"][provider]["models"][model_id]
    model["deprecated"] = True
    model["deprecation_date"] = deprecation_date
    if replacement:
        model["replacement"] = replacement

    print(f"✅ Marked {provider}/{model_id} as deprecated (removal: {deprecation_date})")
    if replacement:
        print(f"   Replacement: {replacement}")

    return registry


def add_model(
    registry: Dict[str, Any],
    provider: str,
    model_id: str,
    full_id: str,
    cost_prompt: float,
    cost_completion: float,
    context_window: int = 128000,
    max_output: int = 16384,
    capabilities: Optional[list] = None,
    display_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Add a new model to registry"""
    if provider not in registry["providers"]:
        raise ValueError(f"Unknown provider: {provider}")

    if model_id in registry["providers"][provider]["models"]:
        raise ValueError(f"Model {model_id} already exists for provider {provider}")

    new_model = {
        "id": full_id,
        "display_name": display_name or model_id.upper(),
        "context_window": context_window,
        "max_output_tokens": max_output,
        "cost_per_1k_prompt": cost_prompt,
        "cost_per_1k_completion": cost_completion,
        "capabilities": capabilities or ["chat", "json"],
        "deprecated": False,
        "deprecation_date": None,
        "replacement": None,
        "notes": f"Added on {datetime.now().strftime('%Y-%m-%d')}",
    }

    registry["providers"][provider]["models"][model_id] = new_model
    print(f"✅ Added {provider}/{model_id} -> {full_id}")
    print(f"   Cost: ${cost_prompt:.4f}/1k prompt, ${cost_completion:.4f}/1k completion")

    return registry


def update_pricing(
    registry: Dict[str, Any],
    provider: str,
    model_id: str,
    cost_prompt: Optional[float] = None,
    cost_completion: Optional[float] = None,
) -> Dict[str, Any]:
    """Update model pricing"""
    if provider not in registry["providers"]:
        raise ValueError(f"Unknown provider: {provider}")

    if model_id not in registry["providers"][provider]["models"]:
        raise ValueError(f"Unknown model: {model_id} for provider {provider}")

    model = registry["providers"][provider]["models"][model_id]

    if cost_prompt is not None:
        old_prompt = model["cost_per_1k_prompt"]
        model["cost_per_1k_prompt"] = cost_prompt
        print(f"✅ Updated {provider}/{model_id} prompt cost: ${old_prompt:.4f} -> ${cost_prompt:.4f}")

    if cost_completion is not None:
        old_completion = model["cost_per_1k_completion"]
        model["cost_per_1k_completion"] = cost_completion
        print(f"✅ Updated {provider}/{model_id} completion cost: ${old_completion:.4f} -> ${cost_completion:.4f}")

    return registry


def list_models(registry: Dict[str, Any], provider: Optional[str] = None) -> None:
    """List all models in registry"""
    print("\n" + "=" * 80)
    print("Model Registry")
    print("=" * 80)

    for prov_name, prov_data in registry["providers"].items():
        if provider and prov_name != provider:
            continue

        print(f"\n{prov_data['name']} ({prov_name})")
        print("-" * 80)

        for model_id, model_data in prov_data["models"].items():
            status = " [DEPRECATED]" if model_data.get("deprecated") else ""
            print(f"  {model_id}{status}")
            print(f"    ID: {model_data['id']}")
            print(f"    Cost: ${model_data['cost_per_1k_prompt']:.4f}/1k prompt, ${model_data['cost_per_1k_completion']:.4f}/1k completion")
            if model_data.get("deprecated"):
                print(f"    Deprecation: {model_data.get('deprecation_date', 'TBD')}")
                if model_data.get("replacement"):
                    print(f"    Replacement: {model_data['replacement']}")


def check_deprecations(registry: Dict[str, Any]) -> None:
    """Check for deprecated models"""
    print("\n" + "=" * 80)
    print("Deprecated Models")
    print("=" * 80)

    found_any = False

    for prov_name, prov_data in registry["providers"].items():
        for model_id, model_data in prov_data["models"].items():
            if model_data.get("deprecated"):
                found_any = True
                print(f"\n⚠️  {prov_name}/{model_id}")
                print(f"   Removal date: {model_data.get('deprecation_date', 'TBD')}")
                if model_data.get("replacement"):
                    print(f"   Use instead: {model_data['replacement']}")

    if not found_any:
        print("\n✅ No deprecated models found")


def main():
    parser = argparse.ArgumentParser(
        description="Update model registry (agent/models.json)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Actions
    parser.add_argument("--deprecate", metavar="PROVIDER/MODEL", help="Mark model as deprecated")
    parser.add_argument("--date", metavar="YYYY-MM-DD", help="Deprecation date")
    parser.add_argument("--replacement", metavar="MODEL", help="Replacement model")

    parser.add_argument("--add", metavar="PROVIDER/MODEL", help="Add new model")
    parser.add_argument("--full-id", metavar="ID", help="Full model ID (e.g., gpt-6-2025-11-01)")
    parser.add_argument("--cost-prompt", type=float, metavar="COST", help="Cost per 1k prompt tokens")
    parser.add_argument("--cost-completion", type=float, metavar="COST", help="Cost per 1k completion tokens")
    parser.add_argument("--context-window", type=int, default=128000, help="Context window size")
    parser.add_argument("--max-output", type=int, default=16384, help="Max output tokens")
    parser.add_argument("--capabilities", nargs="+", default=["chat", "json"], help="Model capabilities")
    parser.add_argument("--display-name", help="Display name")

    parser.add_argument("--update", metavar="PROVIDER/MODEL", help="Update existing model pricing")

    parser.add_argument("--list", action="store_true", help="List all models")
    parser.add_argument("--check-deprecations", action="store_true", help="Check for deprecated models")

    parser.add_argument("--registry", type=Path, help="Path to models.json (default: agent/models.json)")

    args = parser.parse_args()

    # Determine registry path
    if args.registry:
        registry_path = args.registry
    else:
        # Default: agent/models.json relative to this script
        script_dir = Path(__file__).resolve().parent.parent
        registry_path = script_dir / "models.json"

    if not registry_path.exists():
        print(f"❌ Registry not found: {registry_path}")
        return 1

    # Load registry
    registry = load_registry(registry_path)

    # Handle actions
    if args.list:
        list_models(registry)
        return 0

    if args.check_deprecations:
        check_deprecations(registry)
        return 0

    if args.deprecate:
        if not args.date:
            print("❌ --date required when using --deprecate")
            return 1

        provider, model_id = args.deprecate.split("/", 1)
        registry = mark_deprecated(registry, provider, model_id, args.date, args.replacement)
        save_registry(registry_path, registry)
        return 0

    if args.add:
        if not (args.full_id and args.cost_prompt is not None and args.cost_completion is not None):
            print("❌ --full-id, --cost-prompt, and --cost-completion required when using --add")
            return 1

        provider, model_id = args.add.split("/", 1)
        registry = add_model(
            registry,
            provider,
            model_id,
            args.full_id,
            args.cost_prompt,
            args.cost_completion,
            args.context_window,
            args.max_output,
            args.capabilities,
            args.display_name,
        )
        save_registry(registry_path, registry)
        return 0

    if args.update:
        if args.cost_prompt is None and args.cost_completion is None:
            print("❌ At least one of --cost-prompt or --cost-completion required when using --update")
            return 1

        provider, model_id = args.update.split("/", 1)
        registry = update_pricing(registry, provider, model_id, args.cost_prompt, args.cost_completion)
        save_registry(registry_path, registry)
        return 0

    # No action specified
    parser.print_help()
    return 1


if __name__ == "__main__":
    exit(main())
