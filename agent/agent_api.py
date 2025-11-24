"""
JARVIS Agent API

WebSocket and REST API for the JARVIS Agent.
Provides real-time streaming of agent thoughts, tool calls, and responses.
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel

# Import agent
try:
    from jarvis_agent import JarvisAgent, AgentEvent, EventType, get_agent
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"[AgentAPI] Agent import failed: {e}")
    AGENT_AVAILABLE = False
    get_agent = None

# Import auth (optional)
try:
    from auth import get_current_user
except ImportError:
    async def get_current_user():
        return None


router = APIRouter(prefix="/api/agent", tags=["agent"])


# ═══════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════

class AgentRequest(BaseModel):
    """Request to run the agent"""
    message: str
    context: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Dict]] = None


class AgentResponse(BaseModel):
    """Response from the agent"""
    task_id: str
    status: str
    response: Optional[str] = None
    events: List[Dict] = []


class CancelRequest(BaseModel):
    """Request to cancel a task"""
    task_id: str


# ═══════════════════════════════════════════════════════════════════════════
# WebSocket Connection Manager
# ═══════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_tasks: Dict[str, str] = {}  # user_id -> task_id

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"[AgentAPI] Client connected: {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.user_tasks:
            del self.user_tasks[client_id]
        print(f"[AgentAPI] Client disconnected: {client_id}")

    async def send_event(self, client_id: str, event: Dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(event)
            except Exception as e:
                print(f"[AgentAPI] Send error: {e}")
                self.disconnect(client_id)

    async def broadcast(self, event: Dict):
        disconnected = []
        for client_id, ws in self.active_connections.items():
            try:
                await ws.send_json(event)
            except Exception:
                disconnected.append(client_id)
        for client_id in disconnected:
            self.disconnect(client_id)


manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════════════════════
# WebSocket Endpoint - Real-time Agent Streaming
# ═══════════════════════════════════════════════════════════════════════════

@router.websocket("/ws/{client_id}")
async def agent_websocket(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time agent interaction.

    The client can send messages and receive events in real-time.

    Client -> Server messages:
    - {"type": "run", "message": "...", "context": {...}}
    - {"type": "cancel"}
    - {"type": "interrupt", "message": "..."}  # Add input during execution

    Server -> Client events:
    - {"type": "thinking", "content": "..."}
    - {"type": "tool_call", "content": "...", "metadata": {...}}
    - {"type": "tool_result", "content": "...", "metadata": {...}}
    - {"type": "response", "content": "..."}
    - {"type": "error", "content": "..."}
    - {"type": "complete", "content": "..."}
    """
    if not AGENT_AVAILABLE:
        await websocket.close(code=1011, reason="Agent not available")
        return

    await manager.connect(websocket, client_id)
    agent = get_agent()
    current_task_id = None

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "run":
                # Run the agent
                message = data.get("message", "")
                context = data.get("context", {})
                history = data.get("conversation_history", [])

                if not message:
                    await manager.send_event(client_id, {
                        "type": "error",
                        "content": "No message provided"
                    })
                    continue

                # Run agent and stream events
                async for event in agent.run(message, context, history):
                    # Track task ID
                    if event.metadata.get("task_id"):
                        current_task_id = event.metadata["task_id"]
                        manager.user_tasks[client_id] = current_task_id

                    # Send event to client
                    await manager.send_event(client_id, event.to_dict())

                    # Small delay to prevent overwhelming the client
                    await asyncio.sleep(0.01)

                current_task_id = None

            elif msg_type == "cancel":
                # Cancel current task
                task_id = data.get("task_id") or current_task_id
                if task_id:
                    cancelled = agent.cancel_task(task_id)
                    await manager.send_event(client_id, {
                        "type": "status",
                        "content": f"Cancel requested for task {task_id}",
                        "metadata": {"cancelled": cancelled}
                    })
                else:
                    await manager.send_event(client_id, {
                        "type": "error",
                        "content": "No task to cancel"
                    })

            elif msg_type == "interrupt":
                # Interrupt with additional input (for future implementation)
                interrupt_message = data.get("message", "")
                await manager.send_event(client_id, {
                    "type": "status",
                    "content": f"Interrupt received: {interrupt_message[:100]}",
                    "metadata": {"interrupt": True}
                })
                # TODO: Implement interrupt handling in agent loop

            elif msg_type == "ping":
                # Keep-alive
                await manager.send_event(client_id, {
                    "type": "pong",
                    "content": "pong",
                    "timestamp": time.time()
                })

            else:
                await manager.send_event(client_id, {
                    "type": "error",
                    "content": f"Unknown message type: {msg_type}"
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        # Cancel any running task
        if current_task_id:
            agent.cancel_task(current_task_id)
    except Exception as e:
        print(f"[AgentAPI] WebSocket error: {e}")
        manager.disconnect(client_id)


# ═══════════════════════════════════════════════════════════════════════════
# REST Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/run", response_model=AgentResponse)
async def run_agent_sync(request: AgentRequest):
    """
    Run the agent synchronously and return all events.

    This is a simpler alternative to WebSocket for clients that don't
    need real-time streaming.
    """
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent not available")

    agent = get_agent()
    events = []
    final_response = None
    task_id = None

    async for event in agent.run(
        request.message,
        request.context,
        request.conversation_history
    ):
        events.append(event.to_dict())

        if event.metadata.get("task_id"):
            task_id = event.metadata["task_id"]

        if event.type == EventType.RESPONSE:
            final_response = event.content

    return AgentResponse(
        task_id=task_id or "unknown",
        status="completed",
        response=final_response,
        events=events
    )


@router.post("/cancel")
async def cancel_task(request: CancelRequest):
    """Cancel a running task"""
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent not available")

    agent = get_agent()
    cancelled = agent.cancel_task(request.task_id)

    return {
        "task_id": request.task_id,
        "cancelled": cancelled
    }


@router.get("/tasks")
async def get_active_tasks():
    """Get list of active tasks"""
    if not AGENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agent not available")

    agent = get_agent()
    return {
        "tasks": agent.get_active_tasks()
    }


@router.get("/status")
async def get_agent_status():
    """Get agent status"""
    return {
        "available": AGENT_AVAILABLE,
        "tools_available": AGENT_AVAILABLE,
        "active_connections": len(manager.active_connections),
        "timestamp": time.time()
    }
