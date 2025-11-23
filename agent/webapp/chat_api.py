"""
Chat API for Jarvis Conversational Interface

FastAPI endpoints for chat functionality.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from jarvis_chat import JarvisChat
from file_context import FileContextManager


# Initialize router
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Global instances
jarvis_chat: Optional[JarvisChat] = None
file_manager: Optional[FileContextManager] = None


def get_jarvis() -> JarvisChat:
    """Get or create Jarvis instance"""
    global jarvis_chat
    if jarvis_chat is None:
        jarvis_chat = JarvisChat(memory_enabled=True)
    return jarvis_chat


def get_file_manager() -> FileContextManager:
    """Get or create file manager instance"""
    global file_manager
    if file_manager is None:
        file_manager = FileContextManager()
    return file_manager


# Request/Response models
class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict] = None


class ChatResponse(BaseModel):
    content: str
    metadata: Dict
    conversation_id: Optional[str] = None


class SessionRequest(BaseModel):
    user_id: str = "default_user"


class FileSearchRequest(BaseModel):
    filename: str
    search_path: Optional[str] = None


# Endpoints

@router.post("/session/start")
async def start_session(request: SessionRequest):
    """Start a new chat session"""
    jarvis = get_jarvis()

    try:
        session_id = await jarvis.start_session(request.user_id)

        return {
            "success": True,
            "session_id": session_id,
            "user_id": request.user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message")
async def send_message(request: ChatMessage):
    """Send a message and get response"""
    jarvis = get_jarvis()

    try:
        response = await jarvis.handle_message(
            user_message=request.message,
            context=request.context
        )

        # Handle both Session object and dict for backward compatibility
        session_id = None
        if jarvis.current_session:
            if hasattr(jarvis.current_session, 'id'):
                session_id = jarvis.current_session.id
            elif isinstance(jarvis.current_session, dict):
                session_id = jarvis.current_session.get("id")

        return ChatResponse(
            content=response["content"],
            metadata=response.get("metadata", {}),
            conversation_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/stream")
async def stream_message(request: ChatMessage):
    """Stream message response"""
    jarvis = get_jarvis()

    async def generate():
        try:
            async for chunk in jarvis.stream_response(
                message=request.message,
                context=request.context
            ):
                # Send as Server-Sent Events format
                yield f"data: {json.dumps(chunk)}\n\n"

        except Exception as e:
            error_chunk = {
                "type": "error",
                "content": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.get("/history")
async def get_history():
    """Get conversation history"""
    jarvis = get_jarvis()

    try:
        history = jarvis.get_conversation_history()

        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file/attach")
async def attach_file(
    file_path: str,
    session_id: Optional[str] = None
):
    """Attach a file to conversation"""
    jarvis = get_jarvis()
    file_mgr = get_file_manager()

    try:
        sess_id = session_id or (jarvis.current_session["id"] if jarvis.current_session else "default")

        attached = await file_mgr.attach_file(file_path, sess_id)

        return {
            "success": True,
            "file": attached.to_dict()
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file"""
    file_mgr = get_file_manager()

    try:
        # Save to temp location
        temp_path = Path("uploads") / file.filename
        temp_path.parent.mkdir(exist_ok=True)

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        return {
            "success": True,
            "filename": file.filename,
            "path": str(temp_path),
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file/search")
async def search_files(request: FileSearchRequest):
    """Search for files"""
    file_mgr = get_file_manager()

    try:
        search_path = Path(request.search_path) if request.search_path else None
        matches = file_mgr.find_files(request.filename, search_path)

        return {
            "success": True,
            "matches": [str(m) for m in matches],
            "count": len(matches)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/list")
async def list_files(
    directory: Optional[str] = None,
    recursive: bool = False
):
    """List files in directory"""
    file_mgr = get_file_manager()

    try:
        files = file_mgr.list_files(directory, recursive)

        return {
            "success": True,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/read")
async def read_file(file_path: str):
    """Read file content"""
    file_mgr = get_file_manager()

    try:
        content = file_mgr.read_file(file_path)
        info = file_mgr.get_file_info(file_path)

        return {
            "success": True,
            "content": content,
            "info": info
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Get chat system status"""
    jarvis = get_jarvis()

    return {
        "success": True,
        "status": "operational",
        "memory_enabled": jarvis.memory_enabled,
        "has_session": jarvis.current_session is not None,
        "message_count": len(jarvis.conversation_history)
    }
