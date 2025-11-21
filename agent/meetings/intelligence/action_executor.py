"""
Real-time action executor for meeting intelligence.

Executes simple tasks DURING meetings.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from agent.meetings.intelligence.meeting_analyzer import ActionItem, MeetingUnderstanding
from agent.llm_client import LLMClient
from agent.core_logging import log_event


class MeetingActionExecutor:
    """
    Executes actions during meetings in real-time.

    Only executes SIMPLE, SAFE tasks:
    - Lookup data
    - Create documents
    - Send messages
    - Schedule meetings

    Complex tasks are deferred for after meeting.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

        # Track what JARVIS has done during meeting
        self.executed_actions: List[Dict] = []

    async def process_understanding(
        self,
        understanding: MeetingUnderstanding
    ) -> List[Dict]:
        """
        Process meeting understanding and execute appropriate actions.

        Returns:
            List of actions taken
        """
        actions_taken = []

        if not understanding.needs_jarvis_action:
            return actions_taken

        # Execute suggested actions
        for suggested_action in understanding.suggested_actions:
            # Only execute immediate and during-meeting actions
            urgency = suggested_action.get("urgency", "after_meeting")

            if urgency in ["immediate", "during_meeting"]:
                result = await self._execute_action(suggested_action)

                if result:
                    actions_taken.append(result)
                    self.executed_actions.append(result)

        return actions_taken

    async def _execute_action(self, action: Dict) -> Optional[Dict]:
        """Execute a single action"""
        action_type = action.get("action_type")

        log_event("executing_meeting_action", {
            "action_type": action_type,
            "description": action.get("description")
        })

        try:
            if action_type == "query_data":
                return await self._query_data(action)

            elif action_type == "search_info":
                return await self._search_info(action)

            elif action_type == "create_document":
                return await self._create_document(action)

            elif action_type == "send_message":
                return await self._send_message(action)

            elif action_type == "schedule_meeting":
                return await self._schedule_meeting(action)

            else:
                log_event("unknown_action_type", {
                    "action_type": action_type
                })
                return None

        except Exception as e:
            log_event("action_execution_failed", {
                "action_type": action_type,
                "error": str(e)
            })
            return None

    async def _query_data(self, action: Dict) -> Dict:
        """
        Query data from database/API.

        Example: "Pull up Q3 revenue numbers"
        """
        params = action.get("parameters", {})
        query = params.get("query", "")

        # Use LLM to generate SQL or API call
        prompt = f"""Generate a query to retrieve this data: {query}

Return JSON with:
{{
  "query_type": "sql|api|search",
  "query": "the actual query",
  "endpoint": "if API"
}}
"""

        query_plan = await self.llm.chat_json(prompt, model="gpt-4o")

        # Execute query (simplified - would integrate with actual DB/APIs)
        result_data = await self._execute_query(query_plan)

        return {
            "action_type": "query_data",
            "description": action.get("description"),
            "result": result_data,
            "timestamp": datetime.now().isoformat()
        }

    async def _search_info(self, action: Dict) -> Dict:
        """
        Search for information online or in documents.

        Example: "Look up current exchange rate"
        """
        params = action.get("parameters", {})
        search_query = params.get("query", "")

        # Perform search (would integrate with search API)
        search_results = f"Searched for: {search_query}"

        return {
            "action_type": "search_info",
            "description": action.get("description"),
            "result": search_results,
            "timestamp": datetime.now().isoformat()
        }

    async def _create_document(self, action: Dict) -> Dict:
        """
        Create a document during meeting.

        Example: "Create a doc for the Q4 plan"
        """
        params = action.get("parameters", {})
        doc_title = params.get("title", "Untitled Document")
        doc_type = params.get("type", "notes")

        # Generate document content
        prompt = f"""Create a {doc_type} document titled "{doc_title}".

Based on meeting context, generate appropriate initial content.

Return markdown format.
"""

        content = await self.llm.chat(prompt, model="gpt-4o")

        # Save document (simplified - would integrate with Google Docs/etc)
        doc_path = f"./meetings/docs/{doc_title}.md"

        return {
            "action_type": "create_document",
            "description": action.get("description"),
            "result": {
                "title": doc_title,
                "path": doc_path,
                "content_length": len(content)
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _send_message(self, action: Dict) -> Dict:
        """
        Send a message/email.

        Example: "Email the team about the decision"
        """
        params = action.get("parameters", {})
        recipient = params.get("recipient", "")
        message = params.get("message", "")

        # Send message (would integrate with email/Slack/etc)

        return {
            "action_type": "send_message",
            "description": action.get("description"),
            "result": {
                "recipient": recipient,
                "sent": True
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _schedule_meeting(self, action: Dict) -> Dict:
        """
        Schedule a follow-up meeting.

        Example: "Schedule follow-up for next week"
        """
        params = action.get("parameters", {})
        title = params.get("title", "Follow-up Meeting")
        when = params.get("when", "")
        attendees = params.get("attendees", [])

        # Schedule meeting (would integrate with calendar API)

        return {
            "action_type": "schedule_meeting",
            "description": action.get("description"),
            "result": {
                "title": title,
                "scheduled_for": when,
                "attendees": attendees
            },
            "timestamp": datetime.now().isoformat()
        }

    async def _execute_query(self, query_plan: Dict) -> str:
        """Execute actual query (placeholder)"""
        # This would integrate with real databases/APIs
        return f"Query result for: {query_plan.get('query', '')}"

    def get_actions_summary(self) -> str:
        """Get summary of all actions taken during meeting"""
        if not self.executed_actions:
            return "No actions taken during meeting."

        summary = f"JARVIS executed {len(self.executed_actions)} actions during meeting:\n\n"

        for i, action in enumerate(self.executed_actions, 1):
            summary += f"{i}. {action.get('description', 'Unknown action')}\n"
            summary += f"   Type: {action.get('action_type')}\n"
            summary += f"   Time: {action.get('timestamp')}\n\n"

        return summary
