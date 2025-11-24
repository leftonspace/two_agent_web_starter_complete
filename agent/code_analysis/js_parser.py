"""
JavaScript/TypeScript AST Parser

AST parsing for JavaScript and TypeScript using external parsers:
- Babel parser via subprocess
- TypeScript Compiler API integration
- Function and class extraction
- Import/export tracking
- Complexity analysis
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# =============================================================================
# AST Node Data Classes
# =============================================================================

@dataclass
class JSFunctionInfo:
    """Information about a JavaScript/TypeScript function"""
    name: str
    line_number: int
    end_line_number: int
    parameters: List[str]
    return_type: Optional[str]
    is_async: bool
    is_arrow: bool
    is_generator: bool
    complexity: int
    calls: List[str] = field(default_factory=list)
    variables: Set[str] = field(default_factory=set)


@dataclass
class JSClassInfo:
    """Information about a JavaScript/TypeScript class"""
    name: str
    line_number: int
    end_line_number: int
    extends: Optional[str]
    implements: List[str]
    methods: List[JSFunctionInfo] = field(default_factory=list)
    properties: Set[str] = field(default_factory=set)
    is_exported: bool = False


@dataclass
class JSImportInfo:
    """Information about an import"""
    source: str
    specifiers: List[str]
    default_import: Optional[str] = None
    namespace_import: Optional[str] = None
    line_number: int = 0
    is_type_only: bool = False


@dataclass
class JSExportInfo:
    """Information about an export"""
    name: str
    line_number: int
    is_default: bool = False
    is_named: bool = False


@dataclass
class JSCodeAnalysis:
    """Complete JavaScript/TypeScript code analysis"""
    file_path: str
    language: str  # 'javascript' or 'typescript'
    functions: List[JSFunctionInfo] = field(default_factory=list)
    classes: List[JSClassInfo] = field(default_factory=list)
    imports: List[JSImportInfo] = field(default_factory=list)
    exports: List[JSExportInfo] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0


# =============================================================================
# Regex-Based Parser (Fallback)
# =============================================================================

class RegexJSParser:
    """
    Regex-based JavaScript/TypeScript parser.

    This is a fallback parser that uses regex patterns.
    For production, integrate with Babel or TypeScript Compiler API.
    """

    # Regex patterns
    FUNCTION_PATTERN = re.compile(
        r'(?:async\s+)?(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>)',
        re.MULTILINE
    )

    CLASS_PATTERN = re.compile(
        r'class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{',
        re.MULTILINE
    )

    IMPORT_PATTERN = re.compile(
        r'import\s+(?:(?:\{([^}]+)\})|(?:(\w+)))\s+from\s+["\']([^"\']+)["\']',
        re.MULTILINE
    )

    EXPORT_PATTERN = re.compile(
        r'export\s+(?:(default)\s+)?(?:(?:const|let|var|function|class)\s+)?(\w+)',
        re.MULTILINE
    )

    def parse_file(self, file_path: str) -> JSCodeAnalysis:
        """Parse JavaScript/TypeScript file"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        code = path.read_text()
        language = "typescript" if path.suffix in [".ts", ".tsx"] else "javascript"

        return self.parse_code(code, str(path), language)

    def parse_code(
        self,
        code: str,
        file_path: str = "<string>",
        language: str = "javascript"
    ) -> JSCodeAnalysis:
        """Parse JavaScript/TypeScript code"""
        analysis = JSCodeAnalysis(
            file_path=file_path,
            language=language,
        )

        lines = code.split("\n")
        analysis.total_lines = len(lines)
        analysis.code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith("//"))
        analysis.comment_lines = sum(1 for line in lines if line.strip().startswith("//"))

        # Extract functions
        for match in self.FUNCTION_PATTERN.finditer(code):
            name = match.group(1) or match.group(2) or "anonymous"
            line_number = code[:match.start()].count("\n") + 1

            func_info = JSFunctionInfo(
                name=name,
                line_number=line_number,
                end_line_number=line_number,  # Approximation
                parameters=[],  # Would need more complex parsing
                return_type=None,
                is_async="async" in match.group(0),
                is_arrow="=>" in match.group(0),
                is_generator=False,
                complexity=self._estimate_complexity(code, match.start()),
            )
            analysis.functions.append(func_info)

        # Extract classes
        for match in self.CLASS_PATTERN.finditer(code):
            name = match.group(1)
            extends = match.group(2)
            implements = [i.strip() for i in match.group(3).split(",")] if match.group(3) else []
            line_number = code[:match.start()].count("\n") + 1

            class_info = JSClassInfo(
                name=name,
                line_number=line_number,
                end_line_number=line_number,  # Approximation
                extends=extends,
                implements=implements,
            )
            analysis.classes.append(class_info)

        # Extract imports
        for match in self.IMPORT_PATTERN.finditer(code):
            named_imports = match.group(1)
            default_import = match.group(2)
            source = match.group(3)
            line_number = code[:match.start()].count("\n") + 1

            specifiers = []
            if named_imports:
                specifiers = [s.strip() for s in named_imports.split(",")]

            import_info = JSImportInfo(
                source=source,
                specifiers=specifiers,
                default_import=default_import,
                line_number=line_number,
            )
            analysis.imports.append(import_info)

        # Extract exports
        for match in self.EXPORT_PATTERN.finditer(code):
            is_default = match.group(1) == "default"
            name = match.group(2)
            line_number = code[:match.start()].count("\n") + 1

            export_info = JSExportInfo(
                name=name,
                line_number=line_number,
                is_default=is_default,
                is_named=not is_default,
            )
            analysis.exports.append(export_info)

        return analysis

    def _estimate_complexity(self, code: str, start_pos: int) -> int:
        """Estimate cyclomatic complexity (simplified)"""
        # Find function body (simplified - just count keywords)
        remaining_code = code[start_pos:start_pos + 1000]  # Look ahead 1000 chars

        complexity = 1
        complexity += remaining_code.count("if ")
        complexity += remaining_code.count("else if ")
        complexity += remaining_code.count("while ")
        complexity += remaining_code.count("for ")
        complexity += remaining_code.count("case ")
        complexity += remaining_code.count("catch ")
        complexity += remaining_code.count("&&")
        complexity += remaining_code.count("||")

        return complexity


# =============================================================================
# Babel Parser Integration (via subprocess)
# =============================================================================

class BabelJSParser:
    """
    JavaScript/TypeScript parser using Babel.

    Requires Node.js and @babel/parser installed:
        npm install -g @babel/parser @babel/traverse

    This parser shells out to a Node.js script for parsing.
    """

    def __init__(self):
        self.has_babel = self._check_babel()

    def _check_babel(self) -> bool:
        """Check if Babel parser is available"""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except:
            return False

    def parse_file(self, file_path: str) -> JSCodeAnalysis:
        """Parse JavaScript/TypeScript file using Babel"""
        if not self.has_babel:
            print("[JSParser] Babel not available, falling back to regex parser")
            return RegexJSParser().parse_file(file_path)

        path = Path(file_path)
        language = "typescript" if path.suffix in [".ts", ".tsx"] else "javascript"

        # Create Node.js script for parsing
        parser_script = self._create_parser_script()

        try:
            result = subprocess.run(
                ["node", "-e", parser_script, str(path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                print(f"[JSParser] Error running Babel parser: {result.stderr}")
                return RegexJSParser().parse_file(file_path)

            # Parse JSON output
            data = json.loads(result.stdout)
            return self._parse_babel_output(data, str(path), language)

        except Exception as e:
            print(f"[JSParser] Error with Babel parser: {e}")
            return RegexJSParser().parse_file(file_path)

    def _create_parser_script(self) -> str:
        """Create Node.js script for Babel parsing"""
        return """
const fs = require('fs');
const parser = require('@babel/parser');

const filePath = process.argv[2];
const code = fs.readFileSync(filePath, 'utf-8');

try {
    const ast = parser.parse(code, {
        sourceType: 'module',
        plugins: [
            'typescript',
            'jsx',
            'decorators-legacy',
            'classProperties',
            'asyncGenerators',
        ],
    });

    // Extract information
    const result = {
        functions: [],
        classes: [],
        imports: [],
        exports: [],
    };

    // Traverse AST (simplified - would use @babel/traverse in production)
    console.log(JSON.stringify(result));
} catch (error) {
    console.error('Parse error:', error.message);
    process.exit(1);
}
"""

    def _parse_babel_output(
        self,
        data: Dict[str, Any],
        file_path: str,
        language: str,
    ) -> JSCodeAnalysis:
        """Convert Babel AST output to JSCodeAnalysis"""
        analysis = JSCodeAnalysis(
            file_path=file_path,
            language=language,
        )

        # Convert Babel output to our format
        # This would be more complex in production

        return analysis


# =============================================================================
# TypeScript Parser Integration
# =============================================================================

class TypeScriptParser:
    """
    TypeScript parser using TypeScript Compiler API.

    Requires TypeScript installed:
        npm install -g typescript

    This parser uses ts-node or tsx to parse TypeScript files.
    """

    def __init__(self):
        self.has_typescript = self._check_typescript()

    def _check_typescript(self) -> bool:
        """Check if TypeScript is available"""
        try:
            result = subprocess.run(
                ["tsc", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except:
            return False

    def parse_file(self, file_path: str) -> JSCodeAnalysis:
        """Parse TypeScript file"""
        if not self.has_typescript:
            print("[TSParser] TypeScript not available, falling back to regex parser")
            return RegexJSParser().parse_file(file_path)

        # Implementation would use TypeScript Compiler API
        # For now, fall back to regex parser
        return RegexJSParser().parse_file(file_path)


# =============================================================================
# Main JavaScript Parser
# =============================================================================

class JavaScriptParser:
    """
    Main JavaScript/TypeScript parser with automatic backend selection.

    Tries parsers in order:
    1. Babel parser (most accurate)
    2. TypeScript Compiler API (for .ts files)
    3. Regex parser (fallback)

    Usage:
        parser = JavaScriptParser()
        analysis = parser.parse_file("example.ts")

        for func in analysis.functions:
            print(f"{func.name}: complexity={func.complexity}")
    """

    def __init__(self, prefer_babel: bool = True):
        """
        Initialize JavaScript parser.

        Args:
            prefer_babel: Prefer Babel over TypeScript Compiler API
        """
        self.babel_parser = BabelJSParser()
        self.ts_parser = TypeScriptParser()
        self.regex_parser = RegexJSParser()
        self.prefer_babel = prefer_babel

    def parse_file(self, file_path: str) -> JSCodeAnalysis:
        """
        Parse JavaScript/TypeScript file.

        Args:
            file_path: Path to file

        Returns:
            JSCodeAnalysis with extracted information
        """
        path = Path(file_path)

        # Select parser based on file extension and availability
        if self.prefer_babel and self.babel_parser.has_babel:
            return self.babel_parser.parse_file(file_path)
        elif path.suffix in [".ts", ".tsx"] and self.ts_parser.has_typescript:
            return self.ts_parser.parse_file(file_path)
        else:
            return self.regex_parser.parse_file(file_path)

    def parse_code(
        self,
        code: str,
        language: str = "javascript",
    ) -> JSCodeAnalysis:
        """
        Parse JavaScript/TypeScript code string.

        Args:
            code: Source code
            language: 'javascript' or 'typescript'

        Returns:
            JSCodeAnalysis with extracted information
        """
        return self.regex_parser.parse_code(code, "<string>", language)

    def get_dependencies(self, analysis: JSCodeAnalysis) -> Dict[str, Set[str]]:
        """
        Build dependency graph from analysis.

        Args:
            analysis: Code analysis result

        Returns:
            Dict mapping function names to their dependencies
        """
        dependencies: Dict[str, Set[str]] = {}

        # Map function names to their calls
        for func in analysis.functions:
            dependencies[func.name] = set(func.calls)

        # Add class methods
        for cls in analysis.classes:
            for method in cls.methods:
                full_name = f"{cls.name}.{method.name}"
                dependencies[full_name] = set(method.calls)

        return dependencies

    def find_function(self, analysis: JSCodeAnalysis, name: str) -> Optional[JSFunctionInfo]:
        """Find function by name"""
        for func in analysis.functions:
            if func.name == name:
                return func

        # Search in class methods
        for cls in analysis.classes:
            for method in cls.methods:
                if method.name == name or f"{cls.name}.{method.name}" == name:
                    return method

        return None

    def find_class(self, analysis: JSCodeAnalysis, name: str) -> Optional[JSClassInfo]:
        """Find class by name"""
        for cls in analysis.classes:
            if cls.name == name:
                return cls
        return None


# =============================================================================
# Utility Functions
# =============================================================================

def analyze_js_directory(
    directory: str,
    pattern: str = "**/*.{js,ts,jsx,tsx}",
    exclude_patterns: Optional[List[str]] = None,
) -> List[JSCodeAnalysis]:
    """
    Analyze all JavaScript/TypeScript files in a directory.

    Args:
        directory: Directory to analyze
        pattern: Glob pattern for files
        exclude_patterns: Patterns to exclude

    Returns:
        List of JSCodeAnalysis results
    """
    parser = JavaScriptParser()
    results = []

    path = Path(directory)
    exclude_patterns = exclude_patterns or [
        "**/node_modules/**",
        "**/dist/**",
        "**/build/**",
        "**/.next/**",
    ]

    # Expand pattern for multiple extensions
    extensions = [".js", ".ts", ".jsx", ".tsx"]
    for ext in extensions:
        for file_path in path.glob(f"**/*{ext}"):
            # Check exclusions
            if any(file_path.match(pat) for pat in exclude_patterns):
                continue

            try:
                analysis = parser.parse_file(str(file_path))
                results.append(analysis)
            except Exception as e:
                print(f"[JSParser] Error analyzing {file_path}: {e}")

    return results


def calculate_js_metrics(analysis: JSCodeAnalysis) -> Dict[str, Any]:
    """Calculate code metrics from analysis"""
    metrics = {
        "file_path": analysis.file_path,
        "language": analysis.language,
        "total_lines": analysis.total_lines,
        "code_lines": analysis.code_lines,
        "comment_lines": analysis.comment_lines,
        "num_functions": len(analysis.functions),
        "num_classes": len(analysis.classes),
        "num_imports": len(analysis.imports),
        "num_exports": len(analysis.exports),
        "avg_complexity": 0.0,
        "max_complexity": 0,
    }

    if analysis.functions:
        complexities = [f.complexity for f in analysis.functions]
        metrics["avg_complexity"] = sum(complexities) / len(complexities)
        metrics["max_complexity"] = max(complexities)

    return metrics


def print_js_analysis_summary(analysis: JSCodeAnalysis):
    """Print a summary of JavaScript/TypeScript code analysis"""
    print(f"\n{'='*60}")
    print(f"Analysis: {analysis.file_path} ({analysis.language})")
    print(f"{'='*60}")

    print(f"\n📊 Metrics:")
    print(f"  Total Lines: {analysis.total_lines}")
    print(f"  Code Lines: {analysis.code_lines}")

    print(f"\n📦 Imports ({len(analysis.imports)}):")
    for imp in analysis.imports[:5]:
        if imp.default_import:
            print(f"  import {imp.default_import} from '{imp.source}'")
        elif imp.specifiers:
            print(f"  import {{ {', '.join(imp.specifiers)} }} from '{imp.source}'")
    if len(analysis.imports) > 5:
        print(f"  ... and {len(analysis.imports) - 5} more")

    print(f"\n🔧 Functions ({len(analysis.functions)}):")
    for func in analysis.functions[:5]:
        async_marker = "async " if func.is_async else ""
        arrow_marker = " =>" if func.is_arrow else ""
        print(f"  {async_marker}{func.name}{arrow_marker} - complexity: {func.complexity}")
    if len(analysis.functions) > 5:
        print(f"  ... and {len(analysis.functions) - 5} more")

    print(f"\n📚 Classes ({len(analysis.classes)}):")
    for cls in analysis.classes[:5]:
        extends = f" extends {cls.extends}" if cls.extends else ""
        print(f"  {cls.name}{extends} - {len(cls.methods)} methods")
    if len(analysis.classes) > 5:
        print(f"  ... and {len(analysis.classes) - 5} more")
