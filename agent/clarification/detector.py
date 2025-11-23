"""
Vague Request Detection

Detect vague or incomplete requests and identify what details are missing.
"""

from typing import List, Dict, Tuple, Optional
from enum import Enum
import re
from dataclasses import dataclass, field


class RequestClarity(Enum):
    """Clarity level of user request"""
    CLEAR = "clear"
    SOMEWHAT_CLEAR = "somewhat_clear"
    VAGUE = "vague"
    VERY_VAGUE = "very_vague"


class RequestType(Enum):
    """Type of request"""
    WEBSITE = "website"
    APPLICATION = "application"
    API = "api"
    DATABASE = "database"
    AUTOMATION = "automation"
    ANALYSIS = "analysis"
    CONTENT = "content"
    GENERAL = "general"


@dataclass
class ClarityAnalysis:
    """Analysis result for request clarity"""
    clarity_level: RequestClarity
    confidence: float
    missing_details: List[str]
    detected_type: RequestType
    specific_elements: Dict[str, any]
    reasoning: str
    vagueness_score: float = 0.0
    word_count: int = 0

    def needs_clarification(self, threshold: RequestClarity = RequestClarity.SOMEWHAT_CLEAR) -> bool:
        """Check if request needs clarification based on threshold"""
        levels = [RequestClarity.VERY_VAGUE, RequestClarity.VAGUE,
                  RequestClarity.SOMEWHAT_CLEAR, RequestClarity.CLEAR]
        return levels.index(self.clarity_level) <= levels.index(threshold)

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "clarity_level": self.clarity_level.value,
            "confidence": self.confidence,
            "missing_details": self.missing_details,
            "detected_type": self.detected_type.value,
            "specific_elements": self.specific_elements,
            "reasoning": self.reasoning,
            "vagueness_score": self.vagueness_score,
            "word_count": self.word_count
        }


class VagueRequestDetector:
    """Detect vague or incomplete requests"""

    def __init__(self):
        # Keywords indicating request types
        self.type_keywords = {
            RequestType.WEBSITE: [
                'website', 'site', 'web page', 'landing page', 'portfolio',
                'blog', 'e-commerce', 'online store', 'web app', 'webpage'
            ],
            RequestType.APPLICATION: [
                'app', 'application', 'software', 'program', 'tool',
                'desktop app', 'mobile app', 'cli', 'utility'
            ],
            RequestType.API: [
                'api', 'endpoint', 'rest', 'graphql', 'service',
                'microservice', 'backend', 'server', 'webhook'
            ],
            RequestType.DATABASE: [
                'database', 'db', 'schema', 'table', 'query',
                'sql', 'nosql', 'data model', 'migration'
            ],
            RequestType.AUTOMATION: [
                'automate', 'script', 'bot', 'workflow', 'pipeline',
                'ci/cd', 'deployment', 'integration', 'cron'
            ],
            RequestType.ANALYSIS: [
                'analyze', 'analysis', 'report', 'metrics', 'dashboard',
                'visualization', 'insights', 'statistics', 'chart',
                'review', 'investigate', 'check', 'inspect', 'examine',
                'audit', 'scan', 'code review', 'find issues', 'find bugs'
            ],
            RequestType.CONTENT: [
                'write', 'content', 'article', 'documentation', 'copy',
                'text', 'blog post', 'guide', 'readme'
            ]
        }

        # Vague trigger phrases
        self.vague_triggers = [
            'something', 'some kind of', 'maybe', 'i guess',
            'not sure', 'whatever', 'just', 'simple', 'basic',
            'normal', 'regular', 'standard', 'typical', 'usual',
            'kind of', 'sort of', 'like a', 'or something'
        ]

        # Specific detail patterns
        self.detail_patterns = {
            'color_scheme': re.compile(r'\b(color|theme|style|dark|light|palette|blue|red|green)\b', re.I),
            'target_audience': re.compile(r'\b(for|audience|users?|customers?|clients?|visitors?|developers?)\b', re.I),
            'features': re.compile(r'\b(feature|function|capability|include|need|want|should have|must have)\b', re.I),
            'technology': re.compile(r'\b(using|with|in|built with|react|vue|python|node|django|flask|typescript)\b', re.I),
            'pages_sections': re.compile(r'\b(page|section|component|part|area|layout|screen|view)\b', re.I),
            'timeline': re.compile(r'\b(by|deadline|asap|urgent|when|timeline|due|priority)\b', re.I),
            'examples': re.compile(r'\b(like|similar to|inspired by|example|reference|based on)\b', re.I),
            'scale': re.compile(r'\b(\d+\s*(users?|items?|pages?|requests?)|small|medium|large|enterprise)\b', re.I)
        }

        # Required details by request type
        self.required_details = {
            RequestType.WEBSITE: ['purpose', 'pages', 'features', 'audience'],
            RequestType.APPLICATION: ['platform', 'features', 'technology'],
            RequestType.API: ['endpoints', 'authentication', 'data_model'],
            RequestType.DATABASE: ['schema', 'relationships', 'technology'],
            RequestType.AUTOMATION: ['trigger', 'actions', 'frequency'],
            RequestType.ANALYSIS: ['data_source', 'metrics', 'output_format'],
            RequestType.CONTENT: ['topic', 'tone', 'length', 'audience'],
            RequestType.GENERAL: ['goal', 'constraints']
        }

    def analyze(self, request: str) -> ClarityAnalysis:
        """Analyze request clarity and completeness"""
        request_lower = request.lower()
        word_count = len(request.split())

        # Detect request type
        detected_type = self._detect_type(request_lower)

        # Check for vague indicators
        vagueness_score = self._calculate_vagueness(request_lower)

        # Extract specific elements
        specific_elements = self._extract_specifics(request)

        # Identify missing details based on type
        missing_details = self._identify_missing_details(
            detected_type,
            specific_elements,
            request
        )

        # Determine clarity level
        clarity_level = self._determine_clarity(
            vagueness_score,
            len(missing_details),
            len(specific_elements),
            word_count
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            clarity_level,
            vagueness_score,
            detected_type
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            clarity_level,
            vagueness_score,
            missing_details,
            specific_elements
        )

        return ClarityAnalysis(
            clarity_level=clarity_level,
            confidence=confidence,
            missing_details=missing_details,
            detected_type=detected_type,
            specific_elements=specific_elements,
            reasoning=reasoning,
            vagueness_score=vagueness_score,
            word_count=word_count
        )

    def _detect_type(self, request: str) -> RequestType:
        """Detect the type of request"""
        scores = {}

        for req_type, keywords in self.type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in request)
            if score > 0:
                scores[req_type] = score

        if scores:
            return max(scores, key=scores.get)

        return RequestType.GENERAL

    def _calculate_vagueness(self, request: str) -> float:
        """Calculate vagueness score (0-1, higher = more vague)"""
        vague_count = sum(1 for trigger in self.vague_triggers if trigger in request)

        # Short requests are often vague
        word_count = len(request.split())
        brevity_score = max(0, 1 - (word_count / 20))

        # Check for question marks (user already unsure)
        question_count = request.count('?')
        uncertainty_score = min(0.2, question_count * 0.1)

        # Combine factors
        vagueness = (vague_count * 0.15 + brevity_score * 0.5 + uncertainty_score)
        return min(1.0, vagueness)

    def _extract_specifics(self, request: str) -> Dict[str, any]:
        """Extract specific elements from request"""
        specifics = {}

        for element, pattern in self.detail_patterns.items():
            if pattern.search(request):
                matches = pattern.findall(request)
                if matches:
                    specifics[element] = matches

        # Extract numbers (potential counts, sizes, etc.)
        numbers = re.findall(r'\b\d+\b', request)
        if numbers:
            specifics['quantities'] = numbers

        # Extract quoted strings (potential names, titles)
        quotes = re.findall(r'"([^"]*)"', request)
        if quotes:
            specifics['quoted_text'] = quotes

        # Extract URLs
        urls = re.findall(r'https?://\S+', request)
        if urls:
            specifics['urls'] = urls

        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', request)
        if emails:
            specifics['emails'] = emails

        return specifics

    def _identify_missing_details(
        self,
        request_type: RequestType,
        specific_elements: Dict,
        request: str
    ) -> List[str]:
        """Identify what details are missing based on request type"""
        missing = []
        request_lower = request.lower()

        # Common missing details - but NOT for analysis/review requests
        # Analysis requests don't need "target audience" questions
        audience_relevant_types = [
            RequestType.WEBSITE, RequestType.APPLICATION,
            RequestType.CONTENT, RequestType.GENERAL
        ]
        if request_type in audience_relevant_types and 'target_audience' not in specific_elements:
            missing.append('target_audience')

        # Type-specific missing details
        if request_type == RequestType.WEBSITE:
            if 'pages_sections' not in specific_elements:
                missing.append('pages_or_sections')
            if 'features' not in specific_elements:
                missing.append('specific_features')
            if 'color_scheme' not in specific_elements:
                missing.append('color_scheme_or_style')
            if 'examples' not in specific_elements:
                missing.append('reference_examples')

        elif request_type == RequestType.APPLICATION:
            if 'technology' not in specific_elements:
                missing.append('technology_stack')
            if 'features' not in specific_elements:
                missing.append('core_functionality')
            if 'platform' not in request_lower and 'web' not in request_lower:
                missing.append('target_platform')

        elif request_type == RequestType.API:
            if 'endpoint' not in request_lower:
                missing.append('endpoint_specifications')
            if 'data' not in request_lower and 'model' not in request_lower:
                missing.append('data_models')
            if 'auth' not in request_lower and 'token' not in request_lower:
                missing.append('authentication_method')

        elif request_type == RequestType.DATABASE:
            if 'schema' not in request_lower and 'table' not in request_lower:
                missing.append('schema_design')
            if 'relation' not in request_lower:
                missing.append('data_relationships')

        elif request_type == RequestType.CONTENT:
            if 'tone' not in request_lower and 'style' not in request_lower:
                missing.append('writing_tone')
            if 'length' not in request_lower and 'word' not in request_lower:
                missing.append('content_length')
            if 'topic' not in request_lower and 'about' not in request_lower:
                missing.append('main_topic')

        elif request_type == RequestType.AUTOMATION:
            if 'trigger' not in request_lower and 'when' not in request_lower:
                missing.append('trigger_condition')
            if 'action' not in request_lower and 'do' not in request_lower:
                missing.append('actions_to_perform')

        return missing

    def _determine_clarity(
        self,
        vagueness_score: float,
        missing_count: int,
        specific_count: int,
        word_count: int
    ) -> RequestClarity:
        """Determine overall clarity level"""
        # Calculate clarity score
        clarity_score = (
            (1 - vagueness_score) * 0.3 +
            max(0, 1 - (missing_count / 5)) * 0.3 +
            min(1, specific_count / 3) * 0.2 +
            min(1, word_count / 30) * 0.2
        )

        if clarity_score >= 0.75:
            return RequestClarity.CLEAR
        elif clarity_score >= 0.5:
            return RequestClarity.SOMEWHAT_CLEAR
        elif clarity_score >= 0.25:
            return RequestClarity.VAGUE
        else:
            return RequestClarity.VERY_VAGUE

    def _calculate_confidence(
        self,
        clarity_level: RequestClarity,
        vagueness_score: float,
        request_type: RequestType
    ) -> float:
        """Calculate confidence in the analysis"""
        base_confidence = 0.7

        # Adjust based on clarity
        if clarity_level == RequestClarity.CLEAR:
            base_confidence += 0.2
        elif clarity_level == RequestClarity.VERY_VAGUE:
            base_confidence += 0.15

        # Adjust based on type detection
        if request_type != RequestType.GENERAL:
            base_confidence += 0.1

        return min(1.0, base_confidence)

    def _generate_reasoning(
        self,
        clarity_level: RequestClarity,
        vagueness_score: float,
        missing_details: List[str],
        specific_elements: Dict
    ) -> str:
        """Generate human-readable reasoning"""
        reasons = []

        if clarity_level == RequestClarity.VERY_VAGUE:
            reasons.append("The request is very brief and lacks specific details")
        elif clarity_level == RequestClarity.VAGUE:
            reasons.append("The request needs more specific information")

        if vagueness_score > 0.5:
            reasons.append("Contains vague language that needs clarification")

        if len(missing_details) > 3:
            reasons.append(f"Missing {len(missing_details)} important details")
        elif len(missing_details) > 0:
            readable_missing = [m.replace('_', ' ') for m in missing_details[:3]]
            reasons.append(f"Missing: {', '.join(readable_missing)}")

        if len(specific_elements) > 2:
            reasons.append(f"Good: includes {', '.join(list(specific_elements.keys())[:3])}")

        return ". ".join(reasons) if reasons else "Request appears complete"


def should_request_clarification(
    request: str,
    threshold: RequestClarity = RequestClarity.SOMEWHAT_CLEAR,
    always_clarify_types: Optional[List[RequestType]] = None
) -> Tuple[bool, ClarityAnalysis]:
    """
    Determine if clarification should be requested

    Args:
        request: User's request text
        threshold: Clarity level below which to request clarification
        always_clarify_types: Request types that always need clarification

    Returns:
        Tuple of (should_clarify, analysis)
    """
    detector = VagueRequestDetector()
    analysis = detector.analyze(request)

    # Check if clarification needed
    should_clarify = False

    # Check clarity threshold
    clarity_levels = [RequestClarity.VERY_VAGUE, RequestClarity.VAGUE,
                      RequestClarity.SOMEWHAT_CLEAR, RequestClarity.CLEAR]
    if clarity_levels.index(analysis.clarity_level) < clarity_levels.index(threshold):
        should_clarify = True

    # Check if type always needs clarification
    if always_clarify_types and analysis.detected_type in always_clarify_types:
        should_clarify = True

    # Override if user explicitly says to skip
    skip_phrases = ['just do it', 'skip questions', 'no questions', 'figure it out',
                    'use defaults', 'your choice', 'surprise me']
    if any(phrase in request.lower() for phrase in skip_phrases):
        should_clarify = False

    # Skip clarification for ANALYSIS requests - they're typically well-defined
    # Code review/analysis doesn't need questions about "target audience" etc.
    if analysis.detected_type == RequestType.ANALYSIS:
        should_clarify = False

    return should_clarify, analysis
