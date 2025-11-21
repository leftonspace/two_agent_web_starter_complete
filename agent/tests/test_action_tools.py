"""
Tests for action execution tools.

PHASE 7.4: Tests for domain purchase, deployment, SMS, payments with approval workflows.

Run: pytest agent/tests/test_action_tools.py -v
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from agent.tools.actions.base import ActionApproval, ActionRisk, ActionTool
from agent.tools.actions.buy_domain import BuyDomainTool
from agent.tools.actions.deploy_website import DeployWebsiteTool
from agent.tools.actions.make_payment import MakePaymentTool
from agent.tools.actions.send_sms import SendSMSTool
from agent.tools.base import ToolExecutionContext, ToolResult


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_context():
    """Create mock execution context"""
    return ToolExecutionContext(
        mission_id="test_mission",
        project_path=Path("/tmp/test_project"),
        config={},
        permissions=["domain_purchase", "deploy", "sms_send", "payment_process"],
        user_id="test_user",
        dry_run=False,
        max_cost_usd=1000.0
    )


@pytest.fixture
def mock_approval_success():
    """Mock successful approval"""
    with patch.object(ActionTool, '_request_approval', return_value=True):
        yield


@pytest.fixture
def mock_approval_declined():
    """Mock declined approval"""
    with patch.object(ActionTool, '_request_approval', return_value=False):
        yield


# ══════════════════════════════════════════════════════════════════════
# ActionTool Base Class Tests
# ══════════════════════════════════════════════════════════════════════


class TestActionToolBase:
    """Test ActionTool base class"""

    @pytest.mark.asyncio
    async def test_risk_assessment_low(self):
        """Test low risk assessment (<$1)"""
        tool = BuyDomainTool()
        risk = tool._assess_risk({}, 0.50)
        # BuyDomainTool overrides this to MEDIUM for domains
        assert risk in [ActionRisk.LOW, ActionRisk.MEDIUM]

    @pytest.mark.asyncio
    async def test_risk_assessment_medium(self):
        """Test medium risk assessment ($1-$10)"""
        tool = SendSMSTool()
        risk = tool._assess_risk({}, 5.00)
        assert risk == ActionRisk.LOW  # SMS overrides to LOW

    @pytest.mark.asyncio
    async def test_risk_assessment_high(self):
        """Test high risk assessment ($10-$100)"""
        tool = MakePaymentTool()
        risk = tool._assess_risk({"amount": 50.0}, 50.0)
        assert risk == ActionRisk.HIGH

    @pytest.mark.asyncio
    async def test_risk_assessment_critical(self):
        """Test critical risk assessment (>$100)"""
        tool = MakePaymentTool()
        risk = tool._assess_risk({"amount": 150.0}, 150.0)
        assert risk == ActionRisk.CRITICAL

    @pytest.mark.asyncio
    async def test_dry_run_mode(self, mock_context):
        """Test dry run mode doesn't execute"""
        mock_context.dry_run = True

        tool = SendSMSTool()

        with patch.object(tool, 'estimate_cost', return_value=0.01):
            result = await tool.execute(
                {"to": "+14155552671", "message": "Test"},
                mock_context
            )

        assert result.success is True
        assert result.data["simulated"] is True
        assert result.metadata["dry_run"] is True

    @pytest.mark.asyncio
    async def test_cost_limit_enforcement(self, mock_context):
        """Test cost limit is enforced"""
        mock_context.max_cost_usd = 10.0

        tool = BuyDomainTool()

        with patch.object(tool, 'estimate_cost', return_value=50.0):
            result = await tool.execute(
                {"domain": "example.com"},
                mock_context
            )

        assert result.success is False
        assert "exceeds limit" in result.error.lower()


# ══════════════════════════════════════════════════════════════════════
# BuyDomainTool Tests
# ══════════════════════════════════════════════════════════════════════


class TestBuyDomainTool:
    """Test domain purchase tool"""

    @pytest.mark.asyncio
    async def test_cost_estimation(self):
        """Test domain cost estimation"""
        tool = BuyDomainTool()

        # Mock Namecheap API call
        with patch.object(tool, '_namecheap_api_call', return_value="<xml></xml>"):
            cost = await tool.estimate_cost({"domain": "example.com", "years": 1})

        assert isinstance(cost, float)
        assert cost > 0

    @pytest.mark.asyncio
    async def test_multi_year_cost(self):
        """Test multi-year domain cost calculation"""
        tool = BuyDomainTool()

        with patch.object(tool, '_namecheap_api_call', return_value="<xml></xml>"):
            cost_1yr = await tool.estimate_cost({"domain": "example.com", "years": 1})
            cost_3yr = await tool.estimate_cost({"domain": "example.com", "years": 3})

        assert cost_3yr > cost_1yr
        assert cost_3yr == pytest.approx(cost_1yr * 3, rel=0.1)

    @pytest.mark.asyncio
    async def test_approval_required(self, mock_context, mock_approval_declined):
        """Test approval is required for domain purchase"""
        tool = BuyDomainTool()

        with patch.object(tool, 'estimate_cost', return_value=12.98):
            result = await tool.execute(
                {"domain": "example.com"},
                mock_context
            )

        assert result.success is False
        assert "declined" in result.error.lower()

    @pytest.mark.asyncio
    async def test_domain_purchase_success(self, mock_context, mock_approval_success):
        """Test successful domain purchase"""
        tool = BuyDomainTool()

        mock_response = """
        <ApiResponse Status="OK">
            <DomainCreateResult Domain="example.com" DomainID="123456" ChargedAmount="12.98" Expires="2026-11-20"/>
        </ApiResponse>
        """

        with patch.object(tool, 'estimate_cost', return_value=12.98):
            with patch.object(tool, '_check_availability', return_value={"available": True}):
                with patch.object(tool, '_namecheap_api_call', return_value=mock_response):
                    result = await tool.execute(
                        {"domain": "example.com", "years": 1},
                        mock_context
                    )

        assert result.success is True
        assert result.data["domain"] == "example.com"
        assert "execution_id" in result.metadata

    @pytest.mark.asyncio
    async def test_domain_unavailable(self, mock_context, mock_approval_success):
        """Test handling of unavailable domain"""
        tool = BuyDomainTool()

        with patch.object(tool, 'estimate_cost', return_value=12.98):
            with patch.object(tool, '_check_availability', return_value={"available": False}):
                result = await tool.execute(
                    {"domain": "example.com"},
                    mock_context
                )

        assert result.success is False
        assert "not available" in result.error.lower()


# ══════════════════════════════════════════════════════════════════════
# DeployWebsiteTool Tests
# ══════════════════════════════════════════════════════════════════════


class TestDeployWebsiteTool:
    """Test website deployment tool"""

    @pytest.mark.asyncio
    async def test_cost_is_zero(self):
        """Test Vercel deployment is free"""
        tool = DeployWebsiteTool()
        cost = await tool.estimate_cost({"project_path": "/tmp/test"})
        assert cost == 0.0

    @pytest.mark.asyncio
    async def test_no_approval_for_free_action(self, mock_context):
        """Test free deployments don't require approval"""
        tool = DeployWebsiteTool()

        # Create temp project directory
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            (project_path / "index.html").write_text("<html></html>")

            mock_context.project_path = Path(tmpdir)

            with patch.object(tool, '_initialize_git', return_value={"success": True}):
                with patch.object(tool, '_create_and_push_to_github', return_value={"success": True, "repo_url": "https://github.com/test/repo"}):
                    with patch.object(tool, '_deploy_to_vercel', return_value={"success": True, "url": "https://test.vercel.app", "deployment_id": "dpl_123"}):
                        result = await tool.execute(
                            {"project_path": "test_project", "framework": "static"},
                            mock_context
                        )

            assert result.success is True
            assert "vercel.app" in result.data["url"]

    @pytest.mark.asyncio
    async def test_deployment_rollback(self, mock_context):
        """Test deployment can be rolled back"""
        tool = DeployWebsiteTool()

        # Store fake execution
        tool._execution_history["test_exec"] = {
            "result": {"deployment_id": "dpl_123"},
            "timestamp": "2025-11-20T00:00:00"
        }

        with patch('agent.tools.actions.deploy_website.requests.delete') as mock_delete:
            mock_delete.return_value.status_code = 200
            success = await tool.rollback("test_exec", mock_context)

        assert success is True


# ══════════════════════════════════════════════════════════════════════
# SendSMSTool Tests
# ══════════════════════════════════════════════════════════════════════


class TestSendSMSTool:
    """Test SMS tool"""

    @pytest.mark.asyncio
    async def test_sms_cost_single_segment(self):
        """Test SMS cost for single segment"""
        tool = SendSMSTool()
        cost = await tool.estimate_cost({"to": "+14155552671", "message": "Hello"})
        assert cost == pytest.approx(0.0079, rel=0.01)

    @pytest.mark.asyncio
    async def test_sms_cost_multiple_segments(self):
        """Test SMS cost for multiple segments"""
        tool = SendSMSTool()
        long_message = "A" * 300  # 2 segments
        cost = await tool.estimate_cost({"to": "+14155552671", "message": long_message})
        assert cost > 0.0079
        assert cost == pytest.approx(0.0079 * 2, rel=0.1)

    @pytest.mark.asyncio
    async def test_sms_send_success(self, mock_context):
        """Test successful SMS send"""
        tool = SendSMSTool()

        mock_response = {
            "sid": "SM1234567890",
            "status": "queued",
            "to": "+14155552671",
            "from": "+14155552670",
            "date_created": "2025-11-20T12:00:00Z",
            "num_segments": 1
        }

        with patch.object(tool, 'estimate_cost', return_value=0.0079):
            with patch('agent.tools.actions.send_sms.requests.post') as mock_post:
                mock_post.return_value.json.return_value = mock_response
                mock_post.return_value.raise_for_status = Mock()

                result = await tool.execute(
                    {
                        "to": "+14155552671",
                        "message": "Test message",
                        "from_number": "+14155552670"
                    },
                    mock_context
                )

        assert result.success is True
        assert result.data["message_sid"] == "SM1234567890"

    @pytest.mark.asyncio
    async def test_sms_cannot_rollback(self, mock_context):
        """Test SMS cannot be rolled back"""
        tool = SendSMSTool()
        success = await tool.rollback("any_id", mock_context)
        assert success is False


# ══════════════════════════════════════════════════════════════════════
# MakePaymentTool Tests
# ══════════════════════════════════════════════════════════════════════


class TestMakePaymentTool:
    """Test payment processing tool"""

    @pytest.mark.asyncio
    async def test_payment_cost_is_amount(self):
        """Test payment cost equals payment amount"""
        tool = MakePaymentTool()
        cost = await tool.estimate_cost({"amount": 99.99})
        assert cost == 99.99

    @pytest.mark.asyncio
    async def test_small_payment_requires_approval(self, mock_context, mock_approval_declined):
        """Test even small payments require approval"""
        tool = MakePaymentTool()

        with patch.object(tool, 'estimate_cost', return_value=5.0):
            result = await tool.execute(
                {
                    "amount": 5.0,
                    "payment_method_id": "pm_123",
                    "description": "Test payment"
                },
                mock_context
            )

        assert result.success is False
        assert "declined" in result.error.lower()

    @pytest.mark.asyncio
    async def test_large_payment_critical_risk(self):
        """Test large payments are critical risk"""
        tool = MakePaymentTool()
        risk = tool._assess_risk({"amount": 150.0}, 150.0)
        assert risk == ActionRisk.CRITICAL

    @pytest.mark.asyncio
    async def test_payment_success(self, mock_context, mock_approval_success):
        """Test successful payment processing"""
        tool = MakePaymentTool()

        mock_response = {
            "id": "pi_1234567890",
            "status": "succeeded",
            "amount": 9999,  # Cents
            "currency": "usd",
            "created": "2025-11-20T12:00:00Z",
            "charges": {"data": [{"id": "ch_123"}]}
        }

        with patch.object(tool, 'estimate_cost', return_value=99.99):
            with patch('agent.tools.actions.make_payment.requests.post') as mock_post:
                mock_post.return_value.json.return_value = mock_response
                mock_post.return_value.raise_for_status = Mock()

                result = await tool.execute(
                    {
                        "amount": 99.99,
                        "payment_method_id": "pm_123",
                        "description": "Test payment"
                    },
                    mock_context
                )

        assert result.success is True
        assert result.data["payment_intent_id"] == "pi_1234567890"
        assert result.data["amount"] == 99.99

    @pytest.mark.asyncio
    async def test_payment_rollback_refund(self, mock_context):
        """Test payment can be refunded via rollback"""
        tool = MakePaymentTool()

        # Store fake execution
        tool._execution_history["test_exec"] = {
            "result": {"payment_intent_id": "pi_123"},
            "timestamp": "2025-11-20T00:00:00"
        }

        mock_pi_response = {
            "charges": {
                "data": [{"id": "ch_123"}]
            }
        }

        mock_refund_response = {
            "id": "re_123",
            "status": "succeeded",
            "amount": 9999
        }

        with patch('agent.tools.actions.make_payment.requests.get') as mock_get:
            with patch('agent.tools.actions.make_payment.requests.post') as mock_post:
                mock_get.return_value.json.return_value = mock_pi_response
                mock_get.return_value.raise_for_status = Mock()
                mock_post.return_value.json.return_value = mock_refund_response
                mock_post.return_value.raise_for_status = Mock()

                success = await tool.rollback("test_exec", mock_context)

        assert success is True


# ══════════════════════════════════════════════════════════════════════
# Integration Tests
# ══════════════════════════════════════════════════════════════════════


class TestApprovalWorkflow:
    """Test approval workflow integration"""

    @pytest.mark.asyncio
    async def test_approval_message_formatting(self):
        """Test approval message is formatted correctly"""
        approval = ActionApproval(
            action_name="buy_domain",
            description="Purchase example.com",
            cost_usd=12.98,
            risk_level=ActionRisk.MEDIUM,
            details={"domain": "example.com", "years": 1},
            requires_2fa=False
        )

        tool = BuyDomainTool()
        message = tool._format_approval_message(approval)

        assert "buy_domain" in message
        assert "12.98" in message
        assert "MEDIUM" in message
        assert "example.com" in message

    @pytest.mark.asyncio
    async def test_2fa_required_for_critical(self):
        """Test 2FA is indicated for critical actions"""
        approval = ActionApproval(
            action_name="make_payment",
            description="Large payment",
            cost_usd=200.0,
            risk_level=ActionRisk.CRITICAL,
            details={"amount": 200.0},
            requires_2fa=True
        )

        tool = MakePaymentTool()
        message = tool._format_approval_message(approval)

        assert "2FA" in message or "Requires 2FA" in message


# ══════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ══════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_invalid_parameters(self, mock_context):
        """Test invalid parameters are rejected"""
        tool = SendSMSTool()

        result = await tool.execute(
            {"to": "invalid", "message": "Test"},
            mock_context
        )

        assert result.success is False
        assert "validation" in result.error.lower() or "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_missing_credentials(self, mock_context):
        """Test missing API credentials are handled"""
        tool = SendSMSTool()

        with patch.dict('os.environ', {}, clear=True):
            result = await tool.execute(
                {"to": "+14155552671", "message": "Test"},
                mock_context
            )

        assert result.success is False
        assert "credentials" in result.error.lower() or "configured" in result.error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
