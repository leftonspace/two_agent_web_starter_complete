"""
Admin API Router for JARVIS

Provides HTTP endpoints for:
- Email integration (summarization, drafting, classification)
- Calendar intelligence (meeting briefs, action items, scheduling)
- Workflow automation (triggers, actions, execution)
"""

from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os
import sys

# Add admin module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from admin.email_integration import (
    EmailIntegration,
    EmailMessage,
    ResponseTone,
)
from admin.calendar_intelligence import (
    CalendarIntelligence,
    CalendarEvent,
    Attendee,
)
from admin.workflow_automation import (
    WorkflowEngine,
    TriggerType,
    ActionType,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Initialize engines
email_engine = EmailIntegration()
calendar_engine = CalendarIntelligence()
workflow_engine = WorkflowEngine()


# ============================================================================
# Request/Response Models
# ============================================================================

class EmailRequest(BaseModel):
    """Email data for analysis."""
    id: str
    subject: str
    sender: str
    sender_email: str
    recipients: List[str]
    body: str
    timestamp: Optional[str] = None
    thread_id: Optional[str] = None


class EmailSummaryResponse(BaseModel):
    """Email summary response."""
    subject: str
    key_points: List[str]
    action_items: List[str]
    sentiment: str
    priority: str
    category: str
    participants: List[str]


class DraftRequest(BaseModel):
    """Request for email draft."""
    email: EmailRequest
    intent: str
    tone: str = "professional"
    context: Optional[str] = None


class DraftResponse(BaseModel):
    """Email draft response."""
    subject: str
    body: str
    tone: str
    suggested_recipients: List[str]
    alternatives: List[str]


class CalendarEventRequest(BaseModel):
    """Calendar event data."""
    id: str
    title: str
    start_time: str
    end_time: str
    attendees: Optional[List[Dict[str, Any]]] = None
    location: Optional[str] = None
    description: Optional[str] = None
    meeting_link: Optional[str] = None


class MeetingBriefResponse(BaseModel):
    """Meeting brief response."""
    meeting_type: str
    priority: str
    preparation_items: List[str]
    talking_points: List[str]
    relevant_context: List[str]
    suggested_questions: List[str]
    recommendations: List[str]


class ActionItemsRequest(BaseModel):
    """Request for action item extraction."""
    meeting_notes: str
    meeting_id: str
    meeting_title: str
    attendees: List[str]


class ActionItemResponse(BaseModel):
    """Action item response."""
    id: str
    description: str
    assignee: Optional[str]
    due_date: Optional[str]
    priority: str
    status: str


class ScheduleOptimizationRequest(BaseModel):
    """Request for schedule optimization."""
    events: List[CalendarEventRequest]
    date: Optional[str] = None
    work_hours: Optional[List[int]] = None


class WorkflowRequest(BaseModel):
    """Workflow creation request."""
    name: str
    description: str
    trigger_config: Dict[str, Any]
    steps: List[Dict[str, Any]]
    tags: Optional[List[str]] = None


class WorkflowExecuteRequest(BaseModel):
    """Workflow execution request."""
    trigger_data: Dict[str, Any]


# ============================================================================
# Email Integration Endpoints
# ============================================================================

@router.post("/email/summarize", response_model=EmailSummaryResponse)
async def summarize_email(request: EmailRequest):
    """
    Generate AI summary of an email.

    Extracts key points, action items, and classifies priority/sentiment.
    """
    try:
        email = EmailMessage(
            id=request.id,
            subject=request.subject,
            sender=request.sender,
            sender_email=request.sender_email,
            recipients=request.recipients,
            body=request.body,
            timestamp=datetime.fromisoformat(request.timestamp) if request.timestamp else None,
            thread_id=request.thread_id
        )

        summary = email_engine.summarize_email(email)

        return EmailSummaryResponse(
            subject=summary.subject,
            key_points=summary.key_points,
            action_items=summary.action_items,
            sentiment=summary.sentiment,
            priority=summary.priority.value,
            category=summary.category.value,
            participants=summary.participants
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/summarize-thread")
async def summarize_thread(emails: List[EmailRequest]):
    """
    Generate summary of an email thread.

    Combines multiple emails into a coherent thread summary.
    """
    try:
        email_objects = [
            EmailMessage(
                id=e.id,
                subject=e.subject,
                sender=e.sender,
                sender_email=e.sender_email,
                recipients=e.recipients,
                body=e.body,
                timestamp=datetime.fromisoformat(e.timestamp) if e.timestamp else None,
                thread_id=e.thread_id
            )
            for e in emails
        ]

        summary = email_engine.summarize_thread(email_objects)

        return {
            "subject": summary.subject,
            "key_points": summary.key_points,
            "action_items": summary.action_items,
            "sentiment": summary.sentiment,
            "priority": summary.priority.value,
            "category": summary.category.value,
            "participants": summary.participants,
            "timeline": summary.timeline,
            "decisions": summary.decisions,
            "questions": summary.questions
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/draft", response_model=DraftResponse)
async def draft_response(request: DraftRequest):
    """
    Generate AI-drafted email response.

    Creates a response based on the original email and user intent.
    """
    try:
        email = EmailMessage(
            id=request.email.id,
            subject=request.email.subject,
            sender=request.email.sender,
            sender_email=request.email.sender_email,
            recipients=request.email.recipients,
            body=request.email.body
        )

        tone = ResponseTone(request.tone) if request.tone else ResponseTone.PROFESSIONAL

        draft = email_engine.draft_response(
            email=email,
            intent=request.intent,
            tone=tone,
            context=request.context
        )

        return DraftResponse(
            subject=draft.subject,
            body=draft.body,
            tone=draft.tone.value,
            suggested_recipients=draft.suggested_recipients,
            alternatives=draft.alternatives
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/quick-replies")
async def get_quick_replies(request: EmailRequest):
    """
    Generate quick reply suggestions for an email.

    Returns 3-5 contextual quick reply options.
    """
    try:
        email = EmailMessage(
            id=request.id,
            subject=request.subject,
            sender=request.sender,
            sender_email=request.sender_email,
            recipients=request.recipients,
            body=request.body
        )

        replies = email_engine.suggest_quick_replies(email)
        return replies
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/classify")
async def classify_email(request: EmailRequest):
    """
    Classify an email by priority, category, and sentiment.
    """
    try:
        email = EmailMessage(
            id=request.id,
            subject=request.subject,
            sender=request.sender,
            sender_email=request.sender_email,
            recipients=request.recipients,
            body=request.body
        )

        summary = email_engine.summarize_email(email)

        return {
            "priority": summary.priority.value,
            "category": summary.category.value,
            "sentiment": summary.sentiment,
            "requires_action": len(summary.action_items) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/email/daily-digest")
async def generate_daily_digest(emails: List[EmailRequest]):
    """
    Generate a daily email digest.

    Summarizes all emails with priority breakdown and action items.
    """
    try:
        email_objects = [
            EmailMessage(
                id=e.id,
                subject=e.subject,
                sender=e.sender,
                sender_email=e.sender_email,
                recipients=e.recipients,
                body=e.body,
                timestamp=datetime.fromisoformat(e.timestamp) if e.timestamp else None
            )
            for e in emails
        ]

        digest = email_engine.generate_daily_digest(email_objects)

        return {
            "date": digest.date,
            "total_emails": digest.total_emails,
            "unread_count": digest.unread_count,
            "priority_breakdown": digest.priority_breakdown,
            "category_breakdown": digest.category_breakdown,
            "action_items": digest.action_items,
            "key_threads": digest.key_threads,
            "summary": digest.summary
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Calendar Intelligence Endpoints
# ============================================================================

@router.post("/calendar/meeting-brief", response_model=MeetingBriefResponse)
async def generate_meeting_brief(request: CalendarEventRequest):
    """
    Generate a meeting preparation brief.

    Provides talking points, preparation items, and context.
    """
    try:
        attendees = []
        if request.attendees:
            for a in request.attendees:
                attendees.append(Attendee(
                    email=a.get("email", ""),
                    name=a.get("name", ""),
                    required=a.get("required", True)
                ))

        event = CalendarEvent(
            id=request.id,
            title=request.title,
            start_time=datetime.fromisoformat(request.start_time),
            end_time=datetime.fromisoformat(request.end_time),
            attendees=attendees,
            location=request.location,
            description=request.description,
            meeting_link=request.meeting_link
        )

        brief = calendar_engine.generate_meeting_brief(event)

        return MeetingBriefResponse(
            meeting_type=brief.meeting_type.value,
            priority=brief.priority.value,
            preparation_items=brief.preparation_items,
            talking_points=brief.talking_points,
            relevant_context=brief.relevant_context,
            suggested_questions=brief.suggested_questions,
            recommendations=brief.recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calendar/action-items")
async def extract_action_items(request: ActionItemsRequest):
    """
    Extract action items from meeting notes.

    Identifies tasks, assignees, and due dates.
    """
    try:
        items = calendar_engine.extract_action_items(
            meeting_notes=request.meeting_notes,
            meeting_id=request.meeting_id,
            meeting_title=request.meeting_title,
            attendees=request.attendees
        )

        return [
            ActionItemResponse(
                id=item.id,
                description=item.description,
                assignee=item.assignee,
                due_date=item.due_date.isoformat() if item.due_date else None,
                priority=item.priority,
                status=item.status
            )
            for item in items
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calendar/meeting-summary")
async def generate_meeting_summary(
    event: CalendarEventRequest,
    notes: str = Form(...),
    transcript: Optional[str] = Form(None)
):
    """
    Generate structured meeting notes from raw notes/transcript.
    """
    try:
        attendees = []
        if event.attendees:
            for a in event.attendees:
                attendees.append(Attendee(
                    email=a.get("email", ""),
                    name=a.get("name", "")
                ))

        cal_event = CalendarEvent(
            id=event.id,
            title=event.title,
            start_time=datetime.fromisoformat(event.start_time),
            end_time=datetime.fromisoformat(event.end_time),
            attendees=attendees
        )

        meeting_notes = calendar_engine.generate_meeting_summary(
            cal_event, notes, transcript
        )

        return {
            "meeting_id": meeting_notes.meeting_id,
            "title": meeting_notes.title,
            "date": meeting_notes.date.isoformat(),
            "attendees": meeting_notes.attendees,
            "summary": meeting_notes.summary,
            "key_decisions": meeting_notes.key_decisions,
            "action_items": [
                {
                    "id": item.id,
                    "description": item.description,
                    "assignee": item.assignee,
                    "due_date": item.due_date.isoformat() if item.due_date else None
                }
                for item in meeting_notes.action_items
            ],
            "discussion_points": meeting_notes.discussion_points,
            "follow_ups": meeting_notes.follow_ups,
            "next_meeting": meeting_notes.next_meeting
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calendar/optimize-schedule")
async def optimize_schedule(request: ScheduleOptimizationRequest):
    """
    Analyze and optimize a day's schedule.

    Provides recommendations for better time management.
    """
    try:
        events = []
        for e in request.events:
            attendees = []
            if e.attendees:
                for a in e.attendees:
                    attendees.append(Attendee(
                        email=a.get("email", ""),
                        name=a.get("name", "")
                    ))

            events.append(CalendarEvent(
                id=e.id,
                title=e.title,
                start_time=datetime.fromisoformat(e.start_time),
                end_time=datetime.fromisoformat(e.end_time),
                attendees=attendees,
                location=e.location,
                description=e.description
            ))

        date = datetime.fromisoformat(request.date) if request.date else None
        work_hours = tuple(request.work_hours) if request.work_hours else (9, 17)

        optimization = calendar_engine.optimize_schedule(
            events, date, work_hours
        )

        return {
            "date": optimization.date,
            "total_meeting_hours": optimization.total_meeting_hours,
            "focus_time_hours": optimization.focus_time_hours,
            "fragmentation_score": optimization.fragmentation_score,
            "productivity_score": optimization.productivity_score,
            "recommendations": optimization.recommendations,
            "suggested_reschedules": optimization.suggested_reschedules,
            "time_blocks": optimization.time_blocks
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calendar/find-slots")
async def find_meeting_slots(
    duration_minutes: int,
    start_date: str,
    end_date: str,
    events: List[CalendarEventRequest],
    preferences: Optional[Dict[str, Any]] = None
):
    """
    Find optimal time slots for a new meeting.
    """
    try:
        event_objects = []
        for e in events:
            event_objects.append(CalendarEvent(
                id=e.id,
                title=e.title,
                start_time=datetime.fromisoformat(e.start_time),
                end_time=datetime.fromisoformat(e.end_time)
            ))

        slots = calendar_engine.find_optimal_slots(
            events=event_objects,
            duration_minutes=duration_minutes,
            date_range=(
                datetime.fromisoformat(start_date),
                datetime.fromisoformat(end_date)
            ),
            preferences=preferences
        )

        return [
            {
                "start": slot.start.isoformat(),
                "end": slot.end.isoformat(),
                "score": slot.score,
                "conflicts": slot.conflicts
            }
            for slot in slots
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/calendar/detect-conflicts")
async def detect_conflicts(events: List[CalendarEventRequest]):
    """
    Detect scheduling conflicts in calendar events.
    """
    try:
        event_objects = []
        for e in events:
            event_objects.append(CalendarEvent(
                id=e.id,
                title=e.title,
                start_time=datetime.fromisoformat(e.start_time),
                end_time=datetime.fromisoformat(e.end_time)
            ))

        conflicts = calendar_engine.detect_conflicts(event_objects)
        return {"conflicts": conflicts}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Workflow Automation Endpoints
# ============================================================================

@router.post("/workflow/create")
async def create_workflow(request: WorkflowRequest):
    """
    Create a new automation workflow.
    """
    try:
        workflow = workflow_engine.create_workflow(
            name=request.name,
            description=request.description,
            trigger_config=request.trigger_config,
            steps=request.steps,
            tags=request.tags
        )

        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "enabled": workflow.enabled,
            "trigger_type": workflow.trigger.type.value,
            "step_count": len(workflow.steps),
            "tags": workflow.tags
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflow/{workflow_id}")
async def get_workflow(workflow_id: str):
    """
    Get workflow details.
    """
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "enabled": workflow.enabled,
        "trigger": {
            "type": workflow.trigger.type.value,
            "name": workflow.trigger.name,
            "config": workflow.trigger.config
        },
        "steps": [
            {
                "id": step.id,
                "action_type": step.action.type.value,
                "name": step.action.name,
                "config": step.action.config
            }
            for step in workflow.steps
        ],
        "tags": workflow.tags,
        "created_at": workflow.created_at.isoformat(),
        "updated_at": workflow.updated_at.isoformat(),
        "version": workflow.version
    }


@router.get("/workflows")
async def list_workflows(
    tags: Optional[str] = None,
    enabled_only: bool = False
):
    """
    List all workflows.
    """
    tag_list = tags.split(",") if tags else None
    workflows = workflow_engine.list_workflows(
        tags=tag_list,
        enabled_only=enabled_only
    )

    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "enabled": w.enabled,
            "trigger_type": w.trigger.type.value,
            "tags": w.tags
        }
        for w in workflows
    ]


@router.post("/workflow/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: WorkflowExecuteRequest):
    """
    Execute a workflow with trigger data.
    """
    try:
        context = await workflow_engine.execute_workflow(
            workflow_id=workflow_id,
            trigger_data=request.trigger_data
        )

        return {
            "execution_id": context.execution_id,
            "workflow_id": context.workflow_id,
            "status": context.status.value,
            "started_at": context.started_at.isoformat(),
            "step_outputs": context.step_outputs,
            "error": context.error
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflow/{workflow_id}/executions/{execution_id}")
async def get_execution(workflow_id: str, execution_id: str):
    """
    Get execution details.
    """
    context = workflow_engine.get_execution(execution_id)
    if not context:
        raise HTTPException(status_code=404, detail="Execution not found")

    logs = workflow_engine.get_execution_logs(execution_id)

    return {
        "execution_id": context.execution_id,
        "workflow_id": context.workflow_id,
        "status": context.status.value,
        "started_at": context.started_at.isoformat(),
        "current_step": context.current_step,
        "step_outputs": context.step_outputs,
        "error": context.error,
        "logs": [
            {
                "timestamp": log.timestamp.isoformat(),
                "step_id": log.step_id,
                "action_type": log.action_type,
                "status": log.status,
                "duration_ms": log.duration_ms,
                "error": log.error
            }
            for log in logs
        ]
    }


@router.put("/workflow/{workflow_id}")
async def update_workflow(workflow_id: str, updates: Dict[str, Any]):
    """
    Update a workflow.
    """
    workflow = workflow_engine.update_workflow(workflow_id, updates)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {
        "id": workflow.id,
        "name": workflow.name,
        "enabled": workflow.enabled,
        "version": workflow.version,
        "updated_at": workflow.updated_at.isoformat()
    }


@router.delete("/workflow/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """
    Delete a workflow.
    """
    success = workflow_engine.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"success": True, "message": "Workflow deleted"}


@router.post("/webhook/{path:path}")
async def handle_webhook(path: str, payload: Dict[str, Any]):
    """
    Handle incoming webhooks for workflow triggers.
    """
    webhook_path = f"/webhook/{path}"
    execution_id = workflow_engine.handle_webhook(webhook_path, payload)

    if not execution_id:
        raise HTTPException(
            status_code=404,
            detail=f"No workflow registered for webhook: {webhook_path}"
        )

    return {
        "accepted": True,
        "execution_id": execution_id,
        "webhook_path": webhook_path
    }


# Pre-built workflow templates

@router.post("/workflow/templates/zapier-webhook")
async def create_zapier_webhook(
    name: str,
    webhook_path: str,
    target_url: str,
    transform: Optional[Dict[str, Any]] = None
):
    """
    Create a Zapier-style webhook workflow.
    """
    try:
        workflow = workflow_engine.create_zapier_webhook_workflow(
            name=name,
            webhook_path=webhook_path,
            target_url=target_url,
            transform_config=transform
        )

        return {
            "id": workflow.id,
            "name": workflow.name,
            "webhook_url": f"/api/admin{webhook_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflow/templates/email-automation")
async def create_email_automation(
    name: str,
    trigger_keywords: List[str],
    response_template: str,
    ai_process: bool = False
):
    """
    Create an email automation workflow.
    """
    try:
        workflow = workflow_engine.create_email_automation(
            name=name,
            trigger_keywords=trigger_keywords,
            response_template=response_template,
            ai_process=ai_process
        )

        return {
            "id": workflow.id,
            "name": workflow.name,
            "trigger_keywords": trigger_keywords
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/workflow/templates/scheduled-report")
async def create_scheduled_report(
    name: str,
    schedule: str,
    data_source_url: str,
    recipients: List[str]
):
    """
    Create a scheduled report workflow.
    """
    try:
        workflow = workflow_engine.create_scheduled_report(
            name=name,
            schedule=schedule,
            data_source_url=data_source_url,
            recipients=recipients
        )

        return {
            "id": workflow.id,
            "name": workflow.name,
            "schedule": schedule,
            "recipients": recipients
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check
@router.get("/health")
async def admin_health():
    """Check admin API health status."""
    return {
        "status": "healthy",
        "modules": {
            "email_integration": "active",
            "calendar_intelligence": "active",
            "workflow_automation": "active"
        },
        "workflows_count": len(workflow_engine.workflows)
    }
