"""
AI Agents Status API

FastAPI router for monitoring AI agent status and activity.

Provides:
- GET /api/agents/status - Get all agents status
- GET /api/agents/{agent_id}/status - Get specific agent status
- GET /api/agents/activity - Get recent agent activity feed
- WebSocket /api/agents/stream - Real-time agent status updates

Usage:
    from agents_api import router as agents_router
    app.include_router(agents_router)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

import core_logging

# Import auth if available
try:
    from webapp.auth import User, require_auth
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    User = None
    def require_auth():
        return None

# Import agent messaging
try:
    from agent_messaging import AgentRole, AgentMessageBus, get_message_bus
    MESSAGING_AVAILABLE = True
except ImportError:
    MESSAGING_AVAILABLE = False
    AgentRole = None


# =============================================================================
# Agent Status Models
# =============================================================================

class AgentStatus(str, Enum):
    """Agent operational status"""
    ACTIVE = "active"           # Currently processing
    IDLE = "idle"               # Ready but not processing
    OFFLINE = "offline"         # Not available
    ERROR = "error"             # In error state
    WAITING = "waiting"         # Waiting for input/approval


class AgentType(str, Enum):
    """Types of agents in the system"""
    JARVIS = "jarvis"           # Main orchestrator/butler
    MANAGER = "manager"         # High-level planner
    SUPERVISOR = "supervisor"   # Task coordinator
    EMPLOYEE = "employee"       # Task executor
    SPECIALIST = "specialist"   # Domain expert


@dataclass
class AgentInfo:
    """Information about an agent"""
    id: str
    name: str
    type: AgentType
    status: AgentStatus
    description: str
    avatar: str                 # Emoji or icon
    color: str                  # CSS color for UI
    last_activity: Optional[datetime] = None
    current_task: Optional[str] = None
    tasks_completed: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "description": self.description,
            "avatar": self.avatar,
            "color": self.color,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "current_task": self.current_task,
            "tasks_completed": self.tasks_completed,
            "error_message": self.error_message,
            "metadata": self.metadata or {}
        }
        return result


@dataclass
class AgentActivity:
    """Activity log entry for an agent"""
    agent_id: str
    agent_name: str
    action: str
    timestamp: datetime
    details: Optional[str] = None
    status: str = "info"  # info, success, warning, error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "status": self.status
        }


# =============================================================================
# Agent Registry
# =============================================================================

class AgentRegistry:
    """
    Registry for tracking all AI agents in the system.

    Maintains status, activity history, and provides real-time updates.
    """

    # Define the standard agents in the system
    STANDARD_AGENTS = [
        AgentInfo(
            id="jarvis",
            name="JARVIS",
            type=AgentType.JARVIS,
            status=AgentStatus.ACTIVE,
            description="Chief butler and master orchestrator. Coordinates all operations with impeccable British composure.",
            avatar="🎩",
            color="#9b59b6",
            metadata={"role": "orchestrator", "tier": 0}
        ),
        AgentInfo(
            id="manager",
            name="Manager",
            type=AgentType.MANAGER,
            status=AgentStatus.IDLE,
            description="Strategic planner. Breaks down complex tasks into actionable plans.",
            avatar="👔",
            color="#3498db",
            metadata={"role": "planner", "tier": 1}
        ),
        AgentInfo(
            id="supervisor",
            name="Supervisor",
            type=AgentType.SUPERVISOR,
            status=AgentStatus.IDLE,
            description="Quality controller. Monitors execution and ensures standards.",
            avatar="🔍",
            color="#e67e22",
            metadata={"role": "qa", "tier": 2}
        ),
        AgentInfo(
            id="employee_code",
            name="Code Employee",
            type=AgentType.EMPLOYEE,
            status=AgentStatus.IDLE,
            description="Code writer. Implements features and fixes bugs.",
            avatar="💻",
            color="#2ecc71",
            metadata={"role": "coder", "tier": 3, "specialty": "code"}
        ),
        AgentInfo(
            id="employee_test",
            name="Test Employee",
            type=AgentType.EMPLOYEE,
            status=AgentStatus.IDLE,
            description="Test runner. Validates code quality and correctness.",
            avatar="🧪",
            color="#1abc9c",
            metadata={"role": "tester", "tier": 3, "specialty": "testing"}
        ),
        AgentInfo(
            id="employee_docs",
            name="Docs Employee",
            type=AgentType.EMPLOYEE,
            status=AgentStatus.IDLE,
            description="Documentation writer. Creates clear, helpful documentation.",
            avatar="📝",
            color="#f39c12",
            metadata={"role": "writer", "tier": 3, "specialty": "documentation"}
        ),
        AgentInfo(
            id="specialist_security",
            name="Security Specialist",
            type=AgentType.SPECIALIST,
            status=AgentStatus.OFFLINE,
            description="Security expert. Reviews code for vulnerabilities.",
            avatar="🛡️",
            color="#e74c3c",
            metadata={"role": "security", "tier": 2, "specialty": "security"}
        ),
        AgentInfo(
            id="specialist_performance",
            name="Performance Specialist",
            type=AgentType.SPECIALIST,
            status=AgentStatus.OFFLINE,
            description="Performance optimizer. Identifies and fixes bottlenecks.",
            avatar="⚡",
            color="#9b59b6",
            metadata={"role": "performance", "tier": 2, "specialty": "performance"}
        ),
    ]

    def __init__(self):
        # Initialize agents dictionary
        self.agents: Dict[str, AgentInfo] = {}
        for agent in self.STANDARD_AGENTS:
            self.agents[agent.id] = agent

        # Activity log
        self.activity_log: List[AgentActivity] = []
        self.max_activity_log = 100

        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []

        # Initialize JARVIS as active
        self.agents["jarvis"].status = AgentStatus.ACTIVE
        self.agents["jarvis"].last_activity = datetime.now()

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def get_all_agents(self) -> List[AgentInfo]:
        """Get all registered agents"""
        return list(self.agents.values())

    def get_agents_by_status(self, status: AgentStatus) -> List[AgentInfo]:
        """Get agents with a specific status"""
        return [a for a in self.agents.values() if a.status == status]

    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentInfo]:
        """Get agents of a specific type"""
        return [a for a in self.agents.values() if a.type == agent_type]

    def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
        current_task: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Update agent status"""
        agent = self.agents.get(agent_id)
        if agent:
            old_status = agent.status
            agent.status = status
            agent.last_activity = datetime.now()

            if current_task is not None:
                agent.current_task = current_task
            if error_message is not None:
                agent.error_message = error_message

            # Log activity
            self._log_activity(
                agent_id,
                agent.name,
                f"Status changed: {old_status.value} → {status.value}",
                current_task,
                "info" if status != AgentStatus.ERROR else "error"
            )

            # Broadcast update
            asyncio.create_task(self._broadcast_update(agent))

    def mark_task_completed(self, agent_id: str, task_description: str):
        """Mark a task as completed for an agent"""
        agent = self.agents.get(agent_id)
        if agent:
            agent.tasks_completed += 1
            agent.current_task = None
            agent.last_activity = datetime.now()

            self._log_activity(
                agent_id,
                agent.name,
                "Task completed",
                task_description,
                "success"
            )

            asyncio.create_task(self._broadcast_update(agent))

    def _log_activity(
        self,
        agent_id: str,
        agent_name: str,
        action: str,
        details: Optional[str] = None,
        status: str = "info"
    ):
        """Log agent activity"""
        activity = AgentActivity(
            agent_id=agent_id,
            agent_name=agent_name,
            action=action,
            timestamp=datetime.now(),
            details=details,
            status=status
        )

        self.activity_log.insert(0, activity)

        # Trim log if needed
        if len(self.activity_log) > self.max_activity_log:
            self.activity_log = self.activity_log[:self.max_activity_log]

    def get_activity_log(self, limit: int = 20) -> List[AgentActivity]:
        """Get recent activity log"""
        return self.activity_log[:limit]

    async def _broadcast_update(self, agent: AgentInfo):
        """Broadcast agent update to all WebSocket connections"""
        message = {
            "type": "agent_update",
            "agent": agent.to_dict()
        }

        disconnected = []
        for ws in self.websocket_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections.remove(ws)

    def add_websocket(self, ws: WebSocket):
        """Add WebSocket connection"""
        self.websocket_connections.append(ws)

    def remove_websocket(self, ws: WebSocket):
        """Remove WebSocket connection"""
        if ws in self.websocket_connections:
            self.websocket_connections.remove(ws)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        agents = list(self.agents.values())

        return {
            "total_agents": len(agents),
            "active": len([a for a in agents if a.status == AgentStatus.ACTIVE]),
            "idle": len([a for a in agents if a.status == AgentStatus.IDLE]),
            "offline": len([a for a in agents if a.status == AgentStatus.OFFLINE]),
            "error": len([a for a in agents if a.status == AgentStatus.ERROR]),
            "waiting": len([a for a in agents if a.status == AgentStatus.WAITING]),
            "total_tasks_completed": sum(a.tasks_completed for a in agents)
        }


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get or create the global agent registry"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


# =============================================================================
# API Models
# =============================================================================

class AgentStatusResponse(BaseModel):
    """Response model for agent status"""
    id: str
    name: str
    type: str
    status: str
    description: str
    avatar: str
    color: str
    last_activity: Optional[str]
    current_task: Optional[str]
    tasks_completed: int


class AgentsSummaryResponse(BaseModel):
    """Summary of all agents"""
    total_agents: int
    active: int
    idle: int
    offline: int
    error: int
    waiting: int
    total_tasks_completed: int


class UpdateAgentStatusRequest(BaseModel):
    """Request to update agent status"""
    status: str
    current_task: Optional[str] = None
    error_message: Optional[str] = None


# =============================================================================
# Router Setup
# =============================================================================

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/status")
async def get_all_agents_status(
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """
    Get status of all AI agents.

    Returns list of all agents with their current status.
    """
    registry = get_agent_registry()
    agents = registry.get_all_agents()

    return {
        "agents": [agent.to_dict() for agent in agents],
        "summary": registry.get_summary()
    }


@router.get("/summary")
async def get_agents_summary(
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Get summary statistics of agent status"""
    registry = get_agent_registry()
    return registry.get_summary()


@router.get("/{agent_id}/status")
async def get_agent_status(
    agent_id: str,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Get status of a specific agent"""
    registry = get_agent_registry()
    agent = registry.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    return agent.to_dict()


@router.post("/{agent_id}/status")
async def update_agent_status(
    agent_id: str,
    request: UpdateAgentStatusRequest,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Update status of an agent (for internal use)"""
    registry = get_agent_registry()
    agent = registry.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")

    try:
        status = AgentStatus(request.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")

    registry.update_agent_status(
        agent_id,
        status,
        current_task=request.current_task,
        error_message=request.error_message
    )

    return {"status": "updated", "agent": registry.get_agent(agent_id).to_dict()}


@router.get("/activity")
async def get_agent_activity(
    limit: int = 20,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Get recent agent activity log"""
    registry = get_agent_registry()
    activities = registry.get_activity_log(limit)

    return {
        "activities": [a.to_dict() for a in activities]
    }


@router.get("/by-type/{agent_type}")
async def get_agents_by_type(
    agent_type: str,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Get all agents of a specific type"""
    registry = get_agent_registry()

    try:
        type_enum = AgentType(agent_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid agent type: {agent_type}")

    agents = registry.get_agents_by_type(type_enum)
    return {"agents": [a.to_dict() for a in agents]}


@router.get("/by-status/{status}")
async def get_agents_by_status(
    status: str,
    current_user: User = Depends(require_auth) if AUTH_AVAILABLE else None
):
    """Get all agents with a specific status"""
    registry = get_agent_registry()

    try:
        status_enum = AgentStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    agents = registry.get_agents_by_status(status_enum)
    return {"agents": [a.to_dict() for a in agents]}


# =============================================================================
# WebSocket for Real-time Updates
# =============================================================================

@router.websocket("/stream")
async def agents_websocket(websocket: WebSocket):
    """
    WebSocket for real-time agent status updates.

    Clients receive updates whenever an agent's status changes.
    """
    await websocket.accept()
    registry = get_agent_registry()
    registry.add_websocket(websocket)

    try:
        # Send initial status
        agents = registry.get_all_agents()
        await websocket.send_json({
            "type": "initial",
            "agents": [a.to_dict() for a in agents],
            "summary": registry.get_summary()
        })

        # Keep connection alive and handle messages
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0
                )

                # Handle ping
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        pass
    finally:
        registry.remove_websocket(websocket)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    'router',
    'AgentRegistry',
    'AgentInfo',
    'AgentStatus',
    'AgentType',
    'get_agent_registry',
]
