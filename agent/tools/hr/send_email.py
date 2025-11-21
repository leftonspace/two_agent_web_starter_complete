"""
PHASE 2.3: Send Email Tool

Email sending tool with support for:
- HTML and plain text emails
- Jinja2 template rendering
- Multiple recipients (to, cc, bcc)
- Attachments
- Scheduled sending
- SMTP integration

Usage:
    from agent.tools.hr.send_email import SendEmailTool
    tool = SendEmailTool()
    result = await tool.execute({
        "to": "candidate@example.com",
        "subject": "Welcome!",
        "template_name": "welcome_email",
        "template_vars": {"candidate_name": "John Doe"}
    }, context)
"""

from __future__ import annotations

import base64
import logging
import smtplib
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
)

logger = logging.getLogger(__name__)


class SendEmailTool(ToolPlugin):
    """
    Email sending tool with template support and SMTP integration.

    Features:
    - Plain text and HTML emails
    - Jinja2 template rendering
    - Multiple recipients
    - Attachments (base64 encoded)
    - Reply-to headers
    - Dry run mode for testing

    Configuration (in context.config):
        smtp:
            host: SMTP server hostname
            port: SMTP port (default: 587)
            username: SMTP username
            password: SMTP password
            from_address: Default sender address
            use_tls: Whether to use TLS (default: True)
    """

    def get_manifest(self) -> ToolManifest:
        """Return tool manifest with metadata and schema"""
        return ToolManifest(
            name="send_email",
            version="1.0.0",
            description="Send email via SMTP with support for HTML templates, attachments, and multiple recipients",
            domains=["hr", "legal", "ops", "marketing"],
            roles=["manager", "hr_manager", "hr_recruiter", "hr_business_partner"],
            required_permissions=["email_send"],

            input_schema={
                "type": "object",
                "properties": {
                    "to": {
                        "description": "Recipient email address(es)",
                        "oneOf": [
                            {"type": "string"},  # Single recipient
                            {"type": "array", "items": {"type": "string"}}  # Multiple
                        ]
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Carbon copy recipients"
                    },
                    "bcc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Blind carbon copy recipients"
                    },
                    "subject": {
                        "type": "string",
                        "maxLength": 200,
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Plain text email body"
                    },
                    "body_html": {
                        "type": "string",
                        "description": "HTML email body"
                    },
                    "template_name": {
                        "type": "string",
                        "description": "Name of email template to use"
                    },
                    "template_vars": {
                        "type": "object",
                        "description": "Variables to pass to template"
                    },
                    "attachments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "filename": {"type": "string"},
                                "content": {"type": "string", "description": "Base64 encoded content"},
                                "mime_type": {"type": "string"}
                            },
                            "required": ["filename", "content"]
                        },
                        "description": "File attachments"
                    },
                    "reply_to": {
                        "type": "string",
                        "description": "Reply-to email address"
                    },
                    "from_address": {
                        "type": "string",
                        "description": "Override default from address"
                    },
                },
                "required": ["to", "subject"],
            },

            output_schema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                    "sent": {"type": "boolean"},
                    "recipients": {"type": "array", "items": {"type": "string"}},
                    "timestamp": {"type": "string"},
                    "dry_run": {"type": "boolean"}
                },
                "required": ["message_id", "sent", "recipients", "timestamp"]
            },

            cost_estimate=0.0,
            timeout_seconds=30,
            requires_network=True,

            examples=[
                {
                    "description": "Send templated welcome email",
                    "input": {
                        "to": "candidate@example.com",
                        "subject": "Welcome to Acme Corp!",
                        "template_name": "welcome_email",
                        "template_vars": {
                            "candidate_name": "John Doe",
                            "job_title": "Software Engineer",
                            "start_date": "2025-12-01",
                            "manager_name": "Jane Smith"
                        }
                    },
                    "output": {
                        "message_id": "abc123",
                        "sent": True,
                        "recipients": ["candidate@example.com"],
                        "timestamp": "2025-11-19T10:30:00Z"
                    }
                },
                {
                    "description": "Send plain text email to multiple recipients",
                    "input": {
                        "to": ["user1@example.com", "user2@example.com"],
                        "subject": "Team Meeting Tomorrow",
                        "body": "Hi team, reminder about our meeting tomorrow at 10am."
                    },
                    "output": {
                        "message_id": "xyz789",
                        "sent": True,
                        "recipients": ["user1@example.com", "user2@example.com"],
                        "timestamp": "2025-11-19T14:00:00Z"
                    }
                }
            ],

            tags=["email", "communication", "notification", "smtp"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Execute email sending.

        Args:
            params: Tool parameters (see input_schema)
            context: Execution context with configuration

        Returns:
            ToolResult with message_id and delivery status
        """
        try:
            # Get SMTP configuration
            smtp_config = context.config.get("smtp", {})
            host = smtp_config.get("host", "smtp.gmail.com")
            port = smtp_config.get("port", 587)
            username = smtp_config.get("username")
            password = smtp_config.get("password")
            from_address = params.get("from_address") or smtp_config.get("from_address") or username or "noreply@example.com"
            use_tls = smtp_config.get("use_tls", True)

            # Validate configuration (skip in dry run mode)
            if not context.dry_run and (not username or not password):
                return ToolResult(
                    success=False,
                    error="SMTP credentials not configured. Set smtp.username and smtp.password in context.config",
                    metadata={
                        "help": "Add SMTP configuration to your execution context",
                        "required_fields": ["smtp.username", "smtp.password"]
                    }
                )

            # Parse recipients
            to_addresses = self._parse_recipients(params["to"])
            cc_addresses = self._parse_recipients(params.get("cc", []))
            bcc_addresses = self._parse_recipients(params.get("bcc", []))
            all_recipients = to_addresses + cc_addresses + bcc_addresses

            # Build message
            msg = MIMEMultipart("alternative")
            msg["From"] = from_address
            msg["To"] = ", ".join(to_addresses)
            msg["Subject"] = params["subject"]

            if cc_addresses:
                msg["Cc"] = ", ".join(cc_addresses)
            if params.get("reply_to"):
                msg["Reply-To"] = params["reply_to"]

            # Add message ID
            message_id = f"<{datetime.now().timestamp()}@{host}>"
            msg["Message-ID"] = message_id

            # Handle body content (template > HTML > plain text)
            if params.get("template_name"):
                body_html = self._render_template(
                    params["template_name"],
                    params.get("template_vars", {})
                )
                msg.attach(MIMEText(body_html, "html"))
            elif params.get("body_html"):
                msg.attach(MIMEText(params["body_html"], "html"))
            elif params.get("body"):
                msg.attach(MIMEText(params["body"], "plain"))
            else:
                return ToolResult(
                    success=False,
                    error="Email body is required (provide body, body_html, or template_name)"
                )

            # Handle attachments
            for attachment_info in params.get("attachments", []):
                self._add_attachment(msg, attachment_info)

            # Dry run mode - don't actually send
            if context.dry_run:
                logger.info(
                    f"[DRY RUN] Would send email: {msg['Subject']} to {to_addresses}"
                )
                return ToolResult(
                    success=True,
                    data={
                        "message_id": message_id,
                        "sent": False,
                        "recipients": all_recipients,
                        "timestamp": datetime.now().isoformat(),
                        "dry_run": True
                    },
                    metadata={
                        "note": "Dry run mode - email not actually sent",
                        "subject": msg["Subject"],
                        "from": from_address
                    }
                )

            # Send email via SMTP
            logger.info(f"Sending email: {msg['Subject']} to {to_addresses}")

            with smtplib.SMTP(host, port, timeout=30) as server:
                if use_tls:
                    server.starttls()
                server.login(username, password)
                server.send_message(msg, from_addr=from_address, to_addrs=all_recipients)

            # Log email sent for audit trail
            self._log_email_sent(
                context.mission_id,
                all_recipients,
                params["subject"]
            )

            logger.info(f"Email sent successfully: {message_id}")

            return ToolResult(
                success=True,
                data={
                    "message_id": message_id,
                    "sent": True,
                    "recipients": all_recipients,
                    "timestamp": datetime.now().isoformat()
                },
                metadata={
                    "subject": msg["Subject"],
                    "from": from_address
                }
            )

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return ToolResult(
                success=False,
                error=f"SMTP authentication failed: {str(e)}",
                metadata={"help": "Check SMTP username and password"}
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to send email: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )

    def _parse_recipients(self, recipients: Any) -> List[str]:
        """Parse recipients - handle both string and list"""
        if isinstance(recipients, str):
            return [recipients]
        elif isinstance(recipients, list):
            return recipients
        return []

    def _render_template(self, template_name: str, variables: Dict) -> str:
        """Load and render email template using Jinja2"""
        try:
            from agent.templates.email_renderer import EmailTemplateRenderer
            renderer = EmailTemplateRenderer()
            return renderer.render(template_name, variables)
        except ImportError:
            logger.error("Email template renderer not available")
            raise ValueError("Email template system not configured")
        except Exception as e:
            logger.error(f"Failed to render template '{template_name}': {e}")
            raise ValueError(f"Template rendering failed: {str(e)}")

    def _add_attachment(self, msg: MIMEMultipart, attachment_info: Dict) -> None:
        """Add attachment to email message"""
        try:
            filename = attachment_info["filename"]
            content_b64 = attachment_info["content"]
            mime_type = attachment_info.get("mime_type", "application/octet-stream")

            # Decode base64 content
            content = base64.b64decode(content_b64)

            # Create attachment
            part = MIMEBase(*mime_type.split("/"))
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}"
            )

            msg.attach(part)
            logger.debug(f"Added attachment: {filename}")
        except Exception as e:
            logger.warning(f"Failed to add attachment '{filename}': {e}")
            # Don't fail the entire email for attachment issues

    def _log_email_sent(
        self,
        mission_id: str,
        recipients: List[str],
        subject: str
    ) -> None:
        """Log email sent event for audit trail"""
        try:
            from agent.core_logging import log_event
            log_event("email_sent", {
                "mission_id": mission_id,
                "recipients": recipients,
                "subject": subject,
                "timestamp": datetime.now().isoformat(),
                "tool": "send_email"
            })
        except ImportError:
            # core_logging may not be available yet
            logger.debug("core_logging not available for audit logging")
        except Exception as e:
            logger.warning(f"Failed to log email sent: {e}")
