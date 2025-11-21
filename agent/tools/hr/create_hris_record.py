"""
PHASE 2.3: Create HRIS Record Tool

HRIS (Human Resource Information System) integration tool with support for:
- BambooHR API
- Workday API
- Generic HTTP-based HRIS systems
- Employee onboarding data
- Validation and error handling

Usage:
    from agent.tools.hr.create_hris_record import CreateHRISRecordTool
    tool = CreateHRISRecordTool()
    result = await tool.execute({
        "system": "bamboohr",
        "employee_data": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "start_date": "2025-12-01"
        }
    }, context)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
)

logger = logging.getLogger(__name__)


class CreateHRISRecordTool(ToolPlugin):
    """
    Create employee records in HRIS systems (BambooHR, Workday, custom).

    Features:
    - BambooHR API integration
    - Workday API integration (stub)
    - Generic HTTP API support
    - Comprehensive employee data validation
    - Dry run mode

    Configuration (in context.config):
        hris:
            system: "bamboohr" | "workday" | "generic"
            bamboohr:
                api_key: BambooHR API key
                subdomain: Company subdomain
            workday:
                api_key: Workday API credentials
                tenant: Tenant ID
            generic:
                base_url: API base URL
                api_key: API key
                auth_header: Authorization header name
    """

    def get_manifest(self) -> ToolManifest:
        """Return tool manifest with metadata and schema"""
        return ToolManifest(
            name="create_hris_record",
            version="1.0.0",
            description="Create employee record in HRIS system (BambooHR, Workday, or custom)",
            domains=["hr"],
            roles=["hr_manager", "hr_business_partner"],  # Not recruiters
            required_permissions=["hris_write"],

            input_schema={
                "type": "object",
                "properties": {
                    "system": {
                        "type": "string",
                        "enum": ["bamboohr", "workday", "generic"],
                        "default": "generic",
                        "description": "HRIS system to use"
                    },
                    "employee_data": {
                        "type": "object",
                        "properties": {
                            "first_name": {
                                "type": "string",
                                "description": "Employee first name"
                            },
                            "last_name": {
                                "type": "string",
                                "description": "Employee last name"
                            },
                            "email": {
                                "type": "string",
                                "format": "email",
                                "description": "Employee email address"
                            },
                            "job_title": {
                                "type": "string",
                                "description": "Job title/position"
                            },
                            "department": {
                                "type": "string",
                                "description": "Department name"
                            },
                            "start_date": {
                                "type": "string",
                                "format": "date",
                                "description": "Employment start date (YYYY-MM-DD)"
                            },
                            "employment_type": {
                                "type": "string",
                                "enum": ["full_time", "part_time", "contractor", "intern"],
                                "description": "Employment type"
                            },
                            "manager_email": {
                                "type": "string",
                                "format": "email",
                                "description": "Direct manager's email"
                            },
                            "salary": {
                                "type": "number",
                                "minimum": 0,
                                "description": "Annual salary (optional)"
                            },
                            "location": {
                                "type": "string",
                                "description": "Work location/office"
                            },
                            "phone": {
                                "type": "string",
                                "description": "Phone number"
                            },
                            "address": {
                                "type": "object",
                                "properties": {
                                    "street": {"type": "string"},
                                    "city": {"type": "string"},
                                    "state": {"type": "string"},
                                    "zip": {"type": "string"},
                                    "country": {"type": "string"}
                                },
                                "description": "Employee address"
                            },
                            "custom_fields": {
                                "type": "object",
                                "description": "System-specific custom fields"
                            }
                        },
                        "required": ["first_name", "last_name", "email", "start_date"]
                    }
                },
                "required": ["employee_data"]
            },

            output_schema={
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "system_id": {"type": "string"},
                    "created": {"type": "boolean"},
                    "profile_url": {"type": "string"},
                    "dry_run": {"type": "boolean"}
                },
                "required": ["employee_id", "system_id", "created"]
            },

            cost_estimate=0.0,
            timeout_seconds=30,
            requires_network=True,

            examples=[
                {
                    "description": "Create employee in BambooHR",
                    "input": {
                        "system": "bamboohr",
                        "employee_data": {
                            "first_name": "John",
                            "last_name": "Doe",
                            "email": "john.doe@example.com",
                            "job_title": "Software Engineer",
                            "department": "Engineering",
                            "start_date": "2025-12-01",
                            "employment_type": "full_time",
                            "manager_email": "jane.smith@example.com",
                            "location": "San Francisco"
                        }
                    },
                    "output": {
                        "employee_id": "12345",
                        "system_id": "bamboohr_12345",
                        "created": True,
                        "profile_url": "https://acme.bamboohr.com/employees/12345"
                    }
                }
            ],

            tags=["hris", "employee", "onboarding", "bamboohr", "workday"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Execute HRIS record creation.

        Args:
            params: Tool parameters (see input_schema)
            context: Execution context with configuration

        Returns:
            ToolResult with employee_id and profile_url
        """
        try:
            system = params.get("system", "generic")
            employee_data = params["employee_data"]

            # Get HRIS integration config
            hris_config = context.config.get("hris", {})
            system_config = hris_config.get(system, {})

            # Validate configuration (unless dry run)
            if not system_config and not context.dry_run:
                return ToolResult(
                    success=False,
                    error=f"HRIS system '{system}' not configured. Add hris.{system} configuration.",
                    metadata={
                        "required_config": f"hris.{system}",
                        "help": "Configure HRIS integration credentials"
                    }
                )

            # Dry run mode - simulate creation
            if context.dry_run:
                logger.info(
                    f"[DRY RUN] Would create employee: {employee_data['first_name']} "
                    f"{employee_data['last_name']} in {system}"
                )
                return ToolResult(
                    success=True,
                    data={
                        "employee_id": "dry_run_12345",
                        "system_id": f"{system}_dry_run",
                        "created": False,
                        "profile_url": f"https://{system}.example.com/dry_run",
                        "dry_run": True
                    },
                    metadata={
                        "note": "Dry run mode - employee not actually created",
                        "employee_name": f"{employee_data['first_name']} {employee_data['last_name']}"
                    }
                )

            # Create employee based on system type
            logger.info(f"Creating employee in {system}: {employee_data['email']}")

            if system == "bamboohr":
                result = await self._create_bamboohr_employee(employee_data, system_config)
            elif system == "workday":
                result = await self._create_workday_employee(employee_data, system_config)
            else:
                result = await self._create_generic_employee(employee_data, system_config)

            if result.success:
                logger.info(f"Employee created successfully: {result.data.get('employee_id')}")

            return result

        except Exception as e:
            logger.error(f"Failed to create HRIS record: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to create HRIS record: {str(e)}"
            )

    async def _create_bamboohr_employee(
        self,
        employee_data: Dict,
        config: Dict
    ) -> ToolResult:
        """
        Create employee in BambooHR via REST API.

        API Docs: https://documentation.bamboohr.com/reference/add-employee-1

        Args:
            employee_data: Employee information
            config: BambooHR configuration

        Returns:
            ToolResult with employee ID and profile URL
        """
        api_key = config.get("api_key")
        subdomain = config.get("subdomain")

        if not api_key or not subdomain:
            return ToolResult(
                success=False,
                error="BambooHR configuration incomplete. Required: api_key, subdomain"
            )

        # Map our fields to BambooHR fields
        bamboo_data = {
            "firstName": employee_data["first_name"],
            "lastName": employee_data["last_name"],
            "email": employee_data["email"],
            "hireDate": employee_data["start_date"],
        }

        # Optional fields
        if employee_data.get("job_title"):
            bamboo_data["jobTitle"] = employee_data["job_title"]
        if employee_data.get("department"):
            bamboo_data["department"] = employee_data["department"]
        if employee_data.get("location"):
            bamboo_data["location"] = employee_data["location"]
        if employee_data.get("phone"):
            bamboo_data["mobilePhone"] = employee_data["phone"]
        if employee_data.get("employment_type"):
            bamboo_data["employmentHistoryStatus"] = employee_data["employment_type"]

        # Add custom fields
        if employee_data.get("custom_fields"):
            bamboo_data.update(employee_data["custom_fields"])

        # Make API request
        try:
            url = f"https://api.bamboohr.com/api/gateway.php/{subdomain}/v1/employees/"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=bamboo_data,
                    headers=headers,
                    auth=aiohttp.BasicAuth(api_key, "x"),  # BambooHR uses api_key:x
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 201:
                        # Successfully created
                        # BambooHR returns employee ID in Location header
                        location = response.headers.get("Location", "")
                        employee_id = location.split("/")[-1] if location else "unknown"

                        return ToolResult(
                            success=True,
                            data={
                                "employee_id": employee_id,
                                "system_id": f"bamboohr_{employee_id}",
                                "created": True,
                                "profile_url": f"https://{subdomain}.bamboohr.com/employees/{employee_id}"
                            },
                            metadata={
                                "system": "bamboohr",
                                "employee_name": f"{employee_data['first_name']} {employee_data['last_name']}"
                            }
                        )
                    else:
                        error_text = await response.text()
                        return ToolResult(
                            success=False,
                            error=f"BambooHR API error ({response.status}): {error_text}"
                        )

        except aiohttp.ClientError as e:
            return ToolResult(
                success=False,
                error=f"BambooHR API connection error: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"BambooHR integration error: {str(e)}"
            )

    async def _create_workday_employee(
        self,
        employee_data: Dict,
        config: Dict
    ) -> ToolResult:
        """
        Create employee in Workday via REST API.

        Note: Workday API is complex and requires extensive setup.
        This is a simplified implementation stub.

        Args:
            employee_data: Employee information
            config: Workday configuration

        Returns:
            ToolResult with employee ID
        """
        # Workday implementation would go here
        # Requires: tenant, client_id, client_secret, refresh_token
        # API: https://community.workday.com/sites/default/files/file-hosting/restapi/index.html

        logger.warning("Workday integration not fully implemented")
        return ToolResult(
            success=False,
            error="Workday integration not yet implemented. Use 'generic' system type for custom HTTP API."
        )

    async def _create_generic_employee(
        self,
        employee_data: Dict,
        config: Dict
    ) -> ToolResult:
        """
        Create employee using generic HTTP POST API.

        Args:
            employee_data: Employee information
            config: Generic HRIS configuration

        Returns:
            ToolResult with employee ID
        """
        base_url = config.get("base_url")
        api_key = config.get("api_key")
        auth_header = config.get("auth_header", "Authorization")
        endpoint = config.get("endpoint", "/api/employees")

        if not base_url or not api_key:
            return ToolResult(
                success=False,
                error="Generic HRIS configuration incomplete. Required: base_url, api_key"
            )

        # Build request
        url = f"{base_url.rstrip('/')}{endpoint}"
        headers = {
            auth_header: f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=employee_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in (200, 201):
                        result_data = await response.json()
                        employee_id = result_data.get("id") or result_data.get("employee_id") or "unknown"

                        return ToolResult(
                            success=True,
                            data={
                                "employee_id": str(employee_id),
                                "system_id": f"generic_{employee_id}",
                                "created": True,
                                "profile_url": result_data.get("profile_url", f"{base_url}/employees/{employee_id}")
                            },
                            metadata={"system": "generic"}
                        )
                    else:
                        error_text = await response.text()
                        return ToolResult(
                            success=False,
                            error=f"HRIS API error ({response.status}): {error_text}"
                        )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"HRIS API error: {str(e)}"
            )
