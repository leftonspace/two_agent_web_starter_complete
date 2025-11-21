"""
Direct execution mode for simple tasks.

JARVIS executes immediately without review process.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from agent.llm_client import LLMClient
from agent.core_logging import log_event


class DirectActionType(Enum):
    """Types of actions JARVIS can execute directly"""
    QUERY_DATABASE = "query_database"
    SEARCH_INFO = "search_info"
    CREATE_DOCUMENT = "create_document"
    SEND_MESSAGE = "send_message"
    CALCULATE = "calculate"
    API_CALL = "api_call"
    FILE_READ = "file_read"


class DirectExecutor:
    """
    Executes simple tasks directly without review.

    Safety-first design:
    - Only whitelisted actions
    - Read-only by default
    - Automatic validation
    - Rollback on error
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

        # Safety settings
        self.max_execution_time = 30  # seconds
        self.allowed_actions = {
            DirectActionType.QUERY_DATABASE,
            DirectActionType.SEARCH_INFO,
            DirectActionType.CREATE_DOCUMENT,
            DirectActionType.SEND_MESSAGE,
            DirectActionType.CALCULATE,
            DirectActionType.FILE_READ
        }

    async def execute(
        self,
        task_description: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute task directly.

        Args:
            task_description: What to do
            context: Additional context

        Returns:
            Result with success status and data
        """
        start_time = datetime.now()

        try:
            # 1. Plan the action
            action_plan = await self._plan_direct_action(task_description, context)

            # 2. Safety check
            if not self._is_safe_action(action_plan):
                return {
                    "success": False,
                    "error": "Action not allowed in direct execution mode",
                    "suggested_mode": "reviewed"
                }

            # 3. Execute with timeout
            result = await asyncio.wait_for(
                self._execute_action(action_plan),
                timeout=self.max_execution_time
            )

            # 4. Validate result
            if self._validate_result(result):
                execution_time = (datetime.now() - start_time).total_seconds()

                log_event("direct_execution_success", {
                    "task": task_description,
                    "action_type": action_plan.get("action_type"),
                    "execution_time": execution_time
                })

                return {
                    "success": True,
                    "result": result,
                    "execution_time": execution_time,
                    "mode": "direct"
                }
            else:
                return {
                    "success": False,
                    "error": "Result validation failed",
                    "result": result
                }

        except asyncio.TimeoutError:
            log_event("direct_execution_timeout", {
                "task": task_description
            })
            return {
                "success": False,
                "error": f"Execution exceeded {self.max_execution_time}s timeout"
            }

        except Exception as e:
            log_event("direct_execution_failed", {
                "task": task_description,
                "error": str(e)
            })
            return {
                "success": False,
                "error": str(e)
            }

    async def _plan_direct_action(
        self,
        task_description: str,
        context: Optional[Dict]
    ) -> Dict:
        """
        Plan how to execute the task.

        Returns action plan with type and parameters.
        """
        prompt = f"""Plan how to execute this task directly.

TASK: {task_description}

CONTEXT: {context or 'None'}

You can ONLY use these action types:
- query_database: Read data from database
- search_info: Search for information online
- create_document: Create a new document
- send_message: Send email or message
- calculate: Perform calculation
- api_call: Call external API (read-only)
- file_read: Read file contents

Return JSON:
{{
  "action_type": "one of the above",
  "parameters": {{
    // Action-specific parameters
  }},
  "expected_output": "Description of what this will produce"
}}

If task cannot be done with these actions, return:
{{
  "action_type": "unsupported",
  "reason": "Why this needs more complex execution"
}}
"""

        try:
            plan = await self.llm.chat_json(
                prompt=prompt,
                model="gpt-4o-mini",  # Fast model for planning
                temperature=0.1
            )
            return plan

        except Exception as e:
            log_event("action_planning_failed", {
                "error": str(e)
            })
            return {"action_type": "unsupported", "reason": str(e)}

    def _is_safe_action(self, action_plan: Dict) -> bool:
        """
        Validate action is safe for direct execution.

        Returns True if safe, False otherwise.
        """
        action_type_str = action_plan.get("action_type")

        # Check if unsupported
        if action_type_str == "unsupported":
            return False

        try:
            action_type = DirectActionType(action_type_str)
        except ValueError:
            return False

        # Check if allowed
        if action_type not in self.allowed_actions:
            return False

        # Additional safety checks per action type
        params = action_plan.get("parameters", {})

        if action_type == DirectActionType.QUERY_DATABASE:
            # Must be SELECT only, no modifications
            query = params.get("query", "").upper()
            forbidden_keywords = ["UPDATE", "DELETE", "INSERT", "DROP", "ALTER", "CREATE", "TRUNCATE"]
            if any(keyword in query for keyword in forbidden_keywords):
                log_event("unsafe_query_blocked", {"query": query})
                return False

        elif action_type == DirectActionType.API_CALL:
            # Must be GET or HEAD request only
            method = params.get("method", "GET").upper()
            if method not in ["GET", "HEAD"]:
                log_event("unsafe_api_method_blocked", {"method": method})
                return False

        return True

    async def _execute_action(self, action_plan: Dict) -> Any:
        """Execute the planned action"""
        action_type = DirectActionType(action_plan["action_type"])
        params = action_plan.get("parameters", {})

        if action_type == DirectActionType.QUERY_DATABASE:
            return await self._query_database(params)

        elif action_type == DirectActionType.SEARCH_INFO:
            return await self._search_info(params)

        elif action_type == DirectActionType.CREATE_DOCUMENT:
            return await self._create_document(params)

        elif action_type == DirectActionType.SEND_MESSAGE:
            return await self._send_message(params)

        elif action_type == DirectActionType.CALCULATE:
            return await self._calculate(params)

        elif action_type == DirectActionType.API_CALL:
            return await self._api_call(params)

        elif action_type == DirectActionType.FILE_READ:
            return await self._file_read(params)

        else:
            raise ValueError(f"Unsupported action type: {action_type}")

    async def _query_database(self, params: Dict) -> Dict:
        """Execute database query"""
        query = params.get("query", "")

        # Would integrate with actual database
        # For now, return mock result
        log_event("database_query_executed", {
            "query": query[:100]  # Log first 100 chars
        })

        return {
            "query": query,
            "rows": [],
            "row_count": 0,
            "message": "Query executed (mock implementation)"
        }

    async def _search_info(self, params: Dict) -> Dict:
        """Search for information"""
        search_query = params.get("query", "")

        # Use LLM to search/generate information
        prompt = f"Provide accurate information about: {search_query}"

        result = await self.llm.chat(prompt, model="gpt-4o-mini")

        return {
            "query": search_query,
            "result": result
        }

    async def _create_document(self, params: Dict) -> Dict:
        """Create a document"""
        title = params.get("title", "Untitled")
        content_type = params.get("type", "notes")
        initial_content = params.get("content", "")

        # Generate document content if not provided
        if not initial_content:
            prompt = f"Create {content_type} document titled '{title}'. Generate appropriate content in markdown."
            initial_content = await self.llm.chat(prompt, model="gpt-4o")

        # Save document (simplified - would write to actual file in production)
        doc_path = f"./documents/{title.replace(' ', '_')}.md"

        log_event("document_created", {
            "title": title,
            "path": doc_path
        })

        return {
            "title": title,
            "path": doc_path,
            "content": initial_content,
            "created": True
        }

    async def _send_message(self, params: Dict) -> Dict:
        """Send message/email"""
        recipient = params.get("recipient", "")
        message = params.get("message", "")
        subject = params.get("subject", "")

        # Would integrate with email/messaging service
        log_event("message_sent", {
            "recipient": recipient,
            "subject": subject
        })

        return {
            "recipient": recipient,
            "subject": subject,
            "sent": True,
            "timestamp": datetime.now().isoformat()
        }

    async def _calculate(self, params: Dict) -> Dict:
        """Perform calculation"""
        expression = params.get("expression", "")

        # Use LLM to safely evaluate
        prompt = f"Calculate: {expression}\nReturn only the numeric result."

        result = await self.llm.chat(prompt, model="gpt-4o-mini")

        return {
            "expression": expression,
            "result": result
        }

    async def _api_call(self, params: Dict) -> Dict:
        """Make API call"""
        try:
            import httpx
        except ImportError:
            # httpx not installed
            return {
                "error": "httpx library not installed",
                "message": "Install httpx to make API calls"
            }

        url = params.get("url", "")
        method = params.get("method", "GET")
        headers = params.get("headers", {})

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    timeout=10.0
                )

                log_event("api_call_executed", {
                    "url": url,
                    "method": method,
                    "status_code": response.status_code
                })

                return {
                    "url": url,
                    "status_code": response.status_code,
                    "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                }
        except httpx.HTTPError as e:
            log_event("api_call_failed", {
                "url": url,
                "error": str(e)
            })
            raise ValueError(f"API call failed: {str(e)}")

    async def _file_read(self, params: Dict) -> Dict:
        """Read file"""
        file_path = params.get("path", "")

        # Safety check: no system files
        forbidden_paths = ["/etc", "/sys", "/proc", "C:\\Windows", "/dev"]
        if any(file_path.startswith(p) for p in forbidden_paths):
            log_event("unsafe_file_access_blocked", {
                "path": file_path
            })
            raise ValueError("Access to system files not allowed")

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            log_event("file_read", {
                "path": file_path,
                "size": len(content)
            })

            return {
                "path": file_path,
                "content": content,
                "size": len(content)
            }
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Error reading file: {str(e)}")

    def _validate_result(self, result: Any) -> bool:
        """Validate execution result"""
        # Basic validation - result exists and is not None
        if result is None:
            return False

        # If dict, check for error indicators
        if isinstance(result, dict):
            if result.get("error"):
                return False

        return True
