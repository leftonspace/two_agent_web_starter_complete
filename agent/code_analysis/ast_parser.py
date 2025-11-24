"""
Python AST Parser and Analysis

Complete Abstract Syntax Tree parsing for Python code with:
- Function and class extraction
- Variable and import tracking
- Complexity analysis
- Dependency graph generation
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# =============================================================================
# AST Node Data Classes
# =============================================================================

@dataclass
class FunctionInfo:
    """Information about a function"""
    name: str
    line_number: int
    end_line_number: int
    parameters: List[str]
    return_type: Optional[str]
    decorators: List[str]
    docstring: Optional[str]
    is_async: bool
    complexity: int
    calls: List[str] = field(default_factory=list)
    variables: Set[str] = field(default_factory=set)


@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    line_number: int
    end_line_number: int
    base_classes: List[str]
    decorators: List[str]
    docstring: Optional[str]
    methods: List[FunctionInfo] = field(default_factory=list)
    attributes: Set[str] = field(default_factory=set)
    is_dataclass: bool = False


@dataclass
class ImportInfo:
    """Information about an import"""
    module: str
    names: List[str]
    is_from_import: bool
    alias: Optional[str] = None
    line_number: int = 0


@dataclass
class VariableInfo:
    """Information about a variable"""
    name: str
    line_number: int
    type_annotation: Optional[str] = None
    value: Optional[str] = None
    scope: str = "module"  # module, class, function


@dataclass
class CodeAnalysis:
    """Complete code analysis result"""
    file_path: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    variables: List[VariableInfo] = field(default_factory=list)
    docstring: Optional[str] = None
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0


# =============================================================================
# AST Visitors
# =============================================================================

class ComplexityVisitor(ast.NodeVisitor):
    """Calculate cyclomatic complexity"""

    def __init__(self):
        self.complexity = 1  # Start with 1

    def visit_If(self, node: ast.If):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.complexity += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        # Each boolean operator adds complexity
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        # Each comparison adds complexity
        self.complexity += len(node.ops)
        self.generic_visit(node)


class CallVisitor(ast.NodeVisitor):
    """Extract function calls"""

    def __init__(self):
        self.calls: List[str] = []

    def visit_Call(self, node: ast.Call):
        # Extract function name
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like obj.method()
            if isinstance(node.func.value, ast.Name):
                self.calls.append(f"{node.func.value.id}.{node.func.attr}")
            else:
                self.calls.append(node.func.attr)

        self.generic_visit(node)


class VariableVisitor(ast.NodeVisitor):
    """Extract variable usage"""

    def __init__(self):
        self.variables: Set[str] = set()

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Store):
            self.variables.add(node.id)
        self.generic_visit(node)


# =============================================================================
# Python AST Parser
# =============================================================================

class PythonASTParser:
    """
    Python AST parser with comprehensive code analysis.

    Features:
    - Function and class extraction
    - Import tracking
    - Variable analysis
    - Complexity calculation
    - Dependency graph generation

    Usage:
        parser = PythonASTParser()
        analysis = parser.parse_file("example.py")

        for func in analysis.functions:
            print(f"{func.name}: complexity={func.complexity}")
    """

    def __init__(self):
        self.tree: Optional[ast.AST] = None

    def parse_file(self, file_path: str) -> CodeAnalysis:
        """
        Parse Python file and extract analysis.

        Args:
            file_path: Path to Python file

        Returns:
            CodeAnalysis with all extracted information
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        code = path.read_text()
        return self.parse_code(code, str(path))

    def parse_code(self, code: str, file_path: str = "<string>") -> CodeAnalysis:
        """
        Parse Python code string.

        Args:
            code: Python source code
            file_path: Optional file path for reference

        Returns:
            CodeAnalysis with all extracted information
        """
        try:
            self.tree = ast.parse(code)
        except SyntaxError as e:
            print(f"[PythonAST] Syntax error in {file_path}: {e}")
            return CodeAnalysis(file_path=file_path)

        analysis = CodeAnalysis(file_path=file_path)

        # Extract module docstring
        analysis.docstring = ast.get_docstring(self.tree)

        # Count lines
        lines = code.split("\n")
        analysis.total_lines = len(lines)
        analysis.code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))
        analysis.comment_lines = sum(1 for line in lines if line.strip().startswith("#"))

        # Extract elements
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only process top-level functions and methods
                if self._is_top_level_or_method(node):
                    func_info = self._extract_function(node)
                    analysis.functions.append(func_info)

            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class(node)
                analysis.classes.append(class_info)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._extract_import(node)
                analysis.imports.append(import_info)

            elif isinstance(node, ast.Assign):
                # Only process module-level variables
                if isinstance(node, ast.Assign) and hasattr(node, "lineno"):
                    var_info = self._extract_variable(node)
                    if var_info:
                        analysis.variables.append(var_info)

        return analysis

    def _is_top_level_or_method(self, node: ast.FunctionDef) -> bool:
        """Check if function is top-level or a method"""
        # This is a simplified check - in practice we'd track parent nodes
        return True

    def _extract_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
        """Extract function information"""
        # Extract parameters
        params = []
        for arg in node.args.args:
            params.append(arg.arg)

        # Extract return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns) if hasattr(ast, "unparse") else None

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)

        # Calculate complexity
        complexity_visitor = ComplexityVisitor()
        complexity_visitor.visit(node)

        # Extract function calls
        call_visitor = CallVisitor()
        call_visitor.visit(node)

        # Extract variables
        var_visitor = VariableVisitor()
        var_visitor.visit(node)

        return FunctionInfo(
            name=node.name,
            line_number=node.lineno,
            end_line_number=node.end_lineno or node.lineno,
            parameters=params,
            return_type=return_type,
            decorators=decorators,
            docstring=ast.get_docstring(node),
            is_async=isinstance(node, ast.AsyncFunctionDef),
            complexity=complexity_visitor.complexity,
            calls=call_visitor.calls,
            variables=var_visitor.variables,
        )

    def _extract_class(self, node: ast.ClassDef) -> ClassInfo:
        """Extract class information"""
        # Extract base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.value.id if isinstance(base.value, ast.Name) else '?'}.{base.attr}")

        # Extract decorators
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)

        # Check if dataclass
        is_dataclass = "dataclass" in decorators

        # Extract methods
        methods = []
        attributes = set()

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_function(item)
                methods.append(method_info)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Class attribute with type annotation
                attributes.add(item.target.id)
            elif isinstance(item, ast.Assign):
                # Class attribute without type annotation
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.add(target.id)

        return ClassInfo(
            name=node.name,
            line_number=node.lineno,
            end_line_number=node.end_lineno or node.lineno,
            base_classes=bases,
            decorators=decorators,
            docstring=ast.get_docstring(node),
            methods=methods,
            attributes=attributes,
            is_dataclass=is_dataclass,
        )

    def _extract_import(self, node: ast.Import | ast.ImportFrom) -> ImportInfo:
        """Extract import information"""
        if isinstance(node, ast.Import):
            # import module [as alias]
            for alias in node.names:
                return ImportInfo(
                    module=alias.name,
                    names=[alias.name],
                    is_from_import=False,
                    alias=alias.asname,
                    line_number=node.lineno,
                )
        else:
            # from module import name [as alias]
            names = [alias.name for alias in node.names]
            return ImportInfo(
                module=node.module or "",
                names=names,
                is_from_import=True,
                line_number=node.lineno,
            )

    def _extract_variable(self, node: ast.Assign) -> Optional[VariableInfo]:
        """Extract variable information"""
        # Only handle simple assignments for now
        if len(node.targets) != 1:
            return None

        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return None

        # Extract value
        value = None
        if hasattr(ast, "unparse"):
            try:
                value = ast.unparse(node.value)
            except:
                pass

        return VariableInfo(
            name=target.id,
            line_number=node.lineno,
            value=value,
        )

    def get_dependencies(self, analysis: CodeAnalysis) -> Dict[str, Set[str]]:
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

    def find_function(self, analysis: CodeAnalysis, name: str) -> Optional[FunctionInfo]:
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

    def find_class(self, analysis: CodeAnalysis, name: str) -> Optional[ClassInfo]:
        """Find class by name"""
        for cls in analysis.classes:
            if cls.name == name:
                return cls
        return None


# =============================================================================
# Utility Functions
# =============================================================================

def analyze_directory(
    directory: str,
    pattern: str = "**/*.py",
    exclude_patterns: Optional[List[str]] = None,
) -> List[CodeAnalysis]:
    """
    Analyze all Python files in a directory.

    Args:
        directory: Directory to analyze
        pattern: Glob pattern for files
        exclude_patterns: Patterns to exclude

    Returns:
        List of CodeAnalysis results
    """
    parser = PythonASTParser()
    results = []

    path = Path(directory)
    exclude_patterns = exclude_patterns or ["**/venv/**", "**/__pycache__/**", "**/build/**"]

    for file_path in path.glob(pattern):
        # Check exclusions
        if any(file_path.match(pat) for pat in exclude_patterns):
            continue

        try:
            analysis = parser.parse_file(str(file_path))
            results.append(analysis)
        except Exception as e:
            print(f"[PythonAST] Error analyzing {file_path}: {e}")

    return results


def calculate_metrics(analysis: CodeAnalysis) -> Dict[str, Any]:
    """
    Calculate code metrics from analysis.

    Args:
        analysis: Code analysis result

    Returns:
        Dict with various metrics
    """
    metrics = {
        "file_path": analysis.file_path,
        "total_lines": analysis.total_lines,
        "code_lines": analysis.code_lines,
        "comment_lines": analysis.comment_lines,
        "num_functions": len(analysis.functions),
        "num_classes": len(analysis.classes),
        "num_imports": len(analysis.imports),
        "avg_complexity": 0.0,
        "max_complexity": 0,
        "complex_functions": [],
    }

    if analysis.functions:
        complexities = [f.complexity for f in analysis.functions]
        metrics["avg_complexity"] = sum(complexities) / len(complexities)
        metrics["max_complexity"] = max(complexities)

        # Find functions with high complexity (>10)
        metrics["complex_functions"] = [
            {
                "name": f.name,
                "complexity": f.complexity,
                "line_number": f.line_number,
            }
            for f in analysis.functions
            if f.complexity > 10
        ]

    return metrics


def print_analysis_summary(analysis: CodeAnalysis):
    """Print a summary of code analysis"""
    print(f"\n{'='*60}")
    print(f"Analysis: {analysis.file_path}")
    print(f"{'='*60}")

    print(f"\n📊 Metrics:")
    print(f"  Total Lines: {analysis.total_lines}")
    print(f"  Code Lines: {analysis.code_lines}")
    print(f"  Comment Lines: {analysis.comment_lines}")

    print(f"\n📦 Imports ({len(analysis.imports)}):")
    for imp in analysis.imports[:5]:
        if imp.is_from_import:
            print(f"  from {imp.module} import {', '.join(imp.names)}")
        else:
            print(f"  import {imp.module}")
    if len(analysis.imports) > 5:
        print(f"  ... and {len(analysis.imports) - 5} more")

    print(f"\n🔧 Functions ({len(analysis.functions)}):")
    for func in analysis.functions[:5]:
        async_marker = "async " if func.is_async else ""
        print(f"  {async_marker}{func.name}({', '.join(func.parameters)}) - complexity: {func.complexity}")
    if len(analysis.functions) > 5:
        print(f"  ... and {len(analysis.functions) - 5} more")

    print(f"\n📚 Classes ({len(analysis.classes)}):")
    for cls in analysis.classes[:5]:
        bases = f"({', '.join(cls.base_classes)})" if cls.base_classes else ""
        print(f"  {cls.name}{bases} - {len(cls.methods)} methods")
    if len(analysis.classes) > 5:
        print(f"  ... and {len(analysis.classes) - 5} more")
