"""
PHASE 4.2: Base Workflow Class

Defines the base class for domain-specific workflows with real QA execution.
"""

from __future__ import annotations

import ast
import json
import logging
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """
    A single step in a workflow.

    Attributes:
        name: Step name
        action: Action type (e.g., "qa_check", "tool_call", "specialist_pass")
        config: Step-specific configuration
    """
    name: str
    action: str
    config: Dict[str, Any]


class Workflow(ABC):
    """
    Base class for domain-specific workflows.

    Each workflow defines a sequence of QA checks, tool invocations,
    and specialist passes appropriate for its domain.
    """

    def __init__(self):
        """Initialize workflow."""
        self.steps: List[WorkflowStep] = []
        self._build_steps()

    @abstractmethod
    def _build_steps(self) -> None:
        """
        Build the workflow steps.

        Subclasses must implement this to define their specific pipeline.
        """
        pass

    def run(self, mission_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the workflow.

        Args:
            mission_context: Context including mission_id, task, domain, files, etc.

        Returns:
            Workflow result with QA findings, tool outputs, specialist feedback

        PHASE 4.3 (R6): Workflow failures are tracked and can block execution
        based on workflow_enforcement config setting.
        """
        results = {
            "workflow_name": self.__class__.__name__,
            "steps_completed": [],
            "steps_failed": [],
            "qa_findings": [],
            "specialist_feedback": [],
            "has_failures": False,  # PHASE 4.3 (R6): Track if any steps failed
            "enforcement_level": "warn",  # Default to warn mode
        }

        for step in self.steps:
            try:
                step_result = self._execute_step(step, mission_context)
                results["steps_completed"].append({
                    "step": step.name,
                    "action": step.action,
                    "result": step_result,
                })

                # Collect QA findings
                if step.action == "qa_check" and step_result.get("findings"):
                    results["qa_findings"].extend(step_result["findings"])

                # Collect specialist feedback
                if step.action == "specialist_pass" and step_result.get("feedback"):
                    results["specialist_feedback"].append(step_result["feedback"])

                # PHASE 4.3 (R6): Track step failures
                if step_result.get("status") in ["failed", "error"]:
                    results["has_failures"] = True

            except Exception as e:
                logger.error(f"Workflow step '{step.name}' failed: {e}")
                results["steps_failed"].append({
                    "step": step.name,
                    "error": str(e),
                })
                results["has_failures"] = True  # PHASE 4.3 (R6)

        return results

    def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single workflow step.

        Args:
            step: Step to execute
            context: Mission context

        Returns:
            Step execution result
        """
        if step.action == "qa_check":
            return self._run_qa_check(step.config, context)
        elif step.action == "tool_call":
            return self._run_tool(step.config, context)
        elif step.action == "specialist_pass":
            return self._run_specialist(step.config, context)
        else:
            return {"status": "skipped", "reason": f"Unknown action: {step.action}"}

    # =========================================================================
    # QA Check Implementation
    # =========================================================================

    def _run_qa_check(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a QA check based on check_type.

        Args:
            config: Check configuration including check_type
            context: Mission context with code, files, etc.

        Returns:
            Check result with status, findings, and details
        """
        check_type = config.get("check_type", "generic")

        check_handlers = {
            "syntax": self._check_syntax,
            "data_integrity": self._check_data_integrity,
            "calculations": self._check_calculations,
            "compliance": self._check_compliance,
            "hr_policy": self._check_hr_policy,
            "privacy": self._check_privacy,
            "sensitivity": self._check_sensitivity,
            "structure": self._check_structure,
            "citations": self._check_citations,
            "legal_compliance": self._check_legal_compliance,
            "config": self._check_config,
            "infrastructure": self._check_infrastructure,
        }

        handler = check_handlers.get(check_type, self._check_generic)

        try:
            return handler(config, context)
        except Exception as e:
            logger.error(f"QA check '{check_type}' failed: {e}")
            return {
                "status": "error",
                "check_type": check_type,
                "error": str(e),
                "findings": [{
                    "severity": "error",
                    "message": f"Check failed with exception: {e}",
                }]
            }

    def _check_syntax(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check code syntax validity."""
        findings = []
        code = context.get("code", "")
        files = context.get("files", [])
        project_path = context.get("project_path", ".")

        # Check inline code
        if code:
            try:
                ast.parse(code)
            except SyntaxError as e:
                findings.append({
                    "severity": "error",
                    "type": "syntax_error",
                    "message": f"Syntax error at line {e.lineno}: {e.msg}",
                    "line": e.lineno,
                    "offset": e.offset,
                })

        # Check files
        for file_path in files:
            if file_path.endswith(".py"):
                full_path = Path(project_path) / file_path
                if full_path.exists():
                    try:
                        ast.parse(full_path.read_text())
                    except SyntaxError as e:
                        findings.append({
                            "severity": "error",
                            "type": "syntax_error",
                            "file": file_path,
                            "message": f"Syntax error at line {e.lineno}: {e.msg}",
                            "line": e.lineno,
                        })

        return {
            "status": "failed" if findings else "passed",
            "check_type": "syntax",
            "findings": findings,
            "files_checked": len(files) + (1 if code else 0),
        }

    def _check_data_integrity(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check data integrity - validate data structures and types."""
        findings = []
        data = context.get("data", {})

        # Check for null/None values in required fields
        required_fields = config.get("required_fields", [])
        for field in required_fields:
            if field not in data or data[field] is None:
                findings.append({
                    "severity": "error",
                    "type": "missing_required_field",
                    "message": f"Required field '{field}' is missing or null",
                    "field": field,
                })

        # Check for data type consistency
        type_checks = config.get("type_checks", {})
        for field, expected_type in type_checks.items():
            if field in data:
                actual_type = type(data[field]).__name__
                if actual_type != expected_type:
                    findings.append({
                        "severity": "warning",
                        "type": "type_mismatch",
                        "message": f"Field '{field}' expected {expected_type}, got {actual_type}",
                        "field": field,
                    })

        return {
            "status": "failed" if any(f["severity"] == "error" for f in findings) else "passed",
            "check_type": "data_integrity",
            "findings": findings,
        }

    def _check_calculations(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify numerical calculations."""
        findings = []
        calculations = context.get("calculations", [])

        for calc in calculations:
            expected = calc.get("expected")
            actual = calc.get("actual")
            tolerance = calc.get("tolerance", 0.0001)
            name = calc.get("name", "unnamed")

            if expected is not None and actual is not None:
                if abs(float(expected) - float(actual)) > tolerance:
                    findings.append({
                        "severity": "error",
                        "type": "calculation_mismatch",
                        "message": f"Calculation '{name}' mismatch: expected {expected}, got {actual}",
                        "expected": expected,
                        "actual": actual,
                    })

        return {
            "status": "failed" if findings else "passed",
            "check_type": "calculations",
            "findings": findings,
        }

    def _check_compliance(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with standards (GAAP, IFRS, etc.)."""
        findings = []
        standards = config.get("standards", [])
        content = context.get("content", "") or context.get("code", "")

        compliance_patterns = {
            "GAAP": [
                (r"revenue\s*recognition", "warning", "Revenue recognition should follow GAAP guidelines"),
                (r"depreciation", "info", "Ensure depreciation method is GAAP compliant"),
            ],
            "IFRS": [
                (r"fair\s*value", "warning", "Fair value measurements should follow IFRS 13"),
                (r"lease", "info", "Lease accounting should follow IFRS 16"),
            ],
            "SOX": [
                (r"internal\s*control", "info", "Internal controls should be documented"),
                (r"audit\s*trail", "info", "Audit trail requirements apply"),
            ],
        }

        for standard in standards:
            patterns = compliance_patterns.get(standard, [])
            for pattern, severity, message in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    findings.append({
                        "severity": severity,
                        "type": "compliance_note",
                        "standard": standard,
                        "message": message,
                    })

        return {
            "status": "passed",  # Compliance checks are advisory
            "check_type": "compliance",
            "standards_checked": standards,
            "findings": findings,
        }

    def _check_hr_policy(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check HR policy compliance."""
        findings = []
        content = context.get("content", "")

        # Check for discrimination-related terms
        sensitive_terms = [
            (r"\b(age|gender|race|religion|disability)\b.*\b(requirement|must be|only)\b",
             "error", "Potential discriminatory language detected"),
            (r"\b(young|old|male|female)\s*(only|preferred)\b",
             "error", "Potentially discriminatory requirement"),
        ]

        for pattern, severity, message in sensitive_terms:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append({
                    "severity": severity,
                    "type": "hr_policy_violation",
                    "message": message,
                })

        # Check for required disclaimers
        if "equal opportunity" not in content.lower() and len(content) > 500:
            findings.append({
                "severity": "warning",
                "type": "missing_disclaimer",
                "message": "Consider adding equal opportunity employer statement",
            })

        return {
            "status": "failed" if any(f["severity"] == "error" for f in findings) else "passed",
            "check_type": "hr_policy",
            "findings": findings,
        }

    def _check_privacy(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check for privacy concerns (PII, GDPR, CCPA)."""
        findings = []
        content = context.get("content", "") or context.get("code", "")
        standards = config.get("standards", ["GDPR", "CCPA"])

        # PII patterns
        pii_patterns = [
            (r"\b\d{3}-\d{2}-\d{4}\b", "error", "Social Security Number detected"),
            (r"\b\d{16}\b", "error", "Potential credit card number detected"),
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "warning", "Email address detected"),
            (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "warning", "Phone number detected"),
        ]

        for pattern, severity, message in pii_patterns:
            matches = re.findall(pattern, content)
            if matches:
                findings.append({
                    "severity": severity,
                    "type": "pii_detected",
                    "message": f"{message} ({len(matches)} instance(s))",
                    "count": len(matches),
                })

        # GDPR specific checks
        if "GDPR" in standards:
            if "consent" not in content.lower() and "personal data" in content.lower():
                findings.append({
                    "severity": "warning",
                    "type": "gdpr_concern",
                    "message": "Personal data mentioned without consent mechanism",
                })

        return {
            "status": "failed" if any(f["severity"] == "error" for f in findings) else "passed",
            "check_type": "privacy",
            "standards_checked": standards,
            "findings": findings,
        }

    def _check_sensitivity(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check for sensitive content."""
        findings = []
        content = context.get("content", "")

        # Sensitive content patterns
        sensitive_patterns = [
            (r"\b(confidential|secret|classified)\b", "warning", "Sensitive classification marker found"),
            (r"\b(password|api.?key|secret.?key|private.?key)\s*[:=]", "error", "Potential credential exposure"),
            (r"\b(salary|compensation|bonus)\s*[:=\s]\s*\$?\d+", "warning", "Compensation information detected"),
        ]

        for pattern, severity, message in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append({
                    "severity": severity,
                    "type": "sensitive_content",
                    "message": message,
                })

        return {
            "status": "failed" if any(f["severity"] == "error" for f in findings) else "passed",
            "check_type": "sensitivity",
            "findings": findings,
        }

    def _check_structure(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check document structure."""
        findings = []
        content = context.get("content", "")

        # Check for required sections
        required_sections = config.get("required_sections", [])
        for section in required_sections:
            if section.lower() not in content.lower():
                findings.append({
                    "severity": "warning",
                    "type": "missing_section",
                    "message": f"Required section '{section}' not found",
                    "section": section,
                })

        # Check for proper heading hierarchy (markdown)
        headings = re.findall(r"^(#{1,6})\s+(.+)$", content, re.MULTILINE)
        prev_level = 0
        for heading_marks, heading_text in headings:
            level = len(heading_marks)
            if level > prev_level + 1 and prev_level > 0:
                findings.append({
                    "severity": "warning",
                    "type": "heading_hierarchy",
                    "message": f"Heading '{heading_text}' skips levels (h{prev_level} to h{level})",
                })
            prev_level = level

        return {
            "status": "failed" if any(f["severity"] == "error" for f in findings) else "passed",
            "check_type": "structure",
            "findings": findings,
        }

    def _check_citations(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Verify citation format and validity."""
        findings = []
        content = context.get("content", "")

        # Find citations (basic patterns)
        citation_patterns = [
            r"\[(\d+)\]",  # [1] style
            r"\(([A-Z][a-z]+,?\s*\d{4})\)",  # (Author, 2024) style
        ]

        citations_found = []
        for pattern in citation_patterns:
            citations_found.extend(re.findall(pattern, content))

        # Check for uncited references
        references_section = re.search(r"(?:References|Bibliography)(.*)", content, re.IGNORECASE | re.DOTALL)
        if references_section and not citations_found:
            findings.append({
                "severity": "warning",
                "type": "uncited_references",
                "message": "References section exists but no citations found in text",
            })

        # Check citation numbers are sequential (for numbered citations)
        numbered_citations = sorted([int(c) for c in citations_found if c.isdigit()])
        if numbered_citations:
            expected = list(range(1, len(numbered_citations) + 1))
            if numbered_citations != expected:
                findings.append({
                    "severity": "warning",
                    "type": "citation_sequence",
                    "message": "Citation numbers are not sequential",
                    "found": numbered_citations,
                })

        return {
            "status": "passed",
            "check_type": "citations",
            "citations_found": len(citations_found),
            "findings": findings,
        }

    def _check_legal_compliance(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check legal document compliance."""
        findings = []
        content = context.get("content", "")

        # Required legal clauses
        required_clauses = config.get("required_clauses", [
            "governing law",
            "jurisdiction",
            "confidentiality",
        ])

        for clause in required_clauses:
            if clause.lower() not in content.lower():
                findings.append({
                    "severity": "warning",
                    "type": "missing_clause",
                    "message": f"Required clause '{clause}' not found",
                    "clause": clause,
                })

        # Check for defined terms usage
        defined_terms = re.findall(r'"([A-Z][^"]+)"', content)
        for term in defined_terms:
            # Check if defined term is used after definition
            if content.count(term) < 2:
                findings.append({
                    "severity": "info",
                    "type": "unused_defined_term",
                    "message": f"Defined term '{term}' may be unused",
                })

        return {
            "status": "passed",
            "check_type": "legal_compliance",
            "findings": findings,
        }

    def _check_config(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration files."""
        findings = []
        content = context.get("content", "")
        file_path = context.get("file_path", "")

        # Try JSON parsing
        if file_path.endswith(".json") or content.strip().startswith("{"):
            try:
                json.loads(content)
            except json.JSONDecodeError as e:
                findings.append({
                    "severity": "error",
                    "type": "json_parse_error",
                    "message": f"Invalid JSON: {e.msg} at line {e.lineno}",
                    "line": e.lineno,
                })

        # Try YAML parsing (if available)
        if file_path.endswith((".yml", ".yaml")):
            try:
                import yaml
                yaml.safe_load(content)
            except ImportError:
                pass  # YAML not available
            except yaml.YAMLError as e:
                findings.append({
                    "severity": "error",
                    "type": "yaml_parse_error",
                    "message": f"Invalid YAML: {e}",
                })

        # Check for common config issues
        if "password" in content.lower() and not re.search(r"\$\{|%\(|<.*>", content):
            findings.append({
                "severity": "warning",
                "type": "hardcoded_credential",
                "message": "Potential hardcoded password detected",
            })

        return {
            "status": "failed" if any(f["severity"] == "error" for f in findings) else "passed",
            "check_type": "config",
            "findings": findings,
        }

    def _check_infrastructure(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Check infrastructure configuration."""
        findings = []
        content = context.get("content", "")

        # Check for security issues in infrastructure config
        security_patterns = [
            (r"0\.0\.0\.0", "warning", "Binding to all interfaces (0.0.0.0) detected"),
            (r"port\s*[:=]\s*22\b", "info", "SSH port 22 configured"),
            (r"ssl\s*[:=]\s*false", "error", "SSL disabled"),
            (r"verify\s*[:=]\s*false", "warning", "SSL verification disabled"),
            (r"root\s*[:=]", "warning", "Root user configuration detected"),
        ]

        for pattern, severity, message in security_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append({
                    "severity": severity,
                    "type": "infrastructure_security",
                    "message": message,
                })

        return {
            "status": "failed" if any(f["severity"] == "error" for f in findings) else "passed",
            "check_type": "infrastructure",
            "findings": findings,
        }

    def _check_generic(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Generic check - placeholder for unknown check types."""
        return {
            "status": "passed",
            "check_type": config.get("check_type", "generic"),
            "findings": [],
            "note": "Generic check performed - no specific rules defined",
        }

    # =========================================================================
    # Tool Execution Implementation
    # =========================================================================

    def _run_tool(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run a tool using the tool plugin system.

        Args:
            config: Tool configuration including tool_name
            context: Mission context

        Returns:
            Tool execution result
        """
        tool_name = config.get("tool_name", "")
        project_path = Path(context.get("project_path", "."))

        # Tool handlers
        tool_handlers = {
            "format_code": self._tool_format_code,
            "run_unit_tests": self._tool_run_tests,
            "run_tests": self._tool_run_tests,
            "run_linter": self._tool_run_linter,
        }

        handler = tool_handlers.get(tool_name)
        if handler:
            try:
                return handler(config, context, project_path)
            except Exception as e:
                logger.error(f"Tool '{tool_name}' failed: {e}")
                return {
                    "status": "error",
                    "tool": tool_name,
                    "error": str(e),
                }
        else:
            return {
                "status": "skipped",
                "tool": tool_name,
                "reason": f"Unknown tool: {tool_name}",
            }

    def _tool_format_code(self, config: Dict[str, Any], context: Dict[str, Any], project_path: Path) -> Dict[str, Any]:
        """Run code formatter (ruff/black/prettier)."""
        formatter = config.get("formatter", "ruff")
        paths = config.get("paths", ["."])
        check_only = config.get("check_only", True)  # Default to check-only in workflow

        if not shutil.which(formatter):
            return {
                "status": "skipped",
                "tool": "format_code",
                "formatter": formatter,
                "reason": f"{formatter} not installed",
            }

        # Build command
        if formatter == "ruff":
            cmd = ["ruff", "format"] + (["--check"] if check_only else []) + paths
        elif formatter == "black":
            cmd = ["black"] + (["--check"] if check_only else []) + paths
        else:
            return {"status": "skipped", "reason": f"Unknown formatter: {formatter}"}

        try:
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "tool": "format_code",
                "formatter": formatter,
                "exit_code": result.returncode,
                "output": result.stdout[:1000] if result.stdout else "",
                "errors": result.stderr[:1000] if result.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "tool": "format_code", "error": "Timeout"}
        except Exception as e:
            return {"status": "error", "tool": "format_code", "error": str(e)}

    def _tool_run_tests(self, config: Dict[str, Any], context: Dict[str, Any], project_path: Path) -> Dict[str, Any]:
        """Run unit tests with pytest."""
        test_path = config.get("test_path", "tests")

        if not shutil.which("pytest"):
            return {
                "status": "skipped",
                "tool": "run_tests",
                "reason": "pytest not installed",
            }

        # Check if test path exists
        full_path = project_path / test_path
        if not full_path.exists():
            return {
                "status": "skipped",
                "tool": "run_tests",
                "reason": f"Test path not found: {test_path}",
            }

        try:
            result = subprocess.run(
                ["pytest", test_path, "--tb=short", "-q"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse results
            output = result.stdout
            passed = len(re.findall(r"(\d+) passed", output))
            failed = len(re.findall(r"(\d+) failed", output))

            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "tool": "run_tests",
                "exit_code": result.returncode,
                "passed": passed,
                "failed": failed,
                "output": output[:2000] if output else "",
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "tool": "run_tests", "error": "Timeout (5 min)"}
        except Exception as e:
            return {"status": "error", "tool": "run_tests", "error": str(e)}

    def _tool_run_linter(self, config: Dict[str, Any], context: Dict[str, Any], project_path: Path) -> Dict[str, Any]:
        """Run linter (ruff check)."""
        paths = config.get("paths", ["."])

        if not shutil.which("ruff"):
            return {
                "status": "skipped",
                "tool": "run_linter",
                "reason": "ruff not installed",
            }

        try:
            result = subprocess.run(
                ["ruff", "check"] + paths,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Count issues
            issues = result.stdout.count("\n") if result.stdout else 0

            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "tool": "run_linter",
                "exit_code": result.returncode,
                "issues_found": issues,
                "output": result.stdout[:2000] if result.stdout else "",
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "tool": "run_linter", "error": "Timeout"}
        except Exception as e:
            return {"status": "error", "tool": "run_linter", "error": str(e)}

    # =========================================================================
    # Specialist Pass Implementation
    # =========================================================================

    def _run_specialist(self, config: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to a specialist for review.

        Args:
            config: Specialist configuration including specialist_type
            context: Mission context

        Returns:
            Specialist review result
        """
        specialist_type = config.get("specialist_type", "qa")

        try:
            # Try to get specialist from pool
            from core.specialists import get_pool_manager
            pool_manager = get_pool_manager()

            # Map specialist types to domains
            domain_map = {
                "security": "security",
                "qa": "code_review",
                "data": "research",
                "devops": "ops",
                "frontend": "coding",
                "backend": "coding",
            }

            domain = domain_map.get(specialist_type, "administration")
            pool = pool_manager.get_pool(domain)

            if pool and pool.specialists:
                # Get best specialist
                specialist = max(pool.specialists, key=lambda s: getattr(s, 'score', 0))

                return {
                    "status": "completed",
                    "specialist_type": specialist_type,
                    "specialist_name": getattr(specialist, 'name', 'unknown'),
                    "specialist_score": getattr(specialist, 'score', 0),
                    "feedback": {
                        "assigned": True,
                        "message": f"Review assigned to {getattr(specialist, 'name', 'specialist')}",
                    },
                }
            else:
                return {
                    "status": "skipped",
                    "specialist_type": specialist_type,
                    "reason": f"No specialists available for domain: {domain}",
                }

        except ImportError:
            logger.debug("Specialist pool not available, skipping specialist pass")
            return {
                "status": "skipped",
                "specialist_type": specialist_type,
                "reason": "Specialist pool system not available",
            }
        except Exception as e:
            logger.error(f"Specialist pass failed: {e}")
            return {
                "status": "error",
                "specialist_type": specialist_type,
                "error": str(e),
            }
