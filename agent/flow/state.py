"""
Flow State Management

State management for flow execution including context, step results,
and typed state containers.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List, Generic, TypeVar
from datetime import datetime
import json
from enum import Enum

StateT = TypeVar('StateT', bound=BaseModel)


class FlowStatus(str, Enum):
    """Flow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(str, Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepResult(BaseModel):
    """Result of a single step execution"""
    step_name: str
    status: StepStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    output: Any = None
    error: Optional[str] = None
    retries: int = 0
    duration_seconds: Optional[float] = None

    class Config:
        arbitrary_types_allowed = True

    def calculate_duration(self):
        """Calculate step duration"""
        if self.completed_at and self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()

    def is_successful(self) -> bool:
        """Check if step completed successfully"""
        return self.status == StepStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if step failed"""
        return self.status == StepStatus.FAILED


class FlowContext(BaseModel):
    """Runtime context for flow execution"""
    flow_id: str = Field(default_factory=lambda: f"flow_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    status: FlowStatus = FlowStatus.PENDING
    current_step: Optional[str] = None
    completed_steps: List[str] = Field(default_factory=list)
    step_results: Dict[str, StepResult] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True

    def start(self):
        """Mark flow as started"""
        self.status = FlowStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, success: bool = True):
        """Mark flow as completed"""
        self.status = FlowStatus.COMPLETED if success else FlowStatus.FAILED
        self.completed_at = datetime.now()

    def fail(self, error: str):
        """Mark flow as failed"""
        self.status = FlowStatus.FAILED
        self.error = error
        self.completed_at = datetime.now()

    def pause(self):
        """Mark flow as paused"""
        self.status = FlowStatus.PAUSED

    def resume(self):
        """Resume paused flow"""
        if self.status == FlowStatus.PAUSED:
            self.status = FlowStatus.RUNNING

    def cancel(self):
        """Cancel flow execution"""
        self.status = FlowStatus.CANCELLED
        self.completed_at = datetime.now()

    def add_step_result(self, result: StepResult):
        """Add a step result"""
        self.step_results[result.step_name] = result
        if result.status == StepStatus.COMPLETED:
            if result.step_name not in self.completed_steps:
                self.completed_steps.append(result.step_name)

    def get_step_output(self, step_name: str) -> Any:
        """Get output from a completed step"""
        if step_name in self.step_results:
            return self.step_results[step_name].output
        return None

    def is_step_completed(self, step_name: str) -> bool:
        """Check if a step is completed"""
        return step_name in self.completed_steps

    def get_duration(self) -> Optional[float]:
        """Get total flow duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def set_variable(self, key: str, value: Any):
        """Set a context variable"""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a context variable"""
        return self.variables.get(key, default)

    def is_running(self) -> bool:
        """Check if flow is currently running"""
        return self.status == FlowStatus.RUNNING

    def is_finished(self) -> bool:
        """Check if flow has finished (completed, failed, or cancelled)"""
        return self.status in [FlowStatus.COMPLETED, FlowStatus.FAILED, FlowStatus.CANCELLED]


class FlowState(BaseModel, Generic[StateT]):
    """Typed flow state container"""
    data: Any  # Will hold StateT
    context: FlowContext = Field(default_factory=FlowContext)
    history: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def update(self, **kwargs):
        """Update state data"""
        for key, value in kwargs.items():
            if hasattr(self.data, key):
                setattr(self.data, key, value)

        # Record in history
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "updates": kwargs
        })

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from state data"""
        if hasattr(self.data, key):
            return getattr(self.data, key)
        return default

    def checkpoint(self) -> Dict[str, Any]:
        """Create a checkpoint of current state"""
        data_dict = self.data.dict() if hasattr(self.data, 'dict') else {}
        return {
            "data": data_dict,
            "context": self.context.dict(),
            "history_length": len(self.history)
        }

    def restore(self, checkpoint: Dict[str, Any], state_class: type = None):
        """Restore from checkpoint"""
        if state_class and checkpoint.get("data"):
            self.data = state_class(**checkpoint["data"])
        self.context = FlowContext(**checkpoint["context"])

    def to_json(self) -> str:
        """Serialize state to JSON"""
        return json.dumps(self.checkpoint(), default=str)

    @classmethod
    def from_json(cls, json_str: str, state_class: type) -> 'FlowState':
        """Deserialize state from JSON"""
        data = json.loads(json_str)
        state_data = state_class(**data["data"]) if state_class else None
        context = FlowContext(**data["context"])
        return cls(data=state_data, context=context)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current state"""
        return {
            "flow_id": self.context.flow_id,
            "status": self.context.status.value,
            "current_step": self.context.current_step,
            "completed_steps": len(self.context.completed_steps),
            "total_steps": len(self.context.step_results),
            "duration": self.context.get_duration(),
            "error": self.context.error
        }
