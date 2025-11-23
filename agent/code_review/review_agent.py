"""
Code Review Agent for JARVIS.

Provides automated code review capabilities including:
- Code quality analysis
- Security vulnerability scanning
- Best practices enforcement
- Automated PR reviews
"""

import re
import ast
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(Enum):
    """Issue categories."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    BUG_RISK = "bug_risk"
    STYLE = "style"
    BEST_PRACTICE = "best_practice"


@dataclass
class ReviewIssue:
    """A single code review issue."""
    category: IssueCategory
    severity: Severity
    title: str
    description: str
    file_path: str = ""
    line_number: int = 0
    code_snippet: str = ""
    suggestion: str = ""
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID


@dataclass
class ReviewReport:
    """Complete code review report."""
    file_path: str
    language: str
    issues: List[ReviewIssue] = field(default_factory=list)
    summary: str = ""
    score: int = 100  # 0-100 quality score
    passed: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "language": self.language,
            "issues": [
                {
                    "category": i.category.value,
                    "severity": i.severity.value,
                    "title": i.title,
                    "description": i.description,
                    "line_number": i.line_number,
                    "code_snippet": i.code_snippet,
                    "suggestion": i.suggestion,
                    "cwe_id": i.cwe_id
                }
                for i in self.issues
            ],
            "summary": self.summary,
            "score": self.score,
            "passed": self.passed
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown(self) -> str:
        """Convert to markdown report."""
        md = f"# Code Review Report\n\n"
        md += f"**File:** `{self.file_path}`\n"
        md += f"**Language:** {self.language}\n"
        md += f"**Score:** {self.score}/100\n"
        md += f"**Status:** {'PASSED' if self.passed else 'NEEDS ATTENTION'}\n\n"

        if self.summary:
            md += f"## Summary\n\n{self.summary}\n\n"

        if self.issues:
            md += "## Issues Found\n\n"

            # Group by severity
            by_severity = {}
            for issue in self.issues:
                sev = issue.severity.value
                if sev not in by_severity:
                    by_severity[sev] = []
                by_severity[sev].append(issue)

            severity_order = ["critical", "high", "medium", "low", "info"]
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵",
                "info": "ℹ️"
            }

            for sev in severity_order:
                if sev in by_severity:
                    md += f"### {severity_emoji[sev]} {sev.upper()} ({len(by_severity[sev])})\n\n"
                    for issue in by_severity[sev]:
                        md += f"#### {issue.title}\n"
                        md += f"- **Category:** {issue.category.value}\n"
                        if issue.line_number:
                            md += f"- **Line:** {issue.line_number}\n"
                        if issue.cwe_id:
                            md += f"- **CWE:** {issue.cwe_id}\n"
                        md += f"\n{issue.description}\n"
                        if issue.code_snippet:
                            md += f"\n```\n{issue.code_snippet}\n```\n"
                        if issue.suggestion:
                            md += f"\n**Suggestion:** {issue.suggestion}\n"
                        md += "\n---\n\n"

        return md


class SecurityScanner:
    """Scans code for security vulnerabilities."""

    # Security patterns by language
    PATTERNS = {
        "python": {
            "sql_injection": [
                (r'execute\s*\(\s*["\'].*%s', "SQL injection via string formatting", "CWE-89"),
                (r'execute\s*\(\s*f["\']', "SQL injection via f-string", "CWE-89"),
                (r'cursor\.execute\s*\([^,]+\+', "SQL injection via concatenation", "CWE-89"),
            ],
            "command_injection": [
                (r'os\.system\s*\(', "OS command injection risk", "CWE-78"),
                (r'subprocess\.\w+\s*\([^)]*shell\s*=\s*True', "Shell injection via subprocess", "CWE-78"),
                (r'eval\s*\(', "Code injection via eval()", "CWE-94"),
                (r'exec\s*\(', "Code injection via exec()", "CWE-94"),
            ],
            "hardcoded_secrets": [
                (r'password\s*=\s*["\'][^"\']{4,}["\']', "Hardcoded password", "CWE-798"),
                (r'api_key\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded API key", "CWE-798"),
                (r'secret\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded secret", "CWE-798"),
                (r'AWS_SECRET_ACCESS_KEY', "AWS secret in code", "CWE-798"),
            ],
            "insecure_random": [
                (r'random\.\w+\(', "Insecure random for crypto", "CWE-330"),
            ],
            "path_traversal": [
                (r'open\s*\([^)]*\+', "Potential path traversal", "CWE-22"),
            ],
            "pickle": [
                (r'pickle\.load', "Unsafe pickle deserialization", "CWE-502"),
                (r'pickle\.loads', "Unsafe pickle deserialization", "CWE-502"),
            ],
            "yaml_load": [
                (r'yaml\.load\s*\([^)]*\)', "Unsafe YAML load", "CWE-502"),
            ],
        },
        "javascript": {
            "xss": [
                (r'innerHTML\s*=', "XSS via innerHTML", "CWE-79"),
                (r'document\.write\s*\(', "XSS via document.write", "CWE-79"),
                (r'\.html\s*\([^)]*\+', "XSS via jQuery .html()", "CWE-79"),
            ],
            "eval": [
                (r'eval\s*\(', "Code injection via eval()", "CWE-94"),
                (r'new\s+Function\s*\(', "Code injection via Function constructor", "CWE-94"),
            ],
            "hardcoded_secrets": [
                (r'password\s*[:=]\s*["\'][^"\']{4,}["\']', "Hardcoded password", "CWE-798"),
                (r'apiKey\s*[:=]\s*["\'][^"\']{8,}["\']', "Hardcoded API key", "CWE-798"),
                (r'secret\s*[:=]\s*["\'][^"\']{8,}["\']', "Hardcoded secret", "CWE-798"),
            ],
            "prototype_pollution": [
                (r'__proto__', "Prototype pollution risk", "CWE-1321"),
            ],
        },
    }

    def scan(self, code: str, language: str, file_path: str = "") -> List[ReviewIssue]:
        """Scan code for security issues."""
        issues = []

        patterns = self.PATTERNS.get(language, {})

        for category, pattern_list in patterns.items():
            for pattern, description, cwe_id in pattern_list:
                try:
                    matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        line_num = code[:match.start()].count('\n') + 1
                        # Get the line content
                        lines = code.split('\n')
                        code_snippet = lines[line_num - 1] if line_num <= len(lines) else ""

                        issues.append(ReviewIssue(
                            category=IssueCategory.SECURITY,
                            severity=Severity.HIGH if category in ['sql_injection', 'command_injection'] else Severity.MEDIUM,
                            title=description,
                            description=f"Potential {category.replace('_', ' ')} vulnerability detected.",
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=code_snippet.strip(),
                            cwe_id=cwe_id
                        ))
                except re.error:
                    continue

        return issues


class BestPracticesChecker:
    """Checks code for best practices violations."""

    def check_python(self, code: str, file_path: str = "") -> List[ReviewIssue]:
        """Check Python code for best practices."""
        issues = []

        # Check for bare except
        for match in re.finditer(r'except\s*:', code):
            line_num = code[:match.start()].count('\n') + 1
            issues.append(ReviewIssue(
                category=IssueCategory.BEST_PRACTICE,
                severity=Severity.MEDIUM,
                title="Bare except clause",
                description="Bare except catches all exceptions including KeyboardInterrupt and SystemExit.",
                file_path=file_path,
                line_number=line_num,
                suggestion="Use 'except Exception:' or catch specific exceptions."
            ))

        # Check for mutable default arguments
        for match in re.finditer(r'def\s+\w+\s*\([^)]*=\s*(\[\]|\{\})', code):
            line_num = code[:match.start()].count('\n') + 1
            issues.append(ReviewIssue(
                category=IssueCategory.BUG_RISK,
                severity=Severity.MEDIUM,
                title="Mutable default argument",
                description="Mutable default arguments are shared between function calls.",
                file_path=file_path,
                line_number=line_num,
                suggestion="Use None as default and create the mutable object inside the function."
            ))

        # Check for print statements (should use logging)
        for match in re.finditer(r'^\s*print\s*\(', code, re.MULTILINE):
            line_num = code[:match.start()].count('\n') + 1
            issues.append(ReviewIssue(
                category=IssueCategory.BEST_PRACTICE,
                severity=Severity.LOW,
                title="Print statement instead of logging",
                description="Consider using the logging module instead of print for production code.",
                file_path=file_path,
                line_number=line_num,
                suggestion="Replace with logging.info(), logging.debug(), etc."
            ))

        # Check for TODO/FIXME comments
        for match in re.finditer(r'#\s*(TODO|FIXME|XXX|HACK):', code, re.IGNORECASE):
            line_num = code[:match.start()].count('\n') + 1
            lines = code.split('\n')
            code_snippet = lines[line_num - 1] if line_num <= len(lines) else ""
            issues.append(ReviewIssue(
                category=IssueCategory.MAINTAINABILITY,
                severity=Severity.INFO,
                title=f"{match.group(1).upper()} comment found",
                description="Outstanding TODO/FIXME comment that should be addressed.",
                file_path=file_path,
                line_number=line_num,
                code_snippet=code_snippet.strip()
            ))

        return issues

    def check_javascript(self, code: str, file_path: str = "") -> List[ReviewIssue]:
        """Check JavaScript code for best practices."""
        issues = []

        # Check for var usage (should use let/const)
        for match in re.finditer(r'\bvar\s+\w+', code):
            line_num = code[:match.start()].count('\n') + 1
            issues.append(ReviewIssue(
                category=IssueCategory.BEST_PRACTICE,
                severity=Severity.LOW,
                title="Use of 'var' keyword",
                description="'var' has function scope and can lead to bugs. Use 'let' or 'const' instead.",
                file_path=file_path,
                line_number=line_num,
                suggestion="Replace 'var' with 'let' or 'const'."
            ))

        # Check for == instead of ===
        for match in re.finditer(r'[^=!]==[^=]', code):
            line_num = code[:match.start()].count('\n') + 1
            issues.append(ReviewIssue(
                category=IssueCategory.BUG_RISK,
                severity=Severity.LOW,
                title="Loose equality comparison",
                description="Using == instead of === can lead to unexpected type coercion.",
                file_path=file_path,
                line_number=line_num,
                suggestion="Use === for strict equality comparison."
            ))

        # Check for console.log (should be removed in production)
        for match in re.finditer(r'console\.(log|debug|info|warn|error)\s*\(', code):
            line_num = code[:match.start()].count('\n') + 1
            issues.append(ReviewIssue(
                category=IssueCategory.BEST_PRACTICE,
                severity=Severity.LOW,
                title="Console statement found",
                description="Console statements should be removed or replaced with proper logging in production.",
                file_path=file_path,
                line_number=line_num
            ))

        return issues


class ComplexityAnalyzer:
    """Analyzes code complexity."""

    def analyze_python(self, code: str, file_path: str = "") -> List[ReviewIssue]:
        """Analyze Python code complexity."""
        issues = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check function length
                func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    issues.append(ReviewIssue(
                        category=IssueCategory.MAINTAINABILITY,
                        severity=Severity.MEDIUM,
                        title=f"Long function: {node.name}",
                        description=f"Function '{node.name}' has {func_lines} lines. Consider breaking it down.",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Break the function into smaller, focused functions."
                    ))

                # Check number of arguments
                num_args = len(node.args.args) + len(node.args.kwonlyargs)
                if num_args > 5:
                    issues.append(ReviewIssue(
                        category=IssueCategory.MAINTAINABILITY,
                        severity=Severity.LOW,
                        title=f"Too many arguments: {node.name}",
                        description=f"Function '{node.name}' has {num_args} arguments. Consider using a class or data object.",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Group related arguments into a class or dataclass."
                    ))

                # Check nesting depth (simple approximation)
                max_depth = self._get_max_nesting(node)
                if max_depth > 4:
                    issues.append(ReviewIssue(
                        category=IssueCategory.MAINTAINABILITY,
                        severity=Severity.MEDIUM,
                        title=f"Deep nesting: {node.name}",
                        description=f"Function '{node.name}' has nesting depth of {max_depth}.",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Use early returns or extract nested logic into helper functions."
                    ))

            elif isinstance(node, ast.ClassDef):
                # Check class method count
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    issues.append(ReviewIssue(
                        category=IssueCategory.MAINTAINABILITY,
                        severity=Severity.MEDIUM,
                        title=f"Large class: {node.name}",
                        description=f"Class '{node.name}' has {len(methods)} methods. Consider splitting it.",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="Apply Single Responsibility Principle and split into smaller classes."
                    ))

        return issues

    def _get_max_nesting(self, node, current_depth=0) -> int:
        """Calculate maximum nesting depth."""
        max_depth = current_depth

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                max_depth = max(max_depth, self._get_max_nesting(child, current_depth + 1))
            else:
                max_depth = max(max_depth, self._get_max_nesting(child, current_depth))

        return max_depth


class CodeReviewAgent:
    """Main code review agent that combines all analyzers."""

    def __init__(self):
        self.security_scanner = SecurityScanner()
        self.best_practices = BestPracticesChecker()
        self.complexity = ComplexityAnalyzer()

    def review(self, code: str, language: str, file_path: str = "") -> ReviewReport:
        """Perform comprehensive code review."""
        report = ReviewReport(
            file_path=file_path or "unknown",
            language=language
        )

        # Security scan
        report.issues.extend(self.security_scanner.scan(code, language, file_path))

        # Best practices check
        if language == "python":
            report.issues.extend(self.best_practices.check_python(code, file_path))
            report.issues.extend(self.complexity.analyze_python(code, file_path))
        elif language in ("javascript", "typescript"):
            report.issues.extend(self.best_practices.check_javascript(code, file_path))

        # Calculate score
        report.score = self._calculate_score(report.issues)
        report.passed = report.score >= 60 and not any(
            i.severity in (Severity.CRITICAL, Severity.HIGH) and i.category == IssueCategory.SECURITY
            for i in report.issues
        )

        # Generate summary
        report.summary = self._generate_summary(report)

        return report

    def _calculate_score(self, issues: List[ReviewIssue]) -> int:
        """Calculate quality score based on issues."""
        score = 100

        severity_penalties = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3,
            Severity.INFO: 1
        }

        for issue in issues:
            penalty = severity_penalties.get(issue.severity, 0)
            # Security issues get double penalty
            if issue.category == IssueCategory.SECURITY:
                penalty *= 2
            score -= penalty

        return max(0, score)

    def _generate_summary(self, report: ReviewReport) -> str:
        """Generate human-readable summary."""
        issue_counts = {}
        for issue in report.issues:
            sev = issue.severity.value
            issue_counts[sev] = issue_counts.get(sev, 0) + 1

        parts = []

        if not report.issues:
            parts.append("No issues found. Code looks good!")
        else:
            total = len(report.issues)
            parts.append(f"Found {total} issue(s):")

            for sev in ["critical", "high", "medium", "low", "info"]:
                if sev in issue_counts:
                    parts.append(f"  - {issue_counts[sev]} {sev}")

            security_issues = [i for i in report.issues if i.category == IssueCategory.SECURITY]
            if security_issues:
                parts.append(f"\n⚠️ {len(security_issues)} security-related issue(s) require attention!")

        return "\n".join(parts)

    def review_file(self, file_path: str) -> ReviewReport:
        """Review a file from disk."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        code = path.read_text()

        # Detect language
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
        }
        language = ext_map.get(path.suffix.lower(), 'unknown')

        return self.review(code, language, str(path))

    def review_pr(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Review multiple files (PR review)."""
        reports = []
        total_issues = 0
        critical_count = 0
        high_count = 0

        for file_info in files:
            code = file_info.get('content', '')
            path = file_info.get('path', '')
            language = file_info.get('language', 'unknown')

            if code:
                report = self.review(code, language, path)
                reports.append(report.to_dict())
                total_issues += len(report.issues)
                critical_count += len([i for i in report.issues if i.severity == Severity.CRITICAL])
                high_count += len([i for i in report.issues if i.severity == Severity.HIGH])

        # Determine overall recommendation
        if critical_count > 0:
            recommendation = "REQUEST_CHANGES"
            recommendation_text = "Critical security issues found. Changes required."
        elif high_count > 2:
            recommendation = "REQUEST_CHANGES"
            recommendation_text = "Multiple high-severity issues found. Please address before merging."
        elif total_issues > 10:
            recommendation = "COMMENT"
            recommendation_text = "Several issues found. Consider addressing before merging."
        else:
            recommendation = "APPROVE"
            recommendation_text = "Code looks good. Minor issues can be addressed in future PRs."

        return {
            "files_reviewed": len(reports),
            "total_issues": total_issues,
            "critical_issues": critical_count,
            "high_issues": high_count,
            "recommendation": recommendation,
            "recommendation_text": recommendation_text,
            "reports": reports
        }


# Singleton instance
_review_agent = None

def get_review_agent() -> CodeReviewAgent:
    """Get or create the code review agent instance."""
    global _review_agent
    if _review_agent is None:
        _review_agent = CodeReviewAgent()
    return _review_agent
