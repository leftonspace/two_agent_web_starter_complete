"""
Test Generation System

Automatically generates unit tests from code analysis.

Uses LLM to generate pytest-compatible tests based on:
- Function signatures and docstrings
- Code structure and patterns
- Existing test examples
- Edge cases and boundary conditions
"""

from __future__ import annotations

import ast
import inspect
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from .code_analysis.ast_parser import PythonASTParser, FunctionInfo, ClassInfo
    from .llm import get_completion
    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False
    PythonASTParser = None


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class TestGenConfig:
    """Configuration for test generation"""

    # Test framework
    framework: str = "pytest"  # pytest, unittest, nose

    # Test directory
    test_dir: Path = Path("tests")
    test_prefix: str = "test_"

    # Generation settings
    generate_fixtures: bool = True
    generate_mocks: bool = True
    generate_edge_cases: bool = True
    generate_docstrings: bool = True

    # Coverage targets
    min_test_coverage: float = 0.8

    # LLM settings
    model: str = "gpt-4"
    temperature: float = 0.2  # Low temperature for consistency
    max_tokens: int = 2000


@dataclass
class TestCase:
    """Generated test case"""
    name: str
    description: str
    test_code: str
    fixtures: List[str] = field(default_factory=list)
    mocks: List[str] = field(default_factory=list)
    assertions: List[str] = field(default_factory=list)


@dataclass
class TestSuite:
    """Collection of tests for a module"""
    module_name: str
    file_path: Path
    test_cases: List[TestCase] = field(default_factory=list)
    setup_code: str = ""
    teardown_code: str = ""
    fixtures: Dict[str, str] = field(default_factory=dict)


# =============================================================================
# Test Generator
# =============================================================================

class TestGenerator:
    """
    Automated test generation system.

    Generates comprehensive unit tests for Python code using:
    - AST analysis for code structure
    - LLM for test logic generation
    - Template-based generation for common patterns

    Usage:
        generator = TestGenerator()

        # Generate tests for a file
        test_suite = await generator.generate_tests_for_file("agent/utils.py")

        # Write tests to file
        test_file = generator.write_test_suite(test_suite)
        print(f"Generated tests: {test_file}")
    """

    def __init__(self, config: Optional[TestGenConfig] = None):
        """
        Initialize test generator.

        Args:
            config: Test generation configuration
        """
        if not AST_AVAILABLE:
            raise ImportError(
                "AST parser not available. Ensure agent.code_analysis is installed."
            )

        self.config = config or TestGenConfig()
        self.parser = PythonASTParser()

        print(f"[TestGenerator] Initialized with framework: {self.config.framework}")

    # =========================================================================
    # Test Generation
    # =========================================================================

    async def generate_tests_for_file(
        self,
        file_path: str | Path,
        existing_tests: Optional[Path] = None,
    ) -> TestSuite:
        """
        Generate comprehensive tests for a Python file.

        Args:
            file_path: Path to Python file to test
            existing_tests: Path to existing test file (for learning patterns)

        Returns:
            TestSuite with generated tests
        """
        file_path = Path(file_path)

        # Parse source code
        analysis = self.parser.parse_file(str(file_path))

        print(f"[TestGenerator] Analyzing {file_path.name}...")
        print(f"  Functions: {len(analysis.functions)}")
        print(f"  Classes: {len(analysis.classes)}")

        # Create test suite
        test_suite = TestSuite(
            module_name=file_path.stem,
            file_path=file_path,
        )

        # Parse existing tests for patterns
        existing_patterns = []
        if existing_tests and existing_tests.exists():
            existing_patterns = self._extract_test_patterns(existing_tests)

        # Generate tests for functions
        for func in analysis.functions:
            if not func.name.startswith("_"):  # Skip private functions
                test_cases = await self._generate_function_tests(func, existing_patterns)
                test_suite.test_cases.extend(test_cases)

        # Generate tests for classes
        for cls in analysis.classes:
            test_cases = await self._generate_class_tests(cls, existing_patterns)
            test_suite.test_cases.extend(test_cases)

        # Generate fixtures
        if self.config.generate_fixtures:
            test_suite.fixtures = self._generate_fixtures(analysis)

        # Generate setup/teardown
        test_suite.setup_code = self._generate_setup(analysis)
        test_suite.teardown_code = self._generate_teardown(analysis)

        print(f"[TestGenerator] Generated {len(test_suite.test_cases)} test cases")

        return test_suite

    async def _generate_function_tests(
        self,
        func: FunctionInfo,
        existing_patterns: List[Dict[str, Any]],
    ) -> List[TestCase]:
        """Generate tests for a function"""
        test_cases = []

        # Basic functionality test
        basic_test = await self._generate_basic_function_test(func)
        test_cases.append(basic_test)

        # Edge cases
        if self.config.generate_edge_cases:
            edge_cases = await self._generate_edge_case_tests(func)
            test_cases.extend(edge_cases)

        # Error handling tests
        error_tests = await self._generate_error_handling_tests(func)
        test_cases.extend(error_tests)

        return test_cases

    async def _generate_basic_function_test(self, func: FunctionInfo) -> TestCase:
        """Generate basic functionality test"""

        # Build prompt for LLM
        prompt = f"""Generate a pytest test for this Python function:

Function name: {func.name}
Parameters: {func.parameters}
Docstring: {func.docstring or "No docstring provided"}
Returns: {func.return_type or "Unknown"}

Generate a test that:
1. Calls the function with typical inputs
2. Verifies the output is correct
3. Checks any side effects
4. Uses descriptive variable names
5. Includes a docstring explaining what's tested

Return only the test function code (def test_...), no imports or extra text."""

        try:
            # Get LLM completion
            test_code = await get_completion(
                prompt=prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            # Clean up code
            test_code = self._clean_generated_code(test_code)

            return TestCase(
                name=f"test_{func.name}_basic",
                description=f"Test basic functionality of {func.name}",
                test_code=test_code,
            )

        except Exception as e:
            print(f"[TestGenerator] Error generating test for {func.name}: {e}")
            # Fallback to template
            return self._generate_template_test(func)

    async def _generate_edge_case_tests(self, func: FunctionInfo) -> List[TestCase]:
        """Generate edge case tests"""

        prompt = f"""Generate pytest edge case tests for this Python function:

Function: {func.name}({', '.join(func.parameters)})
Docstring: {func.docstring or "No docstring"}

Generate 2-3 edge case tests for:
- Boundary values (empty inputs, zero, None, etc.)
- Unusual but valid inputs
- Maximum/minimum values

Return each test as a separate function."""

        try:
            test_code = await get_completion(
                prompt=prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            # Split into separate test functions
            tests = self._split_test_functions(test_code)

            return [
                TestCase(
                    name=f"test_{func.name}_edge_case_{i}",
                    description=f"Edge case test {i} for {func.name}",
                    test_code=test,
                )
                for i, test in enumerate(tests, 1)
            ]

        except Exception as e:
            print(f"[TestGenerator] Error generating edge cases: {e}")
            return []

    async def _generate_error_handling_tests(self, func: FunctionInfo) -> List[TestCase]:
        """Generate error handling tests"""

        # Only generate if function has error handling
        if "raise" not in func.calls and "except" not in func.docstring.lower():
            return []

        prompt = f"""Generate pytest error handling tests for: {func.name}

Function: {func.name}({', '.join(func.parameters)})

Generate tests for:
- Invalid input types
- Expected exceptions
- Error messages are correct

Use pytest.raises() for exception testing."""

        try:
            test_code = await get_completion(
                prompt=prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            return [
                TestCase(
                    name=f"test_{func.name}_error_handling",
                    description=f"Error handling test for {func.name}",
                    test_code=self._clean_generated_code(test_code),
                )
            ]

        except Exception as e:
            print(f"[TestGenerator] Error generating error tests: {e}")
            return []

    async def _generate_class_tests(
        self,
        cls: ClassInfo,
        existing_patterns: List[Dict[str, Any]],
    ) -> List[TestCase]:
        """Generate tests for a class"""
        test_cases = []

        # Test class instantiation
        init_test = await self._generate_init_test(cls)
        test_cases.append(init_test)

        # Test each public method
        for method in cls.methods:
            if not method.name.startswith("_") or method.name == "__init__":
                method_tests = await self._generate_function_tests(method, existing_patterns)
                # Prefix with class name
                for test in method_tests:
                    test.name = f"test_{cls.name}_{test.name}"
                test_cases.extend(method_tests)

        return test_cases

    async def _generate_init_test(self, cls: ClassInfo) -> TestCase:
        """Generate test for class initialization"""

        prompt = f"""Generate a pytest test for class initialization:

Class: {cls.name}
Base classes: {cls.base_classes}
Docstring: {cls.docstring or "No docstring"}

Generate a test that:
1. Creates an instance of the class
2. Verifies attributes are set correctly
3. Checks the instance is of the correct type"""

        try:
            test_code = await get_completion(
                prompt=prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            return TestCase(
                name=f"test_{cls.name}_init",
                description=f"Test {cls.name} initialization",
                test_code=self._clean_generated_code(test_code),
            )

        except Exception as e:
            print(f"[TestGenerator] Error generating init test: {e}")
            return self._generate_template_init_test(cls)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _extract_test_patterns(self, test_file: Path) -> List[Dict[str, Any]]:
        """Extract patterns from existing tests"""
        try:
            analysis = self.parser.parse_file(str(test_file))

            patterns = []
            for func in analysis.functions:
                if func.name.startswith("test_"):
                    patterns.append({
                        "name": func.name,
                        "parameters": func.parameters,
                        "assertions": [call for call in func.calls if "assert" in call],
                        "fixtures": [param for param in func.parameters if param != "self"],
                    })

            return patterns

        except Exception as e:
            print(f"[TestGenerator] Error extracting patterns: {e}")
            return []

    def _generate_fixtures(self, analysis) -> Dict[str, str]:
        """Generate pytest fixtures"""
        fixtures = {}

        # Generate fixtures for classes
        for cls in analysis.classes:
            fixture_name = f"{cls.name.lower()}_instance"
            fixture_code = f"""@pytest.fixture
def {fixture_name}():
    \"\"\"Fixture for {cls.name} instance\"\"\"
    return {cls.name}()"""
            fixtures[fixture_name] = fixture_code

        return fixtures

    def _generate_setup(self, analysis) -> str:
        """Generate setup code for test module"""
        imports = [
            "import pytest",
            f"from {analysis.module} import *",
        ]

        if self.config.generate_mocks:
            imports.append("from unittest.mock import Mock, patch, MagicMock")

        return "\n".join(imports)

    def _generate_teardown(self, analysis) -> str:
        """Generate teardown code"""
        return ""

    def _generate_template_test(self, func: FunctionInfo) -> TestCase:
        """Generate test from template (fallback)"""
        test_code = f"""def test_{func.name}():
    \"\"\"Test {func.name} functionality\"\"\"
    # TODO: Implement test
    pass"""

        return TestCase(
            name=f"test_{func.name}",
            description=f"Template test for {func.name}",
            test_code=test_code,
        )

    def _generate_template_init_test(self, cls: ClassInfo) -> TestCase:
        """Generate init test from template (fallback)"""
        test_code = f"""def test_{cls.name}_init():
    \"\"\"Test {cls.name} initialization\"\"\"
    instance = {cls.name}()
    assert isinstance(instance, {cls.name})"""

        return TestCase(
            name=f"test_{cls.name}_init",
            description=f"Template init test for {cls.name}",
            test_code=test_code,
        )

    def _clean_generated_code(self, code: str) -> str:
        """Clean up LLM-generated code"""
        # Remove markdown code blocks
        code = code.replace("```python", "").replace("```", "")

        # Remove leading/trailing whitespace
        code = code.strip()

        # Ensure proper indentation
        lines = code.split("\n")
        if lines and not lines[0].startswith("def "):
            # Find first def line
            for i, line in enumerate(lines):
                if line.startswith("def "):
                    code = "\n".join(lines[i:])
                    break

        return code

    def _split_test_functions(self, code: str) -> List[str]:
        """Split multiple test functions from generated code"""
        code = self._clean_generated_code(code)

        # Split on "def test_"
        parts = code.split("\ndef test_")

        tests = []
        for i, part in enumerate(parts):
            if i == 0 and part.startswith("def test_"):
                tests.append(part)
            elif part:
                tests.append("def test_" + part)

        return tests

    # =========================================================================
    # File Writing
    # =========================================================================

    def write_test_suite(self, test_suite: TestSuite) -> Path:
        """
        Write test suite to file.

        Args:
            test_suite: TestSuite to write

        Returns:
            Path to created test file
        """
        # Determine test file path
        test_file = self.config.test_dir / f"{self.config.test_prefix}{test_suite.module_name}.py"
        self.config.test_dir.mkdir(parents=True, exist_ok=True)

        # Build test file content
        content_parts = []

        # Setup
        content_parts.append(test_suite.setup_code)
        content_parts.append("")

        # Fixtures
        if test_suite.fixtures:
            content_parts.append("# Fixtures")
            for fixture_code in test_suite.fixtures.values():
                content_parts.append(fixture_code)
                content_parts.append("")

        # Test cases
        content_parts.append("# Test Cases")
        for test_case in test_suite.test_cases:
            content_parts.append(test_case.test_code)
            content_parts.append("")

        # Teardown
        if test_suite.teardown_code:
            content_parts.append(test_suite.teardown_code)

        # Write to file
        content = "\n".join(content_parts)
        test_file.write_text(content)

        print(f"[TestGenerator] Wrote {len(test_suite.test_cases)} tests to {test_file}")

        return test_file


# =============================================================================
# Convenience Functions
# =============================================================================

async def generate_tests(
    file_path: str | Path,
    output_dir: Optional[Path] = None,
    config: Optional[TestGenConfig] = None,
) -> Path:
    """
    Generate tests for a Python file (convenience function).

    Args:
        file_path: Path to Python file
        output_dir: Directory for generated tests
        config: Test generation configuration

    Returns:
        Path to generated test file

    Example:
        test_file = await generate_tests("agent/utils.py")
        print(f"Generated: {test_file}")
    """
    if config is None:
        config = TestGenConfig()

    if output_dir:
        config.test_dir = output_dir

    generator = TestGenerator(config)
    test_suite = await generator.generate_tests_for_file(file_path)
    return generator.write_test_suite(test_suite)


# =============================================================================
# CLI for Testing
# =============================================================================

async def test_test_generator():
    """Test the test generator"""
    import sys

    print("\n" + "="*60)
    print("Test Generator - Test Mode")
    print("="*60 + "\n")

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default test file
        file_path = "agent/utils.py"

    print(f"Generating tests for: {file_path}\n")

    try:
        test_file = await generate_tests(file_path)
        print(f"\n✅ Success! Generated tests at: {test_file}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_test_generator())
