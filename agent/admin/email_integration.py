"""
Email Integration Module for JARVIS

Provides intelligent email management capabilities:
- Email summarization (threads, daily digest)
- Smart response drafting with context
- Priority classification
- Action item extraction
- Outlook/Gmail plugin support
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
import re
import json


class EmailPriority(Enum):
    """Email priority levels."""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class EmailCategory(Enum):
    """Email categories for classification."""
    ACTION_REQUIRED = "action_required"
    MEETING = "meeting"
    FYI = "fyi"
    NEWSLETTER = "newsletter"
    PROMOTIONAL = "promotional"
    PERSONAL = "personal"
    AUTOMATED = "automated"
    SUPPORT = "support"


class ResponseTone(Enum):
    """Response tone options."""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    CASUAL = "casual"
    EMPATHETIC = "empathetic"
    ASSERTIVE = "assertive"


@dataclass
class EmailMessage:
    """Represents an email message."""
    id: str
    subject: str
    sender: str
    sender_email: str
    recipients: List[str]
    cc: List[str] = field(default_factory=list)
    body: str = ""
    html_body: Optional[str] = None
    timestamp: Optional[datetime] = None
    thread_id: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    is_read: bool = False
    is_flagged: bool = False
    labels: List[str] = field(default_factory=list)


@dataclass
class EmailSummary:
    """Summary of an email or thread."""
    subject: str
    key_points: List[str]
    action_items: List[str]
    sentiment: str
    priority: EmailPriority
    category: EmailCategory
    participants: List[str]
    timeline: Optional[str] = None
    decisions: List[str] = field(default_factory=list)
    questions: List[str] = field(default_factory=list)


@dataclass
class DraftResponse:
    """A drafted email response."""
    subject: str
    body: str
    tone: ResponseTone
    suggested_recipients: List[str]
    suggested_cc: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class DailyDigest:
    """Daily email digest."""
    date: str
    total_emails: int
    unread_count: int
    priority_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    action_items: List[Dict[str, str]]
    key_threads: List[Dict[str, Any]]
    summary: str


class EmailIntegration:
    """
    Email Integration Engine for JARVIS.

    Provides intelligent email analysis and response capabilities.
    """

    def __init__(self):
        """Initialize email integration."""
        # Priority keywords for classification
        self.urgent_keywords = [
            "urgent", "asap", "immediately", "critical", "emergency",
            "deadline", "time-sensitive", "priority", "important"
        ]

        self.meeting_keywords = [
            "meeting", "call", "sync", "discussion", "conference",
            "calendar", "schedule", "appointment", "invite"
        ]

        self.action_keywords = [
            "please", "could you", "can you", "need you to", "action required",
            "requesting", "follow up", "review", "approve", "sign off"
        ]

        # Sentiment patterns
        self.positive_patterns = [
            r"\b(thanks|thank you|appreciate|great|excellent|wonderful)\b",
            r"\b(pleased|happy|glad|excited|looking forward)\b"
        ]

        self.negative_patterns = [
            r"\b(concern|issue|problem|unfortunately|disappointed)\b",
            r"\b(urgent|asap|delay|failed|error|mistake)\b"
        ]

    def summarize_email(self, email: EmailMessage) -> EmailSummary:
        """
        Generate a comprehensive summary of a single email.

        Args:
            email: Email message to summarize

        Returns:
            EmailSummary with key points, actions, and classification
        """
        body_lower = email.body.lower()
        subject_lower = email.subject.lower()
        combined_text = f"{email.subject} {email.body}"

        # Extract key points (sentences with important information)
        key_points = self._extract_key_points(email.body)

        # Extract action items
        action_items = self._extract_action_items(email.body)

        # Determine sentiment
        sentiment = self._analyze_sentiment(combined_text)

        # Classify priority
        priority = self._classify_priority(email)

        # Classify category
        category = self._classify_category(email)

        # Extract participants
        participants = [email.sender] + email.recipients + email.cc
        participants = list(set(participants))

        # Extract questions
        questions = self._extract_questions(email.body)

        # Extract decisions/conclusions
        decisions = self._extract_decisions(email.body)

        return EmailSummary(
            subject=email.subject,
            key_points=key_points,
            action_items=action_items,
            sentiment=sentiment,
            priority=priority,
            category=category,
            participants=participants,
            questions=questions,
            decisions=decisions
        )

    def summarize_thread(self, emails: List[EmailMessage]) -> EmailSummary:
        """
        Generate a summary of an email thread.

        Args:
            emails: List of emails in the thread (chronological order)

        Returns:
            EmailSummary covering the entire thread
        """
        if not emails:
            raise ValueError("Empty email thread")

        # Sort by timestamp
        sorted_emails = sorted(
            emails,
            key=lambda e: e.timestamp or datetime.min
        )

        # Combine all summaries
        all_key_points = []
        all_action_items = []
        all_participants = set()
        all_questions = []
        all_decisions = []

        for email in sorted_emails:
            summary = self.summarize_email(email)
            all_key_points.extend(summary.key_points)
            all_action_items.extend(summary.action_items)
            all_participants.update(summary.participants)
            all_questions.extend(summary.questions)
            all_decisions.extend(summary.decisions)

        # Deduplicate
        key_points = list(dict.fromkeys(all_key_points))[:5]
        action_items = list(dict.fromkeys(all_action_items))
        questions = list(dict.fromkeys(all_questions))
        decisions = list(dict.fromkeys(all_decisions))

        # Overall priority (highest in thread)
        priorities = [self._classify_priority(e) for e in sorted_emails]
        priority_order = [EmailPriority.URGENT, EmailPriority.HIGH,
                        EmailPriority.NORMAL, EmailPriority.LOW]
        priority = min(priorities, key=lambda p: priority_order.index(p))

        # Timeline
        if len(sorted_emails) > 1:
            first = sorted_emails[0].timestamp
            last = sorted_emails[-1].timestamp
            if first and last:
                duration = last - first
                timeline = f"{len(sorted_emails)} messages over {self._format_duration(duration)}"
            else:
                timeline = f"{len(sorted_emails)} messages"
        else:
            timeline = "Single message"

        return EmailSummary(
            subject=sorted_emails[-1].subject,
            key_points=key_points,
            action_items=action_items,
            sentiment=self._analyze_sentiment(" ".join(e.body for e in sorted_emails)),
            priority=priority,
            category=self._classify_category(sorted_emails[-1]),
            participants=list(all_participants),
            timeline=timeline,
            questions=questions,
            decisions=decisions
        )

    def generate_daily_digest(
        self,
        emails: List[EmailMessage],
        date: Optional[datetime] = None
    ) -> DailyDigest:
        """
        Generate a daily digest of emails.

        Args:
            emails: List of emails from the day
            date: Date for the digest (defaults to today)

        Returns:
            DailyDigest with overview and key items
        """
        date = date or datetime.now()
        date_str = date.strftime("%Y-%m-%d")

        # Basic counts
        total = len(emails)
        unread = sum(1 for e in emails if not e.is_read)

        # Priority breakdown
        priority_counts = {p.value: 0 for p in EmailPriority}
        category_counts = {c.value: 0 for c in EmailCategory}

        action_items = []
        key_threads = {}

        for email in emails:
            # Classify and count
            priority = self._classify_priority(email)
            category = self._classify_category(email)

            priority_counts[priority.value] += 1
            category_counts[category.value] += 1

            # Extract action items
            items = self._extract_action_items(email.body)
            for item in items:
                action_items.append({
                    "item": item,
                    "from": email.sender,
                    "subject": email.subject,
                    "priority": priority.value
                })

            # Track threads
            thread_id = email.thread_id or email.id
            if thread_id not in key_threads:
                key_threads[thread_id] = {
                    "subject": email.subject,
                    "participants": set(),
                    "message_count": 0,
                    "priority": priority.value
                }
            key_threads[thread_id]["participants"].add(email.sender)
            key_threads[thread_id]["message_count"] += 1

        # Convert threads to list and sort by activity
        threads_list = [
            {
                "subject": t["subject"],
                "participants": list(t["participants"]),
                "message_count": t["message_count"],
                "priority": t["priority"]
            }
            for t in key_threads.values()
        ]
        threads_list.sort(key=lambda x: x["message_count"], reverse=True)

        # Generate summary text
        summary = self._generate_digest_summary(
            total, unread, priority_counts, category_counts, action_items
        )

        return DailyDigest(
            date=date_str,
            total_emails=total,
            unread_count=unread,
            priority_breakdown=priority_counts,
            category_breakdown=category_counts,
            action_items=action_items[:10],  # Top 10
            key_threads=threads_list[:5],  # Top 5 threads
            summary=summary
        )

    def draft_response(
        self,
        email: EmailMessage,
        intent: str,
        tone: ResponseTone = ResponseTone.PROFESSIONAL,
        context: Optional[str] = None,
        include_greeting: bool = True,
        include_signature: bool = True
    ) -> DraftResponse:
        """
        Draft a response to an email.

        Args:
            email: Original email to respond to
            intent: What the response should communicate
            tone: Desired tone of the response
            context: Additional context for the response
            include_greeting: Whether to include a greeting
            include_signature: Whether to include a signature placeholder

        Returns:
            DraftResponse with suggested response text
        """
        # Extract sender's first name for greeting
        sender_name = self._extract_first_name(email.sender)

        # Build response components
        greeting = self._get_greeting(sender_name, tone) if include_greeting else ""

        # Generate body based on intent and context
        body_content = self._generate_response_body(
            email, intent, tone, context
        )

        # Add signature placeholder
        signature = "\n\nBest regards,\n[Your Name]" if include_signature else ""

        # Combine
        full_body = f"{greeting}\n\n{body_content}{signature}"

        # Generate alternative responses
        alternatives = self._generate_alternatives(email, intent, tone)

        # Determine recipients
        suggested_recipients = [email.sender_email]
        suggested_cc = []

        # If replying to all, include others
        if "all" in intent.lower():
            suggested_recipients.extend(email.recipients)
            suggested_cc = email.cc

        # Determine subject
        subject = email.subject
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        return DraftResponse(
            subject=subject,
            body=full_body.strip(),
            tone=tone,
            suggested_recipients=list(set(suggested_recipients)),
            suggested_cc=list(set(suggested_cc)),
            alternatives=alternatives,
            confidence=0.85
        )

    def classify_emails(
        self,
        emails: List[EmailMessage]
    ) -> Dict[str, List[EmailMessage]]:
        """
        Classify a batch of emails by category and priority.

        Args:
            emails: List of emails to classify

        Returns:
            Dict with classified emails
        """
        result = {
            "urgent": [],
            "action_required": [],
            "meetings": [],
            "fyi": [],
            "newsletters": [],
            "other": []
        }

        for email in emails:
            priority = self._classify_priority(email)
            category = self._classify_category(email)

            if priority == EmailPriority.URGENT:
                result["urgent"].append(email)
            elif category == EmailCategory.ACTION_REQUIRED:
                result["action_required"].append(email)
            elif category == EmailCategory.MEETING:
                result["meetings"].append(email)
            elif category == EmailCategory.FYI:
                result["fyi"].append(email)
            elif category == EmailCategory.NEWSLETTER:
                result["newsletters"].append(email)
            else:
                result["other"].append(email)

        return result

    def suggest_quick_replies(
        self,
        email: EmailMessage
    ) -> List[Dict[str, str]]:
        """
        Generate quick reply suggestions for an email.

        Args:
            email: Email to generate replies for

        Returns:
            List of quick reply options
        """
        replies = []

        # Analyze email content
        is_question = "?" in email.body
        is_meeting_request = any(
            kw in email.body.lower() for kw in self.meeting_keywords
        )
        is_action_request = any(
            kw in email.body.lower() for kw in self.action_keywords
        )

        sender_name = self._extract_first_name(email.sender)

        if is_meeting_request:
            replies.extend([
                {
                    "label": "Accept",
                    "text": f"Hi {sender_name},\n\nThat time works for me. Looking forward to it.\n\nBest regards"
                },
                {
                    "label": "Decline",
                    "text": f"Hi {sender_name},\n\nUnfortunately, I'm not available at that time. Could we find an alternative?\n\nBest regards"
                },
                {
                    "label": "Tentative",
                    "text": f"Hi {sender_name},\n\nLet me check my schedule and get back to you shortly.\n\nBest regards"
                }
            ])
        elif is_question:
            replies.extend([
                {
                    "label": "Will check",
                    "text": f"Hi {sender_name},\n\nGood question. Let me look into this and get back to you.\n\nBest regards"
                },
                {
                    "label": "Confirm",
                    "text": f"Hi {sender_name},\n\nYes, that's correct.\n\nBest regards"
                },
                {
                    "label": "Deny",
                    "text": f"Hi {sender_name},\n\nActually, that's not quite right. Let me clarify...\n\nBest regards"
                }
            ])
        elif is_action_request:
            replies.extend([
                {
                    "label": "On it",
                    "text": f"Hi {sender_name},\n\nThanks for reaching out. I'll take care of this and update you once done.\n\nBest regards"
                },
                {
                    "label": "Need more info",
                    "text": f"Hi {sender_name},\n\nThanks for this. Before I proceed, could you clarify...\n\nBest regards"
                },
                {
                    "label": "Delegate",
                    "text": f"Hi {sender_name},\n\nI've looped in the right person to help with this.\n\nBest regards"
                }
            ])
        else:
            replies.extend([
                {
                    "label": "Acknowledge",
                    "text": f"Hi {sender_name},\n\nThanks for the update.\n\nBest regards"
                },
                {
                    "label": "Follow up",
                    "text": f"Hi {sender_name},\n\nThanks for sharing. I have a follow-up question...\n\nBest regards"
                }
            ])

        return replies

    # Private helper methods

    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from email body."""
        key_points = []

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        # Filter for substantive sentences
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            # Check for key indicators
            has_numbers = bool(re.search(r'\d+', sentence))
            has_names = bool(re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', sentence))
            has_dates = bool(re.search(
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|'
                r'january|february|march|april|may|june|july|august|september|'
                r'october|november|december|\d{1,2}/\d{1,2}|\d{4})\b',
                sentence.lower()
            ))
            has_action_words = any(
                kw in sentence.lower() for kw in self.action_keywords
            )

            if has_numbers or has_names or has_dates or has_action_words:
                key_points.append(sentence)

        return key_points[:5]  # Top 5 key points

    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from email body."""
        action_items = []

        # Patterns for action items
        patterns = [
            r"please\s+(.+?)[.\n]",
            r"could you\s+(.+?)[.\n?]",
            r"can you\s+(.+?)[.\n?]",
            r"need you to\s+(.+?)[.\n]",
            r"action required[:\s]+(.+?)[.\n]",
            r"todo[:\s]+(.+?)[.\n]",
            r"- \[ \]\s*(.+?)[\n]",  # Markdown checkbox
            r"\*\s+(.+?)[\n]",  # Bullet points
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 10 and len(match) < 200:
                    action_items.append(match.strip())

        return list(dict.fromkeys(action_items))  # Deduplicate

    def _extract_questions(self, text: str) -> List[str]:
        """Extract questions from email body."""
        questions = []

        # Find sentences ending with ?
        sentences = re.split(r'(?<=[.!?])\s+', text)
        for sentence in sentences:
            if sentence.strip().endswith('?'):
                questions.append(sentence.strip())

        return questions

    def _extract_decisions(self, text: str) -> List[str]:
        """Extract decisions or conclusions from email body."""
        decisions = []

        # Decision indicators
        patterns = [
            r"(?:we've decided|decided to|decision is|concluded that)\s+(.+?)[.\n]",
            r"(?:going forward|moving forward)[,\s]+(.+?)[.\n]",
            r"(?:final answer|in conclusion)[:\s]+(.+?)[.\n]",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            decisions.extend(matches)

        return list(dict.fromkeys(decisions))

    def _analyze_sentiment(self, text: str) -> str:
        """Analyze overall sentiment of text."""
        text_lower = text.lower()

        positive_score = sum(
            len(re.findall(pattern, text_lower))
            for pattern in self.positive_patterns
        )

        negative_score = sum(
            len(re.findall(pattern, text_lower))
            for pattern in self.negative_patterns
        )

        if positive_score > negative_score + 2:
            return "positive"
        elif negative_score > positive_score + 2:
            return "negative"
        else:
            return "neutral"

    def _classify_priority(self, email: EmailMessage) -> EmailPriority:
        """Classify email priority."""
        combined = f"{email.subject} {email.body}".lower()

        # Check for urgent indicators
        if any(kw in combined for kw in self.urgent_keywords):
            return EmailPriority.URGENT

        # Check for flagged
        if email.is_flagged:
            return EmailPriority.HIGH

        # Check for action required
        if any(kw in combined for kw in self.action_keywords[:5]):
            return EmailPriority.HIGH

        # Check for newsletters/promotional
        if any(kw in combined for kw in ["unsubscribe", "newsletter", "promotional"]):
            return EmailPriority.LOW

        return EmailPriority.NORMAL

    def _classify_category(self, email: EmailMessage) -> EmailCategory:
        """Classify email category."""
        combined = f"{email.subject} {email.body}".lower()

        # Meeting related
        if any(kw in combined for kw in self.meeting_keywords):
            return EmailCategory.MEETING

        # Action required
        if any(kw in combined for kw in self.action_keywords):
            return EmailCategory.ACTION_REQUIRED

        # Newsletter
        if "unsubscribe" in combined or "newsletter" in combined:
            return EmailCategory.NEWSLETTER

        # Promotional
        if any(kw in combined for kw in ["sale", "discount", "offer", "promo"]):
            return EmailCategory.PROMOTIONAL

        # Automated
        if any(kw in combined for kw in ["noreply", "no-reply", "automated", "notification"]):
            return EmailCategory.AUTOMATED

        # Support
        if any(kw in combined for kw in ["ticket", "support", "help desk", "case #"]):
            return EmailCategory.SUPPORT

        return EmailCategory.FYI

    def _extract_first_name(self, full_name: str) -> str:
        """Extract first name from full name or email."""
        # Try to extract from "First Last" format
        parts = full_name.split()
        if parts:
            first = parts[0]
            # Remove any email formatting
            if "<" in first:
                first = first.split("<")[0].strip()
            return first.title()
        return "there"

    def _get_greeting(self, name: str, tone: ResponseTone) -> str:
        """Generate appropriate greeting based on tone."""
        greetings = {
            ResponseTone.FORMAL: f"Dear {name},",
            ResponseTone.PROFESSIONAL: f"Hi {name},",
            ResponseTone.FRIENDLY: f"Hey {name}!",
            ResponseTone.CASUAL: f"Hi {name},",
            ResponseTone.EMPATHETIC: f"Hi {name},",
            ResponseTone.ASSERTIVE: f"{name},"
        }
        return greetings.get(tone, f"Hi {name},")

    def _generate_response_body(
        self,
        email: EmailMessage,
        intent: str,
        tone: ResponseTone,
        context: Optional[str]
    ) -> str:
        """Generate response body based on intent."""
        intent_lower = intent.lower()

        # Common response templates
        if "acknowledge" in intent_lower or "thank" in intent_lower:
            return "Thank you for your email. I've received your message and will review it shortly."

        if "confirm" in intent_lower:
            return "I'm writing to confirm receipt of your message. Everything looks good on my end."

        if "decline" in intent_lower or "reject" in intent_lower:
            return "Thank you for thinking of me. Unfortunately, I won't be able to accommodate this request at this time."

        if "follow up" in intent_lower:
            return "I wanted to follow up on my previous message. Please let me know if you have any questions."

        if "request" in intent_lower:
            return f"I'm reaching out regarding {context or 'a matter that requires your attention'}. Could you please provide your input?"

        if "meeting" in intent_lower:
            return "I'd like to schedule some time to discuss this further. Would you be available for a brief call?"

        # Default - use intent as basis
        return f"Regarding your message: {intent}"

    def _generate_alternatives(
        self,
        email: EmailMessage,
        intent: str,
        tone: ResponseTone
    ) -> List[str]:
        """Generate alternative response options."""
        alternatives = []

        # More formal version
        if tone != ResponseTone.FORMAL:
            alternatives.append(
                "I acknowledge receipt of your correspondence and will respond in due course."
            )

        # More casual version
        if tone != ResponseTone.CASUAL:
            alternatives.append(
                "Got it, thanks! I'll take a look and get back to you soon."
            )

        return alternatives

    def _generate_digest_summary(
        self,
        total: int,
        unread: int,
        priority_counts: Dict[str, int],
        category_counts: Dict[str, int],
        action_items: List[Dict]
    ) -> str:
        """Generate digest summary text."""
        parts = []

        parts.append(f"You have {total} emails today ({unread} unread).")

        if priority_counts["urgent"] > 0:
            parts.append(f"{priority_counts['urgent']} urgent emails require immediate attention.")

        if priority_counts["high"] > 0:
            parts.append(f"{priority_counts['high']} high-priority items to address.")

        if len(action_items) > 0:
            parts.append(f"{len(action_items)} action items extracted from your emails.")

        if category_counts["meeting"] > 0:
            parts.append(f"{category_counts['meeting']} meeting-related emails.")

        return " ".join(parts)

    def _format_duration(self, duration: timedelta) -> str:
        """Format duration in human-readable form."""
        days = duration.days
        hours = duration.seconds // 3600

        if days > 0:
            return f"{days} day{'s' if days > 1 else ''}"
        elif hours > 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            minutes = duration.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
