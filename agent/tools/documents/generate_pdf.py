"""
PHASE 2.4: Generate PDF Tool

Tool plugin for generating PDF documents from HTML or structured data.

Features:
- HTML-to-PDF conversion (weasyprint)
- ReportLab-based reports
- Tables, headings, paragraphs
- PDF merging

Usage:
    tool = GeneratePDFTool()
    result = await tool.execute({
        "mode": "html",
        "html_path": "report.html",
        "output_path": "output/report.pdf"
    }, context)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from agent.documents.pdf_generator import PDFGenerator
from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
)

logger = logging.getLogger(__name__)


class GeneratePDFTool(ToolPlugin):
    """Generate PDF documents from HTML or structured data."""

    def get_manifest(self) -> ToolManifest:
        """Return tool manifest"""
        return ToolManifest(
            name="generate_pdf",
            version="1.0.0",
            description="Generate PDF from HTML or structured data",
            domains=["hr", "legal", "finance", "ops", "marketing", "coding"],
            roles=["manager", "supervisor", "employee", "hr_manager", "legal_counsel", "finance_controller"],
            required_permissions=["filesystem_write", "document_write"],

            input_schema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["html", "report"],
                        "description": "Generation mode"
                    },
                    "html_path": {
                        "type": "string",
                        "description": "Path to HTML file (for html mode)"
                    },
                    "title": {
                        "type": "string",
                        "description": "Report title (for report mode)"
                    },
                    "content": {
                        "type": "array",
                        "description": "Content blocks (for report mode)"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save PDF"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Optional metadata"
                    }
                },
                "required": ["mode", "output_path"]
            },

            output_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "generated": {"type": "boolean"},
                    "dry_run": {"type": "boolean"}
                }
            },

            cost_estimate=0.0,
            timeout_seconds=90,
            requires_filesystem=True,

            examples=[
                {
                    "description": "Convert HTML to PDF",
                    "input": {
                        "mode": "html",
                        "html_path": "report.html",
                        "output_path": "output/report.pdf"
                    }
                },
                {
                    "description": "Generate report",
                    "input": {
                        "mode": "report",
                        "title": "Quarterly Report",
                        "content": [
                            {"type": "heading", "text": "Summary", "level": 1},
                            {"type": "paragraph", "text": "This quarter..."}
                        ],
                        "output_path": "output/report.pdf"
                    }
                }
            ],

            tags=["document", "pdf", "generation"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Execute PDF generation"""
        try:
            mode = params["mode"]
            output_path = Path(context.project_path) / params["output_path"]

            if context.dry_run:
                logger.info(f"[DRY RUN] Would generate PDF: {output_path}")
                return ToolResult(
                    success=True,
                    data={
                        "file_path": str(output_path),
                        "generated": False,
                        "dry_run": True
                    }
                )

            generator = PDFGenerator()

            if mode == "html":
                if not params.get("html_path"):
                    return ToolResult(success=False, error="html_path required for html mode")

                html_path = Path(context.project_path) / params["html_path"]
                result_path = generator.generate_from_html(html_path, output_path)

            elif mode == "report":
                if not params.get("title") or not params.get("content"):
                    return ToolResult(success=False, error="title and content required for report mode")

                title = params["title"]
                content = params["content"]
                metadata = params.get("metadata")

                result_path = generator.generate_report(title, content, output_path, metadata)

            else:
                return ToolResult(success=False, error=f"Unknown mode: {mode}")

            logger.info(f"Generated PDF: {result_path}")

            return ToolResult(
                success=True,
                data={
                    "file_path": str(result_path),
                    "generated": True
                },
                metadata={
                    "mode": mode,
                    "size_bytes": result_path.stat().st_size
                }
            )

        except ImportError as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"help": "Install: pip install reportlab weasyprint"}
            )
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to generate PDF: {str(e)}"
            )
