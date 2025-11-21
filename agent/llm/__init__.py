"""
PHASE 9: Advanced LLM Integration Module

This module provides:
- Ollama integration for local LLMs (Llama 3, Mistral, etc.)
- Intelligent LLM routing between cloud and local models
- Performance tracking and analytics
- Hybrid execution strategy for cost optimization

Components:
- ollama_client: Ollama API client with streaming support
- llm_router: Intelligent model selection and routing
- performance_tracker: Metrics tracking for all LLM calls
- hybrid_strategy: Cost-optimized hybrid cloud/local execution

Re-exports from llm.py (for backward compatibility):
- chat_json: Main LLM chat function with JSON response parsing
- chat: Simple text chat wrapper
- validate_api_connectivity: API connectivity validation
"""

from .ollama_client import OllamaClient
from .llm_router import LLMRouter, ModelTier
from .performance_tracker import PerformanceTracker
from .hybrid_strategy import HybridStrategy, TaskComplexity

# Re-export functions from llm.py (the module file) to maintain backward compatibility
# This is needed because the llm/ package shadows the llm.py module file
import importlib.util
from pathlib import Path

_llm_module_path = Path(__file__).parent.parent / "llm.py"
_spec = importlib.util.spec_from_file_location("llm_module", _llm_module_path)
_llm_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_llm_module)

# Re-export the key functions
chat_json = _llm_module.chat_json
chat = _llm_module.chat
validate_api_connectivity = _llm_module.validate_api_connectivity

__all__ = [
    # Phase 9 components
    "OllamaClient",
    "LLMRouter",
    "ModelTier",
    "PerformanceTracker",
    "HybridStrategy",
    "TaskComplexity",
    # Re-exported from llm.py
    "chat_json",
    "chat",
    "validate_api_connectivity",
]

# ----------------------------------------------------------------------
# Backwards compatibility: expose chat_json from legacy llm.py
# so imports like `from llm import chat_json` keep working.
# ----------------------------------------------------------------------
try:
    import importlib.util
    from pathlib import Path as _Path

    _legacy_llm_path = _Path(__file__).resolve().parent.parent / "llm.py"
    if _legacy_llm_path.exists():
        spec = importlib.util.spec_from_file_location("legacy_llm", _legacy_llm_path)
        legacy_llm = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(legacy_llm)  # type: ignore[arg-type]
        # Re-export for callers
        chat_json = legacy_llm.chat_json  # type: ignore[attr-defined]
except Exception:
    # If anything goes wrong, don't crash import; callers will see normal errors.
    pass
