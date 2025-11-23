"""
JARVIS Vision API

FastAPI router for visual perception endpoints.

Provides:
- POST /api/vision/analyze - Analyze uploaded image
- POST /api/vision/camera - Analyze camera capture
- POST /api/vision/ocr - Extract text from image
- POST /api/vision/document - Analyze document
- POST /api/vision/chat - Vision-enabled chat message

Usage:
    from vision_api import router as vision_router
    app.include_router(vision_router)
"""

from __future__ import annotations

import base64
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import core_logging

# Import auth if available
try:
    from webapp.auth import User, require_auth, get_current_user
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    User = None
    def require_auth():
        return None
    def get_current_user():
        return None

# Use optional auth for vision endpoints (allow unauthenticated access when auth is disabled)
def optional_auth():
    """Optional authentication - allows access without login but uses user if available"""
    if AUTH_AVAILABLE:
        return get_current_user
    return lambda: None

# Import vision components
try:
    from jarvis_vision import (
        JarvisVision,
        VisionConfig,
        VisionAnalysis,
        AnalysisType,
        resize_image_for_upload,
        base64_to_image,
    )
    VISION_AVAILABLE = True
except ImportError as e:
    VISION_AVAILABLE = False
    print(f"[Vision API] Vision components not available: {e}")

# Import chat for vision-integrated responses
try:
    from jarvis_chat import JarvisChat
    CHAT_AVAILABLE = True
except ImportError:
    JarvisChat = None
    CHAT_AVAILABLE = False


# =============================================================================
# API Models
# =============================================================================

class AnalyzeImageRequest(BaseModel):
    """Request to analyze an image"""
    image_base64: str
    prompt: Optional[str] = None
    analysis_type: str = "general"


class AnalyzeImageResponse(BaseModel):
    """Response from image analysis"""
    description: str
    objects: List[str]
    text_content: Optional[str]
    analysis_type: str
    processing_time_ms: float


class CameraCaptureRequest(BaseModel):
    """Request to analyze camera capture"""
    frame_base64: str
    prompt: Optional[str] = None
    context: Optional[str] = None


class VisionChatRequest(BaseModel):
    """Chat message with image"""
    message: str
    image_base64: str
    context: Optional[Dict[str, Any]] = None


class VisionChatResponse(BaseModel):
    """Response to vision chat"""
    content: str
    vision_analysis: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


class VisionStatusResponse(BaseModel):
    """Vision system status"""
    available: bool
    provider: Optional[str]
    supported_formats: List[str]


# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter(prefix="/api/vision", tags=["vision"])

# Global vision instance
_vision: Optional[JarvisVision] = None
_chat: Optional[JarvisChat] = None


def get_vision() -> JarvisVision:
    """Get or create vision instance"""
    global _vision

    if not VISION_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Vision system not available. Check dependencies and API keys."
        )

    if _vision is None:
        _vision = JarvisVision()

    if not _vision.is_available():
        raise HTTPException(
            status_code=503,
            detail="Vision engine not initialized. Check API keys."
        )

    return _vision


def get_chat() -> Optional[JarvisChat]:
    """Get or create chat instance for vision-integrated responses"""
    global _chat

    if CHAT_AVAILABLE and _chat is None:
        _chat = JarvisChat()

    return _chat


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/status", response_model=VisionStatusResponse)
async def vision_status():
    """
    Get vision system status.

    Returns availability and supported formats.
    """
    if not VISION_AVAILABLE:
        return VisionStatusResponse(
            available=False,
            provider=None,
            supported_formats=[]
        )

    try:
        vision = get_vision()
        return VisionStatusResponse(
            available=True,
            provider=vision.config.provider.value,
            supported_formats=["image/jpeg", "image/png", "image/gif", "image/webp"]
        )
    except Exception:
        return VisionStatusResponse(
            available=False,
            provider=None,
            supported_formats=[]
        )


@router.post("/analyze", response_model=AnalyzeImageResponse)
async def analyze_image(
    request: AnalyzeImageRequest,
    current_user: Optional[User] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Analyze an uploaded image.

    Args:
        request: AnalyzeImageRequest with base64 image and optional prompt

    Returns:
        AnalyzeImageResponse with analysis results
    """
    try:
        vision = get_vision()

        # Decode image
        image_bytes = base64_to_image(request.image_base64)

        # Resize if needed
        image_bytes = resize_image_for_upload(image_bytes)

        # Determine analysis type
        try:
            analysis_type = AnalysisType(request.analysis_type)
        except ValueError:
            analysis_type = AnalysisType.GENERAL

        # Analyze
        result = await vision.analyze_image(
            image_bytes,
            prompt=request.prompt,
            analysis_type=analysis_type
        )

        return AnalyzeImageResponse(
            description=result.description,
            objects=result.objects,
            text_content=result.text_content,
            analysis_type=result.analysis_type.value,
            processing_time_ms=result.processing_time_ms
        )

    except Exception as e:
        print(f"[Vision API] Analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/upload")
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    analysis_type: str = Form("general"),
    current_user: Optional[User] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Analyze an uploaded image file.

    Accepts multipart form data with image file.
    """
    try:
        vision = get_vision()

        # Read file
        image_bytes = await file.read()

        # Validate file type
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Resize if needed
        image_bytes = resize_image_for_upload(image_bytes)

        # Determine analysis type
        try:
            a_type = AnalysisType(analysis_type)
        except ValueError:
            a_type = AnalysisType.GENERAL

        # Analyze
        result = await vision.analyze_image(
            image_bytes,
            prompt=prompt,
            analysis_type=a_type
        )

        return {
            "description": result.description,
            "objects": result.objects,
            "text_content": result.text_content,
            "analysis_type": result.analysis_type.value,
            "processing_time_ms": result.processing_time_ms,
            "filename": file.filename
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Vision API] Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/camera")
async def analyze_camera_frame(
    request: CameraCaptureRequest,
    current_user: Optional[User] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Analyze a camera capture frame.

    For real-time camera analysis from webcam or phone camera.
    """
    try:
        vision = get_vision()

        # Decode frame
        frame_bytes = base64_to_image(request.frame_base64)

        # Resize for faster processing
        frame_bytes = resize_image_for_upload(frame_bytes, max_dimension=1024)

        # Analyze
        result = await vision.analyze_camera_frame(
            frame_bytes,
            prompt=request.prompt,
            context=request.context
        )

        return {
            "description": result.description,
            "objects": result.objects,
            "processing_time_ms": result.processing_time_ms
        }

    except Exception as e:
        print(f"[Vision API] Camera error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr")
async def extract_text(
    request: AnalyzeImageRequest,
    current_user: Optional[User] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Extract text from image (OCR).

    Optimized for text extraction from documents, screenshots, etc.
    """
    try:
        vision = get_vision()

        image_bytes = base64_to_image(request.image_base64)
        image_bytes = resize_image_for_upload(image_bytes)

        result = await vision.read_text(image_bytes)

        return {
            "text": result.description,
            "processing_time_ms": result.processing_time_ms
        }

    except Exception as e:
        print(f"[Vision API] OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document")
async def analyze_document(
    request: AnalyzeImageRequest,
    current_user: Optional[User] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Analyze a document image.

    Extracts key information, summarizes content, identifies document type.
    """
    try:
        vision = get_vision()

        image_bytes = base64_to_image(request.image_base64)
        image_bytes = resize_image_for_upload(image_bytes)

        result = await vision.analyze_document(image_bytes)

        return {
            "analysis": result.description,
            "text_content": result.text_content,
            "processing_time_ms": result.processing_time_ms
        }

    except Exception as e:
        print(f"[Vision API] Document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code")
async def analyze_code_image(
    request: AnalyzeImageRequest,
    current_user: Optional[User] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Analyze code or technical diagram in image.

    For screenshots of code, architecture diagrams, etc.
    """
    try:
        vision = get_vision()

        image_bytes = base64_to_image(request.image_base64)
        image_bytes = resize_image_for_upload(image_bytes)

        result = await vision.analyze_code(image_bytes)

        return {
            "analysis": result.description,
            "processing_time_ms": result.processing_time_ms
        }

    except Exception as e:
        print(f"[Vision API] Code error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=VisionChatResponse)
async def vision_chat(
    request: VisionChatRequest,
    current_user: Optional[User] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Send a chat message with an image.

    JARVIS will analyze the image and respond to your question about it.
    """
    try:
        vision = get_vision()

        # Decode and resize image
        image_bytes = base64_to_image(request.image_base64)
        image_bytes = resize_image_for_upload(image_bytes)

        # Get JARVIS-style description
        jarvis_response = await vision.describe_for_jarvis(
            image_bytes,
            user_question=request.message
        )

        # If chat is available, enhance response
        chat = get_chat()
        if chat:
            # Process through chat for richer response
            enhanced_prompt = f"""The user shared an image and asked: "{request.message}"

Based on my visual analysis: {jarvis_response}

Respond to the user's question about the image in my characteristic JARVIS manner."""

            chat_result = await chat.handle_message(enhanced_prompt, request.context)
            final_response = chat_result.get("content", jarvis_response)
        else:
            final_response = jarvis_response

        return VisionChatResponse(
            content=final_response,
            vision_analysis={
                "raw_analysis": jarvis_response[:500] if jarvis_response else None
            },
            metadata={
                "type": "vision_chat",
                "has_image": True
            }
        )

    except Exception as e:
        print(f"[Vision API] Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_images(
    images: List[UploadFile] = File(...),
    prompt: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Compare multiple images.

    Upload 2 or more images to compare them.
    """
    if len(images) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 images to compare")

    try:
        vision = get_vision()

        # Read all images
        image_data = []
        for img in images:
            img_bytes = await img.read()
            img_bytes = resize_image_for_upload(img_bytes)
            image_data.append(img_bytes)

        # Compare
        result = await vision.compare_images(image_data, prompt)

        return {
            "comparison": result.description,
            "processing_time_ms": result.processing_time_ms
        }

    except Exception as e:
        print(f"[Vision API] Compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Exports
# =============================================================================

__all__ = ['router']
