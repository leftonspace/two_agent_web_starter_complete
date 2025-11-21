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
