"""
PHASE 2.3: Email Template Renderer

Jinja2-based template rendering system for email templates.

Features:
- Load HTML templates from filesystem
- Variable substitution
- Conditional logic and loops
- Template inheritance
- Safe HTML escaping
- Custom filters

Usage:
    renderer = EmailTemplateRenderer()
    html = renderer.render("welcome_email", {
        "candidate_name": "John Doe",
        "company_name": "Acme Corp",
        "start_date": "2025-12-01"
    })
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class EmailTemplateRenderer:
    """
    Render email templates using Jinja2 template engine.

    Templates are loaded from agent/templates/email/ directory by default.
    Templates should be named {template_name}.html.

    Example template (welcome_email.html):
        <h1>Welcome, {{ candidate_name }}!</h1>
        <p>Start date: {{ start_date }}</p>
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize email template renderer.

        Args:
            templates_dir: Directory containing email templates
                          (default: agent/templates/email/)
        """
        if templates_dir is None:
            # Default to email templates directory
            templates_dir = Path(__file__).parent / "email"

        self.templates_dir = templates_dir

        # Ensure templates directory exists
        if not self.templates_dir.exists():
            logger.warning(
                f"Email templates directory not found: {self.templates_dir}. "
                "Creating directory..."
            )
            self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape

            self.env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )

            # Add custom filters
            self.env.filters['format_date'] = self._format_date
            self.env.filters['format_currency'] = self._format_currency

            logger.debug(f"Email template renderer initialized: {self.templates_dir}")

        except ImportError:
            logger.error(
                "Jinja2 not installed. Email template rendering unavailable. "
                "Install with: pip install jinja2"
            )
            raise ImportError("Jinja2 is required for email template rendering")

    def render(self, template_name: str, variables: Dict[str, Any]) -> str:
        """
        Render email template with variables.

        Args:
            template_name: Template name (without .html extension)
            variables: Dictionary of template variables

        Returns:
            Rendered HTML string

        Raises:
            FileNotFoundError: If template not found
            Exception: If template rendering fails

        Example:
            html = renderer.render("welcome_email", {
                "candidate_name": "John Doe",
                "start_date": "2025-12-01",
                "job_title": "Software Engineer"
            })
        """
        try:
            # Load template
            template_filename = f"{template_name}.html"
            template_path = self.templates_dir / template_filename

            if not template_path.exists():
                available_templates = [
                    f.stem for f in self.templates_dir.glob("*.html")
                ]
                raise FileNotFoundError(
                    f"Email template '{template_name}' not found at {template_path}. "
                    f"Available templates: {', '.join(available_templates) if available_templates else 'none'}"
                )

            template = self.env.get_template(template_filename)

            # Render template
            html = template.render(**variables)

            logger.debug(f"Rendered template '{template_name}' ({len(html)} bytes)")

            return html

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to render template '{template_name}': {e}", exc_info=True)
            raise ValueError(f"Template rendering failed: {str(e)}")

    def render_string(self, template_string: str, variables: Dict[str, Any]) -> str:
        """
        Render template from string instead of file.

        Args:
            template_string: Template as string
            variables: Dictionary of template variables

        Returns:
            Rendered HTML string

        Example:
            html = renderer.render_string(
                "<h1>Hello {{ name }}!</h1>",
                {"name": "World"}
            )
        """
        try:
            from jinja2 import Template

            template = Template(template_string, autoescape=True)
            return template.render(**variables)

        except Exception as e:
            logger.error(f"Failed to render template string: {e}")
            raise ValueError(f"Template string rendering failed: {str(e)}")

    def list_templates(self) -> list[str]:
        """
        List available email templates.

        Returns:
            List of template names (without .html extension)
        """
        if not self.templates_dir.exists():
            return []

        return [
            template_file.stem
            for template_file in self.templates_dir.glob("*.html")
        ]

    def template_exists(self, template_name: str) -> bool:
        """
        Check if template exists.

        Args:
            template_name: Template name (without .html extension)

        Returns:
            True if template exists
        """
        template_path = self.templates_dir / f"{template_name}.html"
        return template_path.exists()

    # Custom Jinja2 filters

    def _format_date(self, date_str: str, format: str = "%B %d, %Y") -> str:
        """
        Format date string for display.

        Args:
            date_str: Date string (ISO format)
            format: strftime format string

        Returns:
            Formatted date string
        """
        try:
            from datetime import datetime
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return date.strftime(format)
        except:
            return date_str

    def _format_currency(self, amount: float, currency: str = "USD") -> str:
        """
        Format currency for display.

        Args:
            amount: Numeric amount
            currency: Currency code

        Returns:
            Formatted currency string
        """
        if currency == "USD":
            return f"${amount:,.2f}"
        elif currency == "EUR":
            return f"€{amount:,.2f}"
        elif currency == "GBP":
            return f"£{amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"


# Convenience function for quick rendering
def render_email_template(template_name: str, variables: Dict[str, Any]) -> str:
    """
    Convenience function to render email template.

    Args:
        template_name: Template name
        variables: Template variables

    Returns:
        Rendered HTML

    Example:
        html = render_email_template("welcome_email", {
            "candidate_name": "John Doe"
        })
    """
    renderer = EmailTemplateRenderer()
    return renderer.render(template_name, variables)
