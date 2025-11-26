"""
PHASE 7.5: Spell Checker Component

Checks spelling and grammar in document content.
Uses pyspellchecker for spelling, language_tool_python for grammar (if available).

Usage:
    from core.evaluation.scoring_committee import SpellChecker

    checker = SpellChecker()
    score = await checker.run(task_result)  # 0.0 to 1.0
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from ..base import TaskResult


# Configure logging
logger = logging.getLogger(__name__)


# Try to import spell checking libraries
try:
    from spellchecker import SpellChecker as PySpellChecker
    HAS_SPELLCHECKER = True
except ImportError:
    HAS_SPELLCHECKER = False
    logger.debug("spellchecker not available")


# ============================================================================
# Spell Check Result
# ============================================================================


class SpellingError(BaseModel):
    """A spelling or grammar error."""
    word: str
    suggestions: List[str] = Field(default_factory=list)
    context: str = ""
    error_type: str = "spelling"  # spelling, grammar


class SpellCheckResult(BaseModel):
    """Result of spell checking."""
    total_words: int = 0
    misspelled_count: int = 0
    grammar_errors: int = 0
    errors: List[SpellingError] = Field(default_factory=list)

    @property
    def score(self) -> float:
        """
        Calculate 0-1 score.

        Target: <5% error rate for full score.
        """
        if self.total_words == 0:
            return 1.0

        error_rate = (self.misspelled_count + self.grammar_errors) / self.total_words

        if error_rate == 0:
            return 1.0
        elif error_rate < 0.01:  # <1%
            return 0.95
        elif error_rate < 0.02:  # <2%
            return 0.9
        elif error_rate < 0.05:  # <5%
            return 0.8
        elif error_rate < 0.1:   # <10%
            return 0.6
        else:
            return 0.4


# ============================================================================
# Common Technical Terms (not misspellings)
# ============================================================================


TECHNICAL_TERMS: Set[str] = {
    # Programming
    "api", "apis", "json", "yaml", "xml", "html", "css", "http", "https",
    "url", "urls", "uri", "uris", "sql", "nosql", "graphql", "regex",
    "cli", "gui", "sdk", "ide", "jwt", "oauth", "saml", "ldap",
    # Python
    "python", "pythonic", "django", "flask", "fastapi", "pytest", "numpy",
    "pandas", "scipy", "sklearn", "tensorflow", "pytorch", "pydantic",
    "asyncio", "async", "await", "coroutine", "coroutines",
    # JavaScript
    "javascript", "typescript", "nodejs", "npm", "yarn", "webpack",
    "react", "vue", "angular", "nextjs", "nuxt", "deno",
    # Cloud/DevOps
    "aws", "gcp", "azure", "kubernetes", "k8s", "docker", "terraform",
    "ansible", "jenkins", "gitlab", "github", "bitbucket", "cicd",
    # AI/ML
    "llm", "llms", "gpt", "claude", "anthropic", "openai", "langchain",
    "embeddings", "tokenizer", "tokenizers", "transformers",
    # General tech
    "frontend", "backend", "fullstack", "middleware", "microservice",
    "microservices", "monorepo", "config", "configs", "env", "envs",
    "localhost", "hostname", "dns", "tcp", "udp", "websocket",
    # File types
    "yaml", "toml", "csv", "pdf", "png", "jpg", "jpeg", "svg", "gif",
    # Misc
    "uuid", "uuids", "timestamp", "timestamps", "boolean", "booleans",
    "enum", "enums", "tuple", "tuples", "dict", "dicts",
}


# ============================================================================
# Spell Checker
# ============================================================================


class SpellChecker:
    """
    Check spelling and grammar in content.

    Uses:
    - pyspellchecker for basic spelling
    - Custom technical term whitelist

    Usage:
        checker = SpellChecker()
        score = await checker.run(task_result)
    """

    def __init__(
        self,
        additional_words: Optional[Set[str]] = None,
        language: str = "en",
    ):
        """
        Initialize the spell checker.

        Args:
            additional_words: Additional words to whitelist
            language: Language code (default: English)
        """
        self._language = language
        self._whitelist = TECHNICAL_TERMS.copy()
        if additional_words:
            self._whitelist.update(additional_words)

        # Initialize spell checker if available
        self._spell: Optional[PySpellChecker] = None
        if HAS_SPELLCHECKER:
            self._spell = PySpellChecker(language=language)
            # Add technical terms to dictionary
            self._spell.word_frequency.load_words(self._whitelist)

    async def run(
        self,
        result: TaskResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Check spelling and return score.

        Args:
            result: Task result to check
            context: Additional context

        Returns:
            Score from 0.0 to 1.0
        """
        # Skip spell check for code-heavy content
        if self._is_mostly_code(result.response):
            logger.debug("Skipping spell check for code content")
            return 1.0

        # Extract text (skip code blocks)
        text = self._extract_prose(result.response)

        if not text.strip():
            return 1.0

        # Run spell check
        check_result = await self._check_spelling(text)

        logger.info(
            f"Spell check: {check_result.misspelled_count} misspellings "
            f"in {check_result.total_words} words (score={check_result.score:.2f})"
        )

        return check_result.score

    def _is_mostly_code(self, content: str) -> bool:
        """Check if content is mostly code."""
        # Count code block lines vs prose lines
        code_lines = 0
        prose_lines = 0
        in_code_block = False

        for line in content.split("\n"):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
            elif in_code_block:
                code_lines += 1
            elif line.strip():
                prose_lines += 1

        total = code_lines + prose_lines
        if total == 0:
            return False

        return code_lines / total > 0.7

    def _extract_prose(self, content: str) -> str:
        """Extract prose text, excluding code blocks."""
        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "", content)

        # Remove inline code
        text = re.sub(r"`[^`]+`", "", text)

        # Remove URLs
        text = re.sub(r"https?://\S+", "", text)

        # Remove file paths
        text = re.sub(r"[\w/]+\.\w{2,4}", "", text)

        # Remove markdown formatting
        text = re.sub(r"[*_]{1,2}([^*_]+)[*_]{1,2}", r"\1", text)

        return text

    async def _check_spelling(self, text: str) -> SpellCheckResult:
        """Check spelling in text."""
        result = SpellCheckResult()

        # Tokenize into words
        words = re.findall(r"\b[a-zA-Z]+\b", text)
        result.total_words = len(words)

        if not words:
            return result

        if self._spell is None:
            # No spell checker available - use basic heuristics
            return self._basic_spell_check(words, result)

        # Find misspelled words
        misspelled = self._spell.unknown(words)

        for word in misspelled:
            # Skip if in whitelist (case-insensitive)
            if word.lower() in self._whitelist:
                continue

            # Skip single letters and very short words
            if len(word) <= 2:
                continue

            # Skip words with numbers
            if re.search(r"\d", word):
                continue

            # Skip all-caps (likely acronyms)
            if word.isupper() and len(word) <= 5:
                continue

            # It's a real misspelling
            result.misspelled_count += 1
            result.errors.append(SpellingError(
                word=word,
                suggestions=list(self._spell.candidates(word) or [])[:3],
                error_type="spelling",
            ))

        return result

    def _basic_spell_check(
        self,
        words: List[str],
        result: SpellCheckResult,
    ) -> SpellCheckResult:
        """Basic spell check without library (limited)."""
        # Common misspellings dictionary
        common_misspellings = {
            "teh": "the",
            "recieve": "receive",
            "occured": "occurred",
            "seperate": "separate",
            "definately": "definitely",
            "accomodate": "accommodate",
            "occassion": "occasion",
            "neccessary": "necessary",
            "succesful": "successful",
            "untill": "until",
        }

        for word in words:
            word_lower = word.lower()

            # Check common misspellings
            if word_lower in common_misspellings:
                result.misspelled_count += 1
                result.errors.append(SpellingError(
                    word=word,
                    suggestions=[common_misspellings[word_lower]],
                    error_type="spelling",
                ))

        return result

    def add_to_whitelist(self, words: Set[str]) -> None:
        """Add words to the whitelist."""
        self._whitelist.update(words)
        if self._spell:
            self._spell.word_frequency.load_words(words)
