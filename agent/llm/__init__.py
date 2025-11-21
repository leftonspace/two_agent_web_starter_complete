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
"""

from .ollama_client import OllamaClient
from .llm_router import LLMRouter, ModelTier
from .performance_tracker import PerformanceTracker
from .hybrid_strategy import HybridStrategy, TaskComplexity

__all__ = [
    "OllamaClient",
    "LLMRouter",
    "ModelTier",
    "PerformanceTracker",
    "HybridStrategy",
    "TaskComplexity",
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
