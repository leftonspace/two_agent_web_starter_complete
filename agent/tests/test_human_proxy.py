"""
Comprehensive Tests for Human-in-the-Loop Controller

Tests for:
- UserProxyAgent
- ApprovalCheckpoint system
- OrchestratorWithApproval
- WebSocket integration
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from agent.human_proxy import (
    # Enums
    InputMode,
    ApprovalStatus,
    ApprovalCheckpoint,
    NotificationChannel,
    # Data classes
    ApprovalResult,
    ApprovalRequest,
    CheckpointConfig,
    # Main classes
    UserProxyAgent,
    OrchestratorWithApproval,
    ApprovalWebSocketHandler,
    # Convenience functions
    create_approval_proxy,
    create_orchestrator_with_checkpoints,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def user_proxy():
    """Create a basic UserProxyAgent"""
    return UserProxyAgent()


@pytest.fixture
def user_proxy_with_queue():
    """Create UserProxyAgent with queued responses"""
    proxy = UserProxyAgent()
    return proxy


@pytest.fixture
def checkpoint_config():
    """Create a basic CheckpointConfig"""
    return CheckpointConfig(
        enabled_checkpoints=[
            ApprovalCheckpoint.PLAN_REVIEW,
            ApprovalCheckpoint.CODE_REVIEW
        ]
    )


@pytest.fixture
def orchestrator(user_proxy_with_queue, checkpoint_config):
    """Create OrchestratorWithApproval"""
    return OrchestratorWithApproval(
        user_proxy=user_proxy_with_queue,
        checkpoint_config=checkpoint_config
    )


# =============================================================================
# ApprovalResult Tests
# =============================================================================

class TestApprovalResult:
    """Test ApprovalResult dataclass"""

    def test_is_approved(self):
        """Test is_approved property"""
        result = ApprovalResult(status=ApprovalStatus.APPROVED)
        assert result.is_approved == True
        assert result.is_rejected == False

    def test_is_rejected(self):
        """Test is_rejected property"""
        result = ApprovalResult(status=ApprovalStatus.REJECTED)
        assert result.is_rejected == True
        assert result.is_approved == False

    def test_is_rejected_on_timeout(self):
        """Test timeout counts as rejected"""
        result = ApprovalResult(status=ApprovalStatus.TIMEOUT)
        assert result.is_rejected == True

    def test_is_modified(self):
        """Test is_modified property"""
        result = ApprovalResult(
            status=ApprovalStatus.MODIFIED,
            modified_content="Updated content"
        )
        assert result.is_modified == True

    def test_reason_on_timeout(self):
        """Test reason property for timeout"""
        result = ApprovalResult(status=ApprovalStatus.TIMEOUT)
        assert "timeout" in result.reason.lower()

    def test_to_dict(self):
        """Test serialization"""
        result = ApprovalResult(
            status=ApprovalStatus.APPROVED,
            feedback="Looks good"
        )
        d = result.to_dict()
        assert d["status"] == "approved"
        assert d["feedback"] == "Looks good"


# =============================================================================
# ApprovalRequest Tests
# =============================================================================

class TestApprovalRequest:
    """Test ApprovalRequest dataclass"""

    def test_default_creation(self):
        """Test default request creation"""
        request = ApprovalRequest()
        assert request.id is not None
        assert request.checkpoint == ApprovalCheckpoint.CUSTOM
        assert "Approve" in request.options

    def test_is_expired(self):
        """Test expiration check"""
        # Not expired
        request = ApprovalRequest(
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert request.is_expired() == False

        # Expired
        request = ApprovalRequest(
            expires_at=datetime.now() - timedelta(hours=1)
        )
        assert request.is_expired() == True

        # No expiration
        request = ApprovalRequest(expires_at=None)
        assert request.is_expired() == False

    def test_to_dict(self):
        """Test serialization"""
        request = ApprovalRequest(
            checkpoint=ApprovalCheckpoint.PLAN_REVIEW,
            content="Review this plan"
        )
        d = request.to_dict()
        assert d["checkpoint"] == "plan_review"
        assert d["content"] == "Review this plan"


# =============================================================================
# CheckpointConfig Tests
# =============================================================================

class TestCheckpointConfig:
    """Test CheckpointConfig"""

    def test_is_checkpoint_enabled(self):
        """Test checkpoint enabled check"""
        config = CheckpointConfig(
            enabled_checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
        )
        assert config.is_checkpoint_enabled(ApprovalCheckpoint.PLAN_REVIEW) == True
        assert config.is_checkpoint_enabled(ApprovalCheckpoint.CODE_REVIEW) == False

    def test_enable_checkpoint(self):
        """Test enabling checkpoint"""
        config = CheckpointConfig()
        config.enable_checkpoint(ApprovalCheckpoint.PLAN_REVIEW)
        assert ApprovalCheckpoint.PLAN_REVIEW in config.enabled_checkpoints

    def test_disable_checkpoint(self):
        """Test disabling checkpoint"""
        config = CheckpointConfig(
            enabled_checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
        )
        config.disable_checkpoint(ApprovalCheckpoint.PLAN_REVIEW)
        assert ApprovalCheckpoint.PLAN_REVIEW not in config.enabled_checkpoints


# =============================================================================
# UserProxyAgent Approval Detection Tests
# =============================================================================

class TestApprovalDetection:
    """Test approval/rejection detection in UserProxyAgent"""

    def test_approval_detection_approved(self, user_proxy):
        """Test APPROVED keyword detection"""
        result = user_proxy.check_approval("APPROVED")
        assert result.is_approved == True

    def test_approval_detection_lgtm(self, user_proxy):
        """Test LGTM keyword detection"""
        result = user_proxy.check_approval("LGTM looks good")
        assert result.is_approved == True

    def test_approval_detection_proceed(self, user_proxy):
        """Test 'proceed' keyword detection"""
        result = user_proxy.check_approval("proceed with changes")
        assert result.is_approved == True

    def test_approval_detection_yes(self, user_proxy):
        """Test 'yes' keyword detection"""
        result = user_proxy.check_approval("yes, that looks fine")
        assert result.is_approved == True

    def test_rejection_detection_rejected(self, user_proxy):
        """Test REJECTED keyword detection"""
        result = user_proxy.check_approval("REJECTED")
        assert result.is_rejected == True

    def test_rejection_detection_stop(self, user_proxy):
        """Test 'stop' keyword detection"""
        result = user_proxy.check_approval("stop this")
        assert result.is_rejected == True

    def test_rejection_detection_with_reason(self, user_proxy):
        """Test rejection with reason"""
        result = user_proxy.check_approval("REJECTED - too expensive")
        assert result.is_rejected == True
        assert "expensive" in result.feedback

    def test_modification_detection(self, user_proxy):
        """Test modification keyword detection"""
        result = user_proxy.check_approval("modify: add more details")
        assert result.is_modified == True
        assert result.modified_content is not None

        # Also test other modification patterns
        result2 = user_proxy.check_approval("please change: use dark theme")
        assert result2.is_modified == True

    def test_case_insensitive(self, user_proxy):
        """Test case insensitive matching"""
        assert user_proxy.check_approval("approved").is_approved
        assert user_proxy.check_approval("APPROVED").is_approved
        assert user_proxy.check_approval("Approved").is_approved

    def test_unclear_response(self, user_proxy):
        """Test unclear response handling"""
        result = user_proxy.check_approval("maybe later")
        assert result.status == ApprovalStatus.PENDING


# =============================================================================
# UserProxyAgent Timeout Tests
# =============================================================================

class TestApprovalTimeout:
    """Test timeout handling in UserProxyAgent"""

    @pytest.mark.asyncio
    async def test_approval_timeout_default_reject(self):
        """Test timeout with default reject action"""
        proxy = UserProxyAgent(timeout_seconds=0.1, default_on_timeout="reject")

        # Don't queue any response - will timeout
        result = await proxy.get_human_input_with_timeout({})

        assert result.is_rejected == True
        assert result.status == ApprovalStatus.TIMEOUT
        assert "timeout" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_approval_timeout_auto_approve(self):
        """Test timeout with auto-approve action"""
        proxy = UserProxyAgent(timeout_seconds=0.1, default_on_timeout="approve")

        result = await proxy.get_human_input_with_timeout({})

        assert result.is_approved == True
        assert "auto-approved" in result.feedback.lower()

    @pytest.mark.asyncio
    async def test_approval_timeout_skip(self):
        """Test timeout with skip action"""
        proxy = UserProxyAgent(timeout_seconds=0.1, default_on_timeout="skip")

        result = await proxy.get_human_input_with_timeout({})

        assert result.status == ApprovalStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_response_before_timeout(self):
        """Test successful response before timeout"""
        proxy = UserProxyAgent(timeout_seconds=5)
        proxy.queue_response("APPROVED")

        result = await proxy.get_human_input_with_timeout({})

        assert result.is_approved == True


# =============================================================================
# UserProxyAgent Request/Response Tests
# =============================================================================

class TestUserProxyRequests:
    """Test UserProxyAgent request handling"""

    @pytest.mark.asyncio
    async def test_queued_responses(self):
        """Test queued response handling"""
        proxy = UserProxyAgent()
        proxy.queue_response("First response")
        proxy.queue_response("Second response")

        first = await proxy.get_human_input({})
        second = await proxy.get_human_input({})

        assert first == "First response"
        assert second == "Second response"

    @pytest.mark.asyncio
    async def test_request_approval(self):
        """Test full approval request flow"""
        proxy = UserProxyAgent(timeout_seconds=5)
        proxy.queue_response("APPROVED")

        result = await proxy.request_approval(
            checkpoint=ApprovalCheckpoint.PLAN_REVIEW,
            content="Review this plan",
            options=["Approve", "Reject"]
        )

        assert result.is_approved == True

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Test statistics tracking"""
        proxy = UserProxyAgent(timeout_seconds=5)

        proxy.queue_response("APPROVED")
        await proxy.request_approval(ApprovalCheckpoint.PLAN_REVIEW, "test")

        proxy.queue_response("REJECTED")
        await proxy.request_approval(ApprovalCheckpoint.CODE_REVIEW, "test")

        stats = proxy.get_stats()
        assert stats["total_requests"] == 2
        assert stats["approved"] == 1
        assert stats["rejected"] == 1

    def test_reset_stats(self, user_proxy):
        """Test stats reset"""
        user_proxy._stats["approved"] = 5
        user_proxy.reset_stats()
        assert user_proxy.get_stats()["approved"] == 0


# =============================================================================
# OrchestratorWithApproval Tests
# =============================================================================

class TestOrchestratorWithApproval:
    """Test OrchestratorWithApproval"""

    @pytest.mark.asyncio
    async def test_checkpoint_integration(self):
        """Test checkpoint integration"""
        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
        )

        orchestrator = OrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )

        # Mock user approval
        proxy.queue_response("APPROVED")

        result = await orchestrator.run_with_approval("Build a website")

        assert result["status"] != "cancelled"

    @pytest.mark.asyncio
    async def test_checkpoint_rejection_stops_execution(self):
        """Test that rejection stops execution"""
        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
        )

        orchestrator = OrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )

        proxy.queue_response("REJECTED - too expensive")

        result = await orchestrator.run_with_approval("Build a website")

        assert result["status"] == "cancelled"
        assert "expensive" in result["reason"]

    @pytest.mark.asyncio
    async def test_no_checkpoints_runs_directly(self):
        """Test execution without checkpoints"""
        proxy = UserProxyAgent()
        config = CheckpointConfig(enabled_checkpoints=[])

        orchestrator = OrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )

        result = await orchestrator.run_with_approval("Simple task")

        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_modification_merges_into_task(self):
        """Test that modifications are merged"""
        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
        )

        orchestrator = OrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )

        # Queue modification then approval
        proxy.queue_response("modify: add dark theme")
        proxy.queue_response("APPROVED")

        result = await orchestrator.run_with_approval("Build a website")

        # Check modification was processed
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_multiple_checkpoints(self):
        """Test multiple checkpoints in sequence"""
        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[
                ApprovalCheckpoint.PLAN_REVIEW,
                ApprovalCheckpoint.TASK_COMPLETE
            ]
        )

        orchestrator = OrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )

        # Queue responses for both checkpoints
        proxy.queue_response("APPROVED")  # Plan review
        proxy.queue_response("APPROVED")  # Task complete

        result = await orchestrator.run_with_approval("Build a website")

        assert result["status"] == "completed"
        assert len(result["checkpoints_passed"]) >= 1

    @pytest.mark.asyncio
    async def test_execution_log(self):
        """Test execution log tracking"""
        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
        )

        orchestrator = OrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )

        proxy.queue_response("APPROVED")
        await orchestrator.run_with_approval("Test task")

        log = orchestrator.get_execution_log()
        assert len(log) > 0
        assert any(entry["type"] == "checkpoint" for entry in log)

    @pytest.mark.asyncio
    async def test_callbacks(self):
        """Test checkpoint and approval callbacks"""
        checkpoint_events = []
        approval_events = []

        async def on_checkpoint(cp, ctx):
            checkpoint_events.append(cp)

        async def on_approval(result):
            approval_events.append(result)

        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
        )

        orchestrator = OrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config,
            on_checkpoint=on_checkpoint,
            on_approval=on_approval
        )

        proxy.queue_response("APPROVED")
        await orchestrator.run_with_approval("Test task")

        assert len(checkpoint_events) > 0
        assert len(approval_events) > 0


# =============================================================================
# Custom Orchestrator Tests
# =============================================================================

class MockOrchestratorWithApproval(OrchestratorWithApproval):
    """Mock orchestrator for testing"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._plan_generates_code = False
        self._plan_requires_deployment = False

    def set_plan_generates_code(self, value: bool):
        self._plan_generates_code = value

    def set_plan_requires_deployment(self, value: bool):
        self._plan_requires_deployment = value

    def _requires_code_generation(self, plan: Dict[str, Any]) -> bool:
        return self._plan_generates_code

    def _requires_deployment(self, plan: Dict[str, Any]) -> bool:
        return self._plan_requires_deployment


class TestMockOrchestrator:
    """Test mock orchestrator scenarios"""

    @pytest.mark.asyncio
    async def test_code_review_checkpoint(self):
        """Test code review checkpoint"""
        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[
                ApprovalCheckpoint.PLAN_REVIEW,
                ApprovalCheckpoint.CODE_REVIEW
            ]
        )

        orchestrator = MockOrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )
        orchestrator.set_plan_generates_code(True)

        # Queue responses for both checkpoints
        proxy.queue_response("APPROVED")  # Plan
        proxy.queue_response("APPROVED")  # Code

        result = await orchestrator.run_with_approval("Build API")

        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_deployment_checkpoint(self):
        """Test deployment approval checkpoint"""
        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[
                ApprovalCheckpoint.PLAN_REVIEW,
                ApprovalCheckpoint.DEPLOY_APPROVAL
            ]
        )

        orchestrator = MockOrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )
        orchestrator.set_plan_requires_deployment(True)

        proxy.queue_response("APPROVED")  # Plan
        proxy.queue_response("Deploy")  # Deployment

        result = await orchestrator.run_with_approval("Deploy service")

        assert result["status"] == "completed"


# =============================================================================
# WebSocket Handler Tests
# =============================================================================

class TestApprovalWebSocketHandler:
    """Test ApprovalWebSocketHandler"""

    @pytest.fixture
    def handler(self):
        return ApprovalWebSocketHandler()

    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock()
        ws.send = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, handler, mock_websocket):
        """Test WebSocket connection"""
        connection_id = await handler.connect(mock_websocket)

        assert connection_id is not None
        assert handler.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, handler, mock_websocket):
        """Test WebSocket disconnection"""
        connection_id = await handler.connect(mock_websocket)
        await handler.disconnect(connection_id)

        assert handler.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_send_notification(self, handler, mock_websocket):
        """Test sending notification"""
        await handler.connect(mock_websocket)

        request = ApprovalRequest(
            checkpoint=ApprovalCheckpoint.PLAN_REVIEW,
            content="Test content"
        )

        await handler.send_notification(request)

        # Verify send was called
        assert mock_websocket.send.called

    @pytest.mark.asyncio
    async def test_handle_approval_response(self, handler, mock_websocket):
        """Test handling approval response"""
        await handler.connect(mock_websocket)

        request = ApprovalRequest(checkpoint=ApprovalCheckpoint.PLAN_REVIEW)

        # Start request in background
        async def make_request():
            return await handler.request_input(request)

        task = asyncio.create_task(make_request())

        # Small delay to ensure request is pending
        await asyncio.sleep(0.1)

        # Simulate response
        await handler.handle_message("conn", {
            "type": "approval_response",
            "request_id": request.id,
            "response": "APPROVED"
        })

        result = await task
        assert result == "APPROVED"

    def test_register_custom_handler(self, handler):
        """Test registering custom message handler"""
        custom_handler = AsyncMock()
        handler.register_handler("custom_type", custom_handler)

        assert "custom_type" in handler._message_handlers


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_create_approval_proxy(self):
        """Test create_approval_proxy"""
        proxy, config = create_approval_proxy(
            checkpoints=[ApprovalCheckpoint.PLAN_REVIEW],
            timeout_seconds=60
        )

        assert isinstance(proxy, UserProxyAgent)
        assert isinstance(config, CheckpointConfig)
        assert ApprovalCheckpoint.PLAN_REVIEW in config.enabled_checkpoints

    def test_create_orchestrator_with_checkpoints(self):
        """Test create_orchestrator_with_checkpoints"""
        orchestrator = create_orchestrator_with_checkpoints(
            checkpoints=[ApprovalCheckpoint.PLAN_REVIEW, ApprovalCheckpoint.CODE_REVIEW],
            timeout_seconds=120
        )

        assert isinstance(orchestrator, OrchestratorWithApproval)
        assert len(orchestrator.checkpoints) == 2


# =============================================================================
# Input Mode Tests
# =============================================================================

class TestInputModes:
    """Test different input modes"""

    def test_always_mode(self):
        """Test ALWAYS input mode"""
        proxy = UserProxyAgent(input_mode="always")
        assert proxy.input_mode == InputMode.ALWAYS

    def test_approval_required_mode(self):
        """Test APPROVAL_REQUIRED input mode"""
        proxy = UserProxyAgent(input_mode="approval_required")
        assert proxy.input_mode == InputMode.APPROVAL_REQUIRED

    def test_never_mode(self):
        """Test NEVER input mode"""
        proxy = UserProxyAgent(input_mode="never")
        assert proxy.input_mode == InputMode.NEVER

    def test_enum_input(self):
        """Test enum input for mode"""
        proxy = UserProxyAgent(input_mode=InputMode.ALWAYS)
        assert proxy.input_mode == InputMode.ALWAYS


# =============================================================================
# Custom Keywords Tests
# =============================================================================

class TestCustomKeywords:
    """Test custom approval/rejection keywords"""

    def test_custom_approval_keywords(self):
        """Test custom approval keywords"""
        proxy = UserProxyAgent(
            approval_keywords=["ship it", "go for it"]
        )

        assert proxy.check_approval("ship it!").is_approved
        assert proxy.check_approval("go for it").is_approved
        # Default keywords should not work
        assert not proxy.check_approval("LGTM").is_approved

    def test_custom_rejection_keywords(self):
        """Test custom rejection keywords"""
        proxy = UserProxyAgent(
            rejection_keywords=["nope", "no way"]
        )

        assert proxy.check_approval("nope").is_rejected
        assert proxy.check_approval("no way").is_rejected


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for the full approval flow"""

    @pytest.mark.asyncio
    async def test_full_approval_workflow(self):
        """Test complete approval workflow"""
        # Create components
        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[
                ApprovalCheckpoint.PLAN_REVIEW,
                ApprovalCheckpoint.TASK_COMPLETE
            ]
        )

        orchestrator = OrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )

        # Queue all necessary responses
        proxy.queue_response("APPROVED")  # Plan review
        proxy.queue_response("Acknowledge")  # Task complete

        # Run workflow
        result = await orchestrator.run_with_approval(
            "Create a REST API for user management"
        )

        # Verify
        assert result["status"] == "completed"
        assert "REST API" in result["task"]

    @pytest.mark.asyncio
    async def test_rejection_with_retry(self):
        """Test rejection followed by retry"""
        proxy = UserProxyAgent(timeout_seconds=5)
        config = CheckpointConfig(
            enabled_checkpoints=[ApprovalCheckpoint.PLAN_REVIEW]
        )

        orchestrator = OrchestratorWithApproval(
            user_proxy=proxy,
            checkpoint_config=config
        )

        # First attempt: reject
        proxy.queue_response("REJECTED - needs more detail")

        result1 = await orchestrator.run_with_approval("Build app")
        assert result1["status"] == "cancelled"

        # Reset and retry with approval
        orchestrator.reset()
        proxy.queue_response("APPROVED")

        result2 = await orchestrator.run_with_approval("Build app with detailed spec")
        assert result2["status"] == "completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
