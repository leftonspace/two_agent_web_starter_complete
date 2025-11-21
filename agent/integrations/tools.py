"""
Integration Tools - Wrap connectors as agent tools

This module provides tool wrappers for connectors, allowing
agents to interact with external systems through the integration framework.

Usage:
    from integrations.tools import query_database, query_hris, create_hris_record

Author: AI Agent System
Created: Phase 3.2 - Integration Framework
"""

import asyncio
from typing import Dict, List, Optional, Any
import logging

from .base import get_registry, Connector
from .hris.bamboohr import BambooHRConnector
from .database import DatabaseConnector

logger = logging.getLogger(__name__)


# ============================================================================
# TOOL WRAPPERS
# ============================================================================

async def query_database(
    connector_id: str,
    query: str,
    params: Optional[Dict] = None
) -> List[Dict]:
    """
    Query a database integration.

    Tool for agents to execute SQL queries against connected databases.

    Args:
        connector_id: ID of the database connector
        query: SQL query string
        params: Query parameters for binding

    Returns:
        List of result rows

    Example:
        results = await query_database(
            "db_123",
            "SELECT * FROM employees WHERE department = $1",
            {"department": "Engineering"}
        )
    """
    registry = get_registry()
    connector = registry.get(connector_id)

    if not connector:
        raise ValueError(f"Connector {connector_id} not found")

    if not isinstance(connector, DatabaseConnector):
        raise TypeError(f"Connector {connector_id} is not a database connector")

    return await connector.query(query, params)


async def query_hris(
    connector_id: str,
    resource: str,
    filters: Optional[Dict] = None
) -> List[Dict]:
    """
    Query HRIS system (BambooHR).

    Tool for agents to fetch employee data from HRIS.

    Args:
        connector_id: ID of the HRIS connector
        resource: Resource to query ('employees', 'time_off')
        filters: Optional filters

    Returns:
        List of results

    Example:
        employees = await query_hris(
            "bamboo_123",
            "employees",
            {"status": "active", "department": "Engineering"}
        )
    """
    registry = get_registry()
    connector = registry.get(connector_id)

    if not connector:
        raise ValueError(f"Connector {connector_id} not found")

    if not isinstance(connector, BambooHRConnector):
        raise TypeError(f"Connector {connector_id} is not an HRIS connector")

    return await connector.query(resource, filters)


async def create_hris_record(
    connector_id: str,
    entity_type: str,
    data: Dict
) -> Dict:
    """
    Create a record in HRIS.

    Tool for agents to create employees, time off requests, etc.

    Args:
        connector_id: ID of the HRIS connector
        entity_type: Type of entity ('employee', 'time_off_request')
        data: Entity data

    Returns:
        Created entity

    Example:
        employee = await create_hris_record(
            "bamboo_123",
            "employee",
            {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john.doe@company.com",
                "department": "Engineering"
            }
        )
    """
    registry = get_registry()
    connector = registry.get(connector_id)

    if not connector:
        raise ValueError(f"Connector {connector_id} not found")

    if not isinstance(connector, BambooHRConnector):
        raise TypeError(f"Connector {connector_id} is not an HRIS connector")

    return await connector.create(entity_type, data)


async def update_hris_record(
    connector_id: str,
    entity_type: str,
    entity_id: str,
    data: Dict
) -> Dict:
    """
    Update a record in HRIS.

    Tool for agents to update employee data.

    Args:
        connector_id: ID of the HRIS connector
        entity_type: Type of entity ('employee')
        entity_id: Entity ID
        data: Updated data

    Returns:
        Updated entity

    Example:
        employee = await update_hris_record(
            "bamboo_123",
            "employee",
            "12345",
            {"jobTitle": "Senior Engineer"}
        )
    """
    registry = get_registry()
    connector = registry.get(connector_id)

    if not connector:
        raise ValueError(f"Connector {connector_id} not found")

    if not isinstance(connector, BambooHRConnector):
        raise TypeError(f"Connector {connector_id} is not an HRIS connector")

    return await connector.update(entity_type, entity_id, data)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_connector(connector_id: str) -> Optional[Connector]:
    """Get a connector by ID"""
    registry = get_registry()
    return registry.get(connector_id)


def list_connectors(connector_type: Optional[str] = None) -> List[Connector]:
    """
    List all connectors.

    Args:
        connector_type: Optional filter by type ('BambooHRConnector', 'DatabaseConnector')

    Returns:
        List of connectors
    """
    registry = get_registry()

    if connector_type:
        return registry.list_by_type(connector_type)
    else:
        return registry.list_all()


async def execute_with_connector(
    connector_id: str,
    operation: str,
    **kwargs
) -> Any:
    """
    Generic tool to execute operations on any connector.

    Args:
        connector_id: Connector ID
        operation: Operation name ('query', 'create', 'update', 'delete')
        **kwargs: Operation arguments

    Returns:
        Operation result

    Example:
        result = await execute_with_connector(
            "db_123",
            "query",
            query="SELECT * FROM users LIMIT 10"
        )
    """
    connector = get_connector(connector_id)

    if not connector:
        raise ValueError(f"Connector {connector_id} not found")

    if operation == 'query':
        return await connector.query(kwargs.get('query', ''), kwargs.get('params'))

    elif operation == 'create':
        return await connector.create(kwargs['entity_type'], kwargs['data'])

    elif operation == 'update':
        return await connector.update(
            kwargs['entity_type'],
            kwargs['entity_id'],
            kwargs['data']
        )

    elif operation == 'delete':
        return await connector.delete(kwargs['entity_type'], kwargs['entity_id'])

    else:
        raise ValueError(f"Unknown operation: {operation}")


# ============================================================================
# TOOL CATALOG
# ============================================================================

INTEGRATION_TOOLS = {
    'query_database': {
        'function': query_database,
        'description': 'Query a SQL database',
        'parameters': {
            'connector_id': 'ID of database connector',
            'query': 'SQL query string',
            'params': 'Query parameters (optional)'
        }
    },
    'query_hris': {
        'function': query_hris,
        'description': 'Query HRIS system (BambooHR)',
        'parameters': {
            'connector_id': 'ID of HRIS connector',
            'resource': 'Resource to query (employees, time_off)',
            'filters': 'Optional filters'
        }
    },
    'create_hris_record': {
        'function': create_hris_record,
        'description': 'Create a record in HRIS',
        'parameters': {
            'connector_id': 'ID of HRIS connector',
            'entity_type': 'Type of entity to create',
            'data': 'Entity data'
        }
    },
    'update_hris_record': {
        'function': update_hris_record,
        'description': 'Update a record in HRIS',
        'parameters': {
            'connector_id': 'ID of HRIS connector',
            'entity_type': 'Type of entity',
            'entity_id': 'Entity ID',
            'data': 'Updated data'
        }
    }
}


def get_tool_catalog() -> Dict[str, Any]:
    """Get catalog of all integration tools"""
    return INTEGRATION_TOOLS
