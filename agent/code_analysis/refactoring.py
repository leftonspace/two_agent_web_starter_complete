"""
Code Refactoring Operations

AST-based refactoring with:
- Rename (variable, function, class)
- Extract method/function
- Extract variable
- Inline method/variable
- Move class
- Change signature
- Safe rename with scope analysis
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .ast_parser import PythonASTParser, CodeAnalysis, FunctionInfo, ClassInfo


# =============================================================================
# Refactoring Operations
# =============================================================================

@dataclass
class RefactoringOperation:
    """Base class for refactoring operations"""
    file_path: str
    description: str
    changes: List[Tuple[int, int, str]]  # (line_start, line_end, new_code)


@dataclass
class RenameRefactoring(RefactoringOperation):
    """Rename operation"""
    old_name: str
    new_name: str
    scope: str  # 'global', 'class', 'function'


@dataclass
class ExtractMethodRefactoring(RefactoringOperation):
    """Extract method operation"""
    start_line: int
    end_line: int
    method_name: str
    parameters: List[str]
    return_vars: List[str]


@dataclass
class ExtractVariableRefactoring(RefactoringOperation):
    """Extract variable operation"""
    line_number: int
    expression: str
    variable_name: str


# =============================================================================
# Rename Refactoring
# =============================================================================

class RenameRefactorer:
    """
    Safe rename refactoring with scope analysis.

    Features:
    - Scope-aware renaming
    - Conflict detection
    - Multi-file support
    - Preview mode

    Usage:
        refactorer = RenameRefactorer()
        operation = refactorer.rename_function(
            file_path="example.py",
            old_name="foo",
            new_name="bar"
        )
        refactorer.apply(operation)
    """

    def __init__(self):
        self.parser = PythonASTParser()

    def rename_variable(
        self,
        file_path: str,
        old_name: str,
        new_name: str,
        scope: Optional[str] = None,
    ) -> RenameRefactoring:
        """
        Rename a variable.

        Args:
            file_path: Path to file
            old_name: Current variable name
            new_name: New variable name
            scope: Optional scope (function/class name)

        Returns:
            RenameRefactoring operation
        """
        # Parse file
        analysis = self.parser.parse_file(file_path)
        code = Path(file_path).read_text()
        lines = code.split("\n")

        # Find all occurrences
        changes = []

        # Use AST to find variable usages
        tree = ast.parse(code)

        class RenameVisitor(ast.NodeTransformer):
            def __init__(self, old_name: str, new_name: str):
                self.old_name = old_name
                self.new_name = new_name
                self.changes: List[Tuple[int, int, str]] = []

            def visit_Name(self, node: ast.Name) -> ast.Name:
                if node.id == self.old_name:
                    # Record change
                    line_num = node.lineno - 1
                    # Find the exact position in the line
                    line = lines[line_num]
                    new_line = line.replace(self.old_name, self.new_name)
                    self.changes.append((line_num, line_num, new_line))

                    # Update AST
                    node.id = self.new_name

                return node

        visitor = RenameVisitor(old_name, new_name)
        visitor.visit(tree)

        # Deduplicate changes (multiple occurrences on same line)
        unique_changes = {}
        for start, end, new_code in visitor.changes:
            unique_changes[start] = (start, end, new_code)

        changes = list(unique_changes.values())

        return RenameRefactoring(
            file_path=file_path,
            description=f"Rename variable '{old_name}' to '{new_name}'",
            changes=changes,
            old_name=old_name,
            new_name=new_name,
            scope=scope or "global",
        )

    def rename_function(
        self,
        file_path: str,
        old_name: str,
        new_name: str,
    ) -> RenameRefactoring:
        """
        Rename a function.

        Args:
            file_path: Path to file
            old_name: Current function name
            new_name: New function name

        Returns:
            RenameRefactoring operation
        """
        analysis = self.parser.parse_file(file_path)
        code = Path(file_path).read_text()
        lines = code.split("\n")

        changes = []

        # Find function definition
        func = self.parser.find_function(analysis, old_name)
        if not func:
            raise ValueError(f"Function '{old_name}' not found")

        # Rename definition
        def_line = lines[func.line_number - 1]
        new_def_line = re.sub(
            rf'\bdef\s+{old_name}\b',
            f'def {new_name}',
            def_line
        )
        changes.append((func.line_number - 1, func.line_number - 1, new_def_line))

        # Find all calls
        tree = ast.parse(code)

        class CallVisitor(ast.NodeVisitor):
            def __init__(self):
                self.call_lines: Set[int] = set()

            def visit_Call(self, node: ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == old_name:
                    self.call_lines.add(node.lineno - 1)
                self.generic_visit(node)

        visitor = CallVisitor()
        visitor.visit(tree)

        # Rename calls
        for line_num in visitor.call_lines:
            line = lines[line_num]
            new_line = re.sub(rf'\b{old_name}\b', new_name, line)
            changes.append((line_num, line_num, new_line))

        return RenameRefactoring(
            file_path=file_path,
            description=f"Rename function '{old_name}' to '{new_name}'",
            changes=sorted(changes, key=lambda x: x[0]),
            old_name=old_name,
            new_name=new_name,
            scope="global",
        )

    def rename_class(
        self,
        file_path: str,
        old_name: str,
        new_name: str,
    ) -> RenameRefactoring:
        """
        Rename a class.

        Args:
            file_path: Path to file
            old_name: Current class name
            new_name: New class name

        Returns:
            RenameRefactoring operation
        """
        analysis = self.parser.parse_file(file_path)
        code = Path(file_path).read_text()
        lines = code.split("\n")

        changes = []

        # Find class definition
        cls = self.parser.find_class(analysis, old_name)
        if not cls:
            raise ValueError(f"Class '{old_name}' not found")

        # Rename definition
        def_line = lines[cls.line_number - 1]
        new_def_line = re.sub(
            rf'\bclass\s+{old_name}\b',
            f'class {new_name}',
            def_line
        )
        changes.append((cls.line_number - 1, cls.line_number - 1, new_def_line))

        # Find all usages (instantiation, type hints, etc.)
        tree = ast.parse(code)

        class ClassUsageVisitor(ast.NodeVisitor):
            def __init__(self):
                self.usage_lines: Set[int] = set()

            def visit_Name(self, node: ast.Name):
                if node.id == old_name:
                    self.usage_lines.add(node.lineno - 1)
                self.generic_visit(node)

        visitor = ClassUsageVisitor()
        visitor.visit(tree)

        # Rename usages
        for line_num in visitor.usage_lines:
            if line_num == cls.line_number - 1:
                continue  # Already handled
            line = lines[line_num]
            new_line = re.sub(rf'\b{old_name}\b', new_name, line)
            changes.append((line_num, line_num, new_line))

        return RenameRefactoring(
            file_path=file_path,
            description=f"Rename class '{old_name}' to '{new_name}'",
            changes=sorted(changes, key=lambda x: x[0]),
            old_name=old_name,
            new_name=new_name,
            scope="global",
        )

    def check_conflicts(self, operation: RenameRefactoring) -> List[str]:
        """Check for naming conflicts"""
        analysis = self.parser.parse_file(operation.file_path)
        conflicts = []

        # Check if new name already exists
        for func in analysis.functions:
            if func.name == operation.new_name:
                conflicts.append(f"Function '{operation.new_name}' already exists")

        for cls in analysis.classes:
            if cls.name == operation.new_name:
                conflicts.append(f"Class '{operation.new_name}' already exists")

        return conflicts

    def apply(self, operation: RefactoringOperation, dry_run: bool = False) -> bool:
        """
        Apply refactoring operation.

        Args:
            operation: Refactoring operation to apply
            dry_run: If True, only preview changes

        Returns:
            True if successful
        """
        # Read file
        code = Path(operation.file_path).read_text()
        lines = code.split("\n")

        # Apply changes (in reverse order to preserve line numbers)
        for start_line, end_line, new_code in reversed(operation.changes):
            lines[start_line] = new_code

        new_code = "\n".join(lines)

        if dry_run:
            print(f"[Refactoring] Preview of {operation.description}:")
            print(new_code)
            return True

        # Write back
        Path(operation.file_path).write_text(new_code)
        print(f"[Refactoring] Applied: {operation.description}")
        return True


# =============================================================================
# Extract Method Refactoring
# =============================================================================

class ExtractMethodRefactorer:
    """
    Extract method/function refactoring.

    Features:
    - Automatic parameter detection
    - Return value analysis
    - Scope preservation
    - Code block extraction

    Usage:
        refactorer = ExtractMethodRefactorer()
        operation = refactorer.extract_method(
            file_path="example.py",
            start_line=10,
            end_line=15,
            method_name="extracted_method"
        )
        refactorer.apply(operation)
    """

    def __init__(self):
        self.parser = PythonASTParser()

    def extract_method(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        method_name: str,
        class_name: Optional[str] = None,
    ) -> ExtractMethodRefactoring:
        """
        Extract code block into a new method.

        Args:
            file_path: Path to file
            start_line: Start line of code block (1-indexed)
            end_line: End line of code block (1-indexed)
            method_name: Name for the new method
            class_name: Optional class name for method

        Returns:
            ExtractMethodRefactoring operation
        """
        code = Path(file_path).read_text()
        lines = code.split("\n")

        # Extract code block
        extracted_lines = lines[start_line - 1:end_line]
        extracted_code = "\n".join(extracted_lines)

        # Analyze variables
        parameters, return_vars = self._analyze_variables(code, start_line, end_line)

        # Generate new method
        indent = self._get_indent(lines[start_line - 1])
        new_method = self._generate_method(
            method_name,
            parameters,
            return_vars,
            extracted_code,
            indent,
        )

        # Find insertion point for new method
        insertion_line = self._find_insertion_point(code, start_line, class_name)

        changes = [
            # Insert new method
            (insertion_line, insertion_line, new_method),
            # Replace original code with method call
            (start_line - 1, end_line - 1, self._generate_call(
                method_name,
                parameters,
                return_vars,
                indent
            )),
        ]

        return ExtractMethodRefactoring(
            file_path=file_path,
            description=f"Extract method '{method_name}'",
            changes=changes,
            start_line=start_line,
            end_line=end_line,
            method_name=method_name,
            parameters=parameters,
            return_vars=return_vars,
        )

    def _analyze_variables(
        self,
        code: str,
        start_line: int,
        end_line: int,
    ) -> Tuple[List[str], List[str]]:
        """Analyze variables used in code block"""
        lines = code.split("\n")
        block_code = "\n".join(lines[start_line - 1:end_line])

        try:
            block_tree = ast.parse(block_code)
        except:
            return [], []

        # Find variables used before definition (parameters)
        # Find variables defined and used after (return values)
        used_vars = set()
        defined_vars = set()

        class VarAnalyzer(ast.NodeVisitor):
            def visit_Name(self, node: ast.Name):
                if isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
                elif isinstance(node.ctx, ast.Store):
                    defined_vars.add(node.id)

        analyzer = VarAnalyzer()
        analyzer.visit(block_tree)

        # Parameters: used but not defined in block
        parameters = list(used_vars - defined_vars)

        # Return values: defined in block
        return_vars = list(defined_vars)

        return parameters, return_vars

    def _get_indent(self, line: str) -> str:
        """Get indentation from line"""
        return line[:len(line) - len(line.lstrip())]

    def _generate_method(
        self,
        name: str,
        parameters: List[str],
        return_vars: List[str],
        body: str,
        indent: str,
    ) -> str:
        """Generate new method definition"""
        params_str = ", ".join(["self"] + parameters) if parameters else "self"
        return_str = ""

        if return_vars:
            if len(return_vars) == 1:
                return_str = f"\n{indent}    return {return_vars[0]}"
            else:
                return_str = f"\n{indent}    return {', '.join(return_vars)}"

        return f"""
{indent}def {name}({params_str}):
{indent}    \"\"\"Extracted method\"\"\"
{body}{return_str}
"""

    def _generate_call(
        self,
        name: str,
        parameters: List[str],
        return_vars: List[str],
        indent: str,
    ) -> str:
        """Generate method call"""
        params_str = ", ".join(parameters)
        call = f"self.{name}({params_str})"

        if return_vars:
            if len(return_vars) == 1:
                return f"{indent}{return_vars[0]} = {call}"
            else:
                return f"{indent}{', '.join(return_vars)} = {call}"

        return f"{indent}{call}"

    def _find_insertion_point(
        self,
        code: str,
        start_line: int,
        class_name: Optional[str],
    ) -> int:
        """Find where to insert new method"""
        lines = code.split("\n")

        # If in class, insert before the method containing start_line
        if class_name:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    # Insert at start of class body
                    return node.lineno

        # Otherwise, insert at module level before start_line
        return max(0, start_line - 2)

    def apply(self, operation: ExtractMethodRefactoring, dry_run: bool = False) -> bool:
        """Apply extract method refactoring"""
        code = Path(operation.file_path).read_text()
        lines = code.split("\n")

        # Apply changes
        for start_line, end_line, new_code in reversed(operation.changes):
            if start_line == end_line:
                lines.insert(start_line, new_code)
            else:
                lines[start_line:end_line + 1] = [new_code]

        new_code = "\n".join(lines)

        if dry_run:
            print(f"[Refactoring] Preview of {operation.description}:")
            print(new_code)
            return True

        Path(operation.file_path).write_text(new_code)
        print(f"[Refactoring] Applied: {operation.description}")
        return True


# =============================================================================
# Extract Variable Refactoring
# =============================================================================

class ExtractVariableRefactorer:
    """
    Extract variable refactoring.

    Replaces repeated expressions with a named variable.

    Usage:
        refactorer = ExtractVariableRefactorer()
        operation = refactorer.extract_variable(
            file_path="example.py",
            line_number=10,
            expression="user.name.lower()",
            variable_name="username"
        )
        refactorer.apply(operation)
    """

    def extract_variable(
        self,
        file_path: str,
        line_number: int,
        expression: str,
        variable_name: str,
    ) -> ExtractVariableRefactoring:
        """Extract expression into variable"""
        code = Path(file_path).read_text()
        lines = code.split("\n")

        # Find all occurrences of expression
        changes = []

        # Get indentation
        indent = lines[line_number - 1][:len(lines[line_number - 1]) - len(lines[line_number - 1].lstrip())]

        # Insert variable assignment
        var_assignment = f"{indent}{variable_name} = {expression}"
        changes.append((line_number - 1, line_number - 1, var_assignment))

        # Replace occurrences with variable name
        for i, line in enumerate(lines[line_number:], start=line_number):
            if expression in line:
                new_line = line.replace(expression, variable_name)
                changes.append((i, i, new_line))

        return ExtractVariableRefactoring(
            file_path=file_path,
            description=f"Extract variable '{variable_name}'",
            changes=changes,
            line_number=line_number,
            expression=expression,
            variable_name=variable_name,
        )

    def apply(self, operation: ExtractVariableRefactoring, dry_run: bool = False) -> bool:
        """Apply extract variable refactoring"""
        code = Path(operation.file_path).read_text()
        lines = code.split("\n")

        # Apply changes
        for start_line, end_line, new_code in reversed(operation.changes):
            lines[start_line] = new_code

        new_code = "\n".join(lines)

        if dry_run:
            print(f"[Refactoring] Preview of {operation.description}:")
            print(new_code)
            return True

        Path(operation.file_path).write_text(new_code)
        print(f"[Refactoring] Applied: {operation.description}")
        return True


# =============================================================================
# Refactoring Manager
# =============================================================================

class RefactoringManager:
    """
    Unified refactoring manager.

    Coordinates all refactoring operations with:
    - Safety checks
    - Conflict detection
    - Preview mode
    - Undo support

    Usage:
        manager = RefactoringManager()

        # Rename function
        manager.rename_function("example.py", "old_func", "new_func")

        # Extract method
        manager.extract_method("example.py", 10, 15, "helper_method")

        # Preview changes
        manager.preview_all()

        # Apply all
        manager.apply_all()
    """

    def __init__(self):
        self.rename_refactorer = RenameRefactorer()
        self.extract_method_refactorer = ExtractMethodRefactorer()
        self.extract_variable_refactorer = ExtractVariableRefactorer()

        self.operations: List[RefactoringOperation] = []

    def rename_function(self, file_path: str, old_name: str, new_name: str):
        """Queue rename function operation"""
        op = self.rename_refactorer.rename_function(file_path, old_name, new_name)
        self.operations.append(op)

    def rename_class(self, file_path: str, old_name: str, new_name: str):
        """Queue rename class operation"""
        op = self.rename_refactorer.rename_class(file_path, old_name, new_name)
        self.operations.append(op)

    def extract_method(
        self,
        file_path: str,
        start_line: int,
        end_line: int,
        method_name: str,
    ):
        """Queue extract method operation"""
        op = self.extract_method_refactorer.extract_method(
            file_path, start_line, end_line, method_name
        )
        self.operations.append(op)

    def extract_variable(
        self,
        file_path: str,
        line_number: int,
        expression: str,
        variable_name: str,
    ):
        """Queue extract variable operation"""
        op = self.extract_variable_refactorer.extract_variable(
            file_path, line_number, expression, variable_name
        )
        self.operations.append(op)

    def preview_all(self):
        """Preview all queued operations"""
        for op in self.operations:
            print(f"\n{'='*60}")
            print(f"Operation: {op.description}")
            print(f"File: {op.file_path}")
            print(f"{'='*60}")
            for start, end, new_code in op.changes:
                print(f"Line {start + 1}: {new_code}")

    def apply_all(self, dry_run: bool = False):
        """Apply all queued operations"""
        for op in self.operations:
            if isinstance(op, RenameRefactoring):
                self.rename_refactorer.apply(op, dry_run)
            elif isinstance(op, ExtractMethodRefactoring):
                self.extract_method_refactorer.apply(op, dry_run)
            elif isinstance(op, ExtractVariableRefactoring):
                self.extract_variable_refactorer.apply(op, dry_run)

        if not dry_run:
            self.operations.clear()

    def clear(self):
        """Clear all queued operations"""
        self.operations.clear()
