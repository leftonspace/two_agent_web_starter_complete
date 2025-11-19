# Tool Plugin Authoring Guide

**PHASE 2.1: Universal Tool Plugin System**

This guide explains how to create custom tool plugins for the Department-in-a-Box platform. The plugin system enables any department (HR, Finance, Legal, Engineering, etc.) to add custom tools without modifying core code.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Tool Plugin Anatomy](#tool-plugin-anatomy)
4. [Creating Your First Plugin](#creating-your-first-plugin)
5. [Advanced Features](#advanced-features)
6. [Testing Your Plugin](#testing-your-plugin)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

---

## Overview

### What is a Tool Plugin?

A tool plugin is a self-contained module that provides a specific capability to the orchestrator agents. Tools can:

- Send emails
- Query databases
- Generate documents
- Call external APIs
- Execute system commands
- Analyze data
- And much more!

### Key Features

- **Zero-code registration**: Drop a .py file in `agent/tools/{domain}/` and it's automatically discovered
- **Schema-driven**: Define JSON schemas for input/output validation
- **Permission-based**: Declare required permissions for access control
- **Type-safe**: Full type hints with Pydantic models
- **Async-first**: All tools are async for efficient IO operations
- **Cost-aware**: Report estimated costs for model routing decisions

### Architecture

```
agent/tools/
├── __init__.py
├── base.py                  # Core abstractions
├── plugin_loader.py         # Discovery and execution
├── builtin/                 # Built-in development tools
│   ├── format_code.py
│   └── run_tests.py
├── hr/                      # HR department tools
│   ├── send_email.py
│   └── query_hris.py
├── finance/                 # Finance department tools
│   └── generate_invoice.py
└── custom/                  # Your custom tools
    └── your_tool.py
```

---

## Quick Start

### 1. Create a New Tool File

Create a file in `agent/tools/custom/my_tool.py`:

```python
from agent.tools.base import (
    ToolPlugin,
    ToolManifest,
    ToolResult,
    ToolExecutionContext,
    create_success_result,
    create_error_result,
)
from typing import Any, Dict

class MyTool(ToolPlugin):
    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="my_tool",
            version="1.0.0",
            description="A simple example tool",
            domains=["custom"],
            roles=["manager", "employee"],
            required_permissions=["custom_tool_use"],
            input_schema={
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            },
            cost_estimate=0.0,
            timeout_seconds=30
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        message = params["message"]

        # Your tool logic here
        result = f"Processed: {message}"

        return create_success_result(
            {"result": result},
            processing_time_ms=50
        )
```

### 2. Test Your Tool

The tool is automatically discovered on startup. Test it:

```python
from agent.tools.plugin_loader import get_global_registry

registry = get_global_registry()
tools = registry.get_tools_for_domain("custom")
print(tools)  # Should include "my_tool"
```

### 3. Use in Orchestrator

The tool is now available to agents with the "custom" domain and required permissions.

---

## Tool Plugin Anatomy

### Required Components

Every tool plugin must:

1. **Inherit from `ToolPlugin`**
2. **Implement `get_manifest()`** - Returns tool metadata
3. **Implement `execute()`** - Performs the tool's work

### The ToolManifest

The manifest declares your tool's interface:

```python
ToolManifest(
    # Identity
    name="my_tool",                    # Unique identifier (lowercase, underscores)
    version="1.0.0",                   # Semantic version
    description="What this tool does", # For LLM context (10-500 chars)

    # Access Control
    domains=["hr", "finance"],         # Which departments can use
    roles=["manager", "employee"],     # Which roles can use
    required_permissions=["send_email"], # Required permissions

    # Schema Validation
    input_schema={...},                # JSON Schema for inputs
    output_schema={...},               # JSON Schema for outputs

    # Resource Usage
    cost_estimate=0.01,                # Estimated cost in USD
    timeout_seconds=60,                # Max execution time
    requires_network=False,            # Network access needed?
    requires_filesystem=False,         # Filesystem access needed?

    # Documentation
    examples=[...],                    # Example input/output pairs
    tags=["email", "communication"],   # Discovery tags
    author="Your Name",                # Optional
    documentation_url="https://..."    # Optional
)
```

### The Execute Method

The execute method does the actual work:

```python
async def execute(
    self,
    params: Dict[str, Any],           # Input parameters (validated)
    context: ToolExecutionContext     # Runtime context
) -> ToolResult:
    """
    Execute the tool.

    Args:
        params: Input parameters matching input_schema
        context: Runtime context with:
            - mission_id: Current mission ID
            - project_path: Project directory
            - permissions: User permissions
            - dry_run: Simulation mode flag
            - config: Configuration dict

    Returns:
        ToolResult with success status and data/error
    """
    # Your implementation here
    pass
```

---

## Creating Your First Plugin

Let's create a realistic plugin: an email sender for HR.

### Step 1: Create the File

Create `agent/tools/hr/send_email.py`:

```python
"""
HR Email Tool - Send emails via SMTP
"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict

from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
    create_error_result,
    create_success_result,
)


class SendEmailTool(ToolPlugin):
    """Send emails via SMTP for HR communications"""

    def get_manifest(self) -> ToolManifest:
        return ToolManifest(
            name="send_email",
            version="1.0.0",
            description="Send email to candidates or employees via SMTP",

            # Access control
            domains=["hr"],
            roles=["recruiter", "hr_manager", "hr_business_partner"],
            required_permissions=["email_send"],

            # Input schema
            input_schema={
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "format": "email",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200,
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Email body (plain text or HTML)"
                    },
                    "html": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether body is HTML"
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string", "format": "email"},
                        "description": "CC recipients (optional)"
                    }
                },
                "required": ["to", "subject", "body"]
            },

            # Output schema
            output_schema={
                "type": "object",
                "properties": {
                    "message_id": {"type": "string"},
                    "sent_at": {"type": "string", "format": "date-time"},
                    "recipients": {"type": "array", "items": {"type": "string"}}
                }
            },

            # Resource usage
            cost_estimate=0.001,  # $0.001 per email
            timeout_seconds=30,
            requires_network=True,

            # Documentation
            examples=[
                {
                    "input": {
                        "to": "candidate@example.com",
                        "subject": "Interview Invitation",
                        "body": "We'd like to invite you for an interview...",
                        "html": False
                    },
                    "output": {
                        "message_id": "msg_123abc",
                        "sent_at": "2025-01-19T12:00:00Z",
                        "recipients": ["candidate@example.com"]
                    }
                }
            ],
            tags=["email", "communication", "hr", "recruiting"],
            author="HR Team",
            documentation_url="https://docs.example.com/hr/email"
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Send email via SMTP"""

        # Extract parameters
        to = params["to"]
        subject = params["subject"]
        body = params["body"]
        html = params.get("html", False)
        cc = params.get("cc", [])

        # Dry run mode - simulate without sending
        if context.dry_run:
            return create_success_result(
                {
                    "message_id": "dry_run_msg_123",
                    "sent_at": "2025-01-19T12:00:00Z",
                    "recipients": [to] + cc
                },
                dry_run=True,
                simulated=True
            )

        # Get SMTP settings from config
        smtp_host = context.config.get("smtp_host", "smtp.gmail.com")
        smtp_port = context.config.get("smtp_port", 587)
        smtp_user = context.config.get("smtp_user")
        smtp_password = context.config.get("smtp_password")

        if not smtp_user or not smtp_password:
            return create_error_result(
                "SMTP credentials not configured",
                required_config=["smtp_user", "smtp_password"]
            )

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = to
            if cc:
                msg["Cc"] = ", ".join(cc)

            # Attach body
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Send via SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)

                recipients = [to] + cc
                server.sendmail(smtp_user, recipients, msg.as_string())

            # Success!
            from datetime import datetime
            return create_success_result(
                {
                    "message_id": msg["Message-ID"] or "unknown",
                    "sent_at": datetime.utcnow().isoformat() + "Z",
                    "recipients": recipients
                },
                smtp_host=smtp_host,
                smtp_port=smtp_port
            )

        except smtplib.SMTPAuthenticationError:
            return create_error_result(
                "SMTP authentication failed - check credentials",
                smtp_host=smtp_host,
                smtp_user=smtp_user
            )
        except smtplib.SMTPException as e:
            return create_error_result(
                f"SMTP error: {str(e)}",
                smtp_host=smtp_host,
                exception_type=type(e).__name__
            )
        except Exception as e:
            return create_error_result(
                f"Failed to send email: {str(e)}",
                exception_type=type(e).__name__
            )
```

### Step 2: Configure SMTP Settings

Add to `agent/config.py` or project config:

```python
config = {
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your-email@gmail.com",
    "smtp_password": "your-app-password"
}
```

### Step 3: Test the Tool

```python
import asyncio
from pathlib import Path
from agent.tools.plugin_loader import get_global_registry
from agent.tools.base import ToolExecutionContext

async def test_email():
    registry = get_global_registry()

    context = ToolExecutionContext(
        mission_id="test_001",
        project_path=Path("/tmp/test"),
        permissions=["email_send"],
        config={
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "test@example.com",
            "smtp_password": "password"
        }
    )

    result = await registry.execute_tool(
        "send_email",
        {
            "to": "candidate@example.com",
            "subject": "Test Email",
            "body": "This is a test email"
        },
        context
    )

    print(f"Success: {result.success}")
    print(f"Data: {result.data}")
    print(f"Error: {result.error}")

asyncio.run(test_email())
```

---

## Advanced Features

### 1. Async Operations

All tools are async by default. Use `await` for IO operations:

```python
async def execute(self, params, context):
    # Async HTTP request
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    # Async file IO
    async with aiofiles.open(file_path, 'r') as f:
        content = await f.read()

    return create_success_result(data)
```

### 2. Permission Checking

The registry enforces permissions automatically, but you can also check manually:

```python
async def execute(self, params, context):
    # Check if user has admin permission
    if not context.has_permission("admin"):
        return create_error_result(
            "Admin permission required",
            required_permission="admin",
            user_permissions=context.permissions
        )

    # ... proceed with admin operation
```

### 3. Path Validation

Validate paths are within the project directory:

```python
async def execute(self, params, context):
    file_path = Path(params["file_path"])

    if not context.validate_path(file_path):
        return create_error_result(
            f"Path outside project directory: {file_path}",
            project_path=str(context.project_path)
        )

    # Safe to use file_path
```

### 4. Dry Run Mode

Support simulation mode for testing:

```python
async def execute(self, params, context):
    if context.dry_run:
        return create_success_result(
            {"simulated": True, "would_process": params["items"]},
            dry_run=True
        )

    # Actual execution
    result = process_items(params["items"])
    return create_success_result(result)
```

### 5. Cost Tracking

Report actual costs in metadata:

```python
async def execute(self, params, context):
    # Execute expensive operation
    result = call_paid_api(params)

    return create_success_result(
        result,
        actual_cost_usd=0.05,
        api_calls=10
    )
```

---

## Testing Your Plugin

### Unit Test Template

Create `agent/tests/unit/test_my_tool.py`:

```python
import pytest
from pathlib import Path
from agent.tools.base import ToolExecutionContext
from agent.tools.hr.send_email import SendEmailTool

@pytest.fixture
def mock_context():
    return ToolExecutionContext(
        mission_id="test_mission",
        project_path=Path("/tmp/test"),
        permissions=["email_send"],
        config={
            "smtp_host": "localhost",
            "smtp_user": "test@test.com",
            "smtp_password": "test123"
        }
    )

@pytest.mark.anyio
async def test_send_email_dry_run(mock_context):
    """Test email sending in dry run mode"""
    tool = SendEmailTool()
    mock_context.dry_run = True

    result = await tool.execute(
        {
            "to": "test@example.com",
            "subject": "Test",
            "body": "Test body"
        },
        mock_context
    )

    assert result.success is True
    assert result.metadata.get("dry_run") is True

@pytest.mark.anyio
async def test_send_email_missing_params(mock_context):
    """Test parameter validation"""
    tool = SendEmailTool()

    # Missing required "body" parameter
    is_valid, error = tool.validate_params({
        "to": "test@example.com",
        "subject": "Test"
    })

    assert is_valid is False
    assert "body" in error.lower()
```

### Integration Test

```python
from agent.tools.plugin_loader import get_global_registry

def test_tool_discovery():
    """Test that tool is discovered by registry"""
    registry = get_global_registry()

    # Tool should be registered
    tool = registry.get_tool("send_email")
    assert tool is not None

    # Should be available for HR domain
    hr_tools = registry.get_tools_for_domain("hr")
    assert "send_email" in hr_tools
```

---

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def execute(self, params, context):
    try:
        result = await risky_operation()
        return create_success_result(result)
    except SpecificError as e:
        return create_error_result(
            f"Specific error occurred: {e}",
            error_type="specific_error"
        )
    except Exception as e:
        return create_error_result(
            f"Unexpected error: {e}",
            exception_type=type(e).__name__
        )
```

### 2. Input Validation

Use JSON Schema for validation:

```python
input_schema={
    "type": "object",
    "properties": {
        "email": {
            "type": "string",
            "format": "email",
            "description": "Must be valid email"
        },
        "age": {
            "type": "integer",
            "minimum": 0,
            "maximum": 150
        },
        "status": {
            "type": "string",
            "enum": ["active", "inactive", "pending"]
        }
    },
    "required": ["email", "status"]
}
```

### 3. Descriptive Metadata

Add rich metadata to results:

```python
return create_success_result(
    {"user_id": 123, "created": True},
    duration_ms=250,
    database_queries=3,
    cache_hit=False,
    api_version="v2"
)
```

### 4. Documentation

Include clear examples:

```python
examples=[
    {
        "description": "Create new user",
        "input": {
            "name": "John Doe",
            "email": "john@example.com",
            "role": "employee"
        },
        "output": {
            "user_id": 12345,
            "created_at": "2025-01-19T12:00:00Z"
        }
    },
    {
        "description": "Update existing user",
        "input": {
            "user_id": 12345,
            "name": "John Smith"
        },
        "output": {
            "updated": True,
            "updated_at": "2025-01-19T12:30:00Z"
        }
    }
]
```

### 5. Security

- Validate all inputs
- Sanitize outputs
- Never log sensitive data
- Use permissions appropriately
- Validate file paths

```python
# Bad: Direct user input
command = f"rm -rf {params['directory']}"

# Good: Validated and sanitized
directory = Path(params['directory'])
if not context.validate_path(directory):
    return create_error_result("Invalid path")
if not directory.exists():
    return create_error_result("Directory not found")
```

---

## Examples

### Simple Tool: Echo

```python
class EchoTool(ToolPlugin):
    def get_manifest(self):
        return ToolManifest(
            name="echo",
            version="1.0.0",
            description="Echo back the input message",
            domains=["testing"],
            roles=["any"],
            required_permissions=[],
            input_schema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"]
            },
            output_schema={},
            timeout_seconds=5
        )

    async def execute(self, params, context):
        return create_success_result(
            {"echo": params["message"]}
        )
```

### Database Query Tool

```python
class QueryDatabaseTool(ToolPlugin):
    def get_manifest(self):
        return ToolManifest(
            name="query_database",
            version="1.0.0",
            description="Execute SQL query on database",
            domains=["data", "analytics"],
            roles=["analyst", "engineer"],
            required_permissions=["database_read"],
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "params": {"type": "array"}
                },
                "required": ["query"]
            },
            output_schema={},
            timeout_seconds=60,
            requires_network=True
        )

    async def execute(self, params, context):
        import asyncpg

        conn = await asyncpg.connect(
            context.config["database_url"]
        )

        try:
            rows = await conn.fetch(
                params["query"],
                *params.get("params", [])
            )

            result = [dict(row) for row in rows]

            return create_success_result(
                {"rows": result, "count": len(result)},
                query_time_ms=123
            )
        finally:
            await conn.close()
```

---

## Next Steps

1. **Create your first plugin** following the Quick Start
2. **Test thoroughly** with unit and integration tests
3. **Add to documentation** by updating this guide with your examples
4. **Share with the community** by contributing to the plugin library

For more information, see:
- [Developer Guide](DEVELOPER_GUIDE.md)
- [Architecture Documentation](DEPENDENCY_INJECTION.md)
- [API Reference](agent/tools/base.py)

---

**Questions or Issues?**
File an issue at: https://github.com/your-repo/issues
