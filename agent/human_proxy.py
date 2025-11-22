"""
Human-in-the-Loop Controller for JARVIS

Provides user approval workflows, checkpoints, and WebSocket integration
for real-time human interaction with agent workflows.
"""

from typing import List, Dict, Optional, Any, Callable, Awaitable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import uuid
import re


# =============================================================================
# Enums and Data Models
# =============================================================================

class InputMode(Enum):
    """Human input requirements mode"""
    ALWAYS = "always"  # Always wait for human input
    APPROVAL_REQUIRED = "approval_required"  # Wait only at checkpoints
    NEVER = "never"  # Fully autonomous, no human input


class ApprovalStatus(Enum):
    """Status of an approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class ApprovalCheckpoint(Enum):
    """Predefined checkpoints where human approval may be required"""
    PLAN_REVIEW = "plan_review"  # After manager creates plan
    CODE_REVIEW = "code_review"  # Before writing files
    DEPLOY_APPROVAL = "deploy_approval"  # Before deployment
    COST_WARNING = "cost_warning"  # When cost exceeds threshold
    EXTERNAL_API = "external_api"  # Before calling external APIs
    DATA_ACCESS = "data_access"  # Before accessing sensitive data
    TASK_COMPLETE = "task_complete"  # Before marking task as complete
    ERROR_RECOVERY = "error_recovery"  # When error recovery is needed
    CUSTOM = "custom"  # For custom checkpoints


class NotificationChannel(Enum):
    """Channels for sending approval notifications"""
    WEBSOCKET = "websocket"
    CONSOLE = "console"
    CALLBACK = "callback"
    QUEUE = "queue"


@dataclass
class ApprovalResult:
    """Result of an approval request"""
    status: ApprovalStatus
    feedback: str = ""
    modified_content: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    responder: str = "user"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.status in [ApprovalStatus.REJECTED, ApprovalStatus.TIMEOUT]

    @property
    def is_modified(self) -> bool:
        return self.status == ApprovalStatus.MODIFIED

    @property
    def reason(self) -> str:
        """Get the reason for the decision"""
        if self.status == ApprovalStatus.TIMEOUT:
            return "Approval request timed out"
        return self.feedback

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "feedback": self.feedback,
            "modified_content": self.modified_content,
            "timestamp": self.timestamp.isoformat(),
            "responder": self.responder,
            "metadata": self.metadata
        }


@dataclass
class ApprovalRequest:
    """A request for human approval"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    checkpoint: ApprovalCheckpoint = ApprovalCheckpoint.CUSTOM
    content: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    options: List[str] = field(default_factory=lambda: ["Approve", "Reject"])
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    priority: int = 0  # Higher = more urgent
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "checkpoint": self.checkpoint.value,
            "content": self.content,
            "context": self.context,
            "options": self.options,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "priority": self.priority,
            "metadata": self.metadata
        }


@dataclass
class CheckpointConfig:
    """Configuration for approval checkpoints"""
    enabled_checkpoints: List[ApprovalCheckpoint] = field(default_factory=list)
    auto_approve_after: int = 0  # seconds, 0 = never auto-approve
    notification_channel: NotificationChannel = NotificationChannel.WEBSOCKET
    require_reason_on_reject: bool = True
    allow_modification: bool = True
    max_pending_requests: int = 10
    default_timeout: int = 300  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_checkpoint_enabled(self, checkpoint: ApprovalCheckpoint) -> bool:
        return checkpoint in self.enabled_checkpoints

    def enable_checkpoint(self, checkpoint: ApprovalCheckpoint):
        if checkpoint not in self.enabled_checkpoints:
            self.enabled_checkpoints.append(checkpoint)

    def disable_checkpoint(self, checkpoint: ApprovalCheckpoint):
        if checkpoint in self.enabled_checkpoints:
            self.enabled_checkpoints.remove(checkpoint)


# =============================================================================
# User Proxy Agent
# =============================================================================

class UserProxyAgent:
    """
    Agent that represents human user in the workflow.

    Handles human input collection, approval parsing, and timeout management.

    Usage:
        proxy = UserProxyAgent(
            input_mode="APPROVAL_REQUIRED",
            timeout_seconds=300
        )

        approval = await proxy.request_approval(
            checkpoint=ApprovalCheckpoint.PLAN_REVIEW,
            content="Review this plan...",
            options=["Approve", "Modify", "Reject"]
        )

        if approval.is_approved:
            # Proceed with execution
            pass
    """

    # Default keywords for approval detection
    DEFAULT_APPROVAL_KEYWORDS = [
        "APPROVED", "LGTM", "proceed", "yes", "ok", "okay",
        "looks good", "go ahead", "continue", "accept", "confirmed"
    ]

    DEFAULT_REJECTION_KEYWORDS = [
        "REJECTED", "stop", "redo", "no", "cancel", "abort",
        "deny", "refuse", "halt", "don't", "do not"
    ]

    DEFAULT_MODIFICATION_KEYWORDS = [
        "modify:", "change:", "update:", "revise:", "adjust:",
        "edit:", "alter:", "fix:", "correct:",
        "modify this", "change this", "update this",
        "please modify", "please change", "please update"
    ]

    def __init__(
        self,
        name: str = "user",
        input_mode: Union[str, InputMode] = InputMode.APPROVAL_REQUIRED,
        approval_keywords: Optional[List[str]] = None,
        rejection_keywords: Optional[List[str]] = None,
        modification_keywords: Optional[List[str]] = None,
        timeout_seconds: int = 300,
        default_on_timeout: str = "reject",
        input_callback: Optional[Callable[[ApprovalRequest], Awaitable[str]]] = None,
        notification_callback: Optional[Callable[[ApprovalRequest], Awaitable[None]]] = None
    ):
        """
        Initialize UserProxyAgent.

        Args:
            name: Name of the user/agent
            input_mode: When to wait for human input
            approval_keywords: Keywords that indicate approval
            rejection_keywords: Keywords that indicate rejection
            modification_keywords: Keywords that indicate modification request
            timeout_seconds: Timeout for waiting for input
            default_on_timeout: Action on timeout ("reject", "approve", "skip")
            input_callback: Async callback to get input
            notification_callback: Async callback to send notifications
        """
        self.name = name

        if isinstance(input_mode, str):
            self.input_mode = InputMode(input_mode.lower())
        else:
            self.input_mode = input_mode

        self.approval_keywords = approval_keywords or self.DEFAULT_APPROVAL_KEYWORDS
        self.rejection_keywords = rejection_keywords or self.DEFAULT_REJECTION_KEYWORDS
        self.modification_keywords = modification_keywords or self.DEFAULT_MODIFICATION_KEYWORDS

        self.timeout_seconds = timeout_seconds
        self.default_on_timeout = default_on_timeout

        self.input_callback = input_callback
        self.notification_callback = notification_callback

        # State tracking
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._completed_requests: Dict[str, ApprovalResult] = {}
        self._queued_responses: List[str] = []  # For testing

        # Statistics
        self._stats = {
            "total_requests": 0,
            "approved": 0,
            "rejected": 0,
            "modified": 0,
            "timed_out": 0
        }

    async def get_human_input(self, context: Dict[str, Any] = None) -> str:
        """
        Wait for human input via configured channel.

        Args:
            context: Context information for the input request

        Returns:
            Human input string
        """
        context = context or {}

        # Check for queued responses (testing)
        if self._queued_responses:
            return self._queued_responses.pop(0)

        # Use callback if provided
        if self.input_callback:
            request = ApprovalRequest(
                checkpoint=ApprovalCheckpoint.CUSTOM,
                content=context.get("prompt", "Please provide input"),
                context=context
            )
            return await self.input_callback(request)

        # Default: wait for console input (blocking)
        prompt = context.get("prompt", "Enter input: ")
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: input(prompt)
        )

    async def get_human_input_with_timeout(
        self,
        context: Dict[str, Any] = None,
        timeout: Optional[int] = None
    ) -> ApprovalResult:
        """
        Get human input with timeout handling.

        Args:
            context: Context for the request
            timeout: Override default timeout

        Returns:
            ApprovalResult with status and content
        """
        timeout = timeout or self.timeout_seconds

        try:
            response = await asyncio.wait_for(
                self.get_human_input(context),
                timeout=timeout
            )
            return self._parse_response(response)

        except asyncio.TimeoutError:
            self._stats["timed_out"] += 1

            if self.default_on_timeout == "approve":
                return ApprovalResult(
                    status=ApprovalStatus.APPROVED,
                    feedback="Auto-approved due to timeout"
                )
            elif self.default_on_timeout == "skip":
                return ApprovalResult(
                    status=ApprovalStatus.SKIPPED,
                    feedback="Skipped due to timeout"
                )
            else:  # reject
                return ApprovalResult(
                    status=ApprovalStatus.TIMEOUT,
                    feedback="Approval request timed out"
                )

    def check_approval(self, message: str) -> ApprovalResult:
        """
        Parse message for approval/rejection signals.

        Args:
            message: Message to parse

        Returns:
            ApprovalResult with detected status
        """
        return self._parse_response(message)

    def _parse_response(self, response: str) -> ApprovalResult:
        """Parse a response string to determine approval status"""
        response_lower = response.lower().strip()

        # Check for modification first (highest priority)
        for keyword in self.modification_keywords:
            if keyword.lower() in response_lower:
                return ApprovalResult(
                    status=ApprovalStatus.MODIFIED,
                    feedback=response,
                    modified_content=self._extract_modification(response)
                )

        # Check for rejection
        for keyword in self.rejection_keywords:
            if keyword.lower() in response_lower:
                return ApprovalResult(
                    status=ApprovalStatus.REJECTED,
                    feedback=response
                )

        # Check for approval
        for keyword in self.approval_keywords:
            if keyword.lower() in response_lower:
                return ApprovalResult(
                    status=ApprovalStatus.APPROVED,
                    feedback=response
                )

        # Default: treat as pending/unclear
        return ApprovalResult(
            status=ApprovalStatus.PENDING,
            feedback=response
        )

    def _extract_modification(self, response: str) -> str:
        """Extract the modification content from response"""
        # Try to find content after modification keywords
        for keyword in self.modification_keywords:
            pattern = rf'{keyword}[:\s]+(.+)'
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return response

    async def request_approval(
        self,
        checkpoint: ApprovalCheckpoint,
        content: str,
        options: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> ApprovalResult:
        """
        Request approval at a checkpoint.

        Args:
            checkpoint: The checkpoint type
            content: Content to be approved
            options: Available options for the user
            context: Additional context
            timeout: Override default timeout

        Returns:
            ApprovalResult with the decision
        """
        self._stats["total_requests"] += 1

        # Create request
        request = ApprovalRequest(
            checkpoint=checkpoint,
            content=content,
            context=context or {},
            options=options or ["Approve", "Reject"],
            expires_at=datetime.now() + timedelta(seconds=timeout or self.timeout_seconds)
        )

        self._pending_requests[request.id] = request

        # Send notification
        if self.notification_callback:
            await self.notification_callback(request)

        # Wait for response
        input_context = {
            "prompt": self._format_approval_prompt(request),
            "request": request.to_dict()
        }

        result = await self.get_human_input_with_timeout(
            context=input_context,
            timeout=timeout
        )

        # Update statistics
        if result.is_approved:
            self._stats["approved"] += 1
        elif result.is_rejected:
            self._stats["rejected"] += 1
        elif result.is_modified:
            self._stats["modified"] += 1

        # Move to completed
        del self._pending_requests[request.id]
        self._completed_requests[request.id] = result

        return result

    def _format_approval_prompt(self, request: ApprovalRequest) -> str:
        """Format the approval prompt for display"""
        lines = [
            f"\n{'='*60}",
            f"APPROVAL REQUIRED: {request.checkpoint.value}",
            f"{'='*60}",
            "",
            request.content,
            "",
            f"Options: {', '.join(request.options)}",
            f"{'='*60}",
            "Your response: "
        ]
        return "\n".join(lines)

    # Testing helpers
    def queue_response(self, response: str):
        """Queue a response for testing"""
        self._queued_responses.append(response)

    def queue_responses(self, responses: List[str]):
        """Queue multiple responses for testing"""
        self._queued_responses.extend(responses)

    def clear_queued_responses(self):
        """Clear all queued responses"""
        self._queued_responses.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get approval statistics"""
        return self._stats.copy()

    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            "total_requests": 0,
            "approved": 0,
            "rejected": 0,
            "modified": 0,
            "timed_out": 0
        }


# =============================================================================
# Orchestrator with Approval
# =============================================================================

class OrchestratorWithApproval:
    """
    Orchestrator that integrates human approval workflows.

    Provides approval checkpoints at various stages of task execution.

    Usage:
        orchestrator = OrchestratorWithApproval(
            user_proxy=UserProxyAgent(),
            checkpoint_config=CheckpointConfig(
                enabled_checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
            )
        )

        result = await orchestrator.run_with_approval("Build a website")
    """

    def __init__(
        self,
        user_proxy: Optional[UserProxyAgent] = None,
        checkpoint_config: Optional[CheckpointConfig] = None,
        on_checkpoint: Optional[Callable[[ApprovalCheckpoint, Dict], Awaitable[None]]] = None,
        on_approval: Optional[Callable[[ApprovalResult], Awaitable[None]]] = None
    ):
        """
        Initialize OrchestratorWithApproval.

        Args:
            user_proxy: UserProxyAgent instance
            checkpoint_config: Checkpoint configuration
            on_checkpoint: Callback when checkpoint is reached
            on_approval: Callback when approval is received
        """
        self.user_proxy = user_proxy or UserProxyAgent()
        self.checkpoint_config = checkpoint_config or CheckpointConfig()
        self.on_checkpoint = on_checkpoint
        self.on_approval = on_approval

        # State
        self._current_task: Optional[str] = None
        self._execution_log: List[Dict[str, Any]] = []
        self._checkpoint_results: Dict[str, ApprovalResult] = {}

    @property
    def checkpoints(self) -> List[ApprovalCheckpoint]:
        """Get enabled checkpoints"""
        return self.checkpoint_config.enabled_checkpoints

    async def run_with_approval(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a task with approval checkpoints.

        Args:
            task: Task description
            context: Additional context

        Returns:
            Dict with status and results
        """
        self._current_task = task
        context = context or {}

        try:
            # Phase 1: Planning
            plan = await self._planning_phase(task, context)

            if ApprovalCheckpoint.PLAN_REVIEW in self.checkpoints:
                approval = await self._checkpoint(
                    ApprovalCheckpoint.PLAN_REVIEW,
                    plan.get("summary", str(plan)),
                    ["Approve", "Modify", "Reject"]
                )

                if approval.is_rejected:
                    return {
                        "status": "cancelled",
                        "reason": approval.feedback,
                        "phase": "planning"
                    }
                elif approval.is_modified:
                    task = self._merge_modifications(task, approval.feedback)
                    plan = await self._planning_phase(task, context)

            # Phase 2: Code Generation (if applicable)
            if self._requires_code_generation(plan):
                code_result = await self._code_generation_phase(plan, context)

                if ApprovalCheckpoint.CODE_REVIEW in self.checkpoints:
                    approval = await self._checkpoint(
                        ApprovalCheckpoint.CODE_REVIEW,
                        code_result.get("preview", str(code_result)),
                        ["Approve", "Modify", "Reject"]
                    )

                    if approval.is_rejected:
                        return {
                            "status": "cancelled",
                            "reason": approval.feedback,
                            "phase": "code_review"
                        }

            # Phase 3: Execution
            execution_result = await self._execution_phase(plan, context)

            # Phase 4: Deployment (if applicable)
            if self._requires_deployment(plan):
                if ApprovalCheckpoint.DEPLOY_APPROVAL in self.checkpoints:
                    approval = await self._checkpoint(
                        ApprovalCheckpoint.DEPLOY_APPROVAL,
                        f"Ready to deploy: {plan.get('summary', task)}",
                        ["Deploy", "Cancel"]
                    )

                    if approval.is_rejected:
                        return {
                            "status": "cancelled",
                            "reason": approval.feedback,
                            "phase": "deployment"
                        }

                await self._deployment_phase(execution_result, context)

            # Phase 5: Completion
            if ApprovalCheckpoint.TASK_COMPLETE in self.checkpoints:
                await self._checkpoint(
                    ApprovalCheckpoint.TASK_COMPLETE,
                    f"Task completed: {task}",
                    ["Acknowledge"]
                )

            return {
                "status": "completed",
                "task": task,
                "result": execution_result,
                "checkpoints_passed": list(self._checkpoint_results.keys())
            }

        except Exception as e:
            if ApprovalCheckpoint.ERROR_RECOVERY in self.checkpoints:
                approval = await self._checkpoint(
                    ApprovalCheckpoint.ERROR_RECOVERY,
                    f"Error occurred: {str(e)}\n\nRetry or abort?",
                    ["Retry", "Abort"]
                )

                if approval.feedback.lower() == "retry":
                    return await self.run_with_approval(task, context)

            return {
                "status": "failed",
                "error": str(e),
                "phase": "execution"
            }

    async def _checkpoint(
        self,
        checkpoint: ApprovalCheckpoint,
        content: str,
        options: List[str]
    ) -> ApprovalResult:
        """Execute an approval checkpoint"""
        # Trigger callback if provided
        if self.on_checkpoint:
            await self.on_checkpoint(checkpoint, {"content": content})

        # Request approval
        result = await self.user_proxy.request_approval(
            checkpoint=checkpoint,
            content=content,
            options=options,
            context={"task": self._current_task}
        )

        # Store result
        self._checkpoint_results[checkpoint.value] = result

        # Trigger approval callback if provided
        if self.on_approval:
            await self.on_approval(result)

        # Log
        self._execution_log.append({
            "type": "checkpoint",
            "checkpoint": checkpoint.value,
            "status": result.status.value,
            "timestamp": datetime.now().isoformat()
        })

        return result

    async def _planning_phase(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute planning phase (override in subclass)"""
        return {
            "summary": f"Plan for: {task}",
            "steps": ["Step 1", "Step 2", "Step 3"],
            "estimated_duration": "5 minutes"
        }

    async def _code_generation_phase(
        self,
        plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute code generation phase (override in subclass)"""
        return {
            "preview": "# Generated code preview\nprint('Hello, World!')",
            "files": ["main.py"]
        }

    async def _execution_phase(
        self,
        plan: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the main execution phase (override in subclass)"""
        return {
            "output": "Execution completed successfully",
            "artifacts": []
        }

    async def _deployment_phase(
        self,
        execution_result: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute deployment phase (override in subclass)"""
        return {
            "deployed": True,
            "url": "https://example.com"
        }

    def _requires_code_generation(self, plan: Dict[str, Any]) -> bool:
        """Check if task requires code generation"""
        return plan.get("requires_code", False)

    def _requires_deployment(self, plan: Dict[str, Any]) -> bool:
        """Check if task requires deployment"""
        return plan.get("requires_deployment", False)

    def _merge_modifications(self, task: str, feedback: str) -> str:
        """Merge user modifications into task"""
        return f"{task}\n\nUser modifications: {feedback}"

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the execution log"""
        return self._execution_log.copy()

    def get_checkpoint_results(self) -> Dict[str, ApprovalResult]:
        """Get all checkpoint results"""
        return self._checkpoint_results.copy()

    def reset(self):
        """Reset orchestrator state"""
        self._current_task = None
        self._execution_log.clear()
        self._checkpoint_results.clear()


# =============================================================================
# WebSocket Integration
# =============================================================================

class ApprovalWebSocketHandler:
    """
    WebSocket handler for real-time approval requests.

    Manages WebSocket connections and message routing for the approval system.

    Usage:
        handler = ApprovalWebSocketHandler()

        # Register with your WebSocket server
        @websocket_server.on_connect
        async def on_connect(websocket):
            await handler.connect(websocket)

        # Create user proxy with WebSocket callback
        proxy = UserProxyAgent(
            input_callback=handler.request_input,
            notification_callback=handler.send_notification
        )
    """

    def __init__(self):
        """Initialize WebSocket handler"""
        self._connections: Dict[str, Any] = {}  # connection_id -> websocket
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._message_handlers: Dict[str, Callable] = {}

        # Register default handlers
        self._message_handlers["approval_response"] = self._handle_approval_response

    async def connect(self, websocket: Any, connection_id: Optional[str] = None) -> str:
        """
        Register a new WebSocket connection.

        Args:
            websocket: WebSocket connection object
            connection_id: Optional connection ID

        Returns:
            Connection ID
        """
        connection_id = connection_id or str(uuid.uuid4())
        self._connections[connection_id] = websocket

        # Send welcome message
        await self._send_to_connection(connection_id, {
            "type": "connected",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        })

        return connection_id

    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        if connection_id in self._connections:
            del self._connections[connection_id]

        # Cancel any pending responses for this connection
        for request_id, future in list(self._pending_responses.items()):
            if not future.done():
                future.set_exception(ConnectionError("WebSocket disconnected"))

    async def request_input(self, request: ApprovalRequest) -> str:
        """
        Request input via WebSocket.

        Args:
            request: Approval request

        Returns:
            User response string
        """
        # Create future for response
        future = asyncio.Future()
        self._pending_responses[request.id] = future

        # Broadcast request to all connections
        await self._broadcast({
            "type": "approval_request",
            "request": request.to_dict()
        })

        try:
            # Wait for response
            response = await future
            return response
        finally:
            # Clean up
            if request.id in self._pending_responses:
                del self._pending_responses[request.id]

    async def send_notification(self, request: ApprovalRequest):
        """
        Send notification about approval request.

        Args:
            request: Approval request
        """
        await self._broadcast({
            "type": "approval_notification",
            "request": request.to_dict()
        })

    async def handle_message(self, connection_id: str, message: Union[str, Dict]):
        """
        Handle incoming WebSocket message.

        Args:
            connection_id: Source connection ID
            message: Message content
        """
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                return

        message_type = message.get("type")
        handler = self._message_handlers.get(message_type)

        if handler:
            await handler(connection_id, message)

    async def _handle_approval_response(self, connection_id: str, message: Dict):
        """Handle approval response message"""
        request_id = message.get("request_id")
        response = message.get("response", "")

        if request_id in self._pending_responses:
            future = self._pending_responses[request_id]
            if not future.done():
                future.set_result(response)

    async def _broadcast(self, message: Dict):
        """Broadcast message to all connections"""
        message_str = json.dumps(message)

        for connection_id in list(self._connections.keys()):
            try:
                await self._send_to_connection(connection_id, message)
            except Exception:
                # Remove failed connections
                await self.disconnect(connection_id)

    async def _send_to_connection(self, connection_id: str, message: Dict):
        """Send message to specific connection"""
        websocket = self._connections.get(connection_id)
        if websocket:
            message_str = json.dumps(message)
            # Adapt to your WebSocket library's send method
            if hasattr(websocket, 'send'):
                await websocket.send(message_str)
            elif hasattr(websocket, 'send_text'):
                await websocket.send_text(message_str)
            elif hasattr(websocket, 'send_json'):
                await websocket.send_json(message)

    def register_handler(self, message_type: str, handler: Callable):
        """Register a custom message handler"""
        self._message_handlers[message_type] = handler

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self._connections)


# =============================================================================
# Convenience Functions
# =============================================================================

def create_approval_proxy(
    checkpoints: Optional[List[ApprovalCheckpoint]] = None,
    timeout_seconds: int = 300,
    default_on_timeout: str = "reject"
) -> tuple:
    """
    Create a configured approval system.

    Args:
        checkpoints: Checkpoints to enable
        timeout_seconds: Timeout for approvals
        default_on_timeout: Default action on timeout

    Returns:
        Tuple of (UserProxyAgent, CheckpointConfig)
    """
    config = CheckpointConfig(
        enabled_checkpoints=checkpoints or [ApprovalCheckpoint.PLAN_REVIEW],
        default_timeout=timeout_seconds
    )

    proxy = UserProxyAgent(
        timeout_seconds=timeout_seconds,
        default_on_timeout=default_on_timeout
    )

    return proxy, config


def create_orchestrator_with_checkpoints(
    checkpoints: List[ApprovalCheckpoint],
    **kwargs
) -> OrchestratorWithApproval:
    """
    Create an orchestrator with specified checkpoints.

    Args:
        checkpoints: List of checkpoints to enable
        **kwargs: Additional arguments for OrchestratorWithApproval

    Returns:
        Configured OrchestratorWithApproval
    """
    config = CheckpointConfig(enabled_checkpoints=checkpoints)
    proxy = UserProxyAgent(**kwargs)

    return OrchestratorWithApproval(
        user_proxy=proxy,
        checkpoint_config=config
    )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    'InputMode',
    'ApprovalStatus',
    'ApprovalCheckpoint',
    'NotificationChannel',

    # Data classes
    'ApprovalResult',
    'ApprovalRequest',
    'CheckpointConfig',

    # Main classes
    'UserProxyAgent',
    'OrchestratorWithApproval',
    'ApprovalWebSocketHandler',

    # Convenience functions
    'create_approval_proxy',
    'create_orchestrator_with_checkpoints',
]
