"""
Supervisor review queue system.

PHASE 7C.3: Manages review of Employee work output with batching, quality gates,
and automated approval for low-risk work.

Features:
- Queue incoming work from all Employees
- Batch similar reviews together for efficiency
- Auto-approve low-risk work that passes quality gates
- Escalate failures and high-risk work to Manager
- Track comprehensive review metrics
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from agent.llm_client import LLMClient
from agent.core_logging import log_event


class RiskLevel(Enum):
    """Work risk level"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkType(Enum):
    """Type of work being reviewed"""
    CODE = "code"
    DOCUMENT = "document"
    DATA_ANALYSIS = "data_analysis"
    API_CALL = "api_call"
    DATABASE_QUERY = "database_query"
    FILE_OPERATION = "file_operation"
    COMMUNICATION = "communication"
    OTHER = "other"


class ReviewStatus(Enum):
    """Review status"""
    PENDING = "pending"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    AUTO_APPROVED = "auto_approved"


@dataclass
class QualityGateResult:
    """Result of quality gate checks"""
    correctness_passed: bool
    safety_passed: bool
    performance_passed: bool
    code_quality_passed: bool
    overall_passed: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ReviewItem:
    """Work item to be reviewed"""
    work_id: str
    employee_id: str
    task_description: str
    result: Any
    risk_level: RiskLevel
    work_type: WorkType
    submitted_at: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict] = None
    quality_gates: Optional[QualityGateResult] = None


@dataclass
class ReviewResult:
    """Result of review"""
    work_id: str
    status: ReviewStatus
    approved: bool
    reviewer: str  # "supervisor" or "manager"
    feedback: Optional[str] = None
    required_changes: List[str] = field(default_factory=list)
    reviewed_at: datetime = field(default_factory=datetime.now)
    review_duration: float = 0.0


class ReviewQueueManager:
    """
    Manages Supervisor review queue with batching and auto-approval.

    Features:
    - Batch processing of similar work
    - Quality gate validation
    - Auto-approval for low-risk work
    - Escalation to Manager for high-risk/failed work
    - Comprehensive metrics tracking

    Example:
        queue = ReviewQueueManager(llm_client)
        await queue.start()

        # Submit work for review
        work_id = await queue.submit_for_review(
            employee_id="employee_1",
            task_description="Write function",
            result={"code": "def foo(): pass"},
            risk_level=RiskLevel.LOW,
            work_type=WorkType.CODE
        )

        # Get review result
        review = await queue.get_review_result(work_id)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        enable_auto_approval: bool = True,
        enable_batching: bool = True,
        batch_timeout: float = 3.0,  # seconds
        auto_approve_risk_threshold: RiskLevel = RiskLevel.LOW
    ):
        """
        Initialize review queue manager.

        Args:
            llm_client: LLM client for Supervisor reviews
            enable_auto_approval: Enable auto-approval for low-risk work
            enable_batching: Enable batch processing
            batch_timeout: Max time to wait for batch accumulation
            auto_approve_risk_threshold: Max risk level for auto-approval
        """
        self.llm = llm_client
        self.enable_auto_approval = enable_auto_approval
        self.enable_batching = enable_batching
        self.batch_timeout = batch_timeout
        self.auto_approve_threshold = auto_approve_risk_threshold

        # Review queue
        self.review_queue: List[ReviewItem] = []
        self.queue_lock = asyncio.Lock()

        # Completed reviews
        self.review_results: Dict[str, ReviewResult] = {}

        # Result futures
        self.result_futures: Dict[str, asyncio.Future] = {}

        # Batch accumulator
        self.batch_accumulator: Dict[WorkType, List[ReviewItem]] = {}

        # Background processor
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None

        # Metrics
        self.metrics = {
            "total_submitted": 0,
            "total_reviewed": 0,
            "auto_approved": 0,
            "manual_approved": 0,
            "rejected": 0,
            "escalated": 0,
            "total_review_time": 0.0,
            "quality_gate_failures": 0,
            "batches_processed": 0
        }

    async def start(self):
        """Start background review processor"""
        self._running = True
        self._processor_task = asyncio.create_task(self._process_review_queue())
        log_event("review_queue_started", {})

    async def stop(self):
        """Stop background processor"""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        log_event("review_queue_stopped", {})

    async def submit_for_review(
        self,
        employee_id: str,
        task_description: str,
        result: Any,
        risk_level: RiskLevel,
        work_type: WorkType,
        metadata: Optional[Dict] = None,
        work_id: Optional[str] = None
    ) -> str:
        """
        Submit work for review.

        Args:
            employee_id: ID of Employee who produced work
            task_description: Description of task
            result: Work result/output
            risk_level: Risk level assessment
            work_type: Type of work
            metadata: Additional metadata
            work_id: Optional work ID (auto-generated if None)

        Returns:
            Work ID for tracking
        """
        # Generate work ID if not provided
        if not work_id:
            work_id = f"work_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # Create review item
        review_item = ReviewItem(
            work_id=work_id,
            employee_id=employee_id,
            task_description=task_description,
            result=result,
            risk_level=risk_level,
            work_type=work_type,
            metadata=metadata
        )

        # Create result future
        self.result_futures[work_id] = asyncio.Future()

        # Add to queue
        async with self.queue_lock:
            self.review_queue.append(review_item)

        self.metrics["total_submitted"] += 1

        log_event("work_submitted_for_review", {
            "work_id": work_id,
            "employee_id": employee_id,
            "risk_level": risk_level.value,
            "work_type": work_type.value
        })

        return work_id

    async def _process_review_queue(self):
        """Background review processor"""
        while self._running:
            try:
                # Get items from queue
                items_to_process = []
                async with self.queue_lock:
                    if self.review_queue:
                        # Get up to 20 items
                        items_to_process = self.review_queue[:20]
                        self.review_queue = self.review_queue[20:]

                if items_to_process:
                    # Run quality gates first
                    for item in items_to_process:
                        item.quality_gates = await self._run_quality_gates(item)

                    # Separate by processing strategy
                    auto_approve_items = []
                    manual_review_items = []

                    for item in items_to_process:
                        if self._should_auto_approve(item):
                            auto_approve_items.append(item)
                        else:
                            manual_review_items.append(item)

                    # Process auto-approvals
                    for item in auto_approve_items:
                        asyncio.create_task(self._auto_approve(item))

                    # Process manual reviews
                    if manual_review_items:
                        if self.enable_batching:
                            batches = self._group_by_work_type(manual_review_items)
                            for work_type, batch in batches.items():
                                asyncio.create_task(self._review_batch(batch))
                        else:
                            for item in manual_review_items:
                                asyncio.create_task(self._review_single(item))

                # Sleep briefly
                await asyncio.sleep(0.1)

            except Exception as e:
                log_event("review_processor_error", {
                    "error": str(e)
                })
                await asyncio.sleep(1)

    async def _run_quality_gates(self, item: ReviewItem) -> QualityGateResult:
        """
        Run quality gate checks on work.

        Checks:
        - Correctness: Does it do what was asked?
        - Safety: Is it safe (no security issues, destructive operations)?
        - Performance: Is it efficient?
        - Code quality: Is it well-written? (if code)
        """
        issues = []
        warnings = []

        # Correctness check
        correctness_passed = await self._check_correctness(item)
        if not correctness_passed:
            issues.append("Correctness check failed: Output doesn't match task requirements")

        # Safety check
        safety_passed = await self._check_safety(item)
        if not safety_passed:
            issues.append("Safety check failed: Potential security or safety issues detected")

        # Performance check
        performance_passed = await self._check_performance(item)
        if not performance_passed:
            warnings.append("Performance check flagged: May be inefficient")

        # Code quality check (if applicable)
        code_quality_passed = True
        if item.work_type == WorkType.CODE:
            code_quality_passed = await self._check_code_quality(item)
            if not code_quality_passed:
                warnings.append("Code quality check flagged: May need improvements")

        overall_passed = correctness_passed and safety_passed

        if not overall_passed:
            self.metrics["quality_gate_failures"] += 1

        return QualityGateResult(
            correctness_passed=correctness_passed,
            safety_passed=safety_passed,
            performance_passed=performance_passed,
            code_quality_passed=code_quality_passed,
            overall_passed=overall_passed,
            issues=issues,
            warnings=warnings
        )

    async def _check_correctness(self, item: ReviewItem) -> bool:
        """Check if output is correct for the task"""
        # Simple heuristic checks
        if not item.result:
            return False

        if isinstance(item.result, dict):
            # Check for error indicators
            if item.result.get("error"):
                return False
            if item.result.get("success") is False:
                return False

        # For LOW risk, basic checks are sufficient
        if item.risk_level == RiskLevel.LOW:
            return True

        # For higher risk, would use LLM to validate
        # Simplified for now
        return True

    async def _check_safety(self, item: ReviewItem) -> bool:
        """Check for safety issues"""
        # Check work type specific safety
        if item.work_type == WorkType.DATABASE_QUERY:
            # Check for dangerous SQL
            if isinstance(item.result, dict):
                query = item.result.get("query", "")
                if any(kw in query.upper() for kw in ["DROP", "DELETE", "TRUNCATE"]):
                    return False

        elif item.work_type == WorkType.FILE_OPERATION:
            # Check for system file access
            if isinstance(item.result, dict):
                path = item.result.get("path", "")
                if any(p in path for p in ["/etc", "/sys", "/proc", "C:\\Windows"]):
                    return False

        return True

    async def _check_performance(self, item: ReviewItem) -> bool:
        """Check for performance issues"""
        # Check execution time if available
        if isinstance(item.result, dict):
            exec_time = item.result.get("execution_time", 0)
            if exec_time > 30:  # More than 30 seconds
                return False

        return True

    async def _check_code_quality(self, item: ReviewItem) -> bool:
        """Check code quality (if applicable)"""
        if item.work_type != WorkType.CODE:
            return True

        # Basic code quality checks
        if isinstance(item.result, dict):
            code = item.result.get("code", "")
            if not code or len(code) < 10:
                return False

        return True

    def _should_auto_approve(self, item: ReviewItem) -> bool:
        """Determine if work should be auto-approved"""
        if not self.enable_auto_approval:
            return False

        # Only auto-approve if risk level is within threshold
        risk_levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        item_risk_index = risk_levels.index(item.risk_level)
        threshold_index = risk_levels.index(self.auto_approve_threshold)

        if item_risk_index > threshold_index:
            return False

        # Must pass quality gates
        if not item.quality_gates or not item.quality_gates.overall_passed:
            return False

        return True

    async def _auto_approve(self, item: ReviewItem):
        """Auto-approve low-risk work"""
        start_time = datetime.now()

        review_result = ReviewResult(
            work_id=item.work_id,
            status=ReviewStatus.AUTO_APPROVED,
            approved=True,
            reviewer="supervisor_auto",
            feedback="Auto-approved: Low risk, passed all quality gates",
            review_duration=0.1
        )

        self.review_results[item.work_id] = review_result
        self.metrics["auto_approved"] += 1
        self.metrics["total_reviewed"] += 1
        self.metrics["total_review_time"] += review_result.review_duration

        # Set result future
        if item.work_id in self.result_futures:
            self.result_futures[item.work_id].set_result(review_result)

        log_event("work_auto_approved", {
            "work_id": item.work_id,
            "risk_level": item.risk_level.value
        })

    async def _review_single(self, item: ReviewItem):
        """Perform single item review"""
        start_time = datetime.now()

        try:
            # Check if should escalate to Manager
            if self._should_escalate(item):
                review_result = await self._escalate_to_manager(item)
            else:
                # Supervisor review
                review_result = await self._supervisor_review(item)

            review_result.review_duration = (datetime.now() - start_time).total_seconds()

            self.review_results[item.work_id] = review_result
            self.metrics["total_reviewed"] += 1
            self.metrics["total_review_time"] += review_result.review_duration

            if review_result.approved:
                self.metrics["manual_approved"] += 1
            else:
                self.metrics["rejected"] += 1

            # Set result future
            if item.work_id in self.result_futures:
                self.result_futures[item.work_id].set_result(review_result)

        except Exception as e:
            # Review failed
            review_result = ReviewResult(
                work_id=item.work_id,
                status=ReviewStatus.REJECTED,
                approved=False,
                reviewer="supervisor",
                feedback=f"Review error: {str(e)}"
            )

            self.review_results[item.work_id] = review_result
            self.metrics["rejected"] += 1

            if item.work_id in self.result_futures:
                self.result_futures[item.work_id].set_result(review_result)

    async def _review_batch(self, items: List[ReviewItem]):
        """Review batch of similar work"""
        start_time = datetime.now()

        log_event("batch_review_started", {
            "batch_size": len(items),
            "work_type": items[0].work_type.value if items else "unknown"
        })

        # Review each item in batch
        for item in items:
            await self._review_single(item)

        self.metrics["batches_processed"] += 1

        log_event("batch_review_completed", {
            "batch_size": len(items),
            "duration": (datetime.now() - start_time).total_seconds()
        })

    async def _supervisor_review(self, item: ReviewItem) -> ReviewResult:
        """Perform Supervisor review using LLM"""
        prompt = f"""Review this work output from an Employee agent.

TASK: {item.task_description}

WORK TYPE: {item.work_type.value}
RISK LEVEL: {item.risk_level.value}

RESULT:
{item.result}

QUALITY GATES:
- Correctness: {'✓ PASSED' if item.quality_gates.correctness_passed else '✗ FAILED'}
- Safety: {'✓ PASSED' if item.quality_gates.safety_passed else '✗ FAILED'}
- Performance: {'✓ PASSED' if item.quality_gates.performance_passed else '⚠ WARNING'}
- Code Quality: {'✓ PASSED' if item.quality_gates.code_quality_passed else '⚠ WARNING'}

Issues: {', '.join(item.quality_gates.issues) if item.quality_gates.issues else 'None'}
Warnings: {', '.join(item.quality_gates.warnings) if item.quality_gates.warnings else 'None'}

As a Supervisor, review this work. Determine if it should be:
1. APPROVED - Work is good and complete
2. REJECTED - Work has issues that need to be fixed

Return JSON:
{{
  "approved": true/false,
  "feedback": "Brief feedback",
  "required_changes": ["change 1", "change 2"] // if rejected
}}
"""

        try:
            review_data = await self.llm.chat_json(
                prompt=prompt,
                model="gpt-4o",
                temperature=0.2
            )

            return ReviewResult(
                work_id=item.work_id,
                status=ReviewStatus.APPROVED if review_data.get("approved") else ReviewStatus.REJECTED,
                approved=review_data.get("approved", False),
                reviewer="supervisor",
                feedback=review_data.get("feedback"),
                required_changes=review_data.get("required_changes", [])
            )

        except Exception as e:
            log_event("supervisor_review_failed", {
                "work_id": item.work_id,
                "error": str(e)
            })
            # Default to rejection on error
            return ReviewResult(
                work_id=item.work_id,
                status=ReviewStatus.REJECTED,
                approved=False,
                reviewer="supervisor",
                feedback=f"Review error: {str(e)}"
            )

    def _should_escalate(self, item: ReviewItem) -> bool:
        """Determine if work should be escalated to Manager"""
        # Escalate CRITICAL risk
        if item.risk_level == RiskLevel.CRITICAL:
            return True

        # Escalate if quality gates failed badly
        if item.quality_gates and not item.quality_gates.overall_passed:
            if len(item.quality_gates.issues) >= 2:
                return True

        return False

    async def _escalate_to_manager(self, item: ReviewItem) -> ReviewResult:
        """Escalate work to Manager for review"""
        log_event("work_escalated_to_manager", {
            "work_id": item.work_id,
            "risk_level": item.risk_level.value,
            "reason": "Critical risk or quality gate failures"
        })

        self.metrics["escalated"] += 1

        # In full implementation, this would route to Manager agent
        # For now, return escalated status
        return ReviewResult(
            work_id=item.work_id,
            status=ReviewStatus.ESCALATED,
            approved=False,
            reviewer="manager",
            feedback="Escalated to Manager for review due to high risk or quality concerns"
        )

    def _group_by_work_type(
        self,
        items: List[ReviewItem]
    ) -> Dict[WorkType, List[ReviewItem]]:
        """Group items by work type for batch processing"""
        batches = {}
        for item in items:
            if item.work_type not in batches:
                batches[item.work_type] = []
            batches[item.work_type].append(item)
        return batches

    async def get_review_result(self, work_id: str) -> ReviewResult:
        """
        Wait for and get review result.

        Args:
            work_id: Work ID

        Returns:
            Review result
        """
        if work_id in self.review_results:
            return self.review_results[work_id]

        if work_id in self.result_futures:
            return await self.result_futures[work_id]

        raise ValueError(f"Unknown work ID: {work_id}")

    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "queue_length": len(self.review_queue),
            "completed_reviews": len(self.review_results),
            "pending_reviews": len(self.review_queue)
        }

    def get_review_metrics(self) -> Dict[str, Any]:
        """Get comprehensive review metrics"""
        total_reviewed = self.metrics["total_reviewed"]

        return {
            **self.metrics,
            "auto_approval_rate": (
                self.metrics["auto_approved"] / total_reviewed
                if total_reviewed > 0 else 0
            ),
            "approval_rate": (
                (self.metrics["auto_approved"] + self.metrics["manual_approved"]) / total_reviewed
                if total_reviewed > 0 else 0
            ),
            "rejection_rate": (
                self.metrics["rejected"] / total_reviewed
                if total_reviewed > 0 else 0
            ),
            "escalation_rate": (
                self.metrics["escalated"] / total_reviewed
                if total_reviewed > 0 else 0
            ),
            "avg_review_time": (
                self.metrics["total_review_time"] / total_reviewed
                if total_reviewed > 0 else 0
            )
        }
