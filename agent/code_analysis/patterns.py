"""
Design Pattern Detection and Application

AST-based design pattern detection and automatic application:
- Singleton pattern
- Factory pattern
- Observer pattern
- Strategy pattern
- Decorator pattern
- Builder pattern
- Template Method pattern
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .ast_parser import PythonASTParser, CodeAnalysis, ClassInfo


# =============================================================================
# Pattern Types
# =============================================================================

class PatternType(Enum):
    """Supported design patterns"""
    SINGLETON = "singleton"
    FACTORY = "factory"
    OBSERVER = "observer"
    STRATEGY = "strategy"
    DECORATOR = "decorator"
    BUILDER = "builder"
    TEMPLATE_METHOD = "template_method"
    ADAPTER = "adapter"
    FACADE = "facade"


@dataclass
class PatternMatch:
    """Detected design pattern"""
    pattern_type: PatternType
    confidence: float  # 0.0 to 1.0
    class_name: str
    file_path: str
    line_number: int
    evidence: List[str]  # Evidence for detection


# =============================================================================
# Pattern Detection
# =============================================================================

class PatternDetector:
    """
    Detect design patterns in code.

    Features:
    - AST-based pattern recognition
    - Confidence scoring
    - Multiple pattern detection
    - Evidence collection

    Usage:
        detector = PatternDetector()
        patterns = detector.detect_patterns("example.py")

        for pattern in patterns:
            print(f"{pattern.pattern_type.value}: {pattern.class_name} ({pattern.confidence:.2f})")
    """

    def __init__(self):
        self.parser = PythonASTParser()

    def detect_patterns(self, file_path: str) -> List[PatternMatch]:
        """
        Detect all patterns in a file.

        Args:
            file_path: Path to file

        Returns:
            List of detected patterns
        """
        analysis = self.parser.parse_file(file_path)
        patterns = []

        for cls in analysis.classes:
            # Check each pattern type
            patterns.extend(self._detect_singleton(cls, file_path))
            patterns.extend(self._detect_factory(cls, file_path))
            patterns.extend(self._detect_observer(cls, file_path))
            patterns.extend(self._detect_strategy(cls, file_path))
            patterns.extend(self._detect_decorator(cls, file_path))
            patterns.extend(self._detect_builder(cls, file_path))
            patterns.extend(self._detect_template_method(cls, file_path))

        return patterns

    def _detect_singleton(self, cls: ClassInfo, file_path: str) -> List[PatternMatch]:
        """Detect Singleton pattern"""
        evidence = []
        confidence = 0.0

        # Check for __instance class attribute
        if "_instance" in cls.attributes or "__instance" in cls.attributes:
            evidence.append("Has '_instance' class attribute")
            confidence += 0.3

        # Check for __new__ method
        method_names = [m.name for m in cls.methods]
        if "__new__" in method_names:
            evidence.append("Overrides __new__ method")
            confidence += 0.3

        # Check for getInstance or get_instance method
        if any(name in ["getInstance", "get_instance"] for name in method_names):
            evidence.append("Has getInstance/get_instance method")
            confidence += 0.4

        # Check if __init__ is private-like
        if "__init__" in method_names:
            init_method = next(m for m in cls.methods if m.name == "__init__")
            if init_method.docstring and "singleton" in init_method.docstring.lower():
                evidence.append("__init__ mentions singleton")
                confidence += 0.2

        if confidence >= 0.5:
            return [PatternMatch(
                pattern_type=PatternType.SINGLETON,
                confidence=min(confidence, 1.0),
                class_name=cls.name,
                file_path=file_path,
                line_number=cls.line_number,
                evidence=evidence,
            )]

        return []

    def _detect_factory(self, cls: ClassInfo, file_path: str) -> List[PatternMatch]:
        """Detect Factory pattern"""
        evidence = []
        confidence = 0.0

        # Check class name
        if "Factory" in cls.name or "factory" in cls.name.lower():
            evidence.append("Class name contains 'Factory'")
            confidence += 0.3

        # Check for create methods
        method_names = [m.name for m in cls.methods]
        create_methods = [name for name in method_names if name.startswith("create")]

        if create_methods:
            evidence.append(f"Has create methods: {', '.join(create_methods)}")
            confidence += 0.3

        # Check for multiple product creation
        if len(create_methods) >= 2:
            evidence.append("Creates multiple product types")
            confidence += 0.2

        # Check docstring
        if cls.docstring and "factory" in cls.docstring.lower():
            evidence.append("Docstring mentions factory")
            confidence += 0.2

        if confidence >= 0.5:
            return [PatternMatch(
                pattern_type=PatternType.FACTORY,
                confidence=min(confidence, 1.0),
                class_name=cls.name,
                file_path=file_path,
                line_number=cls.line_number,
                evidence=evidence,
            )]

        return []

    def _detect_observer(self, cls: ClassInfo, file_path: str) -> List[PatternMatch]:
        """Detect Observer pattern"""
        evidence = []
        confidence = 0.0

        method_names = [m.name for m in cls.methods]

        # Check for observer-related methods
        observer_methods = {
            "attach": 0.2,
            "detach": 0.2,
            "notify": 0.3,
            "update": 0.3,
            "subscribe": 0.2,
            "unsubscribe": 0.2,
            "add_observer": 0.2,
            "remove_observer": 0.2,
        }

        for method, score in observer_methods.items():
            if method in method_names:
                evidence.append(f"Has {method} method")
                confidence += score

        # Check for observers list
        if any("observer" in attr.lower() for attr in cls.attributes):
            evidence.append("Has observers collection attribute")
            confidence += 0.2

        # Check class name
        if "Observer" in cls.name or "Subject" in cls.name:
            evidence.append("Class name suggests Observer pattern")
            confidence += 0.2

        if confidence >= 0.5:
            return [PatternMatch(
                pattern_type=PatternType.OBSERVER,
                confidence=min(confidence, 1.0),
                class_name=cls.name,
                file_path=file_path,
                line_number=cls.line_number,
                evidence=evidence,
            )]

        return []

    def _detect_strategy(self, cls: ClassInfo, file_path: str) -> List[PatternMatch]:
        """Detect Strategy pattern"""
        evidence = []
        confidence = 0.0

        # Check if class is abstract/interface-like
        if cls.base_classes and any("ABC" in base for base in cls.base_classes):
            evidence.append("Inherits from ABC (abstract base class)")
            confidence += 0.3

        # Check for strategy-like method (single key method)
        public_methods = [m for m in cls.methods if not m.name.startswith("_")]
        if len(public_methods) == 1:
            evidence.append("Has single public method (strategy interface)")
            confidence += 0.3

        # Check class name
        if "Strategy" in cls.name:
            evidence.append("Class name contains 'Strategy'")
            confidence += 0.3

        # Check for algorithm/execute method
        method_names = [m.name for m in cls.methods]
        if any(name in ["execute", "algorithm", "do_operation"] for name in method_names):
            evidence.append("Has execute/algorithm method")
            confidence += 0.2

        if confidence >= 0.5:
            return [PatternMatch(
                pattern_type=PatternType.STRATEGY,
                confidence=min(confidence, 1.0),
                class_name=cls.name,
                file_path=file_path,
                line_number=cls.line_number,
                evidence=evidence,
            )]

        return []

    def _detect_decorator(self, cls: ClassInfo, file_path: str) -> List[PatternMatch]:
        """Detect Decorator pattern"""
        evidence = []
        confidence = 0.0

        # Check class name
        if "Decorator" in cls.name or "Wrapper" in cls.name:
            evidence.append("Class name suggests Decorator pattern")
            confidence += 0.3

        # Check for wrapped component attribute
        if any("component" in attr.lower() or "wrapped" in attr.lower() for attr in cls.attributes):
            evidence.append("Has component/wrapped attribute")
            confidence += 0.3

        # Check if extends same interface as wrapped object
        if cls.base_classes:
            evidence.append("Implements same interface")
            confidence += 0.2

        # Check for __init__ that accepts component
        init_method = next((m for m in cls.methods if m.name == "__init__"), None)
        if init_method and len(init_method.parameters) >= 1:
            evidence.append("Constructor accepts component")
            confidence += 0.2

        if confidence >= 0.5:
            return [PatternMatch(
                pattern_type=PatternType.DECORATOR,
                confidence=min(confidence, 1.0),
                class_name=cls.name,
                file_path=file_path,
                line_number=cls.line_number,
                evidence=evidence,
            )]

        return []

    def _detect_builder(self, cls: ClassInfo, file_path: str) -> List[PatternMatch]:
        """Detect Builder pattern"""
        evidence = []
        confidence = 0.0

        # Check class name
        if "Builder" in cls.name:
            evidence.append("Class name contains 'Builder'")
            confidence += 0.3

        # Check for build/construct method
        method_names = [m.name for m in cls.methods]
        if "build" in method_names or "construct" in method_names:
            evidence.append("Has build/construct method")
            confidence += 0.3

        # Check for multiple setter methods that return self (fluent interface)
        setter_methods = [m for m in cls.methods if m.name.startswith("set_") or m.name.startswith("with_")]
        if len(setter_methods) >= 2:
            evidence.append(f"Has {len(setter_methods)} setter methods (fluent interface)")
            confidence += 0.3

        # Check for product attribute
        if any("product" in attr.lower() for attr in cls.attributes):
            evidence.append("Has product attribute")
            confidence += 0.1

        if confidence >= 0.5:
            return [PatternMatch(
                pattern_type=PatternType.BUILDER,
                confidence=min(confidence, 1.0),
                class_name=cls.name,
                file_path=file_path,
                line_number=cls.line_number,
                evidence=evidence,
            )]

        return []

    def _detect_template_method(self, cls: ClassInfo, file_path: str) -> List[PatternMatch]:
        """Detect Template Method pattern"""
        evidence = []
        confidence = 0.0

        # Check for abstract methods (starting with _)
        abstract_methods = [m for m in cls.methods if m.name.startswith("_") and not m.name.startswith("__")]
        public_methods = [m for m in cls.methods if not m.name.startswith("_")]

        if abstract_methods and public_methods:
            evidence.append(f"Has {len(abstract_methods)} protected/private methods and {len(public_methods)} public methods")
            confidence += 0.3

        # Check if inherits from ABC
        if cls.base_classes and any("ABC" in base for base in cls.base_classes):
            evidence.append("Inherits from ABC")
            confidence += 0.2

        # Check for template method (calls multiple abstract methods)
        for method in public_methods:
            if len(method.calls) >= 2:
                evidence.append(f"Method {method.name} orchestrates multiple calls")
                confidence += 0.3
                break

        if confidence >= 0.5:
            return [PatternMatch(
                pattern_type=PatternType.TEMPLATE_METHOD,
                confidence=min(confidence, 1.0),
                class_name=cls.name,
                file_path=file_path,
                line_number=cls.line_number,
                evidence=evidence,
            )]

        return []


# =============================================================================
# Pattern Application
# =============================================================================

class PatternApplicator:
    """
    Apply design patterns to code.

    Features:
    - Automatic pattern implementation
    - Code generation
    - Safe transformation

    Usage:
        applicator = PatternApplicator()
        applicator.apply_singleton("example.py", "DatabaseConnection")
    """

    def apply_singleton(self, file_path: str, class_name: str) -> str:
        """
        Apply Singleton pattern to a class.

        Args:
            file_path: Path to file
            class_name: Class to make singleton

        Returns:
            Modified code
        """
        code = Path(file_path).read_text()
        lines = code.split("\n")

        # Find class definition
        parser = PythonASTParser()
        analysis = parser.parse_file(file_path)

        cls = parser.find_class(analysis, class_name)
        if not cls:
            raise ValueError(f"Class '{class_name}' not found")

        # Generate singleton code
        singleton_code = f"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        \"\"\"Get singleton instance\"\"\"
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
"""

        # Insert after class definition
        class_line = cls.line_number
        indent = "    "  # Standard Python indent

        # Find insertion point (after class definition)
        insert_line = class_line

        lines.insert(insert_line, singleton_code)

        # Add threading import if not present
        if "import threading" not in code:
            lines.insert(0, "import threading")

        return "\n".join(lines)

    def apply_factory(
        self,
        file_path: str,
        factory_name: str,
        products: List[str],
    ) -> str:
        """
        Apply Factory pattern.

        Args:
            file_path: Path to file
            factory_name: Name for factory class
            products: List of product class names

        Returns:
            Modified code with factory
        """
        factory_code = f"""
class {factory_name}:
    \"\"\"Factory for creating product instances\"\"\"

    @staticmethod
    def create(product_type: str, *args, **kwargs):
        \"\"\"
        Create product instance.

        Args:
            product_type: Type of product to create
            *args, **kwargs: Arguments for product constructor

        Returns:
            Product instance

        Raises:
            ValueError: If product_type is unknown
        \"\"\"
"""

        # Add create logic for each product
        for product in products:
            factory_code += f"""
        if product_type == "{product.lower()}":
            return {product}(*args, **kwargs)
"""

        factory_code += """
        raise ValueError(f"Unknown product type: {product_type}")
"""

        code = Path(file_path).read_text()
        return code + "\n" + factory_code

    def apply_observer(
        self,
        file_path: str,
        subject_class: str,
    ) -> str:
        """
        Apply Observer pattern to a class.

        Args:
            file_path: Path to file
            subject_class: Class to make observable

        Returns:
            Modified code
        """
        observer_code = """
    def __init__(self):
        \"\"\"Initialize subject with empty observers list\"\"\"
        self._observers: List = []
        super().__init__()

    def attach(self, observer):
        \"\"\"Attach an observer\"\"\"
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        \"\"\"Detach an observer\"\"\"
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: str, data: Any = None):
        \"\"\"Notify all observers of an event\"\"\"
        for observer in self._observers:
            observer.update(event, data)
"""

        code = Path(file_path).read_text()
        parser = PythonASTParser()
        analysis = parser.parse_file(file_path)

        cls = parser.find_class(analysis, subject_class)
        if not cls:
            raise ValueError(f"Class '{subject_class}' not found")

        lines = code.split("\n")
        lines.insert(cls.line_number, observer_code)

        return "\n".join(lines)

    def apply_strategy(
        self,
        file_path: str,
        strategy_name: str,
        strategies: List[str],
    ) -> str:
        """
        Apply Strategy pattern.

        Args:
            file_path: Path to file
            strategy_name: Base strategy interface name
            strategies: List of concrete strategy names

        Returns:
            Modified code
        """
        # Generate strategy interface
        strategy_code = f"""
from abc import ABC, abstractmethod

class {strategy_name}(ABC):
    \"\"\"Strategy interface\"\"\"

    @abstractmethod
    def execute(self, *args, **kwargs):
        \"\"\"Execute strategy\"\"\"
        pass
"""

        # Generate concrete strategies
        for strategy in strategies:
            strategy_code += f"""

class {strategy}({strategy_name}):
    \"\"\"Concrete strategy: {strategy}\"\"\"

    def execute(self, *args, **kwargs):
        \"\"\"Execute {strategy} strategy\"\"\"
        # TODO: Implement strategy logic
        pass
"""

        # Generate context class
        strategy_code += f"""

class Context:
    \"\"\"Context that uses a strategy\"\"\"

    def __init__(self, strategy: {strategy_name}):
        self._strategy = strategy

    def set_strategy(self, strategy: {strategy_name}):
        \"\"\"Change strategy at runtime\"\"\"
        self._strategy = strategy

    def execute_strategy(self, *args, **kwargs):
        \"\"\"Execute current strategy\"\"\"
        return self._strategy.execute(*args, **kwargs)
"""

        code = Path(file_path).read_text()
        return code + "\n" + strategy_code


# =============================================================================
# Pattern Suggester
# =============================================================================

class PatternSuggester:
    """
    Suggest design patterns for code improvements.

    Analyzes code structure and suggests applicable patterns.

    Usage:
        suggester = PatternSuggester()
        suggestions = suggester.suggest_patterns("example.py")

        for suggestion in suggestions:
            print(f"{suggestion['pattern']}: {suggestion['reason']}")
    """

    def __init__(self):
        self.parser = PythonASTParser()

    def suggest_patterns(self, file_path: str) -> List[Dict[str, Any]]:
        """Suggest patterns for file"""
        analysis = self.parser.parse_file(file_path)
        suggestions = []

        for cls in analysis.classes:
            # Suggest Singleton for utility classes
            if self._is_utility_class(cls):
                suggestions.append({
                    "pattern": PatternType.SINGLETON,
                    "class": cls.name,
                    "reason": "Utility class - consider Singleton pattern",
                    "confidence": 0.7,
                })

            # Suggest Factory for classes that create many objects
            if self._has_many_create_methods(cls):
                suggestions.append({
                    "pattern": PatternType.FACTORY,
                    "class": cls.name,
                    "reason": "Multiple object creation methods - consider Factory pattern",
                    "confidence": 0.8,
                })

            # Suggest Observer for event-driven classes
            if self._looks_like_event_source(cls):
                suggestions.append({
                    "pattern": PatternType.OBSERVER,
                    "class": cls.name,
                    "reason": "Event-driven behavior - consider Observer pattern",
                    "confidence": 0.7,
                })

            # Suggest Strategy for classes with multiple algorithms
            if self._has_multiple_algorithms(cls):
                suggestions.append({
                    "pattern": PatternType.STRATEGY,
                    "class": cls.name,
                    "reason": "Multiple algorithm implementations - consider Strategy pattern",
                    "confidence": 0.6,
                })

        return suggestions

    def _is_utility_class(self, cls: ClassInfo) -> bool:
        """Check if class is a utility class"""
        # All methods are static/class methods
        return all(
            "staticmethod" in m.decorators or "classmethod" in m.decorators
            for m in cls.methods
        )

    def _has_many_create_methods(self, cls: ClassInfo) -> bool:
        """Check if class has many creation methods"""
        create_methods = [
            m for m in cls.methods
            if m.name.startswith("create") or m.name.startswith("make")
        ]
        return len(create_methods) >= 3

    def _looks_like_event_source(self, cls: ClassInfo) -> bool:
        """Check if class looks like event source"""
        event_keywords = ["event", "listener", "callback", "handler"]
        return any(
            any(keyword in attr.lower() for keyword in event_keywords)
            for attr in cls.attributes
        )

    def _has_multiple_algorithms(self, cls: ClassInfo) -> bool:
        """Check if class has multiple algorithm implementations"""
        # Look for if/elif chains or strategy-like methods
        return len([m for m in cls.methods if m.complexity > 5]) >= 2
