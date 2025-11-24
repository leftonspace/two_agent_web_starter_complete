"""
PHASE 10.4: Cross-session Continuity

Resume conversations across sessions, track ongoing projects,
and remember incomplete tasks.

Features:
- Save and restore conversation state
- Track ongoing projects and their status
- Incomplete task reminders
- Session history and analytics
- Automatic state persistence
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .vector_store import VectorMemoryStore, MemoryType
except ImportError:
    from vector_store import VectorMemoryStore, MemoryType


class ProjectStatus(Enum):
    """Status of tracked projects."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Status of tracked tasks."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class ConversationMessage:
    """Single message in conversation history."""
    role: str  # user, assistant, system
    content: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Task:
    """Tracked task."""
    id: str
    title: str
    description: str
    status: TaskStatus
    project_id: Optional[str]
    created_at: float
    updated_at: float
    completed_at: Optional[float] = None
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Task:
        """Create from dictionary."""
        data = data.copy()
        data["status"] = TaskStatus(data["status"])
        return cls(**data)


@dataclass
class Project:
    """Tracked project."""
    id: str
    name: str
    description: str
    status: ProjectStatus
    created_at: float
    updated_at: float
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Project:
        """Create from dictionary."""
        data = data.copy()
        data["status"] = ProjectStatus(data["status"])
        return cls(**data)


@dataclass
class Session:
    """User session state."""
    id: str
    user_id: str
    started_at: float
    last_activity: float
    message_count: int = 0
    active_project_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SessionManager:
    """
    Manage cross-session continuity.

    Tracks conversations, projects, and tasks across sessions.
    Enables resuming from last interaction.
    """

    def __init__(
        self,
        vector_store: VectorMemoryStore,
        user_id: str,
        state_dir: Optional[Path] = None,
    ):
        """
        Initialize session manager.

        Args:
            vector_store: Vector store for long-term memory
            user_id: User identifier
            state_dir: Directory for session state (default: ./session_state)
        """
        self.vector_store = vector_store
        self.user_id = user_id

        # State directory
        if state_dir is None:
            state_dir = Path(__file__).parent.parent / "session_state"
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Current session
        self.current_session: Optional[Session] = None

        # Conversation history (in-memory)
        self.conversation_history: List[ConversationMessage] = []

        # Projects and tasks
        self.projects: Dict[str, Project] = {}
        self.tasks: Dict[str, Task] = {}

        # Load previous state
        self._load_state()

    def _load_state(self):
        """Load state from disk."""
        state_file = self.state_dir / f"{self.user_id}_state.json"

        if state_file.exists():
            try:
                with open(state_file, "r") as f:
                    data = json.load(f)

                # Load projects
                for proj_data in data.get("projects", []):
                    project = Project.from_dict(proj_data)
                    self.projects[project.id] = project

                # Load tasks
                for task_data in data.get("tasks", []):
                    task = Task.from_dict(task_data)
                    self.tasks[task.id] = task

                print(f"[SessionManager] Loaded state: {len(self.projects)} projects, {len(self.tasks)} tasks")

            except Exception as e:
                print(f"[SessionManager] Error loading state: {e}")

    def _save_state(self):
        """Save state to disk."""
        state_file = self.state_dir / f"{self.user_id}_state.json"

        try:
            data = {
                "projects": [p.to_dict() for p in self.projects.values()],
                "tasks": [t.to_dict() for t in self.tasks.values()],
                "saved_at": time.time(),
            }

            with open(state_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"[SessionManager] Error saving state: {e}")

    def start_session(self, metadata: Optional[Dict[str, Any]] = None) -> Session:
        """
        Start a new session.

        Args:
            metadata: Optional session metadata

        Returns:
            Session object
        """
        # Clear conversation history for the new session
        # This ensures each chat is isolated from previous chats
        # Note: Projects and tasks are preserved across sessions
        self.conversation_history = []

        session = Session(
            id=str(uuid.uuid4()),
            user_id=self.user_id,
            started_at=time.time(),
            last_activity=time.time(),
            metadata=metadata or {},
        )

        self.current_session = session
        print(f"[SessionManager] Started session {session.id} (conversation history cleared)")

        return session

    def end_session(self):
        """End current session and save state."""
        if self.current_session:
            # Save conversation to vector store
            asyncio.create_task(self._save_conversation())

            # Save state to disk
            self._save_state()

            print(f"[SessionManager] Ended session {self.current_session.id}")
            self.current_session = None

    async def _save_conversation(self):
        """Save conversation history to vector store."""
        if not self.conversation_history:
            return

        # Create summary of conversation
        summary = self._summarize_conversation()

        # Store in vector database
        await self.vector_store.store_memory(
            content=summary,
            memory_type=MemoryType.MEETING_SUMMARY,  # Treat as meeting summary
            metadata={
                "user": self.user_id,
                "session_id": self.current_session.id if self.current_session else None,
                "message_count": len(self.conversation_history),
                "timestamp": time.time(),
            }
        )

    def _summarize_conversation(self) -> str:
        """Create summary of conversation."""
        if not self.conversation_history:
            return ""

        # Simple summary: first and last few messages
        summary_parts = ["Conversation summary:"]

        # First message
        if len(self.conversation_history) > 0:
            first = self.conversation_history[0]
            summary_parts.append(f"Started with: {first.content[:100]}")

        # Last few messages
        for msg in self.conversation_history[-3:]:
            snippet = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"{msg.role}: {snippet}")

        return "\n".join(summary_parts)

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Add message to conversation history.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=time.time(),
            metadata=metadata or {},
        )

        self.conversation_history.append(message)

        # Update session
        if self.current_session:
            self.current_session.last_activity = time.time()
            self.current_session.message_count += 1

    def get_conversation_context(self, max_messages: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation context.

        Args:
            max_messages: Maximum messages to return

        Returns:
            List of message dicts
        """
        recent = self.conversation_history[-max_messages:]
        return [msg.to_dict() for msg in recent]

    async def create_project(
        self,
        name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Project:
        """
        Create new project.

        Args:
            name: Project name
            description: Project description
            metadata: Optional metadata

        Returns:
            Project object
        """
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            status=ProjectStatus.ACTIVE,
            created_at=time.time(),
            updated_at=time.time(),
            metadata=metadata or {},
        )

        self.projects[project.id] = project

        # Store in vector database
        await self.vector_store.store_memory(
            content=f"Project: {name}\n{description}",
            memory_type=MemoryType.NOTE,
            metadata={
                "user": self.user_id,
                "project_id": project.id,
                "project_name": name,
                "type": "project",
            }
        )

        self._save_state()
        print(f"[SessionManager] Created project: {name}")

        return project

    def update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
    ) -> bool:
        """
        Update project status.

        Args:
            project_id: Project ID
            status: New status

        Returns:
            True if successful
        """
        if project_id not in self.projects:
            return False

        project = self.projects[project_id]
        project.status = status
        project.updated_at = time.time()

        if status == ProjectStatus.COMPLETED:
            project.completed_at = time.time()

        self._save_state()
        return True

    async def create_task(
        self,
        title: str,
        description: str,
        project_id: Optional[str] = None,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Create new task.

        Args:
            title: Task title
            description: Task description
            project_id: Associated project ID
            priority: Priority level (0=normal, 1=high, 2=urgent)
            metadata: Optional metadata

        Returns:
            Task object
        """
        task = Task(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            status=TaskStatus.TODO,
            project_id=project_id,
            created_at=time.time(),
            updated_at=time.time(),
            priority=priority,
            metadata=metadata or {},
        )

        self.tasks[task.id] = task

        # Store as action item
        await self.vector_store.store_memory(
            content=f"{title}: {description}",
            memory_type=MemoryType.ACTION_ITEM,
            metadata={
                "user": self.user_id,
                "task_id": task.id,
                "project_id": project_id,
                "priority": priority,
            }
        )

        self._save_state()
        print(f"[SessionManager] Created task: {title}")

        return task

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
    ) -> bool:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status

        Returns:
            True if successful
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]
        task.status = status
        task.updated_at = time.time()

        if status == TaskStatus.COMPLETED:
            task.completed_at = time.time()

        self._save_state()
        return True

    def get_incomplete_tasks(
        self,
        project_id: Optional[str] = None,
    ) -> List[Task]:
        """
        Get incomplete tasks.

        Args:
            project_id: Filter by project

        Returns:
            List of incomplete tasks
        """
        incomplete_statuses = {TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED}

        tasks = [
            task for task in self.tasks.values()
            if task.status in incomplete_statuses
        ]

        # Filter by project
        if project_id:
            tasks = [t for t in tasks if t.project_id == project_id]

        # Sort by priority (descending) then created_at
        tasks.sort(key=lambda t: (-t.priority, t.created_at))

        return tasks

    def get_active_projects(self) -> List[Project]:
        """Get active projects."""
        return [
            p for p in self.projects.values()
            if p.status == ProjectStatus.ACTIVE
        ]

    def set_active_project(self, project_id: str):
        """Set active project for current session."""
        if self.current_session and project_id in self.projects:
            self.current_session.active_project_id = project_id

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session state."""
        incomplete_tasks = self.get_incomplete_tasks()
        active_projects = self.get_active_projects()

        return {
            "user_id": self.user_id,
            "current_session": self.current_session.to_dict() if self.current_session else None,
            "conversation_messages": len(self.conversation_history),
            "total_projects": len(self.projects),
            "active_projects": len(active_projects),
            "total_tasks": len(self.tasks),
            "incomplete_tasks": len(incomplete_tasks),
            "high_priority_tasks": len([t for t in incomplete_tasks if t.priority >= 1]),
        }
