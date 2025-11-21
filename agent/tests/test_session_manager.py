"""
PHASE 10.4: Session Manager Tests

Tests for cross-session continuity and project tracking.
"""

import asyncio
import tempfile
import time
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from memory.vector_store import VectorMemoryStore, MemoryType
from memory.session_manager import (
    SessionManager,
    Session,
    Project,
    Task,
    ProjectStatus,
    TaskStatus,
    ConversationMessage,
)


@pytest.fixture
def temp_dirs():
    """Create temporary directories."""
    with tempfile.TemporaryDirectory() as chroma_dir:
        with tempfile.TemporaryDirectory() as state_dir:
            yield {"chroma": chroma_dir, "state": state_dir}


@pytest.fixture
def vector_store(temp_dirs):
    """Create vector store instance."""
    return VectorMemoryStore(
        collection_name="test_sessions",
        persist_directory=temp_dirs["chroma"],
    )


@pytest.fixture
def session_manager(vector_store, temp_dirs):
    """Create session manager instance."""
    return SessionManager(
        vector_store=vector_store,
        user_id="test_user",
        state_dir=Path(temp_dirs["state"]),
    )


def test_session_manager_initialization(session_manager):
    """Test session manager initialization."""
    assert session_manager.user_id == "test_user"
    assert session_manager.current_session is None
    assert len(session_manager.conversation_history) == 0
    assert len(session_manager.projects) == 0
    assert len(session_manager.tasks) == 0


def test_start_session(session_manager):
    """Test starting a new session."""
    session = session_manager.start_session(metadata={"device": "laptop"})

    assert session is not None
    assert session.id is not None
    assert session.user_id == "test_user"
    assert session.started_at > 0
    assert session.metadata["device"] == "laptop"
    assert session_manager.current_session == session


def test_add_message(session_manager):
    """Test adding messages to conversation."""
    session_manager.start_session()

    session_manager.add_message("user", "Hello")
    session_manager.add_message("assistant", "Hi there!")

    assert len(session_manager.conversation_history) == 2
    assert session_manager.conversation_history[0].role == "user"
    assert session_manager.conversation_history[0].content == "Hello"
    assert session_manager.current_session.message_count == 2


def test_get_conversation_context(session_manager):
    """Test getting conversation context."""
    session_manager.start_session()

    # Add multiple messages
    for i in range(15):
        session_manager.add_message("user", f"Message {i}")

    # Get last 10 messages
    context = session_manager.get_conversation_context(max_messages=10)

    assert len(context) == 10
    assert context[0]["content"] == "Message 5"
    assert context[-1]["content"] == "Message 14"


@pytest.mark.asyncio
async def test_create_project(session_manager):
    """Test creating a project."""
    project = await session_manager.create_project(
        name="Website Redesign",
        description="Redesign company website with modern UI",
        metadata={"priority": "high"}
    )

    assert project is not None
    assert project.id is not None
    assert project.name == "Website Redesign"
    assert project.status == ProjectStatus.ACTIVE
    assert project.metadata["priority"] == "high"
    assert project.id in session_manager.projects


def test_update_project_status(session_manager):
    """Test updating project status."""
    # Create project synchronously for test
    project = Project(
        id="proj1",
        name="Test Project",
        description="Test",
        status=ProjectStatus.ACTIVE,
        created_at=time.time(),
        updated_at=time.time(),
    )
    session_manager.projects[project.id] = project

    # Update status
    success = session_manager.update_project_status("proj1", ProjectStatus.COMPLETED)

    assert success is True
    assert session_manager.projects["proj1"].status == ProjectStatus.COMPLETED
    assert session_manager.projects["proj1"].completed_at is not None


def test_update_nonexistent_project(session_manager):
    """Test updating non-existent project."""
    success = session_manager.update_project_status("nonexistent", ProjectStatus.COMPLETED)
    assert success is False


@pytest.mark.asyncio
async def test_create_task(session_manager):
    """Test creating a task."""
    task = await session_manager.create_task(
        title="Write documentation",
        description="Write API documentation for new endpoints",
        priority=1,
        metadata={"estimated_hours": 4}
    )

    assert task is not None
    assert task.id is not None
    assert task.title == "Write documentation"
    assert task.status == TaskStatus.TODO
    assert task.priority == 1
    assert task.id in session_manager.tasks


@pytest.mark.asyncio
async def test_create_task_with_project(session_manager):
    """Test creating task associated with project."""
    project = await session_manager.create_project(
        name="Test Project",
        description="Test"
    )

    task = await session_manager.create_task(
        title="Task 1",
        description="Description",
        project_id=project.id,
    )

    assert task.project_id == project.id


def test_update_task_status(session_manager):
    """Test updating task status."""
    # Create task
    task = Task(
        id="task1",
        title="Test Task",
        description="Test",
        status=TaskStatus.TODO,
        project_id=None,
        created_at=time.time(),
        updated_at=time.time(),
    )
    session_manager.tasks[task.id] = task

    # Update status
    success = session_manager.update_task_status("task1", TaskStatus.COMPLETED)

    assert success is True
    assert session_manager.tasks["task1"].status == TaskStatus.COMPLETED
    assert session_manager.tasks["task1"].completed_at is not None


def test_get_incomplete_tasks(session_manager):
    """Test getting incomplete tasks."""
    # Create tasks with different statuses
    task1 = Task(
        id="task1",
        title="Todo",
        description="",
        status=TaskStatus.TODO,
        project_id=None,
        created_at=time.time(),
        updated_at=time.time(),
        priority=1,
    )

    task2 = Task(
        id="task2",
        title="In Progress",
        description="",
        status=TaskStatus.IN_PROGRESS,
        project_id=None,
        created_at=time.time(),
        updated_at=time.time(),
        priority=0,
    )

    task3 = Task(
        id="task3",
        title="Completed",
        description="",
        status=TaskStatus.COMPLETED,
        project_id=None,
        created_at=time.time(),
        updated_at=time.time(),
    )

    session_manager.tasks = {
        task1.id: task1,
        task2.id: task2,
        task3.id: task3,
    }

    incomplete = session_manager.get_incomplete_tasks()

    assert len(incomplete) == 2
    assert incomplete[0].id == "task1"  # Higher priority first
    assert incomplete[1].id == "task2"


def test_get_incomplete_tasks_by_project(session_manager):
    """Test getting incomplete tasks filtered by project."""
    task1 = Task(
        id="task1",
        title="Task 1",
        description="",
        status=TaskStatus.TODO,
        project_id="proj1",
        created_at=time.time(),
        updated_at=time.time(),
    )

    task2 = Task(
        id="task2",
        title="Task 2",
        description="",
        status=TaskStatus.TODO,
        project_id="proj2",
        created_at=time.time(),
        updated_at=time.time(),
    )

    session_manager.tasks = {task1.id: task1, task2.id: task2}

    # Get tasks for proj1
    proj1_tasks = session_manager.get_incomplete_tasks(project_id="proj1")

    assert len(proj1_tasks) == 1
    assert proj1_tasks[0].id == "task1"


def test_get_active_projects(session_manager):
    """Test getting active projects."""
    proj1 = Project(
        id="proj1",
        name="Active 1",
        description="",
        status=ProjectStatus.ACTIVE,
        created_at=time.time(),
        updated_at=time.time(),
    )

    proj2 = Project(
        id="proj2",
        name="Completed",
        description="",
        status=ProjectStatus.COMPLETED,
        created_at=time.time(),
        updated_at=time.time(),
    )

    proj3 = Project(
        id="proj3",
        name="Active 2",
        description="",
        status=ProjectStatus.ACTIVE,
        created_at=time.time(),
        updated_at=time.time(),
    )

    session_manager.projects = {
        proj1.id: proj1,
        proj2.id: proj2,
        proj3.id: proj3,
    }

    active = session_manager.get_active_projects()

    assert len(active) == 2
    assert all(p.status == ProjectStatus.ACTIVE for p in active)


def test_set_active_project(session_manager):
    """Test setting active project for session."""
    session = session_manager.start_session()

    project = Project(
        id="proj1",
        name="Test",
        description="",
        status=ProjectStatus.ACTIVE,
        created_at=time.time(),
        updated_at=time.time(),
    )
    session_manager.projects[project.id] = project

    session_manager.set_active_project("proj1")

    assert session_manager.current_session.active_project_id == "proj1"


def test_get_session_summary(session_manager):
    """Test getting session summary."""
    session_manager.start_session()

    # Add some data
    session_manager.add_message("user", "Hello")

    project = Project(
        id="proj1",
        name="Test",
        description="",
        status=ProjectStatus.ACTIVE,
        created_at=time.time(),
        updated_at=time.time(),
    )
    session_manager.projects[project.id] = project

    task = Task(
        id="task1",
        title="Task",
        description="",
        status=TaskStatus.TODO,
        project_id=None,
        created_at=time.time(),
        updated_at=time.time(),
        priority=1,
    )
    session_manager.tasks[task.id] = task

    summary = session_manager.get_session_summary()

    assert summary["user_id"] == "test_user"
    assert summary["conversation_messages"] == 1
    assert summary["total_projects"] == 1
    assert summary["active_projects"] == 1
    assert summary["total_tasks"] == 1
    assert summary["incomplete_tasks"] == 1
    assert summary["high_priority_tasks"] == 1


def test_state_persistence(session_manager):
    """Test state saving and loading."""
    # Create project and task
    project = Project(
        id="proj1",
        name="Test Project",
        description="Test",
        status=ProjectStatus.ACTIVE,
        created_at=time.time(),
        updated_at=time.time(),
    )
    session_manager.projects[project.id] = project

    task = Task(
        id="task1",
        title="Test Task",
        description="Test",
        status=TaskStatus.TODO,
        project_id=project.id,
        created_at=time.time(),
        updated_at=time.time(),
    )
    session_manager.tasks[task.id] = task

    # Save state
    session_manager._save_state()

    # Create new manager instance (should load state)
    new_manager = SessionManager(
        vector_store=session_manager.vector_store,
        user_id="test_user",
        state_dir=session_manager.state_dir,
    )

    # Check state was loaded
    assert len(new_manager.projects) == 1
    assert len(new_manager.tasks) == 1
    assert "proj1" in new_manager.projects
    assert "task1" in new_manager.tasks


def test_conversation_message_dataclass():
    """Test ConversationMessage dataclass."""
    msg = ConversationMessage(
        role="user",
        content="Hello",
        timestamp=time.time(),
        metadata={"source": "cli"}
    )

    data = msg.to_dict()
    assert data["role"] == "user"
    assert data["content"] == "Hello"


def test_task_dataclass_serialization():
    """Test Task serialization."""
    task = Task(
        id="task1",
        title="Test",
        description="Description",
        status=TaskStatus.TODO,
        project_id="proj1",
        created_at=time.time(),
        updated_at=time.time(),
    )

    # To dict
    data = task.to_dict()
    assert data["status"] == "todo"

    # From dict
    task2 = Task.from_dict(data)
    assert task2.status == TaskStatus.TODO
    assert task2.id == task.id


def test_project_dataclass_serialization():
    """Test Project serialization."""
    project = Project(
        id="proj1",
        name="Test",
        description="Description",
        status=ProjectStatus.ACTIVE,
        created_at=time.time(),
        updated_at=time.time(),
    )

    # To dict
    data = project.to_dict()
    assert data["status"] == "active"

    # From dict
    project2 = Project.from_dict(data)
    assert project2.status == ProjectStatus.ACTIVE
    assert project2.id == project.id


def test_project_status_enum():
    """Test ProjectStatus enum."""
    assert ProjectStatus.ACTIVE.value == "active"
    assert ProjectStatus.PAUSED.value == "paused"
    assert ProjectStatus.COMPLETED.value == "completed"
    assert ProjectStatus.CANCELLED.value == "cancelled"


def test_task_status_enum():
    """Test TaskStatus enum."""
    assert TaskStatus.TODO.value == "todo"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.BLOCKED.value == "blocked"
    assert TaskStatus.COMPLETED.value == "completed"
    assert TaskStatus.CANCELLED.value == "cancelled"
