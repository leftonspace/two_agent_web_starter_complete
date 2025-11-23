"""
Workflow Automation Module for JARVIS

Provides intelligent workflow automation:
- Zapier/Make.com integration
- Custom automation triggers
- Multi-step task execution
- Conditional workflows
- Webhook handling
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Union
from enum import Enum
from datetime import datetime, timedelta
import json
import re
import uuid
import asyncio
from abc import ABC, abstractmethod


class TriggerType(Enum):
    """Types of automation triggers."""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    EMAIL = "email"
    CALENDAR = "calendar"
    FILE = "file"
    API = "api"
    MANUAL = "manual"
    CONDITION = "condition"


class ActionType(Enum):
    """Types of automation actions."""
    HTTP_REQUEST = "http_request"
    EMAIL_SEND = "email_send"
    CALENDAR_CREATE = "calendar_create"
    FILE_CREATE = "file_create"
    NOTIFY = "notify"
    AI_PROCESS = "ai_process"
    TRANSFORM = "transform"
    CONDITIONAL = "conditional"
    DELAY = "delay"
    LOOP = "loop"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class IntegrationType(Enum):
    """External integration types."""
    ZAPIER = "zapier"
    MAKE = "make"
    SLACK = "slack"
    GOOGLE_WORKSPACE = "google_workspace"
    MICROSOFT_365 = "microsoft_365"
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    NOTION = "notion"
    AIRTABLE = "airtable"
    CUSTOM = "custom"


@dataclass
class TriggerConfig:
    """Configuration for a workflow trigger."""
    id: str
    type: TriggerType
    name: str
    config: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    enabled: bool = True


@dataclass
class ActionConfig:
    """Configuration for a workflow action."""
    id: str
    type: ActionType
    name: str
    config: Dict[str, Any]
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_mapping: Dict[str, str] = field(default_factory=dict)
    retry_count: int = 0
    retry_delay_seconds: int = 5
    timeout_seconds: int = 30
    on_error: str = "fail"  # fail, continue, retry


@dataclass
class WorkflowStep:
    """A step in a workflow."""
    id: str
    action: ActionConfig
    next_steps: List[str] = field(default_factory=list)
    condition: Optional[str] = None  # Expression to evaluate


@dataclass
class Workflow:
    """A complete workflow definition."""
    id: str
    name: str
    description: str
    trigger: TriggerConfig
    steps: List[WorkflowStep]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Context for workflow execution."""
    execution_id: str
    workflow_id: str
    trigger_data: Dict[str, Any]
    variables: Dict[str, Any] = field(default_factory=dict)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    current_step: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    error: Optional[str] = None


@dataclass
class ExecutionLog:
    """Log entry for workflow execution."""
    timestamp: datetime
    step_id: str
    action_type: str
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int = 0


@dataclass
class IntegrationConfig:
    """Configuration for an external integration."""
    id: str
    type: IntegrationType
    name: str
    credentials: Dict[str, str]
    settings: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_sync: Optional[datetime] = None


class ActionExecutor(ABC):
    """Abstract base class for action executors."""

    @abstractmethod
    async def execute(
        self,
        config: ActionConfig,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute the action and return result."""
        pass


class HTTPRequestExecutor(ActionExecutor):
    """Executor for HTTP request actions."""

    async def execute(
        self,
        config: ActionConfig,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute HTTP request."""
        import aiohttp

        url = self._resolve_template(config.config.get("url", ""), context)
        method = config.config.get("method", "GET").upper()
        headers = config.config.get("headers", {})
        body = config.config.get("body")

        if body:
            body = self._resolve_template(json.dumps(body), context)
            body = json.loads(body)

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                json=body if body else None,
                timeout=aiohttp.ClientTimeout(total=config.timeout_seconds)
            ) as response:
                response_body = await response.text()
                try:
                    response_json = json.loads(response_body)
                except json.JSONDecodeError:
                    response_json = {"text": response_body}

                return {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "body": response_json
                }

    def _resolve_template(self, template: str, context: ExecutionContext) -> str:
        """Resolve template variables."""
        result = template

        # Replace {{variable}} patterns
        for var_name, var_value in context.variables.items():
            result = result.replace(f"{{{{{var_name}}}}}", str(var_value))

        # Replace step outputs
        for step_id, output in context.step_outputs.items():
            if isinstance(output, dict):
                for key, value in output.items():
                    result = result.replace(
                        f"{{{{steps.{step_id}.{key}}}}}",
                        str(value)
                    )

        return result


class EmailSendExecutor(ActionExecutor):
    """Executor for email send actions."""

    async def execute(
        self,
        config: ActionConfig,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute email send (simulated)."""
        to = config.config.get("to", [])
        subject = config.config.get("subject", "")
        body = config.config.get("body", "")

        # In production, integrate with actual email service
        return {
            "success": True,
            "message_id": str(uuid.uuid4()),
            "recipients": to,
            "subject": subject
        }


class AIProcessExecutor(ActionExecutor):
    """Executor for AI processing actions."""

    async def execute(
        self,
        config: ActionConfig,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute AI processing."""
        task = config.config.get("task", "")
        input_data = config.config.get("input", "")

        # Resolve templates in input
        if isinstance(input_data, str):
            for var_name, var_value in context.variables.items():
                input_data = input_data.replace(
                    f"{{{{{var_name}}}}}",
                    str(var_value)
                )

        # In production, send to JARVIS AI
        return {
            "success": True,
            "task": task,
            "result": f"AI processed: {input_data[:100]}...",
            "confidence": 0.95
        }


class TransformExecutor(ActionExecutor):
    """Executor for data transformation actions."""

    async def execute(
        self,
        config: ActionConfig,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute data transformation."""
        transform_type = config.config.get("type", "")
        input_data = config.config.get("input", {})

        if transform_type == "extract":
            # Extract fields from input
            fields = config.config.get("fields", [])
            result = {}
            for field in fields:
                if field in input_data:
                    result[field] = input_data[field]
            return result

        elif transform_type == "map":
            # Map/transform each item in list
            items = input_data if isinstance(input_data, list) else [input_data]
            mapping = config.config.get("mapping", {})
            return {
                "items": [
                    {mapping.get(k, k): v for k, v in item.items()}
                    for item in items
                ]
            }

        elif transform_type == "filter":
            # Filter items based on condition
            items = input_data if isinstance(input_data, list) else [input_data]
            condition = config.config.get("condition", {})
            field = condition.get("field", "")
            operator = condition.get("operator", "equals")
            value = condition.get("value", "")

            filtered = []
            for item in items:
                if self._evaluate_condition(item.get(field), operator, value):
                    filtered.append(item)

            return {"items": filtered}

        elif transform_type == "aggregate":
            # Aggregate items
            items = input_data if isinstance(input_data, list) else [input_data]
            operation = config.config.get("operation", "count")
            field = config.config.get("field", "")

            if operation == "count":
                return {"result": len(items)}
            elif operation == "sum":
                return {"result": sum(item.get(field, 0) for item in items)}
            elif operation == "avg":
                values = [item.get(field, 0) for item in items]
                return {"result": sum(values) / len(values) if values else 0}

        return {"input": input_data}

    def _evaluate_condition(
        self,
        value: Any,
        operator: str,
        compare_value: Any
    ) -> bool:
        """Evaluate a condition."""
        if operator == "equals":
            return value == compare_value
        elif operator == "not_equals":
            return value != compare_value
        elif operator == "contains":
            return compare_value in str(value)
        elif operator == "greater_than":
            return float(value) > float(compare_value)
        elif operator == "less_than":
            return float(value) < float(compare_value)
        return False


class ConditionalExecutor(ActionExecutor):
    """Executor for conditional branching."""

    async def execute(
        self,
        config: ActionConfig,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Evaluate condition and return branch."""
        condition = config.config.get("condition", {})
        field = condition.get("field", "")
        operator = condition.get("operator", "equals")
        value = condition.get("value", "")

        # Get field value from context
        actual_value = context.variables.get(field)

        # Evaluate
        result = self._evaluate(actual_value, operator, value)

        return {
            "result": result,
            "branch": "true" if result else "false"
        }

    def _evaluate(self, actual: Any, operator: str, expected: Any) -> bool:
        """Evaluate the condition."""
        if operator == "equals":
            return str(actual) == str(expected)
        elif operator == "not_equals":
            return str(actual) != str(expected)
        elif operator == "contains":
            return str(expected) in str(actual)
        elif operator == "is_empty":
            return not actual
        elif operator == "is_not_empty":
            return bool(actual)
        elif operator == "greater_than":
            return float(actual or 0) > float(expected)
        elif operator == "less_than":
            return float(actual or 0) < float(expected)
        return False


class DelayExecutor(ActionExecutor):
    """Executor for delay actions."""

    async def execute(
        self,
        config: ActionConfig,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute delay."""
        seconds = config.config.get("seconds", 1)
        await asyncio.sleep(seconds)
        return {"delayed_seconds": seconds}


class WorkflowEngine:
    """
    Workflow Automation Engine for JARVIS.

    Manages workflow definitions, execution, and integrations.
    """

    def __init__(self):
        """Initialize workflow engine."""
        self.workflows: Dict[str, Workflow] = {}
        self.executions: Dict[str, ExecutionContext] = {}
        self.execution_logs: Dict[str, List[ExecutionLog]] = {}
        self.integrations: Dict[str, IntegrationConfig] = {}

        # Register action executors
        self.executors: Dict[ActionType, ActionExecutor] = {
            ActionType.HTTP_REQUEST: HTTPRequestExecutor(),
            ActionType.EMAIL_SEND: EmailSendExecutor(),
            ActionType.AI_PROCESS: AIProcessExecutor(),
            ActionType.TRANSFORM: TransformExecutor(),
            ActionType.CONDITIONAL: ConditionalExecutor(),
            ActionType.DELAY: DelayExecutor(),
        }

        # Webhook handlers
        self.webhook_handlers: Dict[str, str] = {}  # path -> workflow_id

    def create_workflow(
        self,
        name: str,
        description: str,
        trigger_config: Dict[str, Any],
        steps: List[Dict[str, Any]],
        tags: Optional[List[str]] = None
    ) -> Workflow:
        """
        Create a new workflow.

        Args:
            name: Workflow name
            description: Workflow description
            trigger_config: Trigger configuration
            steps: List of step configurations
            tags: Optional tags

        Returns:
            Created Workflow
        """
        workflow_id = str(uuid.uuid4())

        # Build trigger
        trigger = TriggerConfig(
            id=f"trigger_{workflow_id}",
            type=TriggerType(trigger_config.get("type", "manual")),
            name=trigger_config.get("name", "Trigger"),
            config=trigger_config.get("config", {}),
            filters=trigger_config.get("filters")
        )

        # Build steps
        workflow_steps = []
        for i, step_config in enumerate(steps):
            action = ActionConfig(
                id=f"action_{workflow_id}_{i}",
                type=ActionType(step_config.get("type", "transform")),
                name=step_config.get("name", f"Step {i + 1}"),
                config=step_config.get("config", {}),
                input_mapping=step_config.get("input_mapping", {}),
                output_mapping=step_config.get("output_mapping", {}),
                retry_count=step_config.get("retry_count", 0),
                on_error=step_config.get("on_error", "fail")
            )

            step = WorkflowStep(
                id=f"step_{workflow_id}_{i}",
                action=action,
                next_steps=step_config.get("next_steps", []),
                condition=step_config.get("condition")
            )
            workflow_steps.append(step)

        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            trigger=trigger,
            steps=workflow_steps,
            tags=tags or []
        )

        self.workflows[workflow_id] = workflow

        # Register webhook if needed
        if trigger.type == TriggerType.WEBHOOK:
            webhook_path = trigger.config.get("path", f"/webhook/{workflow_id}")
            self.webhook_handlers[webhook_path] = workflow_id

        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        trigger_data: Dict[str, Any]
    ) -> ExecutionContext:
        """
        Execute a workflow.

        Args:
            workflow_id: ID of workflow to execute
            trigger_data: Data from the trigger

        Returns:
            ExecutionContext with results
        """
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if not workflow.enabled:
            raise ValueError(f"Workflow is disabled: {workflow_id}")

        # Create execution context
        execution_id = str(uuid.uuid4())
        context = ExecutionContext(
            execution_id=execution_id,
            workflow_id=workflow_id,
            trigger_data=trigger_data,
            variables=dict(trigger_data),
            status=WorkflowStatus.RUNNING
        )

        self.executions[execution_id] = context
        self.execution_logs[execution_id] = []

        try:
            # Execute steps
            await self._execute_steps(workflow, context)
            context.status = WorkflowStatus.COMPLETED

        except Exception as e:
            context.status = WorkflowStatus.FAILED
            context.error = str(e)

        return context

    async def _execute_steps(
        self,
        workflow: Workflow,
        context: ExecutionContext
    ):
        """Execute workflow steps."""
        # Start with first step
        current_step_ids = [workflow.steps[0].id] if workflow.steps else []

        while current_step_ids:
            next_step_ids = []

            for step_id in current_step_ids:
                step = self._get_step_by_id(workflow, step_id)
                if not step:
                    continue

                # Check condition if any
                if step.condition:
                    if not self._evaluate_condition(step.condition, context):
                        continue

                # Execute the action
                context.current_step = step_id
                start_time = datetime.now()

                try:
                    result = await self._execute_action(step.action, context)
                    context.step_outputs[step_id] = result

                    # Log success
                    self._log_step(
                        context.execution_id,
                        step_id,
                        step.action.type.value,
                        "success",
                        context.variables,
                        result,
                        duration_ms=(datetime.now() - start_time).microseconds // 1000
                    )

                    # Determine next steps
                    if step.next_steps:
                        next_step_ids.extend(step.next_steps)
                    else:
                        # Continue to next sequential step
                        step_index = workflow.steps.index(step)
                        if step_index + 1 < len(workflow.steps):
                            next_step_ids.append(workflow.steps[step_index + 1].id)

                except Exception as e:
                    # Log failure
                    self._log_step(
                        context.execution_id,
                        step_id,
                        step.action.type.value,
                        "failed",
                        context.variables,
                        error=str(e),
                        duration_ms=(datetime.now() - start_time).microseconds // 1000
                    )

                    if step.action.on_error == "fail":
                        raise
                    elif step.action.on_error == "retry" and step.action.retry_count > 0:
                        # Retry logic
                        for attempt in range(step.action.retry_count):
                            await asyncio.sleep(step.action.retry_delay_seconds)
                            try:
                                result = await self._execute_action(step.action, context)
                                context.step_outputs[step_id] = result
                                break
                            except Exception:
                                if attempt == step.action.retry_count - 1:
                                    raise

            current_step_ids = next_step_ids

    async def _execute_action(
        self,
        action: ActionConfig,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute a single action."""
        executor = self.executors.get(action.type)
        if not executor:
            raise ValueError(f"No executor for action type: {action.type}")

        # Apply input mapping
        for target, source in action.input_mapping.items():
            if source.startswith("trigger."):
                key = source.replace("trigger.", "")
                context.variables[target] = context.trigger_data.get(key)
            elif source.startswith("steps."):
                parts = source.replace("steps.", "").split(".")
                step_id = parts[0]
                key = parts[1] if len(parts) > 1 else None
                step_output = context.step_outputs.get(step_id, {})
                if key:
                    context.variables[target] = step_output.get(key)
                else:
                    context.variables[target] = step_output

        # Execute
        result = await executor.execute(action, context)

        # Apply output mapping
        for target, source in action.output_mapping.items():
            if source in result:
                context.variables[target] = result[source]

        return result

    def _get_step_by_id(
        self,
        workflow: Workflow,
        step_id: str
    ) -> Optional[WorkflowStep]:
        """Get a step by ID."""
        for step in workflow.steps:
            if step.id == step_id:
                return step
        return None

    def _evaluate_condition(
        self,
        condition: str,
        context: ExecutionContext
    ) -> bool:
        """Evaluate a condition expression."""
        # Simple expression evaluation
        # Format: "variable operator value"
        parts = condition.split()
        if len(parts) < 3:
            return True

        var_name = parts[0]
        operator = parts[1]
        value = " ".join(parts[2:])

        actual = context.variables.get(var_name)

        if operator == "==":
            return str(actual) == value
        elif operator == "!=":
            return str(actual) != value
        elif operator == ">":
            return float(actual or 0) > float(value)
        elif operator == "<":
            return float(actual or 0) < float(value)
        elif operator == "contains":
            return value in str(actual)

        return True

    def _log_step(
        self,
        execution_id: str,
        step_id: str,
        action_type: str,
        status: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        duration_ms: int = 0
    ):
        """Log step execution."""
        log = ExecutionLog(
            timestamp=datetime.now(),
            step_id=step_id,
            action_type=action_type,
            status=status,
            input_data=input_data,
            output_data=output_data,
            error=error,
            duration_ms=duration_ms
        )

        if execution_id not in self.execution_logs:
            self.execution_logs[execution_id] = []

        self.execution_logs[execution_id].append(log)

    def handle_webhook(
        self,
        path: str,
        data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Handle incoming webhook.

        Args:
            path: Webhook path
            data: Webhook payload

        Returns:
            Execution ID if workflow triggered, None otherwise
        """
        workflow_id = self.webhook_handlers.get(path)
        if not workflow_id:
            return None

        # Execute workflow asynchronously
        execution_id = str(uuid.uuid4())

        # In production, this would use asyncio.create_task
        # For now, return the execution ID
        return execution_id

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)

    def list_workflows(
        self,
        tags: Optional[List[str]] = None,
        enabled_only: bool = False
    ) -> List[Workflow]:
        """List workflows with optional filtering."""
        workflows = list(self.workflows.values())

        if enabled_only:
            workflows = [w for w in workflows if w.enabled]

        if tags:
            workflows = [
                w for w in workflows
                if any(t in w.tags for t in tags)
            ]

        return workflows

    def get_execution(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get execution context by ID."""
        return self.executions.get(execution_id)

    def get_execution_logs(
        self,
        execution_id: str
    ) -> List[ExecutionLog]:
        """Get logs for an execution."""
        return self.execution_logs.get(execution_id, [])

    def update_workflow(
        self,
        workflow_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Workflow]:
        """Update a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        if "name" in updates:
            workflow.name = updates["name"]
        if "description" in updates:
            workflow.description = updates["description"]
        if "enabled" in updates:
            workflow.enabled = updates["enabled"]
        if "tags" in updates:
            workflow.tags = updates["tags"]

        workflow.updated_at = datetime.now()
        workflow.version += 1

        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self.workflows:
            workflow = self.workflows[workflow_id]

            # Remove webhook handler
            if workflow.trigger.type == TriggerType.WEBHOOK:
                path = workflow.trigger.config.get("path", f"/webhook/{workflow_id}")
                if path in self.webhook_handlers:
                    del self.webhook_handlers[path]

            del self.workflows[workflow_id]
            return True
        return False

    # Integration management

    def add_integration(
        self,
        integration_type: IntegrationType,
        name: str,
        credentials: Dict[str, str],
        settings: Optional[Dict[str, Any]] = None
    ) -> IntegrationConfig:
        """Add an external integration."""
        integration_id = str(uuid.uuid4())

        config = IntegrationConfig(
            id=integration_id,
            type=integration_type,
            name=name,
            credentials=credentials,
            settings=settings or {}
        )

        self.integrations[integration_id] = config
        return config

    def get_integration(
        self,
        integration_id: str
    ) -> Optional[IntegrationConfig]:
        """Get an integration by ID."""
        return self.integrations.get(integration_id)

    def list_integrations(self) -> List[IntegrationConfig]:
        """List all integrations."""
        return list(self.integrations.values())

    # Pre-built workflow templates

    def create_zapier_webhook_workflow(
        self,
        name: str,
        webhook_path: str,
        target_url: str,
        transform_config: Optional[Dict[str, Any]] = None
    ) -> Workflow:
        """
        Create a Zapier-style webhook workflow.

        Receives webhook -> Transforms data -> Sends to target.
        """
        steps = []

        # Transform step if config provided
        if transform_config:
            steps.append({
                "type": "transform",
                "name": "Transform Data",
                "config": transform_config
            })

        # HTTP request step
        steps.append({
            "type": "http_request",
            "name": "Send to Target",
            "config": {
                "url": target_url,
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "body": "{{trigger_data}}"
            }
        })

        return self.create_workflow(
            name=name,
            description=f"Zapier-style webhook workflow: {webhook_path}",
            trigger_config={
                "type": "webhook",
                "name": "Webhook Trigger",
                "config": {"path": webhook_path}
            },
            steps=steps,
            tags=["zapier", "webhook"]
        )

    def create_email_automation(
        self,
        name: str,
        trigger_keywords: List[str],
        response_template: str,
        ai_process: bool = False
    ) -> Workflow:
        """
        Create an email automation workflow.

        Triggered by email -> Optional AI processing -> Send response.
        """
        steps = []

        if ai_process:
            steps.append({
                "type": "ai_process",
                "name": "AI Analysis",
                "config": {
                    "task": "analyze_email",
                    "input": "{{email_body}}"
                }
            })

        steps.append({
            "type": "email_send",
            "name": "Send Response",
            "config": {
                "to": ["{{sender_email}}"],
                "subject": "Re: {{subject}}",
                "body": response_template
            }
        })

        return self.create_workflow(
            name=name,
            description=f"Email automation for: {', '.join(trigger_keywords)}",
            trigger_config={
                "type": "email",
                "name": "Email Trigger",
                "config": {"keywords": trigger_keywords}
            },
            steps=steps,
            tags=["email", "automation"]
        )

    def create_scheduled_report(
        self,
        name: str,
        schedule: str,  # cron expression
        data_source_url: str,
        recipients: List[str]
    ) -> Workflow:
        """
        Create a scheduled report workflow.

        Schedule -> Fetch data -> Process -> Send report.
        """
        steps = [
            {
                "type": "http_request",
                "name": "Fetch Data",
                "config": {
                    "url": data_source_url,
                    "method": "GET"
                }
            },
            {
                "type": "ai_process",
                "name": "Generate Report",
                "config": {
                    "task": "generate_report",
                    "input": "{{steps.step_0.body}}"
                }
            },
            {
                "type": "email_send",
                "name": "Send Report",
                "config": {
                    "to": recipients,
                    "subject": f"{name} - {{{{date}}}}",
                    "body": "{{steps.step_1.result}}"
                }
            }
        ]

        return self.create_workflow(
            name=name,
            description=f"Scheduled report: {schedule}",
            trigger_config={
                "type": "schedule",
                "name": "Schedule Trigger",
                "config": {"cron": schedule}
            },
            steps=steps,
            tags=["report", "scheduled"]
        )
