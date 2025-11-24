"""
Static Code Analysis Integration

Integrates multiple static analysis tools:
- Semgrep: Pattern-based security and quality checks
- Pylint: Python linting and code quality
- Mypy: Static type checking
- Bandit: Security vulnerability detection
- Radon: Code complexity metrics
- Safety: Dependency vulnerability scanning

Provides unified interface for running analysis and aggregating results.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# Configuration
# =============================================================================

class Severity(Enum):
    """Issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AnalyzerType(Enum):
    """Supported static analyzers"""
    SEMGREP = "semgrep"
    PYLINT = "pylint"
    MYPY = "mypy"
    BANDIT = "bandit"
    RADON = "radon"
    SAFETY = "safety"
    FLAKE8 = "flake8"


@dataclass
class AnalysisConfig:
    """Configuration for static analysis"""

    # Analyzers to run
    enabled_analyzers: List[AnalyzerType] = field(default_factory=lambda: [
        AnalyzerType.SEMGREP,
        AnalyzerType.PYLINT,
        AnalyzerType.MYPY,
        AnalyzerType.BANDIT,
    ])

    # Paths
    target_path: Path = Path(".")
    exclude_paths: List[str] = field(default_factory=lambda: [
        "**/__pycache__/**",
        "**/node_modules/**",
        "**/.git/**",
        "**/venv/**",
        "**/.venv/**",
        "**/dist/**",
        "**/build/**",
    ])

    # Semgrep configuration
    semgrep_rules: List[str] = field(default_factory=lambda: [
        "p/security-audit",
        "p/python",
        "p/django",
        "p/flask",
    ])
    semgrep_config: Optional[Path] = None

    # Severity thresholds
    fail_on_severity: Severity = Severity.ERROR
    max_warnings: Optional[int] = None  # Fail if warnings exceed this

    # Output
    output_format: str = "json"  # json, text, sarif
    output_file: Optional[Path] = None


@dataclass
class Finding:
    """Static analysis finding"""
    analyzer: AnalyzerType
    severity: Severity
    message: str
    file_path: str
    line_number: int
    column: Optional[int] = None
    rule_id: Optional[str] = None
    fix_suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    cwe_id: Optional[str] = None  # CWE (Common Weakness Enumeration)
    owasp_category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "analyzer": self.analyzer.value,
            "severity": self.severity.value,
            "message": self.message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column": self.column,
            "rule_id": self.rule_id,
            "fix_suggestion": self.fix_suggestion,
            "code_snippet": self.code_snippet,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
        }


@dataclass
class AnalysisReport:
    """Aggregated analysis report"""
    findings: List[Finding] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    passed: bool = True

    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        """Get findings by severity"""
        return [f for f in self.findings if f.severity == severity]

    def get_findings_by_analyzer(self, analyzer: AnalyzerType) -> List[Finding]:
        """Get findings by analyzer"""
        return [f for f in self.findings if f.analyzer == analyzer]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "stats": self.stats,
            "execution_time": self.execution_time,
            "passed": self.passed,
            "summary": {
                "total": len(self.findings),
                "critical": len(self.get_findings_by_severity(Severity.CRITICAL)),
                "error": len(self.get_findings_by_severity(Severity.ERROR)),
                "warning": len(self.get_findings_by_severity(Severity.WARNING)),
                "info": len(self.get_findings_by_severity(Severity.INFO)),
            }
        }


# =============================================================================
# Static Analyzer
# =============================================================================

class StaticAnalyzer:
    """
    Unified static analysis runner.

    Runs multiple static analysis tools and aggregates results.

    Usage:
        analyzer = StaticAnalyzer()

        # Run all configured analyzers
        report = analyzer.analyze()

        # Check if passed
        if report.passed:
            print("✅ Analysis passed!")
        else:
            print(f"❌ Found {len(report.findings)} issues")

        # View findings
        for finding in report.findings:
            print(f"{finding.severity.value}: {finding.message}")
            print(f"  {finding.file_path}:{finding.line_number}")
    """

    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize static analyzer.

        Args:
            config: Analysis configuration
        """
        self.config = config or AnalysisConfig()
        self._check_tool_availability()

        print(f"[StaticAnalyzer] Initialized with {len(self.config.enabled_analyzers)} analyzers")

    def _check_tool_availability(self):
        """Check which tools are available"""
        available = []

        for analyzer in self.config.enabled_analyzers:
            if self._is_tool_available(analyzer):
                available.append(analyzer)
            else:
                print(f"[StaticAnalyzer] Warning: {analyzer.value} not available, skipping")

        self.config.enabled_analyzers = available

        if not available:
            print("[StaticAnalyzer] Warning: No analyzers available!")

    def _is_tool_available(self, analyzer: AnalyzerType) -> bool:
        """Check if analyzer tool is installed"""
        tool_commands = {
            AnalyzerType.SEMGREP: "semgrep",
            AnalyzerType.PYLINT: "pylint",
            AnalyzerType.MYPY: "mypy",
            AnalyzerType.BANDIT: "bandit",
            AnalyzerType.RADON: "radon",
            AnalyzerType.SAFETY: "safety",
            AnalyzerType.FLAKE8: "flake8",
        }

        try:
            cmd = tool_commands[analyzer]
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    # =========================================================================
    # Analysis Execution
    # =========================================================================

    def analyze(self) -> AnalysisReport:
        """
        Run all enabled analyzers and aggregate results.

        Returns:
            AnalysisReport with all findings
        """
        import time
        start_time = time.time()

        report = AnalysisReport()

        print(f"\n[StaticAnalyzer] Running analysis on {self.config.target_path}...")

        # Run each analyzer
        for analyzer in self.config.enabled_analyzers:
            print(f"  Running {analyzer.value}...")

            try:
                findings = self._run_analyzer(analyzer)
                report.findings.extend(findings)
                print(f"    Found {len(findings)} issues")

            except Exception as e:
                print(f"    Error: {e}")

        # Calculate stats
        report.execution_time = time.time() - start_time
        report.stats = self._calculate_stats(report)

        # Determine pass/fail
        report.passed = self._evaluate_pass_fail(report)

        print(f"\n[StaticAnalyzer] Analysis complete in {report.execution_time:.2f}s")
        print(f"  Total issues: {len(report.findings)}")
        print(f"  Status: {'✅ PASSED' if report.passed else '❌ FAILED'}")

        # Write report if configured
        if self.config.output_file:
            self._write_report(report)

        return report

    def _run_analyzer(self, analyzer: AnalyzerType) -> List[Finding]:
        """Run specific analyzer and parse results"""
        if analyzer == AnalyzerType.SEMGREP:
            return self._run_semgrep()
        elif analyzer == AnalyzerType.PYLINT:
            return self._run_pylint()
        elif analyzer == AnalyzerType.MYPY:
            return self._run_mypy()
        elif analyzer == AnalyzerType.BANDIT:
            return self._run_bandit()
        elif analyzer == AnalyzerType.RADON:
            return self._run_radon()
        elif analyzer == AnalyzerType.SAFETY:
            return self._run_safety()
        elif analyzer == AnalyzerType.FLAKE8:
            return self._run_flake8()
        else:
            return []

    # =========================================================================
    # Semgrep
    # =========================================================================

    def _run_semgrep(self) -> List[Finding]:
        """Run Semgrep security analysis"""
        findings = []

        # Build command
        cmd = ["semgrep", "scan", str(self.config.target_path), "--json"]

        # Add rules
        for rule in self.config.semgrep_rules:
            cmd.extend(["--config", rule])

        # Add config file if specified
        if self.config.semgrep_config:
            cmd.extend(["--config", str(self.config.semgrep_config)])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
            )

            if result.stdout:
                data = json.loads(result.stdout)

                for match in data.get("results", []):
                    findings.append(Finding(
                        analyzer=AnalyzerType.SEMGREP,
                        severity=self._map_semgrep_severity(match.get("extra", {}).get("severity", "WARNING")),
                        message=match.get("extra", {}).get("message", "Semgrep finding"),
                        file_path=match.get("path", ""),
                        line_number=match.get("start", {}).get("line", 0),
                        column=match.get("start", {}).get("col"),
                        rule_id=match.get("check_id"),
                        code_snippet=match.get("extra", {}).get("lines"),
                        cwe_id=match.get("extra", {}).get("metadata", {}).get("cwe"),
                        owasp_category=match.get("extra", {}).get("metadata", {}).get("owasp"),
                    ))

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"      Semgrep error: {e}")

        return findings

    def _map_semgrep_severity(self, sem_severity: str) -> Severity:
        """Map Semgrep severity to our enum"""
        mapping = {
            "ERROR": Severity.ERROR,
            "WARNING": Severity.WARNING,
            "INFO": Severity.INFO,
        }
        return mapping.get(sem_severity.upper(), Severity.WARNING)

    # =========================================================================
    # Pylint
    # =========================================================================

    def _run_pylint(self) -> List[Finding]:
        """Run Pylint code quality analysis"""
        findings = []

        cmd = [
            "pylint",
            str(self.config.target_path),
            "--output-format=json",
            "--reports=no",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.stdout:
                data = json.loads(result.stdout)

                for issue in data:
                    findings.append(Finding(
                        analyzer=AnalyzerType.PYLINT,
                        severity=self._map_pylint_severity(issue.get("type", "warning")),
                        message=issue.get("message", ""),
                        file_path=issue.get("path", ""),
                        line_number=issue.get("line", 0),
                        column=issue.get("column"),
                        rule_id=issue.get("message-id"),
                    ))

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"      Pylint error: {e}")

        return findings

    def _map_pylint_severity(self, pylint_type: str) -> Severity:
        """Map Pylint severity to our enum"""
        mapping = {
            "error": Severity.ERROR,
            "warning": Severity.WARNING,
            "refactor": Severity.INFO,
            "convention": Severity.INFO,
        }
        return mapping.get(pylint_type.lower(), Severity.INFO)

    # =========================================================================
    # Mypy
    # =========================================================================

    def _run_mypy(self) -> List[Finding]:
        """Run Mypy static type checking"""
        findings = []

        cmd = [
            "mypy",
            str(self.config.target_path),
            "--no-error-summary",
            "--show-column-numbers",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Parse mypy output (format: file:line:col: severity: message)
            for line in result.stdout.split("\n"):
                if line.strip():
                    findings.append(self._parse_mypy_line(line))

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"      Mypy error: {e}")

        return [f for f in findings if f]  # Filter None

    def _parse_mypy_line(self, line: str) -> Optional[Finding]:
        """Parse mypy output line"""
        parts = line.split(":", 4)
        if len(parts) >= 4:
            return Finding(
                analyzer=AnalyzerType.MYPY,
                severity=Severity.ERROR if "error" in parts[3] else Severity.WARNING,
                message=parts[4].strip() if len(parts) > 4 else "",
                file_path=parts[0],
                line_number=int(parts[1]) if parts[1].isdigit() else 0,
                column=int(parts[2]) if parts[2].isdigit() else None,
            )
        return None

    # =========================================================================
    # Bandit
    # =========================================================================

    def _run_bandit(self) -> List[Finding]:
        """Run Bandit security analysis"""
        findings = []

        cmd = [
            "bandit",
            "-r", str(self.config.target_path),
            "-f", "json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.stdout:
                data = json.loads(result.stdout)

                for issue in data.get("results", []):
                    findings.append(Finding(
                        analyzer=AnalyzerType.BANDIT,
                        severity=self._map_bandit_severity(issue.get("issue_severity", "LOW")),
                        message=issue.get("issue_text", ""),
                        file_path=issue.get("filename", ""),
                        line_number=issue.get("line_number", 0),
                        rule_id=issue.get("test_id"),
                        code_snippet=issue.get("code"),
                        cwe_id=issue.get("issue_cwe", {}).get("id"),
                    ))

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"      Bandit error: {e}")

        return findings

    def _map_bandit_severity(self, bandit_severity: str) -> Severity:
        """Map Bandit severity to our enum"""
        mapping = {
            "HIGH": Severity.ERROR,
            "MEDIUM": Severity.WARNING,
            "LOW": Severity.INFO,
        }
        return mapping.get(bandit_severity.upper(), Severity.INFO)

    # =========================================================================
    # Radon
    # =========================================================================

    def _run_radon(self) -> List[Finding]:
        """Run Radon complexity analysis"""
        findings = []

        cmd = [
            "radon",
            "cc",
            str(self.config.target_path),
            "-j",
            "-n", "C",  # Only show C and above (complex)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.stdout:
                data = json.loads(result.stdout)

                for file_path, functions in data.items():
                    for func in functions:
                        if func.get("complexity", 0) >= 10:  # Threshold for complex
                            findings.append(Finding(
                                analyzer=AnalyzerType.RADON,
                                severity=Severity.WARNING if func["complexity"] < 20 else Severity.ERROR,
                                message=f"High complexity: {func['complexity']} (recommended: <10)",
                                file_path=file_path,
                                line_number=func.get("lineno", 0),
                                rule_id="CC",
                            ))

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"      Radon error: {e}")

        return findings

    # =========================================================================
    # Safety
    # =========================================================================

    def _run_safety(self) -> List[Finding]:
        """Run Safety dependency vulnerability scan"""
        findings = []

        cmd = ["safety", "check", "--json"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                data = json.loads(result.stdout)

                for vuln in data:
                    findings.append(Finding(
                        analyzer=AnalyzerType.SAFETY,
                        severity=Severity.CRITICAL,
                        message=f"Vulnerable dependency: {vuln.get('package')} {vuln.get('installed_version')}",
                        file_path="requirements.txt",
                        line_number=0,
                        rule_id=vuln.get("vulnerability_id"),
                        fix_suggestion=f"Upgrade to {vuln.get('safe_version')}",
                    ))

        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            print(f"      Safety error: {e}")

        return findings

    # =========================================================================
    # Flake8
    # =========================================================================

    def _run_flake8(self) -> List[Finding]:
        """Run Flake8 style checking"""
        findings = []

        cmd = [
            "flake8",
            str(self.config.target_path),
            "--format=json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Flake8 doesn't have native JSON output, parse text
            for line in result.stdout.split("\n"):
                if line.strip():
                    finding = self._parse_flake8_line(line)
                    if finding:
                        findings.append(finding)

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"      Flake8 error: {e}")

        return findings

    def _parse_flake8_line(self, line: str) -> Optional[Finding]:
        """Parse flake8 output line"""
        # Format: file:line:col: code message
        parts = line.split(":", 3)
        if len(parts) >= 4:
            return Finding(
                analyzer=AnalyzerType.FLAKE8,
                severity=Severity.WARNING,
                message=parts[3].strip(),
                file_path=parts[0],
                line_number=int(parts[1]) if parts[1].isdigit() else 0,
                column=int(parts[2]) if parts[2].isdigit() else None,
            )
        return None

    # =========================================================================
    # Report Generation
    # =========================================================================

    def _calculate_stats(self, report: AnalysisReport) -> Dict[str, Any]:
        """Calculate statistics for report"""
        stats = {
            "total_findings": len(report.findings),
            "by_severity": {
                "critical": len(report.get_findings_by_severity(Severity.CRITICAL)),
                "error": len(report.get_findings_by_severity(Severity.ERROR)),
                "warning": len(report.get_findings_by_severity(Severity.WARNING)),
                "info": len(report.get_findings_by_severity(Severity.INFO)),
            },
            "by_analyzer": {},
        }

        for analyzer in AnalyzerType:
            count = len(report.get_findings_by_analyzer(analyzer))
            if count > 0:
                stats["by_analyzer"][analyzer.value] = count

        return stats

    def _evaluate_pass_fail(self, report: AnalysisReport) -> bool:
        """Determine if analysis passed"""
        # Check critical/error threshold
        critical_count = len(report.get_findings_by_severity(Severity.CRITICAL))
        error_count = len(report.get_findings_by_severity(Severity.ERROR))

        if self.config.fail_on_severity == Severity.CRITICAL:
            if critical_count > 0:
                return False
        elif self.config.fail_on_severity == Severity.ERROR:
            if critical_count > 0 or error_count > 0:
                return False

        # Check warning threshold
        if self.config.max_warnings:
            warning_count = len(report.get_findings_by_severity(Severity.WARNING))
            if warning_count > self.config.max_warnings:
                return False

        return True

    def _write_report(self, report: AnalysisReport):
        """Write report to file"""
        output_file = self.config.output_file

        if self.config.output_format == "json":
            output_file.write_text(json.dumps(report.to_dict(), indent=2))
        else:
            # Text format
            lines = [
                "="*60,
                "Static Analysis Report",
                "="*60,
                f"\nTotal Issues: {len(report.findings)}",
                f"Execution Time: {report.execution_time:.2f}s",
                f"Status: {'PASSED' if report.passed else 'FAILED'}",
                "\nSummary by Severity:",
            ]

            for severity in [Severity.CRITICAL, Severity.ERROR, Severity.WARNING, Severity.INFO]:
                count = len(report.get_findings_by_severity(severity))
                lines.append(f"  {severity.value.upper()}: {count}")

            lines.append("\nFindings:\n")

            for finding in report.findings:
                lines.append(f"{finding.severity.value.upper()}: {finding.message}")
                lines.append(f"  {finding.file_path}:{finding.line_number}")
                if finding.rule_id:
                    lines.append(f"  Rule: {finding.rule_id}")
                lines.append("")

            output_file.write_text("\n".join(lines))

        print(f"[StaticAnalyzer] Report written to {output_file}")


# =============================================================================
# Convenience Functions
# =============================================================================

def analyze(
    path: str | Path = ".",
    config: Optional[AnalysisConfig] = None,
) -> AnalysisReport:
    """
    Run static analysis (convenience function).

    Args:
        path: Path to analyze
        config: Analysis configuration

    Returns:
        AnalysisReport with findings

    Example:
        report = analyze("agent/")
        if not report.passed:
            for finding in report.findings:
                print(f"{finding.severity}: {finding.message}")
    """
    if config is None:
        config = AnalysisConfig()

    config.target_path = Path(path)

    analyzer = StaticAnalyzer(config)
    return analyzer.analyze()


# =============================================================================
# CLI for Testing
# =============================================================================

def test_static_analyzer():
    """Test static analyzer"""
    import sys

    print("\n" + "="*60)
    print("Static Analyzer - Test Mode")
    print("="*60 + "\n")

    path = sys.argv[1] if len(sys.argv) > 1 else "."

    print(f"Analyzing: {path}\n")

    report = analyze(path)

    print("\n" + "="*60)
    print("Analysis Summary")
    print("="*60)
    print(f"\nTotal issues: {len(report.findings)}")
    print(f"Status: {'✅ PASSED' if report.passed else '❌ FAILED'}")
    print(f"\nBy severity:")
    for severity in [Severity.CRITICAL, Severity.ERROR, Severity.WARNING, Severity.INFO]:
        count = len(report.get_findings_by_severity(severity))
        print(f"  {severity.value}: {count}")

    if not report.passed:
        print("\n" + "="*60)
        print("Top Issues")
        print("="*60)
        for finding in report.findings[:10]:  # Show first 10
            print(f"\n{finding.severity.value.upper()}: {finding.message}")
            print(f"  {finding.file_path}:{finding.line_number}")
            if finding.rule_id:
                print(f"  Rule: {finding.rule_id}")

    sys.exit(0 if report.passed else 1)


if __name__ == "__main__":
    test_static_analyzer()
