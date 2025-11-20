"""
Approval Workflow Engine - DAG-based approval system with human-in-the-loop pauses

This module implements a flexible approval workflow engine that supports:
- Multi-step approval chains
- Conditional branching based on request data
- Parallel approval requirements
- Timeouts and escalations
- Integration with the orchestrator for pause/resume

Author: AI Agent System
Created: Phase 3.1 - Approval Workflows
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class ApprovalStatus(Enum):
    """Status of an approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class DecisionType(Enum):
    """Type of approval decision"""
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"
    REQUEST_INFO = "request_info"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ApprovalStep:
    """
    Represents a single step in an approval workflow.

    Supports:
    - Conditional execution based on payload data
    - Parallel execution with other steps
    - Timeouts and escalations
    - Role-based or user-specific approval
    """
    step_id: str
    approver_role: str
    approver_user_id: Optional[str] = None
    condition: Optional[str] = None  # Python expression, e.g., "payload['amount'] > 10000"
    timeout_hours: int = 24
    escalation_role: Optional[str] = None
    parallel: bool = False  # Can run in parallel with other steps
    required_count: int = 1  # For parallel approvals, how many approvals needed
    step_name: Optional[str] = None  # Human-readable name
    description: Optional[str] = None  # Help text for approvers

    def __post_init__(self):
        if not self.step_name:
            self.step_name = f"{self.approver_role} approval"


@dataclass
class ApprovalWorkflow:
    """
    Defines a complete approval workflow as a DAG.

    The workflow consists of sequential and/or parallel approval steps.
    Steps can have conditions that determine if they should execute.
    """
    workflow_id: str
    domain: str  # hr, finance, legal, etc.
    task_type: str  # offer_letter, expense_approval, contract_review, etc.
    steps: List[ApprovalStep]
    auto_approve_conditions: Optional[str] = None  # Python expression for auto-approval
    workflow_name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None

    def __post_init__(self):
        if not self.workflow_name:
            self.workflow_name = f"{self.domain} - {self.task_type}"
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self._validate_dag()

    def _validate_dag(self):
        """Validate that the workflow forms a valid DAG (no cycles)"""
        # For now, we use a simple sequential/parallel model without explicit edges
        # More complex DAGs with explicit dependencies can be added later
        step_ids = [step.step_id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError(f"Duplicate step_ids found in workflow {self.workflow_id}")

        logger.info(f"Workflow {self.workflow_id} validated: {len(self.steps)} steps")


@dataclass
class ApprovalDecision:
    """
    Represents a single approval decision made by an approver.
    """
    decision_id: str
    request_id: str
    step_id: str
    approver_user_id: str
    approver_role: str
    decision: DecisionType
    comments: Optional[str] = None
    decided_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.decided_at:
            self.decided_at = datetime.utcnow().isoformat()


@dataclass
class ApprovalRequest:
    """
    Represents an active or historical approval request.

    Tracks the state of a workflow instance as it progresses through steps.
    """
    request_id: str
    workflow_id: str
    mission_id: str  # Links to orchestrator mission/job
    domain: str
    task_type: str
    payload: Dict[str, Any]  # The data being approved (e.g., offer details)

    # State tracking
    status: ApprovalStatus = ApprovalStatus.PENDING
    current_step_index: int = 0
    current_step_ids: List[str] = field(default_factory=list)  # For parallel steps

    # Timing
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None

    # History
    decisions: List[ApprovalDecision] = field(default_factory=list)
    step_history: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    created_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


# ============================================================================
# APPROVAL ENGINE
# ============================================================================

class ApprovalEngine:
    """
    Core approval workflow engine.

    Manages:
    - Workflow definitions
    - Approval requests
    - Decision processing
    - Timeout handling
    - State persistence
    """

    def __init__(self, db_path: str = "data/knowledge_graph.db"):
        self.db_path = db_path
        self._ensure_schema()
        logger.info(f"ApprovalEngine initialized with database: {db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self):
        """Create approval tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Approval workflows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_workflows (
                workflow_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                task_type TEXT NOT NULL,
                workflow_name TEXT,
                description TEXT,
                steps TEXT NOT NULL,  -- JSON serialized List[ApprovalStep]
                auto_approve_conditions TEXT,
                created_at TEXT NOT NULL,
                created_by TEXT,
                updated_at TEXT NOT NULL,
                metadata TEXT,  -- JSON metadata
                UNIQUE(domain, task_type)
            )
        """)

        # Approval requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_requests (
                request_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                mission_id TEXT NOT NULL,
                domain TEXT NOT NULL,
                task_type TEXT NOT NULL,
                payload TEXT NOT NULL,  -- JSON payload
                status TEXT NOT NULL,
                current_step_index INTEGER NOT NULL,
                current_step_ids TEXT,  -- JSON list of active step IDs
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT,
                created_by TEXT,
                metadata TEXT,  -- JSON metadata
                FOREIGN KEY (workflow_id) REFERENCES approval_workflows(workflow_id)
            )
        """)

        # Approval decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_decisions (
                decision_id TEXT PRIMARY KEY,
                request_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                approver_user_id TEXT NOT NULL,
                approver_role TEXT NOT NULL,
                decision TEXT NOT NULL,
                comments TEXT,
                decided_at TEXT NOT NULL,
                metadata TEXT,  -- JSON metadata
                FOREIGN KEY (request_id) REFERENCES approval_requests(request_id)
            )
        """)

        # Indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_mission ON approval_requests(mission_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON approval_requests(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_domain ON approval_requests(domain)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_request ON approval_decisions(request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_approver ON approval_decisions(approver_user_id)")

        conn.commit()
        conn.close()
        logger.info("Approval workflow schema created/verified")

    # ========================================================================
    # WORKFLOW MANAGEMENT
    # ========================================================================

    def register_workflow(self, workflow: ApprovalWorkflow) -> bool:
        """
        Register a new approval workflow.

        Args:
            workflow: ApprovalWorkflow definition

        Returns:
            True if registered successfully
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Serialize steps
            steps_json = json.dumps([asdict(step) for step in workflow.steps])

            cursor.execute("""
                INSERT OR REPLACE INTO approval_workflows
                (workflow_id, domain, task_type, workflow_name, description,
                 steps, auto_approve_conditions, created_at, created_by, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow.workflow_id,
                workflow.domain,
                workflow.task_type,
                workflow.workflow_name,
                workflow.description,
                steps_json,
                workflow.auto_approve_conditions,
                workflow.created_at,
                workflow.created_by,
                datetime.utcnow().isoformat(),
                None
            ))

            conn.commit()
            logger.info(f"Registered workflow: {workflow.workflow_id} ({workflow.domain}/{workflow.task_type})")
            return True

        except Exception as e:
            logger.error(f"Failed to register workflow {workflow.workflow_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_workflow(self, workflow_id: str) -> Optional[ApprovalWorkflow]:
        """Get workflow by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM approval_workflows WHERE workflow_id = ?
        """, (workflow_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Deserialize steps
        steps_data = json.loads(row['steps'])
        steps = [ApprovalStep(**step_dict) for step_dict in steps_data]

        return ApprovalWorkflow(
            workflow_id=row['workflow_id'],
            domain=row['domain'],
            task_type=row['task_type'],
            steps=steps,
            auto_approve_conditions=row['auto_approve_conditions'],
            workflow_name=row['workflow_name'],
            description=row['description'],
            created_at=row['created_at'],
            created_by=row['created_by']
        )

    def get_workflow_by_type(self, domain: str, task_type: str) -> Optional[ApprovalWorkflow]:
        """Get workflow by domain and task type"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT workflow_id FROM approval_workflows
            WHERE domain = ? AND task_type = ?
        """, (domain, task_type))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self.get_workflow(row['workflow_id'])

    # ========================================================================
    # APPROVAL REQUEST MANAGEMENT
    # ========================================================================

    def create_approval_request(
        self,
        workflow_id: str,
        mission_id: str,
        payload: Dict[str, Any],
        created_by: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Create a new approval request.

        Args:
            workflow_id: ID of the workflow to use
            mission_id: ID of the orchestrator mission/job
            payload: Data to be approved (e.g., offer details, expense info)
            created_by: User ID who created the request

        Returns:
            ApprovalRequest object
        """
        # Get workflow
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Check auto-approve conditions
        if workflow.auto_approve_conditions:
            if self._evaluate_condition(workflow.auto_approve_conditions, payload):
                logger.info(f"Auto-approving request for mission {mission_id}")
                return self._create_auto_approved_request(workflow, mission_id, payload, created_by)

        # Create request
        request_id = str(uuid.uuid4())

        # Determine first step(s)
        current_step_ids, actual_index = self._get_next_steps(workflow, 0, payload)

        request = ApprovalRequest(
            request_id=request_id,
            workflow_id=workflow_id,
            mission_id=mission_id,
            domain=workflow.domain,
            task_type=workflow.task_type,
            payload=payload,
            status=ApprovalStatus.PENDING,
            current_step_index=actual_index,
            current_step_ids=current_step_ids,
            created_by=created_by
        )

        # Save to database
        self._save_request(request)

        logger.info(f"Created approval request {request_id} for mission {mission_id}")
        logger.info(f"  Current steps: {current_step_ids}")

        return request

    def _create_auto_approved_request(
        self,
        workflow: ApprovalWorkflow,
        mission_id: str,
        payload: Dict[str, Any],
        created_by: Optional[str]
    ) -> ApprovalRequest:
        """Create an auto-approved request"""
        request_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        request = ApprovalRequest(
            request_id=request_id,
            workflow_id=workflow.workflow_id,
            mission_id=mission_id,
            domain=workflow.domain,
            task_type=workflow.task_type,
            payload=payload,
            status=ApprovalStatus.APPROVED,
            current_step_index=len(workflow.steps),
            current_step_ids=[],
            created_by=created_by,
            completed_at=now
        )

        # Add auto-approval decision
        decision = ApprovalDecision(
            decision_id=str(uuid.uuid4()),
            request_id=request_id,
            step_id="auto_approve",
            approver_user_id="system",
            approver_role="system",
            decision=DecisionType.APPROVE,
            comments="Auto-approved based on workflow conditions"
        )

        request.decisions.append(decision)
        self._save_request(request)

        return request

    def process_decision(
        self,
        request_id: str,
        approver_user_id: str,
        decision: DecisionType,
        comments: Optional[str] = None,
        approver_role: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Process an approval decision.

        Args:
            request_id: ID of the approval request
            approver_user_id: ID of the user making the decision
            decision: APPROVE, REJECT, ESCALATE, or REQUEST_INFO
            comments: Optional comments from approver
            approver_role: Role of the approver (auto-detected if not provided)

        Returns:
            Updated ApprovalRequest
        """
        # Get request
        request = self.get_request(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request {request_id} is not pending (status: {request.status.value})")

        # Get workflow
        workflow = self.get_workflow(request.workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {request.workflow_id} not found")

        # Find the current step being approved
        current_steps = [s for s in workflow.steps if s.step_id in request.current_step_ids]
        if not current_steps:
            raise ValueError(f"No active steps found for request {request_id}")

        # Validate approver has permission for at least one current step
        valid_step = None
        for step in current_steps:
            if self._validate_approver(step, approver_user_id, approver_role):
                valid_step = step
                break

        if not valid_step:
            raise ValueError(f"User {approver_user_id} not authorized to approve any current steps")

        # Create decision record
        decision_record = ApprovalDecision(
            decision_id=str(uuid.uuid4()),
            request_id=request_id,
            step_id=valid_step.step_id,
            approver_user_id=approver_user_id,
            approver_role=approver_role or valid_step.approver_role,
            decision=decision,
            comments=comments
        )

        request.decisions.append(decision_record)

        # Save decision to database
        self._save_decision(decision_record)

        # Process based on decision type
        if decision == DecisionType.REJECT:
            request.status = ApprovalStatus.REJECTED
            request.completed_at = datetime.utcnow().isoformat()
            request.current_step_ids = []
            logger.info(f"Request {request_id} rejected by {approver_user_id}")

        elif decision == DecisionType.ESCALATE:
            request.status = ApprovalStatus.ESCALATED
            # TODO: Implement escalation logic (reassign to escalation_role)
            logger.info(f"Request {request_id} escalated by {approver_user_id}")

        elif decision == DecisionType.APPROVE:
            # Check if all required approvals for this step are complete
            if self._check_step_complete(request, valid_step, workflow):
                # Move to next step
                request = self._advance_to_next_step(request, workflow)

        elif decision == DecisionType.REQUEST_INFO:
            # Add to history but don't change state
            logger.info(f"Additional info requested for {request_id} by {approver_user_id}")

        # Update request
        request.updated_at = datetime.utcnow().isoformat()
        self._save_request(request)

        return request

    def _validate_approver(
        self,
        step: ApprovalStep,
        approver_user_id: str,
        approver_role: Optional[str]
    ) -> bool:
        """
        Validate that the approver is authorized for this step.

        If step specifies a user, must match.
        If step specifies a role, approver must have that role.
        """
        if step.approver_user_id:
            return approver_user_id == step.approver_user_id

        if approver_role:
            return approver_role == step.approver_role

        # If no role provided, we can't validate
        # In production, we'd look up user's role from auth system
        return True

    def _check_step_complete(
        self,
        request: ApprovalRequest,
        step: ApprovalStep,
        workflow: ApprovalWorkflow
    ) -> bool:
        """
        Check if a step has received all required approvals.

        For parallel steps with required_count > 1, checks if enough approvals received.
        """
        # Count approvals for this step
        approvals = [
            d for d in request.decisions
            if d.step_id == step.step_id and d.decision == DecisionType.APPROVE
        ]

        is_complete = len(approvals) >= step.required_count
        logger.debug(f"Step {step.step_id} complete check: {len(approvals)}/{step.required_count} approvals = {is_complete}")
        return is_complete

    def _advance_to_next_step(
        self,
        request: ApprovalRequest,
        workflow: ApprovalWorkflow
    ) -> ApprovalRequest:
        """
        Advance request to the next step(s) in the workflow.
        """
        # Remove completed step from current_step_ids
        completed_steps = [
            step for step in workflow.steps
            if step.step_id in request.current_step_ids
            and self._check_step_complete(request, step, workflow)
        ]

        for step in completed_steps:
            request.current_step_ids.remove(step.step_id)

        # If no more current steps, try to advance
        if not request.current_step_ids:
            # Find the highest index among completed steps
            max_completed_index = request.current_step_index
            for step in completed_steps:
                for i, workflow_step in enumerate(workflow.steps):
                    if workflow_step.step_id == step.step_id:
                        max_completed_index = max(max_completed_index, i)
                        break

            # Advance to the step after the last completed one
            next_index = max_completed_index + 1

            # Get next step(s) and update step_index
            next_steps, actual_index = self._get_next_steps(
                workflow,
                next_index,
                request.payload
            )

            # Check if workflow complete (either no more steps or index beyond workflow)
            if not next_steps or actual_index >= len(workflow.steps):
                request.status = ApprovalStatus.APPROVED
                request.completed_at = datetime.utcnow().isoformat()
                logger.info(f"Request {request.request_id} fully approved")
            else:
                request.current_step_ids = next_steps
                request.current_step_index = actual_index
                logger.info(f"Request {request.request_id} advanced to index {actual_index}, steps: {next_steps}")

        return request

    def _get_next_steps(
        self,
        workflow: ApprovalWorkflow,
        step_index: int,
        payload: Dict[str, Any]
    ) -> Tuple[List[str], int]:
        """
        Get the next step(s) to execute based on conditions and parallel flags.

        Returns tuple of (step_ids, actual_step_index).
        The actual_step_index accounts for skipped conditional steps.
        """
        if step_index >= len(workflow.steps):
            return [], step_index

        next_steps = []

        # Check first step at this index
        step = workflow.steps[step_index]

        # Evaluate condition if present
        if step.condition:
            if not self._evaluate_condition(step.condition, payload):
                # Skip this step and try next
                return self._get_next_steps(workflow, step_index + 1, payload)

        next_steps.append(step.step_id)

        # If parallel, check subsequent steps
        if step.parallel:
            for i in range(step_index + 1, len(workflow.steps)):
                next_step = workflow.steps[i]

                if not next_step.parallel:
                    break  # End of parallel group

                # Evaluate condition
                if next_step.condition:
                    if not self._evaluate_condition(next_step.condition, payload):
                        continue

                next_steps.append(next_step.step_id)

        return next_steps, step_index

    def _evaluate_condition(self, condition: str, payload: Dict[str, Any]) -> bool:
        """
        Safely evaluate a condition expression.

        Condition has access to:
        - payload: The approval request payload
        - Any safe built-in functions

        Example conditions:
        - "payload['amount'] > 10000"
        - "payload['department'] == 'engineering'"
        - "payload.get('is_urgent', False)"
        """
        try:
            # Create safe namespace
            namespace = {
                'payload': payload,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'abs': abs,
                'min': min,
                'max': max,
                'sum': sum,
                'any': any,
                'all': all,
            }

            # Evaluate
            result = eval(condition, {"__builtins__": {}}, namespace)
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to evaluate condition '{condition}': {e}")
            return False

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM approval_requests WHERE request_id = ?
        """, (request_id,))

        row = cursor.fetchone()

        if not row:
            conn.close()
            return None

        # Get decisions
        cursor.execute("""
            SELECT * FROM approval_decisions WHERE request_id = ? ORDER BY decided_at
        """, (request_id,))

        decision_rows = cursor.fetchall()
        conn.close()

        # Deserialize
        request = ApprovalRequest(
            request_id=row['request_id'],
            workflow_id=row['workflow_id'],
            mission_id=row['mission_id'],
            domain=row['domain'],
            task_type=row['task_type'],
            payload=json.loads(row['payload']),
            status=ApprovalStatus(row['status']),
            current_step_index=row['current_step_index'],
            current_step_ids=json.loads(row['current_step_ids']) if row['current_step_ids'] else [],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            completed_at=row['completed_at'],
            created_by=row['created_by']
        )

        # Add decisions
        for dec_row in decision_rows:
            decision = ApprovalDecision(
                decision_id=dec_row['decision_id'],
                request_id=dec_row['request_id'],
                step_id=dec_row['step_id'],
                approver_user_id=dec_row['approver_user_id'],
                approver_role=dec_row['approver_role'],
                decision=DecisionType(dec_row['decision']),
                comments=dec_row['comments'],
                decided_at=dec_row['decided_at'],
                metadata=json.loads(dec_row['metadata']) if dec_row['metadata'] else None
            )
            request.decisions.append(decision)

        return request

    def get_pending_approvals(
        self,
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending approvals for a user/role.

        Args:
            user_id: Filter by user ID
            role: Filter by role
            domain: Filter by domain (hr, finance, legal, etc.)

        Returns:
            List of pending approval requests with workflow details
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT
                r.*,
                w.workflow_name,
                w.description as workflow_description,
                w.steps as workflow_steps
            FROM approval_requests r
            JOIN approval_workflows w ON r.workflow_id = w.workflow_id
            WHERE r.status = 'pending'
        """
        params = []

        if domain:
            query += " AND r.domain = ?"
            params.append(domain)

        query += " ORDER BY r.created_at DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Filter by user/role and format results
        results = []
        for row in rows:
            request = self.get_request(row['request_id'])
            if not request:
                continue

            # Get workflow
            workflow = self.get_workflow(row['workflow_id'])
            if not workflow:
                continue

            # Check if user/role can approve current steps
            current_steps = [s for s in workflow.steps if s.step_id in request.current_step_ids]

            can_approve = False
            for step in current_steps:
                if user_id and step.approver_user_id == user_id:
                    can_approve = True
                    break
                if role and step.approver_role == role:
                    can_approve = True
                    break
                if not user_id and not role:
                    # No filter, include all
                    can_approve = True
                    break

            if not can_approve:
                continue

            # Calculate timeout
            created_time = datetime.fromisoformat(request.created_at)
            timeout_hours = current_steps[0].timeout_hours if current_steps else 24
            timeout_at = created_time + timedelta(hours=timeout_hours)
            hours_remaining = (timeout_at - datetime.utcnow()).total_seconds() / 3600

            results.append({
                'request_id': request.request_id,
                'mission_id': request.mission_id,
                'workflow_id': request.workflow_id,
                'workflow_name': row['workflow_name'],
                'domain': request.domain,
                'task_type': request.task_type,
                'payload': request.payload,
                'current_steps': [
                    {
                        'step_id': s.step_id,
                        'step_name': s.step_name,
                        'description': s.description,
                        'approver_role': s.approver_role,
                        'timeout_hours': s.timeout_hours
                    }
                    for s in current_steps
                ],
                'created_at': request.created_at,
                'hours_remaining': round(hours_remaining, 1),
                'is_overdue': hours_remaining < 0,
                'previous_decisions': [
                    {
                        'approver': d.approver_user_id,
                        'decision': d.decision.value,
                        'comments': d.comments,
                        'decided_at': d.decided_at
                    }
                    for d in request.decisions
                ]
            })

        return results

    def check_timeouts(self) -> List[ApprovalRequest]:
        """
        Check for timed-out approvals and escalate them.

        This should be run as a background job periodically.

        Returns:
            List of requests that were timed out
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get all pending requests
        cursor.execute("""
            SELECT request_id FROM approval_requests WHERE status = 'pending'
        """)

        rows = cursor.fetchall()
        conn.close()

        timed_out = []

        for row in rows:
            request = self.get_request(row['request_id'])
            if not request:
                continue

            workflow = self.get_workflow(request.workflow_id)
            if not workflow:
                continue

            # Check current steps for timeout
            current_steps = [s for s in workflow.steps if s.step_id in request.current_step_ids]

            for step in current_steps:
                created_time = datetime.fromisoformat(request.created_at)
                timeout_at = created_time + timedelta(hours=step.timeout_hours)

                if datetime.utcnow() > timeout_at:
                    # Timeout! Escalate or mark as timed out
                    logger.warning(f"Request {request.request_id} step {step.step_id} timed out")

                    if step.escalation_role:
                        # Escalate to next level
                        request.status = ApprovalStatus.ESCALATED
                        # TODO: Reassign to escalation_role
                        logger.info(f"Escalating to {step.escalation_role}")
                    else:
                        # No escalation path, mark as timeout
                        request.status = ApprovalStatus.TIMEOUT
                        request.completed_at = datetime.utcnow().isoformat()

                    request.updated_at = datetime.utcnow().isoformat()
                    self._save_request(request)
                    timed_out.append(request)

        return timed_out

    # ========================================================================
    # DATABASE OPERATIONS
    # ========================================================================

    def _save_request(self, request: ApprovalRequest):
        """Save approval request to database"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO approval_requests
                (request_id, workflow_id, mission_id, domain, task_type, payload,
                 status, current_step_index, current_step_ids,
                 created_at, updated_at, completed_at, created_by, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.request_id,
                request.workflow_id,
                request.mission_id,
                request.domain,
                request.task_type,
                json.dumps(request.payload),
                request.status.value,
                request.current_step_index,
                json.dumps(request.current_step_ids),
                request.created_at,
                request.updated_at,
                request.completed_at,
                request.created_by,
                json.dumps(request.metadata) if request.metadata else None
            ))

            conn.commit()
        except Exception as e:
            logger.error(f"Failed to save request {request.request_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def _save_decision(self, decision: ApprovalDecision):
        """Save approval decision to database"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO approval_decisions
                (decision_id, request_id, step_id, approver_user_id, approver_role,
                 decision, comments, decided_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.decision_id,
                decision.request_id,
                decision.step_id,
                decision.approver_user_id,
                decision.approver_role,
                decision.decision.value,
                decision.comments,
                decision.decided_at,
                json.dumps(decision.metadata) if decision.metadata else None
            ))

            conn.commit()
        except Exception as e:
            logger.error(f"Failed to save decision {decision.decision_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    # ========================================================================
    # STATISTICS & REPORTING
    # ========================================================================

    def get_statistics(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Get approval workflow statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()

        query_filter = f"WHERE domain = '{domain}'" if domain else ""

        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN status = 'escalated' THEN 1 ELSE 0 END) as escalated,
                SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout
            FROM approval_requests
            {query_filter}
        """)

        row = cursor.fetchone()
        conn.close()

        return {
            'total_requests': row['total'],
            'pending': row['pending'],
            'approved': row['approved'],
            'rejected': row['rejected'],
            'escalated': row['escalated'],
            'timeout': row['timeout']
        }


# ============================================================================
# EXAMPLE WORKFLOW DEFINITIONS
# ============================================================================

def create_hr_offer_letter_workflow() -> ApprovalWorkflow:
    """
    HR Offer Letter Workflow:
    1. Hiring Manager approval (always required)
    2. Director approval (if salary > $100k)
    3. HR Head approval (always required)
    """
    return ApprovalWorkflow(
        workflow_id="hr_offer_letter_v1",
        domain="hr",
        task_type="offer_letter",
        workflow_name="HR Offer Letter Approval",
        description="Multi-step approval for job offers",
        steps=[
            ApprovalStep(
                step_id="hiring_manager",
                approver_role="hr_hiring_manager",
                timeout_hours=24,
                escalation_role="hr_director",
                step_name="Hiring Manager Approval",
                description="Review candidate qualifications and salary"
            ),
            ApprovalStep(
                step_id="director",
                approver_role="hr_director",
                condition="payload.get('salary', 0) > 100000",
                timeout_hours=48,
                escalation_role="vp_hr",
                step_name="Director Approval",
                description="Required for salaries over $100k"
            ),
            ApprovalStep(
                step_id="hr_head",
                approver_role="hr_head",
                timeout_hours=24,
                step_name="HR Head Final Approval",
                description="Final compliance and policy check"
            )
        ],
        auto_approve_conditions="payload.get('salary', 0) < 50000 and payload.get('level', '') == 'intern'"
    )


def create_finance_expense_workflow() -> ApprovalWorkflow:
    """
    Finance Expense Approval Workflow:
    1. Manager approval (for expenses < $5k)
    2. Controller approval (for expenses $5k-$25k)
    3. CFO approval (for expenses > $25k)
    """
    return ApprovalWorkflow(
        workflow_id="finance_expense_v1",
        domain="finance",
        task_type="expense_approval",
        workflow_name="Expense Approval Workflow",
        description="Tiered approval based on expense amount",
        steps=[
            ApprovalStep(
                step_id="manager",
                approver_role="manager",
                condition="payload.get('amount', 0) < 5000",
                timeout_hours=24,
                step_name="Manager Approval",
                description="For expenses under $5k"
            ),
            ApprovalStep(
                step_id="controller",
                approver_role="finance_controller",
                condition="payload.get('amount', 0) >= 5000 and payload.get('amount', 0) < 25000",
                timeout_hours=48,
                escalation_role="cfo",
                step_name="Controller Approval",
                description="For expenses $5k-$25k"
            ),
            ApprovalStep(
                step_id="cfo",
                approver_role="cfo",
                condition="payload.get('amount', 0) >= 25000",
                timeout_hours=72,
                step_name="CFO Approval",
                description="For expenses over $25k"
            )
        ],
        auto_approve_conditions="payload.get('amount', 0) < 100"
    )


def create_legal_contract_workflow() -> ApprovalWorkflow:
    """
    Legal Contract Review Workflow:
    1. Contract Manager review
    2. Legal Counsel approval (parallel with Finance if > $50k)
    3. Finance approval (if contract value > $50k)
    4. General Counsel final approval (if > $100k)
    """
    return ApprovalWorkflow(
        workflow_id="legal_contract_v1",
        domain="legal",
        task_type="contract_review",
        workflow_name="Contract Review & Approval",
        description="Legal and financial review of contracts",
        steps=[
            ApprovalStep(
                step_id="contract_manager",
                approver_role="legal_contract_manager",
                timeout_hours=48,
                escalation_role="legal_counsel",
                step_name="Contract Manager Review",
                description="Initial contract review"
            ),
            ApprovalStep(
                step_id="legal_counsel",
                approver_role="legal_counsel",
                timeout_hours=72,
                escalation_role="general_counsel",
                parallel=True,
                step_name="Legal Counsel Approval",
                description="Legal review and approval"
            ),
            ApprovalStep(
                step_id="finance_review",
                approver_role="finance_controller",
                condition="payload.get('contract_value', 0) > 50000",
                timeout_hours=72,
                parallel=True,
                step_name="Finance Review",
                description="Financial impact review for high-value contracts"
            ),
            ApprovalStep(
                step_id="general_counsel",
                approver_role="general_counsel",
                condition="payload.get('contract_value', 0) > 100000",
                timeout_hours=96,
                step_name="General Counsel Final Approval",
                description="Final approval for high-value contracts"
            )
        ]
    )


# ============================================================================
# CLI & TESTING
# ============================================================================

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    engine = ApprovalEngine()

    # Register example workflows
    print("Registering example workflows...")
    engine.register_workflow(create_hr_offer_letter_workflow())
    engine.register_workflow(create_finance_expense_workflow())
    engine.register_workflow(create_legal_contract_workflow())

    # Create a test request
    print("\nCreating test approval request...")
    request = engine.create_approval_request(
        workflow_id="hr_offer_letter_v1",
        mission_id="test_mission_123",
        payload={
            "candidate_name": "Jane Doe",
            "position": "Senior Engineer",
            "salary": 150000,
            "level": "senior",
            "department": "engineering"
        },
        created_by="recruiter_001"
    )

    print(f"Created request: {request.request_id}")
    print(f"Status: {request.status.value}")
    print(f"Current steps: {request.current_step_ids}")

    # Get pending approvals
    print("\nPending approvals for hr_hiring_manager:")
    pending = engine.get_pending_approvals(role="hr_hiring_manager")
    for approval in pending:
        print(f"  - {approval['workflow_name']}: {approval['payload'].get('candidate_name')}")

    # Get statistics
    print("\nStatistics:")
    stats = engine.get_statistics(domain="hr")
    for key, value in stats.items():
        print(f"  {key}: {value}")
