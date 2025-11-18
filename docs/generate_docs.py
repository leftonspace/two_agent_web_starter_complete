#!/usr/bin/env python3
# docs/generate_docs.py
"""
Generate reference documentation from agent code docstrings.

Walks all Python files in agent/ directory, extracts module docstrings,
class docstrings, and function docstrings, and generates a comprehensive
REFERENCE.md file.

Does NOT import modules to avoid side effects - parses source code directly.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List, Dict, Any


def main() -> None:
    """Generate reference documentation."""
    print("\n" + "=" * 70)
    print("  Documentation Generator")
    print("=" * 70 + "\n")

    # Find agent directory
    project_root = Path(__file__).resolve().parent.parent
    agent_dir = project_root / "agent"

    if not agent_dir.exists():
        print(f"❌ Error: agent/ directory not found at {agent_dir}")
        return

    # Collect all Python files
    python_files = list(agent_dir.rglob("*.py"))
    python_files = [f for f in python_files if not f.name.startswith("_")]  # Skip private files

    print(f"📁 Found {len(python_files)} Python files")

    # Parse all files
    modules_data = []
    for py_file in sorted(python_files):
        try:
            data = parse_module(py_file, agent_dir)
            if data:
                modules_data.append(data)
                print(f"   ✓ {data['module_name']}")
        except Exception as e:
            print(f"   ⚠️  Failed to parse {py_file.name}: {e}")

    if not modules_data:
        print("\n❌ No modules found to document")
        return

    # Generate markdown
    print(f"\n📝 Generating documentation...")
    markdown = generate_markdown(modules_data)

    # Write to REFERENCE.md
    output_file = project_root / "docs" / "REFERENCE.md"
    output_file.write_text(markdown, encoding="utf-8")

    print(f"\n✅ Documentation generated: {output_file}")
    print(f"   Modules documented: {len(modules_data)}")
    print(f"   Total size: {len(markdown)} characters\n")


def parse_module(file_path: Path, agent_dir: Path) -> Dict[str, Any] | None:
    """
    Parse a Python module and extract documentation.

    Args:
        file_path: Path to Python file
        agent_dir: Base agent directory

    Returns:
        Dictionary with module documentation data, or None if parsing fails
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return None

    # Get module name
    rel_path = file_path.relative_to(agent_dir)
    module_name = str(rel_path.with_suffix("")).replace("/", ".")

    # Extract module docstring
    module_doc = ast.get_docstring(tree, clean=True) or ""

    # Extract classes and functions
    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_doc = ast.get_docstring(node, clean=True) or ""
            methods = []

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_doc = ast.get_docstring(item, clean=True) or ""
                    methods.append({
                        "name": item.name,
                        "docstring": method_doc,
                        "args": get_function_signature(item),
                    })

            classes.append({
                "name": node.name,
                "docstring": class_doc,
                "methods": methods,
            })

        elif isinstance(node, ast.FunctionDef) and not isinstance(node.parent if hasattr(node, 'parent') else None, ast.ClassDef):
            # Top-level functions only
            if node.col_offset == 0:  # Top-level function
                func_doc = ast.get_docstring(node, clean=True) or ""
                functions.append({
                    "name": node.name,
                    "docstring": func_doc,
                    "args": get_function_signature(node),
                })

    return {
        "module_name": module_name,
        "file_path": str(rel_path),
        "docstring": module_doc,
        "classes": classes,
        "functions": functions,
    }


def get_function_signature(func_node: ast.FunctionDef) -> List[str]:
    """
    Extract function argument names.

    Args:
        func_node: AST function definition node

    Returns:
        List of argument names
    """
    args = []
    for arg in func_node.args.args:
        args.append(arg.arg)
    return args


def generate_markdown(modules_data: List[Dict[str, Any]]) -> str:
    """
    Generate markdown documentation from parsed module data.

    Args:
        modules_data: List of module documentation dictionaries

    Returns:
        Markdown string
    """
    lines = []

    # Header
    lines.append("# Multi-Agent Orchestrator - API Reference")
    lines.append("")
    lines.append("*Auto-generated documentation from code docstrings*")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("")
    for module in modules_data:
        lines.append(f"- [{module['module_name']}](#{module['module_name'].replace('.', '')})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Modules
    for module in modules_data:
        lines.append(f"## `{module['module_name']}`")
        lines.append("")
        lines.append(f"**File:** `{module['file_path']}`")
        lines.append("")

        if module['docstring']:
            lines.append(module['docstring'])
            lines.append("")

        # Classes
        if module['classes']:
            lines.append("### Classes")
            lines.append("")

            for cls in module['classes']:
                lines.append(f"#### `{cls['name']}`")
                lines.append("")

                if cls['docstring']:
                    lines.append(cls['docstring'])
                    lines.append("")

                if cls['methods']:
                    lines.append("**Methods:**")
                    lines.append("")

                    for method in cls['methods']:
                        if method['name'].startswith('_') and not method['name'].startswith('__'):
                            continue  # Skip private methods

                        args_str = ", ".join(method['args'])
                        lines.append(f"- **`{method['name']}({args_str})`**")

                        if method['docstring']:
                            # Extract first line of docstring
                            first_line = method['docstring'].split('\n')[0].strip()
                            lines.append(f"  - {first_line}")

                        lines.append("")

                lines.append("")

        # Functions
        if module['functions']:
            lines.append("### Functions")
            lines.append("")

            for func in module['functions']:
                if func['name'].startswith('_'):
                    continue  # Skip private functions

                args_str = ", ".join(func['args'])
                lines.append(f"#### `{func['name']}({args_str})`")
                lines.append("")

                if func['docstring']:
                    lines.append(func['docstring'])
                else:
                    lines.append("*No documentation available*")

                lines.append("")

        lines.append("---")
        lines.append("")

    # Footer
    lines.append("## Notes")
    lines.append("")
    lines.append("This documentation is automatically generated from code docstrings.")
    lines.append("For more detailed information, consult the source code directly.")
    lines.append("")
    lines.append("To regenerate this documentation, run:")
    lines.append("```bash")
    lines.append("python3 docs/generate_docs.py")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
