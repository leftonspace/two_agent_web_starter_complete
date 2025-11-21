"""
BambooHR Connector

Integrates with BambooHR HRIS system for employee data management.

BambooHR API Documentation: https://documentation.bamboohr.com/docs

Features:
- Employee CRUD operations
- Time off requests
- Company reports
- Custom fields support
- File uploads/downloads

Authentication: API Key (subdomain + API key)

Author: AI Agent System
Created: Phase 3.2 - Integration Framework
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import aiohttp
import logging

from ..base import Connector, ConnectionStatus
from ..auth import APIKeyManager, get_credential_store, create_credential

logger = logging.getLogger(__name__)


class BambooHRConnector(Connector):
    """
    BambooHR HRIS connector.

    Provides access to:
    - Employee directory
    - Time off management
    - Company reports
    - Custom fields
    - Employee files
    """

    def __init__(
        self,
        connector_id: str,
        subdomain: str,
        api_key: str,
        config: Optional[Dict] = None
    ):
        """
        Initialize BambooHR connector.

        Args:
            connector_id: Unique connector ID
            subdomain: BambooHR subdomain (e.g., 'mycompany')
            api_key: BambooHR API key
            config: Additional configuration
        """
        # Set up configuration
        base_config = {
            'subdomain': subdomain,
            'api_key': api_key,
            'auth_type': 'api_key',
            'rate_limit_requests': 100,
            'rate_limit_window': 60,
            'max_retries': 3
        }

        if config:
            base_config.update(config)

        super().__init__(
            connector_id=connector_id,
            name=f"BambooHR ({subdomain})",
            config=base_config
        )

        self.subdomain = subdomain
        self.api_key = api_key
        self.base_url = f"https://api.bamboohr.com/api/gateway.php/{subdomain}/v1"
        self.auth_manager = APIKeyManager(api_key, "Authorization")

        # Store credentials securely
        self._store_credentials()

    def _store_credentials(self):
        """Store credentials in secure storage"""
        try:
            store = get_credential_store()
            cred = create_credential(
                connector_id=self.connector_id,
                auth_type='api_key',
                credentials={
                    'subdomain': self.subdomain,
                    'api_key': self.api_key
                },
                metadata={'base_url': self.base_url}
            )
            store.store(cred)
        except Exception as e:
            logger.warning(f"Failed to store credentials: {e}")

    # ========================================================================
    # AUTHENTICATION
    # ========================================================================

    async def authenticate(self) -> bool:
        """
        Authenticate with BambooHR.

        BambooHR uses API key auth, so we just verify the key works.

        Returns:
            True if authentication successful
        """
        try:
            # Test the API key by fetching company info
            async with self.session.get(
                f"{self.base_url}/employees/directory",
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    self.authenticated = True
                    logger.info(f"BambooHR authentication successful for {self.subdomain}")
                    return True
                elif resp.status == 401:
                    logger.error("BambooHR authentication failed: Invalid API key")
                    return False
                else:
                    logger.error(f"BambooHR authentication failed: HTTP {resp.status}")
                    return False

        except Exception as e:
            logger.error(f"BambooHR authentication error: {e}")
            return False

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to BambooHR.

        Returns:
            Test results with latency and status
        """
        start_time = asyncio.get_event_loop().time()

        try:
            async with self.session.get(
                f"{self.base_url}/employees/directory",
                headers=self._get_headers(),
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                latency = (asyncio.get_event_loop().time() - start_time) * 1000

                if resp.status == 200:
                    data = await resp.json()
                    employee_count = len(data.get('employees', []))

                    return {
                        'success': True,
                        'latency_ms': round(latency, 2),
                        'message': 'Connection successful',
                        'details': {
                            'subdomain': self.subdomain,
                            'employee_count': employee_count,
                            'status_code': resp.status
                        }
                    }
                else:
                    return {
                        'success': False,
                        'latency_ms': round(latency, 2),
                        'message': f'HTTP {resp.status}',
                        'details': {'status_code': resp.status}
                    }

        except Exception as e:
            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            return {
                'success': False,
                'latency_ms': round(latency, 2),
                'message': str(e),
                'details': {'error': str(e)}
            }

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authentication"""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        # BambooHR uses Basic Auth with API key as username and 'x' as password
        import base64
        credentials = f"{self.api_key}:x"
        encoded = base64.b64encode(credentials.encode()).decode()
        headers['Authorization'] = f'Basic {encoded}'

        return headers

    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================

    async def query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Query BambooHR data.

        Query format:
        - "employees" - All employees
        - "employees:123" - Employee with ID 123
        - "time_off" - Time off requests
        - "reports:1" - Report with ID 1

        Args:
            query: Query string
            params: Query parameters

        Returns:
            List of results
        """
        parts = query.split(':', 1)
        resource = parts[0]
        resource_id = parts[1] if len(parts) > 1 else None

        if resource == 'employees':
            if resource_id:
                # Get single employee
                employee = await self.get_employee(resource_id)
                return [employee] if employee else []
            else:
                # Get all employees
                return await self.list_employees(params or {})

        elif resource == 'time_off':
            return await self.list_time_off_requests(params or {})

        elif resource == 'reports':
            if resource_id:
                return await self.get_report(resource_id)
            else:
                raise ValueError("Report ID required")

        else:
            raise ValueError(f"Unknown resource type: {resource}")

    async def create(self, entity_type: str, data: Dict) -> Dict:
        """
        Create entity in BambooHR.

        Args:
            entity_type: 'employee', 'time_off_request'
            data: Entity data

        Returns:
            Created entity with ID
        """
        if entity_type == 'employee':
            return await self.create_employee(data)

        elif entity_type == 'time_off_request':
            return await self.create_time_off_request(data)

        else:
            raise ValueError(f"Cannot create entity type: {entity_type}")

    async def update(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict
    ) -> Dict:
        """
        Update entity in BambooHR.

        Args:
            entity_type: 'employee'
            entity_id: Entity ID
            data: Updated data

        Returns:
            Updated entity
        """
        if entity_type == 'employee':
            return await self.update_employee(entity_id, data)

        else:
            raise ValueError(f"Cannot update entity type: {entity_type}")

    # ========================================================================
    # EMPLOYEE OPERATIONS
    # ========================================================================

    async def list_employees(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        List all employees.

        Args:
            filters: Optional filters (status, department, etc.)

        Returns:
            List of employees
        """
        async def _fetch():
            async with self.session.get(
                f"{self.base_url}/employees/directory",
                headers=self._get_headers()
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get('employees', [])

        employees = await self.execute_with_rate_limit(_fetch)

        # Apply filters if provided
        if filters:
            if 'status' in filters:
                employees = [e for e in employees if e.get('status') == filters['status']]
            if 'department' in filters:
                employees = [e for e in employees if e.get('department') == filters['department']]

        return employees

    async def get_employee(self, employee_id: str, fields: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Get single employee by ID.

        Args:
            employee_id: Employee ID
            fields: Optional list of fields to retrieve

        Returns:
            Employee data or None
        """
        # Default fields
        if not fields:
            fields = ['firstName', 'lastName', 'email', 'department', 'jobTitle', 'status', 'hireDate']

        field_str = ','.join(fields)

        async def _fetch():
            async with self.session.get(
                f"{self.base_url}/employees/{employee_id}?fields={field_str}",
                headers=self._get_headers()
            ) as resp:
                if resp.status == 404:
                    return None
                resp.raise_for_status()
                return await resp.json()

        return await self.execute_with_rate_limit(_fetch)

    async def create_employee(self, employee_data: Dict) -> Dict:
        """
        Create a new employee.

        Args:
            employee_data: Employee information

        Returns:
            Created employee with ID
        """
        async def _create():
            async with self.session.post(
                f"{self.base_url}/employees",
                headers=self._get_headers(),
                json=employee_data
            ) as resp:
                resp.raise_for_status()
                # BambooHR returns the employee ID in Location header
                location = resp.headers.get('Location', '')
                employee_id = location.split('/')[-1] if location else None

                # Fetch the created employee
                if employee_id:
                    return await self.get_employee(employee_id)
                else:
                    return {'id': employee_id, **employee_data}

        return await self.execute_with_rate_limit(_create)

    async def update_employee(self, employee_id: str, employee_data: Dict) -> Dict:
        """
        Update an existing employee.

        Args:
            employee_id: Employee ID
            employee_data: Updated employee data

        Returns:
            Updated employee
        """
        async def _update():
            async with self.session.post(
                f"{self.base_url}/employees/{employee_id}",
                headers=self._get_headers(),
                json=employee_data
            ) as resp:
                resp.raise_for_status()
                # Fetch updated employee
                return await self.get_employee(employee_id)

        return await self.execute_with_rate_limit(_update)

    # ========================================================================
    # TIME OFF OPERATIONS
    # ========================================================================

    async def list_time_off_requests(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        List time off requests.

        Args:
            filters: Optional filters (start, end, status, type, employeeId)

        Returns:
            List of time off requests
        """
        params = {}
        if filters:
            if 'start' in filters:
                params['start'] = filters['start']
            if 'end' in filters:
                params['end'] = filters['end']
            if 'status' in filters:
                params['status'] = filters['status']
            if 'type' in filters:
                params['type'] = filters['type']
            if 'employeeId' in filters:
                params['employeeId'] = filters['employeeId']

        async def _fetch():
            async with self.session.get(
                f"{self.base_url}/time_off/requests",
                headers=self._get_headers(),
                params=params
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

        return await self.execute_with_rate_limit(_fetch)

    async def create_time_off_request(self, request_data: Dict) -> Dict:
        """
        Create a time off request.

        Args:
            request_data: Request information (employeeId, start, end, timeOffTypeId, etc.)

        Returns:
            Created request
        """
        async def _create():
            async with self.session.post(
                f"{self.base_url}/time_off/requests",
                headers=self._get_headers(),
                json=request_data
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

        return await self.execute_with_rate_limit(_create)

    async def approve_time_off_request(self, request_id: str, note: Optional[str] = None) -> Dict:
        """
        Approve a time off request.

        Args:
            request_id: Request ID
            note: Optional note

        Returns:
            Updated request
        """
        data = {'status': 'approved'}
        if note:
            data['note'] = note

        async def _approve():
            async with self.session.put(
                f"{self.base_url}/time_off/requests/{request_id}/status",
                headers=self._get_headers(),
                json=data
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

        return await self.execute_with_rate_limit(_approve)

    # ========================================================================
    # REPORTS
    # ========================================================================

    async def get_report(self, report_id: str, format: str = 'JSON') -> List[Dict]:
        """
        Get a company report.

        Args:
            report_id: Report ID
            format: Report format (JSON, CSV, PDF, XLS)

        Returns:
            Report data
        """
        async def _fetch():
            async with self.session.get(
                f"{self.base_url}/reports/{report_id}?format={format}",
                headers=self._get_headers()
            ) as resp:
                resp.raise_for_status()
                if format == 'JSON':
                    data = await resp.json()
                    return data.get('employees', [])
                else:
                    # Return raw data for non-JSON formats
                    return [{'data': await resp.text(), 'format': format}]

        return await self.execute_with_rate_limit(_fetch)

    # ========================================================================
    # CUSTOM FIELDS
    # ========================================================================

    async def list_custom_fields(self) -> List[Dict]:
        """
        List all custom fields.

        Returns:
            List of custom field definitions
        """
        async def _fetch():
            async with self.session.get(
                f"{self.base_url}/meta/fields",
                headers=self._get_headers()
            ) as resp:
                resp.raise_for_status()
                return await resp.json()

        return await self.execute_with_rate_limit(_fetch)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def __repr__(self) -> str:
        return f"BambooHRConnector(subdomain='{self.subdomain}', status={self.status.value})"
