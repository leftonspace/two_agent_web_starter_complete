"""
JARVIS Code Analysis & Transformation System

AST-based code analysis and refactoring with:
- Python and JavaScript/TypeScript parsing
- Complexity analysis and metrics
- Refactoring operations (rename, extract, inline)
- Design pattern detection and application
"""

# Python AST Parser
from .ast_parser import (
    PythonASTParser,
    CodeAnalysis,
    FunctionInfo,
    ClassInfo,
    ImportInfo,
    VariableInfo,
    analyze_directory,
    calculate_metrics,
    print_analysis_summary,
)

# JavaScript/TypeScript Parser
from .js_parser import (
    JavaScriptParser,
    JSCodeAnalysis,
    JSFunctionInfo,
    JSClassInfo,
    JSImportInfo,
    JSExportInfo,
    analyze_js_directory,
    calculate_js_metrics,
    print_js_analysis_summary,
)

# Refactoring Operations
from .refactoring import (
    RefactoringManager,
    RenameRefactorer,
    ExtractMethodRefactorer,
    ExtractVariableRefactorer,
    RefactoringOperation,
    RenameRefactoring,
    ExtractMethodRefactoring,
    ExtractVariableRefactoring,
)

# Design Patterns
from .patterns import (
    PatternDetector,
    PatternApplicator,
    PatternSuggester,
    PatternType,
    PatternMatch,
)

__all__ = [
    # Python AST Parser
    "PythonASTParser",
    "CodeAnalysis",
    "FunctionInfo",
    "ClassInfo",
    "ImportInfo",
    "VariableInfo",
    "analyze_directory",
    "calculate_metrics",
    "print_analysis_summary",

    # JavaScript/TypeScript Parser
    "JavaScriptParser",
    "JSCodeAnalysis",
    "JSFunctionInfo",
    "JSClassInfo",
    "JSImportInfo",
    "JSExportInfo",
    "analyze_js_directory",
    "calculate_js_metrics",
    "print_js_analysis_summary",

    # Refactoring
    "RefactoringManager",
    "RenameRefactorer",
    "ExtractMethodRefactorer",
    "ExtractVariableRefactorer",
    "RefactoringOperation",
    "RenameRefactoring",
    "ExtractMethodRefactoring",
    "ExtractVariableRefactoring",

    # Design Patterns
    "PatternDetector",
    "PatternApplicator",
    "PatternSuggester",
    "PatternType",
    "PatternMatch",
]

__version__ = "1.0.0"
