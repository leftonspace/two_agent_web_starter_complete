"""
JARVIS Vision System

Visual perception capabilities for JARVIS - image analysis, object detection,
scene understanding, and real-time camera processing.

Features:
- Image analysis using GPT-4 Vision / Claude Vision
- Object and scene detection
- Text extraction (OCR)
- Face detection (privacy-aware)
- Real-time camera feed analysis

Usage:
    vision = JarvisVision()

    # Analyze an image
    result = await vision.analyze_image(image_bytes, "What do you see?")

    # Analyze from camera
    result = await vision.analyze_camera_frame(frame_bytes)
"""

from __future__ import annotations

import asyncio
import base64
import io
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import core_logging
except ImportError:
    import logging as core_logging

# Vision provider imports
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# =============================================================================
# Configuration
# =============================================================================

class VisionProvider(Enum):
    """Available vision providers"""
    OPENAI = "openai"       # GPT-4 Vision
    ANTHROPIC = "anthropic" # Claude Vision
    LOCAL = "local"         # Future: local models


class AnalysisType(Enum):
    """Types of visual analysis"""
    GENERAL = "general"           # General scene understanding
    OBJECTS = "objects"           # Object detection
    TEXT = "text"                 # OCR / text extraction
    FACES = "faces"               # Face detection (privacy-aware)
    TECHNICAL = "technical"       # Code, diagrams, technical content
    DOCUMENT = "document"         # Document analysis
    COMPARISON = "comparison"     # Compare multiple images


@dataclass
class VisionConfig:
    """Vision system configuration"""
    provider: VisionProvider = VisionProvider.OPENAI

    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"  # GPT-4 with vision

    # Anthropic settings
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"  # Claude 3.5 Sonnet with vision

    # Processing settings
    max_image_size: int = 20 * 1024 * 1024  # 20MB
    default_detail: str = "high"  # high or low for OpenAI

    # Privacy settings
    blur_faces: bool = False
    redact_personal_info: bool = False

    @classmethod
    def from_env(cls) -> "VisionConfig":
        """Create config from environment variables"""
        provider_str = os.getenv("JARVIS_VISION_PROVIDER", "openai")

        return cls(
            provider=VisionProvider(provider_str),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )


# =============================================================================
# Analysis Results
# =============================================================================

@dataclass
class VisionAnalysis:
    """Result of image analysis"""
    description: str
    objects: List[str] = field(default_factory=list)
    text_content: Optional[str] = None
    confidence: float = 1.0
    analysis_type: AnalysisType = AnalysisType.GENERAL
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "objects": self.objects,
            "text_content": self.text_content,
            "confidence": self.confidence,
            "analysis_type": self.analysis_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
        }


# =============================================================================
# Vision Engines
# =============================================================================

class OpenAIVision:
    """GPT-4 Vision engine"""

    def __init__(self, config: VisionConfig):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai not installed. Run: pip install openai")

        self.config = config
        self.client = openai.AsyncOpenAI(api_key=config.openai_api_key)

        print(f"[Vision] OpenAI vision initialized with model: {config.openai_model}")

    async def analyze(
        self,
        image_data: Union[bytes, str],
        prompt: str,
        detail: str = "high"
    ) -> VisionAnalysis:
        """
        Analyze image with GPT-4 Vision.

        Args:
            image_data: Image bytes or base64 string
            prompt: Analysis prompt
            detail: "high" or "low" detail level

        Returns:
            VisionAnalysis with results
        """
        start_time = datetime.now()

        # Convert to base64 if needed
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode('utf-8')
        else:
            image_b64 = image_data

        # Detect image type
        image_type = self._detect_image_type(image_data if isinstance(image_data, bytes) else base64.b64decode(image_data))

        try:
            response = await self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are JARVIS's visual perception system. Analyze images with precision and wit.

When describing what you see:
- Be detailed but concise
- Note important objects, text, people (without identifying individuals)
- Describe spatial relationships
- If asked about something specific, focus on that
- Maintain JARVIS's dry British butler tone in descriptions

For technical content (code, diagrams), provide accurate analysis.
For documents, extract and summarize key information."""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_type};base64,{image_b64}",
                                    "detail": detail
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )

            description = response.choices[0].message.content

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Extract objects mentioned (simple extraction)
            objects = self._extract_objects(description)

            # Check for text content
            text_content = None
            if any(word in prompt.lower() for word in ["text", "read", "ocr", "words", "written"]):
                text_content = description

            print(f"[Vision] OpenAI analyzed image in {processing_time:.0f}ms")

            return VisionAnalysis(
                description=description,
                objects=objects,
                text_content=text_content,
                confidence=1.0,
                processing_time_ms=processing_time
            )

        except Exception as e:
            print(f"[Vision] OpenAI vision error: {e}")
            raise

    def _detect_image_type(self, image_bytes: bytes) -> str:
        """Detect image MIME type from bytes"""
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return "image/webp"
        else:
            return "image/jpeg"  # Default

    def _extract_objects(self, description: str) -> List[str]:
        """Extract mentioned objects from description"""
        # Simple extraction - could be enhanced with NLP
        common_objects = [
            "person", "people", "man", "woman", "child",
            "car", "vehicle", "computer", "phone", "laptop",
            "table", "chair", "desk", "window", "door",
            "book", "paper", "document", "screen", "monitor",
            "tree", "plant", "animal", "dog", "cat",
            "building", "house", "room", "office", "street"
        ]

        description_lower = description.lower()
        found = [obj for obj in common_objects if obj in description_lower]
        return list(set(found))


class AnthropicVision:
    """Claude Vision engine"""

    def __init__(self, config: VisionConfig):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic not installed. Run: pip install anthropic")

        self.config = config
        self.client = anthropic.AsyncAnthropic(api_key=config.anthropic_api_key)

        print(f"[Vision] Anthropic vision initialized with model: {config.anthropic_model}")

    async def analyze(
        self,
        image_data: Union[bytes, str],
        prompt: str,
        detail: str = "high"
    ) -> VisionAnalysis:
        """Analyze image with Claude Vision"""
        start_time = datetime.now()

        # Convert to base64 if needed
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            image_bytes = image_data
        else:
            image_b64 = image_data
            image_bytes = base64.b64decode(image_data)

        # Detect image type
        media_type = self._detect_media_type(image_bytes)

        try:
            response = await self.client.messages.create(
                model=self.config.anthropic_model,
                max_tokens=1000,
                system="""You are JARVIS's visual perception system. Analyze images with precision and wit.

When describing what you see:
- Be detailed but concise
- Note important objects, text, people (without identifying individuals)
- Describe spatial relationships
- If asked about something specific, focus on that
- Maintain JARVIS's dry British butler tone in descriptions""",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            description = response.content[0].text

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            print(f"[Vision] Anthropic analyzed image in {processing_time:.0f}ms")

            return VisionAnalysis(
                description=description,
                objects=self._extract_objects(description),
                confidence=1.0,
                processing_time_ms=processing_time
            )

        except Exception as e:
            print(f"[Vision] Anthropic vision error: {e}")
            raise

    def _detect_media_type(self, image_bytes: bytes) -> str:
        """Detect image MIME type"""
        if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif image_bytes[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return "image/webp"
        return "image/jpeg"

    def _extract_objects(self, description: str) -> List[str]:
        """Extract mentioned objects"""
        common_objects = [
            "person", "people", "man", "woman", "child",
            "car", "vehicle", "computer", "phone", "laptop",
            "table", "chair", "desk", "window", "door",
            "book", "paper", "document", "screen", "monitor"
        ]
        description_lower = description.lower()
        return list(set(obj for obj in common_objects if obj in description_lower))


# =============================================================================
# Main JARVIS Vision Class
# =============================================================================

class JarvisVision:
    """
    Main JARVIS vision interface.

    Provides image analysis, object detection, and camera processing.

    Usage:
        vision = JarvisVision()

        # Analyze uploaded image
        result = await vision.analyze_image(image_bytes, "What's in this image?")

        # Analyze with specific focus
        result = await vision.analyze_image(image_bytes, "Read the text in this document")

        # Compare images
        result = await vision.compare_images([img1, img2], "What's different?")
    """

    # JARVIS-style prompts for different analysis types
    ANALYSIS_PROMPTS = {
        AnalysisType.GENERAL: "Describe what you see in this image in detail.",
        AnalysisType.OBJECTS: "List and describe all objects visible in this image.",
        AnalysisType.TEXT: "Extract and transcribe all text visible in this image.",
        AnalysisType.FACES: "Describe the people in this image (without identifying individuals).",
        AnalysisType.TECHNICAL: "Analyze this technical content (code, diagram, schematic).",
        AnalysisType.DOCUMENT: "Analyze this document and summarize its key content.",
    }

    def __init__(self, config: Optional[VisionConfig] = None):
        self.config = config or VisionConfig.from_env()

        # Initialize vision engine
        self.engine = None
        self._init_engine()

        print(f"[Vision] JARVIS vision initialized with provider: {self.config.provider.value}")

    def _init_engine(self):
        """Initialize the vision engine based on config"""
        try:
            if self.config.provider == VisionProvider.OPENAI:
                if self.config.openai_api_key:
                    self.engine = OpenAIVision(self.config)
                elif self.config.anthropic_api_key:
                    self.config.provider = VisionProvider.ANTHROPIC
                    self.engine = AnthropicVision(self.config)
            elif self.config.provider == VisionProvider.ANTHROPIC:
                if self.config.anthropic_api_key:
                    self.engine = AnthropicVision(self.config)
                elif self.config.openai_api_key:
                    self.config.provider = VisionProvider.OPENAI
                    self.engine = OpenAIVision(self.config)
        except Exception as e:
            print(f"[Vision] Engine init error: {e}")

    async def analyze_image(
        self,
        image_data: Union[bytes, str, Path],
        prompt: Optional[str] = None,
        analysis_type: AnalysisType = AnalysisType.GENERAL
    ) -> VisionAnalysis:
        """
        Analyze an image.

        Args:
            image_data: Image as bytes, base64 string, or file path
            prompt: Custom analysis prompt (optional)
            analysis_type: Type of analysis to perform

        Returns:
            VisionAnalysis with results
        """
        if not self.engine:
            raise RuntimeError("Vision engine not available. Check API keys.")

        # Load image if path provided
        if isinstance(image_data, Path) or (isinstance(image_data, str) and os.path.exists(image_data)):
            image_data = Path(image_data).read_bytes()

        # Use default prompt if not provided
        if not prompt:
            prompt = self.ANALYSIS_PROMPTS.get(analysis_type, self.ANALYSIS_PROMPTS[AnalysisType.GENERAL])

        # Validate image size
        if isinstance(image_data, bytes) and len(image_data) > self.config.max_image_size:
            raise ValueError(f"Image too large. Max size: {self.config.max_image_size / 1024 / 1024}MB")

        result = await self.engine.analyze(image_data, prompt)
        result.analysis_type = analysis_type

        return result

    async def analyze_camera_frame(
        self,
        frame_data: bytes,
        prompt: Optional[str] = None,
        context: Optional[str] = None
    ) -> VisionAnalysis:
        """
        Analyze a camera frame.

        Args:
            frame_data: Camera frame as JPEG/PNG bytes
            prompt: What to look for
            context: Previous context for continuity

        Returns:
            VisionAnalysis with results
        """
        full_prompt = prompt or "Describe what you see in this camera view."

        if context:
            full_prompt = f"Previous context: {context}\n\nNow: {full_prompt}"

        return await self.analyze_image(frame_data, full_prompt, AnalysisType.GENERAL)

    async def read_text(self, image_data: Union[bytes, str, Path]) -> VisionAnalysis:
        """
        Extract text from image (OCR).

        Args:
            image_data: Image containing text

        Returns:
            VisionAnalysis with extracted text
        """
        prompt = """Extract and transcribe ALL text visible in this image.
        Format the text as it appears (preserve structure where possible).
        If there are multiple text areas, separate them clearly."""

        return await self.analyze_image(image_data, prompt, AnalysisType.TEXT)

    async def analyze_document(self, image_data: Union[bytes, str, Path]) -> VisionAnalysis:
        """
        Analyze a document image.

        Args:
            image_data: Document image

        Returns:
            VisionAnalysis with document analysis
        """
        prompt = """Analyze this document:
        1. What type of document is this?
        2. Extract key information (names, dates, amounts, etc.)
        3. Summarize the main content
        4. Note any important details or action items"""

        return await self.analyze_image(image_data, prompt, AnalysisType.DOCUMENT)

    async def analyze_code(self, image_data: Union[bytes, str, Path]) -> VisionAnalysis:
        """
        Analyze code/technical diagram in image.

        Args:
            image_data: Image containing code or diagram

        Returns:
            VisionAnalysis with technical analysis
        """
        prompt = """Analyze this technical content:
        1. If it's code: identify the language, explain what it does, note any issues
        2. If it's a diagram: describe the components and relationships
        3. If it's a schematic: explain the system architecture
        Provide actionable insights."""

        return await self.analyze_image(image_data, prompt, AnalysisType.TECHNICAL)

    async def compare_images(
        self,
        images: List[Union[bytes, str]],
        prompt: Optional[str] = None
    ) -> VisionAnalysis:
        """
        Compare multiple images.

        Note: This sends images one at a time with context for comparison.

        Args:
            images: List of images to compare
            prompt: What to compare

        Returns:
            VisionAnalysis with comparison results
        """
        if len(images) < 2:
            raise ValueError("Need at least 2 images to compare")

        comparison_prompt = prompt or "Compare these images and describe the differences."

        # Analyze first image
        result1 = await self.analyze_image(images[0], "Describe this image in detail for comparison.")

        # Analyze second with context
        context_prompt = f"""Previous image description: {result1.description}

Now analyze this new image and compare it to the previous one.
{comparison_prompt}"""

        result2 = await self.analyze_image(images[1], context_prompt)
        result2.analysis_type = AnalysisType.COMPARISON

        return result2

    async def describe_for_jarvis(
        self,
        image_data: Union[bytes, str, Path],
        user_question: Optional[str] = None
    ) -> str:
        """
        Get a JARVIS-style description for use in chat.

        Args:
            image_data: Image to describe
            user_question: User's question about the image

        Returns:
            JARVIS-style description string
        """
        prompt = f"""As JARVIS, describe what you observe in this image.

User's question: {user_question or "What do you see?"}

Respond in your characteristic British butler manner - precise, slightly dry, helpful.
If the user asked a specific question, focus on answering that."""

        result = await self.analyze_image(image_data, prompt)
        return result.description

    def is_available(self) -> bool:
        """Check if vision is available"""
        return self.engine is not None


# =============================================================================
# Image Utilities
# =============================================================================

def resize_image_for_upload(
    image_bytes: bytes,
    max_size: int = 4 * 1024 * 1024,
    max_dimension: int = 2048
) -> bytes:
    """
    Resize image if needed for API upload.

    Args:
        image_bytes: Original image bytes
        max_size: Maximum file size in bytes
        max_dimension: Maximum width/height

    Returns:
        Resized image bytes (or original if small enough)
    """
    try:
        from PIL import Image

        if len(image_bytes) <= max_size:
            # Check dimensions
            img = Image.open(io.BytesIO(image_bytes))
            if img.width <= max_dimension and img.height <= max_dimension:
                return image_bytes

        # Need to resize
        img = Image.open(io.BytesIO(image_bytes))

        # Calculate new dimensions
        ratio = min(max_dimension / img.width, max_dimension / img.height)
        if ratio < 1:
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Save with compression
        output = io.BytesIO()

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        quality = 85
        while quality > 20:
            output.seek(0)
            output.truncate()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            if output.tell() <= max_size:
                break
            quality -= 10

        return output.getvalue()

    except ImportError:
        # PIL not available, return original
        return image_bytes


def image_to_base64(image_bytes: bytes) -> str:
    """Convert image bytes to base64 string"""
    return base64.b64encode(image_bytes).decode('utf-8')


def base64_to_image(b64_string: str) -> bytes:
    """Convert base64 string to image bytes"""
    # Remove data URL prefix if present
    if ',' in b64_string:
        b64_string = b64_string.split(',')[1]
    return base64.b64decode(b64_string)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'JarvisVision',
    'VisionConfig',
    'VisionProvider',
    'VisionAnalysis',
    'AnalysisType',
    'resize_image_for_upload',
    'image_to_base64',
    'base64_to_image',
]
