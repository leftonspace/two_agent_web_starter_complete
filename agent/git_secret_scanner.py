# git_secret_scanner.py
"""
PHASE 1.4: Git Secret Scanning Module

Automated detection of secrets (API keys, passwords, tokens, private keys)
before Git commits to prevent accidental exposure of sensitive data.

Addresses vulnerability S4: Auto-commit of secrets via git_utils.commit_all().

Features:
- Pattern-based secret detection (API keys, passwords, tokens, private keys)
- Entropy-based detection for high-entropy strings
- File-based allowlisting (.secretsignore)
- Severity classification (high/medium/low)
- Performance optimized (< 2s for 100 files)

Usage:
    >>> from git_secret_scanner import scan_files_for_secrets
    >>> findings = scan_files_for_secrets([Path("sites/my_project")])
    >>> if findings:
    ...     for finding in findings:
    ...         print(f"{finding.file_path}:{finding.line_number} - {finding.secret_type}")
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set

# ══════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════

# Minimum Shannon entropy to flag as potential secret (scale: 0-8)
# Typical values: Random base64 = 5.5+, English text = 4.0-4.5
MIN_ENTROPY = 4.5

# Minimum length for entropy-based detection
MIN_ENTROPY_STRING_LENGTH = 20

# Maximum file size to scan (10MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Binary file extensions to skip
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib",
    ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".avi", ".mov", ".wav",
    ".db", ".sqlite", ".sqlite3",
}

# Filenames that commonly contain secrets
SECRET_FILENAME_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),  # .env, .env.local, .env.production
    re.compile(r"^\.aws/credentials$", re.IGNORECASE),
    re.compile(r"credentials?\.json$", re.IGNORECASE),
    re.compile(r"secrets?\.ya?ml$", re.IGNORECASE),
    re.compile(r"\.pem$", re.IGNORECASE),
    re.compile(r"\.key$", re.IGNORECASE),
    re.compile(r"\.p12$", re.IGNORECASE),
    re.compile(r"\.pfx$", re.IGNORECASE),
    re.compile(r"config\.secret\.", re.IGNORECASE),
    re.compile(r"\.netrc$", re.IGNORECASE),
]


# ══════════════════════════════════════════════════════════════════════
# Data Structures
# ══════════════════════════════════════════════════════════════════════


@dataclass
class SecretFinding:
    """Represents a potential secret found in code."""
    file_path: Path
    line_number: int
    secret_type: str  # 'api_key', 'password', 'private_key', 'token', 'high_entropy', 'secret_file'
    pattern_matched: str
    context: str  # Surrounding code for review (redacted secret)
    severity: str  # 'high', 'medium', 'low'

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"{self.file_path}:{self.line_number} "
            f"[{self.severity.upper()}] {self.secret_type}: {self.pattern_matched}"
        )


# ══════════════════════════════════════════════════════════════════════
# Secret Detection Patterns
# ══════════════════════════════════════════════════════════════════════


class SecretPattern:
    """Defines a secret detection pattern with metadata."""

    def __init__(
        self,
        name: str,
        pattern: re.Pattern,
        severity: str = "high",
        description: str = "",
    ):
        self.name = name
        self.pattern = pattern
        self.severity = severity
        self.description = description


# High-severity patterns (known secret formats)
SECRET_PATTERNS = [
    # OpenAI API Keys
    SecretPattern(
        "openai_api_key",
        re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b"),
        severity="high",
        description="OpenAI API key (sk-...)",
    ),
    SecretPattern(
        "openai_api_key_new",
        re.compile(r"\bsk-proj-[a-zA-Z0-9_-]{20,}\b"),
        severity="high",
        description="OpenAI API key (sk-proj-...)",
    ),

    # Anthropic API Keys
    SecretPattern(
        "anthropic_api_key",
        re.compile(r"\bsk-ant-[a-zA-Z0-9_-]{20,}\b"),
        severity="high",
        description="Anthropic API key",
    ),

    # AWS Credentials
    SecretPattern(
        "aws_access_key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        severity="high",
        description="AWS Access Key ID",
    ),
    SecretPattern(
        "aws_secret_key",
        re.compile(r"aws_secret_access_key\s*=\s*['\"]?([A-Za-z0-9/+=]{40})['\"]?", re.IGNORECASE),
        severity="high",
        description="AWS Secret Access Key",
    ),

    # GitHub Personal Access Tokens
    SecretPattern(
        "github_token",
        re.compile(r"\bghp_[a-zA-Z0-9]{36,}\b"),
        severity="high",
        description="GitHub Personal Access Token",
    ),
    SecretPattern(
        "github_oauth",
        re.compile(r"\bgho_[a-zA-Z0-9]{36,}\b"),
        severity="high",
        description="GitHub OAuth Token",
    ),

    # Generic API Keys (high confidence)
    SecretPattern(
        "generic_api_key",
        re.compile(r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{32,})['\"]", re.IGNORECASE),
        severity="high",
        description="Generic API key",
    ),

    # Private Keys
    SecretPattern(
        "rsa_private_key",
        re.compile(r"-----BEGIN\s+RSA\s+PRIVATE\s+KEY-----"),
        severity="high",
        description="RSA Private Key",
    ),
    SecretPattern(
        "ec_private_key",
        re.compile(r"-----BEGIN\s+EC\s+PRIVATE\s+KEY-----"),
        severity="high",
        description="EC Private Key",
    ),
    SecretPattern(
        "openssh_private_key",
        re.compile(r"-----BEGIN\s+OPENSSH\s+PRIVATE\s+KEY-----"),
        severity="high",
        description="OpenSSH Private Key",
    ),
    SecretPattern(
        "private_key_generic",
        re.compile(r"-----BEGIN\s+PRIVATE\s+KEY-----"),
        severity="high",
        description="Generic Private Key",
    ),

    # Passwords (medium severity - high false positive rate)
    SecretPattern(
        "password_assignment",
        re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*['\"]([^'\"]{8,})['\"]", re.IGNORECASE),
        severity="medium",
        description="Password assignment",
    ),

    # Database Connection Strings
    SecretPattern(
        "database_url",
        re.compile(r"(?:postgresql|mysql|mongodb)://[^\s:]+:[^\s@]+@", re.IGNORECASE),
        severity="high",
        description="Database connection string with credentials",
    ),

    # Generic Bearer Tokens
    SecretPattern(
        "bearer_token",
        re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.=]{20,}", re.IGNORECASE),
        severity="medium",
        description="Bearer token",
    ),

    # JWT Tokens
    SecretPattern(
        "jwt_token",
        re.compile(r"\beyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b"),
        severity="medium",
        description="JWT token",
    ),

    # Slack Tokens
    SecretPattern(
        "slack_token",
        re.compile(r"\bxox[baprs]-[0-9a-zA-Z]{10,}\b"),
        severity="high",
        description="Slack token",
    ),

    # Stripe API Keys
    SecretPattern(
        "stripe_key",
        re.compile(r"\b(?:sk|rk)_live_[0-9a-zA-Z]{24,}\b"),
        severity="high",
        description="Stripe API key",
    ),

    # Generic Secret Environment Variables
    SecretPattern(
        "env_secret_export",
        re.compile(r"export\s+\w+(?:_KEY|_SECRET|_TOKEN|_PASSWORD)\s*=\s*['\"]?([^\s'\"]+)", re.IGNORECASE),
        severity="medium",
        description="Environment variable secret export",
    ),

    # Google API Keys
    SecretPattern(
        "google_api_key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
        severity="high",
        description="Google API key",
    ),

    # Heroku API Keys
    SecretPattern(
        "heroku_api_key",
        re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
        severity="medium",
        description="Heroku API key (UUID format)",
    ),
]


# ══════════════════════════════════════════════════════════════════════
# Entropy Calculation
# ══════════════════════════════════════════════════════════════════════


def calculate_shannon_entropy(text: str) -> float:
    """
    Calculate Shannon entropy of a string (measure of randomness).

    Shannon entropy measures information density. Higher entropy = more random.

    Args:
        text: String to analyze

    Returns:
        Entropy value (0.0 to 8.0 for byte data)

    Examples:
        >>> calculate_shannon_entropy("aaaaaaa")  # Low entropy
        0.0
        >>> calculate_shannon_entropy("abcdefgh")  # Higher entropy
        3.0
        >>> calculate_shannon_entropy("Kj8#mP2$qL9@")  # High entropy (random)
        3.58
    """
    if not text:
        return 0.0

    # Count character frequencies
    frequencies = {}
    for char in text:
        frequencies[char] = frequencies.get(char, 0) + 1

    # Calculate entropy
    entropy = 0.0
    text_len = len(text)

    for count in frequencies.values():
        probability = count / text_len
        if probability > 0:
            entropy -= probability * math.log2(probability)

    return entropy


def extract_potential_secrets_by_entropy(line: str) -> List[str]:
    """
    Extract substrings with high entropy that might be secrets.

    Args:
        line: Line of text to analyze

    Returns:
        List of high-entropy substrings

    Examples:
        >>> extract_potential_secrets_by_entropy("API_KEY=abc123xyz789def456")
        ["abc123xyz789def456"]
    """
    # Extract quoted strings and assignment values
    candidates = []

    # Pattern 1: Quoted strings
    for match in re.finditer(r"['\"]([^'\"]{20,})['\"]", line):
        candidates.append(match.group(1))

    # Pattern 2: Assignment values (key=value)
    for match in re.finditer(r"[:=]\s*([a-zA-Z0-9_\-\.\/+=]{20,})(?:\s|$|,|;)", line):
        candidates.append(match.group(1))

    # Filter by entropy
    high_entropy_strings = []
    for candidate in candidates:
        if len(candidate) >= MIN_ENTROPY_STRING_LENGTH:
            entropy = calculate_shannon_entropy(candidate)
            if entropy >= MIN_ENTROPY:
                high_entropy_strings.append(candidate)

    return high_entropy_strings


# ══════════════════════════════════════════════════════════════════════
# Allowlist Handling
# ══════════════════════════════════════════════════════════════════════


def load_secret_allowlist(root: Path) -> Set[str]:
    """
    Load .secretsignore file for allowlisted paths/patterns.

    Format (similar to .gitignore):
        # Comment
        tests/fixtures/*.json
        examples/sample_api_key.txt  # pragma: allowlist secret

    Args:
        root: Root directory to search for .secretsignore

    Returns:
        Set of allowlisted path patterns
    """
    allowlist_file = root / ".secretsignore"
    allowlist = set()

    if not allowlist_file.exists():
        return allowlist

    try:
        content = allowlist_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
            # Remove inline comments
            if "#" in line:
                line = line.split("#")[0].strip()
            if line:
                allowlist.add(line)
    except Exception as e:
        print(f"[SecretScanner] Warning: Failed to load .secretsignore: {e}")

    return allowlist


def is_path_allowlisted(file_path: Path, root: Path, allowlist: Set[str]) -> bool:
    """
    Check if a file path matches any allowlist pattern.

    Args:
        file_path: File to check
        root: Root directory
        allowlist: Set of allowlist patterns

    Returns:
        True if file is allowlisted
    """
    try:
        # Get relative path from root
        rel_path = file_path.relative_to(root)
        rel_path_str = str(rel_path)

        for pattern in allowlist:
            # Simple glob-like matching
            if "*" in pattern:
                # Convert glob to regex
                regex_pattern = pattern.replace(".", r"\.").replace("*", ".*")
                if re.match(regex_pattern, rel_path_str):
                    return True
            elif rel_path_str == pattern:
                return True

    except ValueError:
        # file_path is not relative to root
        pass

    return False


def is_line_allowlisted(line: str) -> bool:
    """
    Check if a line contains allowlist pragma.

    Args:
        line: Line of text to check

    Returns:
        True if line contains "pragma: allowlist secret" comment
    """
    # Check for pragma comment
    if "pragma:" in line.lower() and "allowlist" in line.lower() and "secret" in line.lower():
        return True

    # Check for example/test markers
    if any(marker in line.lower() for marker in ["example", "test", "sample", "dummy", "fake"]):
        # Only allow if it's in a comment
        if "#" in line or "//" in line or "/*" in line:
            return True

    return False


# ══════════════════════════════════════════════════════════════════════
# File Scanning
# ══════════════════════════════════════════════════════════════════════


def should_scan_file(file_path: Path) -> bool:
    """
    Determine if a file should be scanned for secrets.

    Args:
        file_path: Path to file

    Returns:
        True if file should be scanned
    """
    # Skip if file doesn't exist or is not a file
    if not file_path.is_file():
        return False

    # Skip if file is too large
    try:
        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return False
    except OSError:
        return False

    # Skip binary files by extension
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return False

    # Skip common non-secret directories
    parts = file_path.parts
    skip_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache", ".venv", "venv"}
    if any(part in skip_dirs for part in parts):
        return False

    return True


def scan_file_for_secrets(
    file_path: Path,
    root: Path,
    allowlist: Set[str],
) -> List[SecretFinding]:
    """
    Scan a single file for secrets.

    Args:
        file_path: Path to file to scan
        root: Root directory (for relative path calculation)
        allowlist: Set of allowlisted path patterns

    Returns:
        List of SecretFinding objects
    """
    findings = []

    # Check if entire file is allowlisted
    if is_path_allowlisted(file_path, root, allowlist):
        return findings

    # Check if filename itself is suspicious
    filename = file_path.name
    for pattern in SECRET_FILENAME_PATTERNS:
        if pattern.match(filename):
            findings.append(SecretFinding(
                file_path=file_path,
                line_number=0,
                secret_type="secret_file",
                pattern_matched=filename,
                context=f"Filename matches secret pattern: {pattern.pattern}",
                severity="high",
            ))
            # Don't scan content if filename is flagged (likely entire file is secret)
            return findings

    # Read file content
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[SecretScanner] Warning: Failed to read {file_path}: {e}")
        return findings

    lines = content.splitlines()

    # Scan each line
    for line_num, line in enumerate(lines, start=1):
        # Skip allowlisted lines
        if is_line_allowlisted(line):
            continue

        # Check pattern-based detection
        for secret_pattern in SECRET_PATTERNS:
            matches = secret_pattern.pattern.finditer(line)
            for match in matches:
                # Redact the matched secret for context
                secret_value = match.group(0)
                redacted_context = line.replace(
                    secret_value,
                    f"{secret_value[:4]}...{secret_value[-4:]}" if len(secret_value) > 8 else "***"
                )

                findings.append(SecretFinding(
                    file_path=file_path,
                    line_number=line_num,
                    secret_type=secret_pattern.name,
                    pattern_matched=secret_pattern.description,
                    context=redacted_context.strip(),
                    severity=secret_pattern.severity,
                ))

        # Check entropy-based detection
        high_entropy_strings = extract_potential_secrets_by_entropy(line)
        for secret_value in high_entropy_strings:
            # Skip if already detected by pattern
            already_detected = any(
                f.line_number == line_num and secret_value in line
                for f in findings
            )
            if already_detected:
                continue

            entropy = calculate_shannon_entropy(secret_value)
            redacted_context = line.replace(
                secret_value,
                f"{secret_value[:4]}...{secret_value[-4:]}" if len(secret_value) > 8 else "***"
            )

            findings.append(SecretFinding(
                file_path=file_path,
                line_number=line_num,
                secret_type="high_entropy",
                pattern_matched=f"High entropy string (entropy={entropy:.2f})",
                context=redacted_context.strip(),
                severity="medium",
            ))

    return findings


def scan_files_for_secrets(file_paths: List[Path]) -> List[SecretFinding]:
    """
    Scan multiple files for secrets.

    This is the main entry point for secret scanning.

    Args:
        file_paths: List of file paths to scan

    Returns:
        List of SecretFinding objects

    Examples:
        >>> findings = scan_files_for_secrets([Path("sites/my_project")])
        >>> for finding in findings:
        ...     print(finding)
    """
    all_findings = []

    # Determine root directory (common ancestor)
    if not file_paths:
        return all_findings

    # Get all unique directories
    dirs = {p.parent if p.is_file() else p for p in file_paths}
    # Find common root
    root = Path.cwd()
    for d in dirs:
        try:
            # Try to find a common parent
            if d.exists():
                root = d
                break
        except Exception:
            pass

    # Load allowlist
    allowlist = load_secret_allowlist(root)

    # Scan each path
    for path in file_paths:
        if path.is_file():
            if should_scan_file(path):
                findings = scan_file_for_secrets(path, root, allowlist)
                all_findings.extend(findings)
        elif path.is_dir():
            # Recursively scan directory
            for file_path in path.rglob("*"):
                if should_scan_file(file_path):
                    findings = scan_file_for_secrets(file_path, root, allowlist)
                    all_findings.extend(findings)

    return all_findings


def format_findings_report(findings: List[SecretFinding]) -> str:
    """
    Format findings into a human-readable report.

    Args:
        findings: List of SecretFinding objects

    Returns:
        Formatted report string
    """
    if not findings:
        return "✅ No secrets detected."

    # Group by severity
    high_severity = [f for f in findings if f.severity == "high"]
    medium_severity = [f for f in findings if f.severity == "medium"]
    low_severity = [f for f in findings if f.severity == "low"]

    report_lines = [
        "🚨 SECRET SCANNING: Potential secrets detected!",
        "",
        f"Found {len(findings)} potential secret(s) in {len(set(f.file_path for f in findings))} file(s):",
        "",
    ]

    # High severity findings
    if high_severity:
        report_lines.append("🔴 HIGH SEVERITY:")
        for finding in high_severity:
            report_lines.append(f"  {finding.file_path}:{finding.line_number}")
            report_lines.append(f"    Type: {finding.secret_type}")
            report_lines.append(f"    Pattern: {finding.pattern_matched}")
            report_lines.append(f"    Context: {finding.context}")
            report_lines.append("")

    # Medium severity findings
    if medium_severity:
        report_lines.append("🟡 MEDIUM SEVERITY:")
        for finding in medium_severity:
            report_lines.append(f"  {finding.file_path}:{finding.line_number}")
            report_lines.append(f"    Type: {finding.secret_type}")
            report_lines.append(f"    Pattern: {finding.pattern_matched}")
            report_lines.append("")

    # Low severity findings
    if low_severity:
        report_lines.append("🟢 LOW SEVERITY:")
        for finding in low_severity:
            report_lines.append(f"  {finding.file_path}:{finding.line_number} - {finding.secret_type}")

    report_lines.extend([
        "",
        "⚠️  Remove these secrets before committing.",
        "💡 Tip: Use environment variables or secret management services instead.",
        "",
        "To bypass this check (not recommended):",
        "  - Add file to .secretsignore",
        "  - Add '# pragma: allowlist secret' comment on the line",
        "  - Set git_secret_scanning_enabled: false in config",
    ])

    return "\n".join(report_lines)


# ══════════════════════════════════════════════════════════════════════
# Testing Helpers
# ══════════════════════════════════════════════════════════════════════


def get_scanner_stats() -> dict:
    """
    Get statistics about the scanner configuration.

    Returns:
        Dict with pattern counts and configuration
    """
    return {
        "total_patterns": len(SECRET_PATTERNS),
        "high_severity_patterns": len([p for p in SECRET_PATTERNS if p.severity == "high"]),
        "medium_severity_patterns": len([p for p in SECRET_PATTERNS if p.severity == "medium"]),
        "low_severity_patterns": len([p for p in SECRET_PATTERNS if p.severity == "low"]),
        "min_entropy_threshold": MIN_ENTROPY,
        "min_string_length": MIN_ENTROPY_STRING_LENGTH,
        "max_file_size_mb": MAX_FILE_SIZE_BYTES / (1024 * 1024),
        "binary_extensions_count": len(BINARY_EXTENSIONS),
        "secret_filename_patterns_count": len(SECRET_FILENAME_PATTERNS),
    }
