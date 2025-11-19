"""
PHASE 2.3: Email Template System

Jinja2-based email template rendering for HR tools.

Templates are stored in agent/templates/email/ directory and can include:
- HTML email templates
- Variable substitution
- Conditional logic
- Template inheritance

Usage:
    from agent.templates.email_renderer import EmailTemplateRenderer
    renderer = EmailTemplateRenderer()
    html = renderer.render("welcome_email", {
        "candidate_name": "John Doe",
        "start_date": "2025-12-01"
    })
"""

__all__ = ["EmailTemplateRenderer"]

from .email_renderer import EmailTemplateRenderer
