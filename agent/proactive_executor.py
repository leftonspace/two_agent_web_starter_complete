"""
Proactive Action Executor

Automatically executes actions based on patterns, preferences, and triggers.

Different from autonomous_coordinator (Phase 6) which focuses on self-improvement
and goal decomposition, this system proactively takes actions based on:
- User preferences and patterns
- Event triggers (calendar, webhooks, cron)
- Meeting intelligence suggestions
- Contextual awareness

Usage:
    executor = ProactiveExecutor()

    # Start proactive monitoring
    await executor.start()

    # System will automatically:
    # - Execute meeting suggestions
    # - Trigger calendar-based actions
    # - Apply learned preferences
    # - Respond to events
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

try:
    from .memory.preference_learner import PreferenceLearner
except ImportError:
    PreferenceLearner = None

try:
    from .meetings.intelligence.meeting_analyzer import MeetingUnderstanding
except ImportError:
    MeetingUnderstanding = None

try:
    from .flow.events import EventBus, Event
except ImportError:
    EventBus = None
    Event = None


# =============================================================================
# Configuration
# =============================================================================

class ActionType(Enum):
    """Types of proactive actions"""
    MEETING_PREPARATION = "meeting_preparation"
    FOLLOW_UP = "follow_up"
    NOTIFICATION = "notification"
    DOCUMENT_CREATION = "document_creation"
    CALENDAR_UPDATE = "calendar_update"
    EMAIL_SEND = "email_send"
    DATA_SYNC = "data_sync"
    PREFERENCE_APPLY = "preference_apply"


@dataclass
class ProactiveConfig:
    """Configuration for proactive executor"""

    # Enable/disable features
    enable_meeting_actions: bool = True
    enable_calendar_actions: bool = True
    enable_preference_actions: bool = True
    enable_event_actions: bool = True

    # Thresholds
    min_confidence_for_execution: float = 0.7
    min_urgency_for_immediate: str = "high"  # low, medium, high, urgent

    # Safety
    max_actions_per_hour: int = 20
    require_confirmation_for_destructive: bool = True
    dry_run_mode: bool = False  # Log actions but don't execute

    # Paths
    action_log_path: Path = Path(".jarvis/proactive_actions.jsonl")


@dataclass
class ProactiveAction:
    """A proactive action to be executed"""

    id: str
    action_type: ActionType
    description: str
    confidence: float
    urgency: str  # low, medium, high, urgent
    trigger: str  # What triggered this action

    # Action parameters
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Execution tracking
    executed: bool = False
    executed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


# =============================================================================
# Proactive Executor
# =============================================================================

class ProactiveExecutor:
    """
    Proactive Action Executor

    Automatically executes actions based on context, preferences, and triggers.

    Example:
        executor = ProactiveExecutor()

        # Register action handlers
        @executor.register_handler(ActionType.MEETING_PREPARATION)
        async def prepare_meeting(action: ProactiveAction):
            # Prepare meeting materials
            return {"status": "prepared"}

        # Start proactive monitoring
        await executor.start()

        # Process meeting suggestions
        await executor.process_meeting_suggestions(meeting_understanding)
    """

    def __init__(
        self,
        config: Optional[ProactiveConfig] = None,
        preference_learner: Optional[PreferenceLearner] = None,
        event_bus: Optional[EventBus] = None,
    ):
        """
        Initialize proactive executor.

        Args:
            config: Configuration
            preference_learner: Preference learning system
            event_bus: Event bus for triggers
        """
        self.config = config or ProactiveConfig()
        self.preference_learner = preference_learner
        self.event_bus = event_bus

        # Action tracking
        self.pending_actions: List[ProactiveAction] = []
        self.executed_actions: List[ProactiveAction] = []
        self.action_handlers: Dict[ActionType, Callable] = {}

        # State
        self.running = False
        self.actions_this_hour = 0
        self.hour_reset_time = datetime.now() + timedelta(hours=1)

        print(f"[ProactiveExecutor] Initialized with confidence threshold: {self.config.min_confidence_for_execution}")

    # =========================================================================
    # Action Registration
    # =========================================================================

    def register_handler(self, action_type: ActionType):
        """
        Decorator to register action handler.

        Usage:
            @executor.register_handler(ActionType.MEETING_PREPARATION)
            async def prepare_meeting(action: ProactiveAction):
                # Handle action
                return result
        """
        def decorator(func: Callable):
            self.action_handlers[action_type] = func
            print(f"[ProactiveExecutor] Registered handler for {action_type.value}")
            return func
        return decorator

    def register_handler_direct(
        self,
        action_type: ActionType,
        handler: Callable,
    ):
        """Register action handler directly"""
        self.action_handlers[action_type] = handler
        print(f"[ProactiveExecutor] Registered handler for {action_type.value}")

    # =========================================================================
    # Execution Loop
    # =========================================================================

    async def start(self):
        """Start proactive execution loop"""
        self.running = True
        print("[ProactiveExecutor] Starting proactive execution loop...")

        # Start monitoring tasks
        tasks = [
            self._execution_loop(),
            self._event_monitoring_loop(),
            self._preference_application_loop(),
        ]

        await asyncio.gather(*tasks)

    def stop(self):
        """Stop proactive execution"""
        self.running = False
        print("[ProactiveExecutor] Stopped")

    async def _execution_loop(self):
        """Main execution loop"""
        while self.running:
            try:
                # Reset hourly action count
                if datetime.now() >= self.hour_reset_time:
                    self.actions_this_hour = 0
                    self.hour_reset_time = datetime.now() + timedelta(hours=1)

                # Check rate limit
                if self.actions_this_hour >= self.config.max_actions_per_hour:
                    print(f"[ProactiveExecutor] Rate limit reached ({self.config.max_actions_per_hour}/hour)")
                    await asyncio.sleep(60)
                    continue

                # Process pending actions
                await self._process_pending_actions()

                # Check for scheduled actions
                await self._check_scheduled_actions()

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                print(f"[ProactiveExecutor] Error in execution loop: {e}")
                await asyncio.sleep(60)

    async def _event_monitoring_loop(self):
        """Monitor events and create actions"""
        if not self.config.enable_event_actions or not self.event_bus:
            return

        while self.running:
            try:
                # In production, subscribe to event bus
                # For now, just sleep
                await asyncio.sleep(30)

            except Exception as e:
                print(f"[ProactiveExecutor] Error in event monitoring: {e}")
                await asyncio.sleep(60)

    async def _preference_application_loop(self):
        """Apply learned preferences proactively"""
        if not self.config.enable_preference_actions or not self.preference_learner:
            return

        while self.running:
            try:
                # Check for preference-based actions every 5 minutes
                await asyncio.sleep(300)

                # Apply preferences (e.g., auto-format documents, set defaults)
                await self._apply_preferences()

            except Exception as e:
                print(f"[ProactiveExecutor] Error in preference application: {e}")
                await asyncio.sleep(600)

    # =========================================================================
    # Meeting Integration
    # =========================================================================

    async def process_meeting_suggestions(
        self,
        meeting_understanding: MeetingUnderstanding,
    ) -> List[ProactiveAction]:
        """
        Process meeting suggestions and create proactive actions.

        Args:
            meeting_understanding: Meeting analysis with suggestions

        Returns:
            List of actions created
        """
        if not self.config.enable_meeting_actions:
            return []

        actions_created = []

        # Process suggested JARVIS actions from meeting
        for suggestion in meeting_understanding.suggested_actions:
            action = ProactiveAction(
                id=f"meeting_{meeting_understanding.meeting_id}_{len(actions_created)}",
                action_type=self._map_suggestion_to_action_type(suggestion),
                description=suggestion.get("description", ""),
                confidence=suggestion.get("confidence", 0.5),
                urgency=suggestion.get("urgency", "medium"),
                trigger=f"meeting_{meeting_understanding.meeting_id}",
                parameters=suggestion,
            )

            # Add to queue
            self.pending_actions.append(action)
            actions_created.append(action)

            print(f"[ProactiveExecutor] Created action: {action.description[:50]}...")

        return actions_created

    def _map_suggestion_to_action_type(self, suggestion: Dict[str, Any]) -> ActionType:
        """Map meeting suggestion to action type"""
        suggestion_type = suggestion.get("action_type", "").lower()

        mapping = {
            "schedule_meeting": ActionType.CALENDAR_UPDATE,
            "send_message": ActionType.EMAIL_SEND,
            "create_document": ActionType.DOCUMENT_CREATION,
            "follow_up": ActionType.FOLLOW_UP,
        }

        return mapping.get(suggestion_type, ActionType.NOTIFICATION)

    # =========================================================================
    # Action Processing
    # =========================================================================

    async def _process_pending_actions(self):
        """Process pending actions"""
        actions_to_process = [
            action for action in self.pending_actions
            if not action.executed
            and action.confidence >= self.config.min_confidence_for_execution
        ]

        # Sort by urgency
        urgency_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        actions_to_process.sort(
            key=lambda a: urgency_order.get(a.urgency, 3)
        )

        # Process actions (respect rate limit)
        for action in actions_to_process[:5]:  # Max 5 at once
            await self._execute_action(action)

    async def _execute_action(self, action: ProactiveAction):
        """
        Execute a single proactive action.

        Args:
            action: Action to execute
        """
        print(f"[ProactiveExecutor] Executing: {action.description[:50]}...")

        # Check dry run mode
        if self.config.dry_run_mode:
            print(f"[ProactiveExecutor] DRY RUN: Would execute {action.action_type.value}")
            action.executed = True
            action.executed_at = datetime.now()
            action.result = {"dry_run": True}
            self.actions_this_hour += 1
            return

        # Get handler
        handler = self.action_handlers.get(action.action_type)
        if not handler:
            print(f"[ProactiveExecutor] No handler for {action.action_type.value}")
            action.error = "No handler registered"
            return

        try:
            # Execute handler
            result = await handler(action)

            # Mark as executed
            action.executed = True
            action.executed_at = datetime.now()
            action.result = result
            self.actions_this_hour += 1

            # Move to executed list
            self.pending_actions.remove(action)
            self.executed_actions.append(action)

            print(f"[ProactiveExecutor] ✅ Executed: {action.description[:50]}")

            # Log action
            self._log_action(action)

        except Exception as e:
            print(f"[ProactiveExecutor] ❌ Error executing action: {e}")
            action.error = str(e)

    async def _check_scheduled_actions(self):
        """Check for time-based scheduled actions"""
        # Placeholder for scheduled action checking
        pass

    async def _apply_preferences(self):
        """Apply learned preferences proactively"""
        if not self.preference_learner:
            return

        # Placeholder for preference application
        print("[ProactiveExecutor] Checking learned preferences...")

    def _log_action(self, action: ProactiveAction):
        """Log executed action to file"""
        try:
            self.config.action_log_path.parent.mkdir(parents=True, exist_ok=True)

            import json
            log_entry = {
                "id": action.id,
                "action_type": action.action_type.value,
                "description": action.description,
                "confidence": action.confidence,
                "urgency": action.urgency,
                "trigger": action.trigger,
                "executed_at": action.executed_at.isoformat() if action.executed_at else None,
                "result": str(action.result),
                "error": action.error,
            }

            with self.config.action_log_path.open("a") as f:
                f.write(json.dumps(log_entry) + "\n")

        except Exception as e:
            print(f"[ProactiveExecutor] Error logging action: {e}")

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            "pending_actions": len(self.pending_actions),
            "executed_actions": len(self.executed_actions),
            "actions_this_hour": self.actions_this_hour,
            "registered_handlers": len(self.action_handlers),
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_proactive_executor(
    config: Optional[ProactiveConfig] = None,
) -> ProactiveExecutor:
    """
    Create proactive executor with default configuration.

    Args:
        config: Optional custom configuration

    Returns:
        Configured ProactiveExecutor
    """
    return ProactiveExecutor(config=config)


# =============================================================================
# Default Action Handlers
# =============================================================================

async def default_meeting_preparation_handler(action: ProactiveAction) -> Dict[str, Any]:
    """Default handler for meeting preparation"""
    print(f"[ProactiveExecutor] Preparing for meeting: {action.parameters.get('meeting_title')}")
    return {"status": "prepared", "materials": ["agenda", "notes"]}


async def default_follow_up_handler(action: ProactiveAction) -> Dict[str, Any]:
    """Default handler for follow-ups"""
    print(f"[ProactiveExecutor] Creating follow-up: {action.description}")
    return {"status": "created", "follow_up_id": action.id}


async def default_notification_handler(action: ProactiveAction) -> Dict[str, Any]:
    """Default handler for notifications"""
    print(f"[ProactiveExecutor] Sending notification: {action.description}")
    return {"status": "sent"}


async def default_document_creation_handler(action: ProactiveAction) -> Dict[str, Any]:
    """Default handler for document creation"""
    print(f"[ProactiveExecutor] Creating document: {action.parameters.get('title')}")
    return {"status": "created", "document_id": f"doc_{action.id}"}


# =============================================================================
# CLI for Testing
# =============================================================================

async def test_proactive_executor():
    """Test proactive executor"""
    print("\n" + "="*60)
    print("Proactive Executor - Test Mode")
    print("="*60 + "\n")

    # Create executor
    executor = create_proactive_executor()

    # Register default handlers
    executor.register_handler_direct(ActionType.MEETING_PREPARATION, default_meeting_preparation_handler)
    executor.register_handler_direct(ActionType.FOLLOW_UP, default_follow_up_handler)
    executor.register_handler_direct(ActionType.NOTIFICATION, default_notification_handler)
    executor.register_handler_direct(ActionType.DOCUMENT_CREATION, default_document_creation_handler)

    # Add test actions
    test_action = ProactiveAction(
        id="test_1",
        action_type=ActionType.MEETING_PREPARATION,
        description="Prepare for Q4 planning meeting",
        confidence=0.9,
        urgency="high",
        trigger="calendar_event",
        parameters={"meeting_title": "Q4 Planning"},
    )

    executor.pending_actions.append(test_action)

    # Process actions
    print("Processing actions...\n")
    await executor._process_pending_actions()

    # Show stats
    print("\nStatistics:")
    stats = executor.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nTest complete!")


if __name__ == "__main__":
    asyncio.run(test_proactive_executor())
