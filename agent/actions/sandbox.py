"""
Sandbox utilities for secure code execution.

PHASE 8.1: Provides security controls for code execution including
import validation, resource limits, and isolation.
"""

import re
from typing import Set, List, Optional


# Dangerous Python modules that should never be imported
DANGEROUS_MODULES = {
    "os",
    "sys",
    "subprocess",
    "importlib",
    "__import__",
    "eval",
    "exec",
    "compile",
    "open",
    "file",
    "input",
    "raw_input",
    "reload",
    "shutil",
    "glob",
    "pickle",
    "shelve",
    "socket",
    "urllib",
    "requests",
    "httplib",
    "ftplib",
    "telnetlib",
    "smtplib",
    "ctypes",
    "multiprocessing",
    "threading",
    "pty",
    "rlcompleter"
}

# Safe Python modules that are allowed
SAFE_MODULES = {
    "math",
    "random",
    "datetime",
    "time",
    "json",
    "re",
    "collections",
    "itertools",
    "functools",
    "operator",
    "string",
    "textwrap",
    "struct",
    "codecs",
    "base64",
    "hashlib",
    "hmac",
    "uuid",
    "decimal",
    "fractions",
    "statistics",
    "array",
    "bisect",
    "heapq",
    "enum",
    "typing"
}

# Whitelisted shell commands (read-only operations)
SAFE_SHELL_COMMANDS = {
    "ls",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "wc",
    "sort",
    "uniq",
    "diff",
    "echo",
    "pwd",
    "which",
    "whoami",
    "date",
    "df",
    "du",
    "file",
    "stat"
}

# Dangerous shell command patterns
DANGEROUS_SHELL_PATTERNS = [
    r"rm\s",
    r"mv\s",
    r"cp\s.*>",
    r"dd\s",
    r"mkfs",
    r"fdisk",
    r"mount",
    r"umount",
    r"kill",
    r"pkill",
    r"reboot",
    r"shutdown",
    r"init\s",
    r">\s*/dev/",
    r"curl.*\|",
    r"wget.*\|",
    r"nc\s",
    r"netcat",
    r"telnet",
    r"ssh",
    r"scp",
    r"rsync",
    r"chmod",
    r"chown",
    r"su\s",
    r"sudo",
    r";\s*rm",
    r"&&\s*rm",
    r"\|\s*sh",
    r"\|\s*bash",
    r"`.*`",
    r"\$\(",
]


class SandboxValidator:
    """Validates code for safe execution"""

    @staticmethod
    def validate_python_imports(code: str) -> tuple[bool, List[str]]:
        """
        Validate Python imports are safe.

        Returns:
            (is_safe, list_of_violations)
        """
        violations = []

        # Check for dangerous imports
        import_pattern = r"(?:^|\n)\s*(?:import|from)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        matches = re.finditer(import_pattern, code)

        for match in matches:
            module = match.group(1)
            if module in DANGEROUS_MODULES:
                violations.append(f"Dangerous module import: {module}")

        # Check for __import__ calls
        if "__import__" in code:
            violations.append("Direct use of __import__ not allowed")

        # Check for eval/exec
        if re.search(r"\beval\s*\(", code):
            violations.append("Use of eval() not allowed")
        if re.search(r"\bexec\s*\(", code):
            violations.append("Use of exec() not allowed")

        # Check for compile
        if re.search(r"\bcompile\s*\(", code):
            violations.append("Use of compile() not allowed")

        # Check for open/file
        if re.search(r"\bopen\s*\(", code):
            violations.append("File operations not allowed (use provided APIs)")
        if re.search(r"\bfile\s*\(", code):
            violations.append("File operations not allowed (use provided APIs)")

        return len(violations) == 0, violations

    @staticmethod
    def validate_shell_command(command: str) -> tuple[bool, List[str]]:
        """
        Validate shell command is safe.

        Returns:
            (is_safe, list_of_violations)
        """
        violations = []

        # Get first command (before pipes/redirects)
        base_command = command.split()[0] if command.split() else ""

        # Check if base command is in whitelist
        if base_command not in SAFE_SHELL_COMMANDS:
            violations.append(f"Command not whitelisted: {base_command}")

        # Check for dangerous patterns
        for pattern in DANGEROUS_SHELL_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                violations.append(f"Dangerous pattern detected: {pattern}")

        # Check for output redirection to sensitive locations
        if re.search(r">\s*/etc/", command):
            violations.append("Output redirection to /etc/ not allowed")
        if re.search(r">\s*/sys/", command):
            violations.append("Output redirection to /sys/ not allowed")

        return len(violations) == 0, violations

    @staticmethod
    def sanitize_python_code(code: str) -> str:
        """
        Sanitize Python code by removing dangerous constructs.

        Note: This is a last-resort safety measure. Code should be
        validated before execution.
        """
        # Remove import statements for dangerous modules
        for module in DANGEROUS_MODULES:
            code = re.sub(
                rf"(?:^|\n)\s*(?:import\s+{module}|from\s+{module}\s+import.*)",
                "",
                code
            )

        return code

    @staticmethod
    def validate_resource_limits(
        timeout: int,
        max_memory_mb: Optional[int] = None
    ) -> tuple[bool, List[str]]:
        """
        Validate resource limits are reasonable.

        Returns:
            (is_valid, list_of_issues)
        """
        issues = []

        # Check timeout
        if timeout <= 0:
            issues.append("Timeout must be positive")
        if timeout > 300:  # 5 minutes max
            issues.append("Timeout too large (max 300 seconds)")

        # Check memory limit
        if max_memory_mb is not None:
            if max_memory_mb <= 0:
                issues.append("Memory limit must be positive")
            if max_memory_mb > 1024:  # 1GB max
                issues.append("Memory limit too large (max 1024 MB)")

        return len(issues) == 0, issues


def create_restricted_python_globals() -> dict:
    """
    Create restricted globals for Python execution.

    Provides safe built-ins only.
    """
    safe_builtins = {
        "abs": abs,
        "all": all,
        "any": any,
        "bin": bin,
        "bool": bool,
        "bytes": bytes,
        "chr": chr,
        "dict": dict,
        "divmod": divmod,
        "enumerate": enumerate,
        "filter": filter,
        "float": float,
        "format": format,
        "frozenset": frozenset,
        "hex": hex,
        "int": int,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "iter": iter,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "next": next,
        "oct": oct,
        "ord": ord,
        "pow": pow,
        "print": print,
        "range": range,
        "repr": repr,
        "reversed": reversed,
        "round": round,
        "set": set,
        "slice": slice,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "type": type,
        "zip": zip,
        "__name__": "__main__",
        "__builtins__": {}
    }

    return safe_builtins
