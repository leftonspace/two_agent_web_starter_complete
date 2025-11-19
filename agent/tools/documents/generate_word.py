"""
PHASE 2.4: Generate Word Document Tool

Tool plugin for generating .docx Word documents from templates or structured data.

Features:
- Template-based generation with variable substitution
- Structure-based generation from dictionaries
- Tables, headings, paragraphs
- Document metadata

Usage:
    tool = GenerateWordDocumentTool()
    result = await tool.execute({
        "mode": "template",
        "template_path": "templates/offer_letter.docx",
        "template_vars": {"candidate_name": "John Doe"},
        "output_path": "output/offer.docx"
    }, context)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from agent.documents.word_generator import WordDocumentGenerator
from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
)

logger = logging.getLogger(__name__)


class GenerateWordDocumentTool(ToolPlugin):
    """
    Generate .docx Word documents from templates or structured data.

    Supports:
    - Template mode: Use .docx template with {{variable}} placeholders
    - Structure mode: Generate from dictionary structure
    - Document metadata (author, title, subject)
    - Dry run mode
    """

    def get_manifest(self) -> ToolManifest:
        """Return tool manifest with metadata and schema"""
        return ToolManifest(
            name="generate_word_document",
            version="1.0.0",
            description="Generate .docx Word document from template or structured data",
            domains=["hr", "legal", "finance", "ops", "marketing", "coding"],
            roles=["manager", "supervisor", "employee", "hr_manager", "hr_recruiter", "legal_counsel", "finance_controller"],
            required_permissions=["filesystem_write", "document_write"],

            input_schema={
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["template", "structure"],
                        "description": "Generation mode"
                    },
                    "template_path": {
                        "type": "string",
                        "description": "Path to template .docx file (for template mode)"
                    },
                    "template_vars": {
                        "type": "object",
                        "description": "Variables for template substitution (for template mode)"
                    },
                    "structure": {
                        "type": "object",
                        "description": "Document structure (for structure mode)",
                        "properties": {
                            "title": {"type": "string"},
                            "sections": {"type": "array"},
                            "tables": {"type": "array"}
                        }
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save generated document (relative to project)"
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "author": {"type": "string"},
                            "title": {"type": "string"},
                            "subject": {"type": "string"}
                        },
                        "description": "Document metadata"
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
                },
                "required": ["file_path", "generated"]
            },

            cost_estimate=0.0,
            timeout_seconds=60,
            requires_filesystem=True,

            examples=[
                {
                    "description": "Generate offer letter from template",
                    "input": {
                        "mode": "template",
                        "template_path": "templates/hr/offer_letter.docx",
                        "template_vars": {
                            "candidate_name": "John Doe",
                            "job_title": "Software Engineer",
                            "salary": "$120,000",
                            "start_date": "2025-12-01",
                            "department": "Engineering"
                        },
                        "output_path": "output/offer_letter_john_doe.docx"
                    },
                    "output": {
                        "file_path": "/project/output/offer_letter_john_doe.docx",
                        "generated": True
                    }
                },
                {
                    "description": "Generate report from structure",
                    "input": {
                        "mode": "structure",
                        "structure": {
                            "title": "Quarterly Report",
                            "sections": [
                                {
                                    "heading": "Executive Summary",
                                    "level": 1,
                                    "content": "This quarter showed strong growth..."
                                }
                            ]
                        },
                        "output_path": "output/quarterly_report.docx",
                        "metadata": {
                            "author": "Finance Team",
                            "title": "Q4 2025 Report",
                            "subject": "Quarterly Financial Results"
                        }
                    },
                    "output": {
                        "file_path": "/project/output/quarterly_report.docx",
                        "generated": True
                    }
                }
            ],

            tags=["document", "word", "docx", "generation"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """
        Execute Word document generation.

        Args:
            params: Tool parameters (see input_schema)
            context: Execution context

        Returns:
            ToolResult with file_path and generation status
        """
        try:
            mode = params["mode"]
            output_path = Path(context.project_path) / params["output_path"]
            metadata = params.get("metadata")

            # Dry run mode
            if context.dry_run:
                logger.info(f"[DRY RUN] Would generate Word document: {output_path}")
                return ToolResult(
                    success=True,
                    data={
                        "file_path": str(output_path),
                        "generated": False,
                        "dry_run": True
                    },
                    metadata={
                        "note": "Dry run mode - document not actually generated",
                        "mode": mode
                    }
                )

            # Create generator
            generator = WordDocumentGenerator()

            # Generate based on mode
            if mode == "template":
                template_path = Path(context.project_path) / params.get("template_path", "")

                if not params.get("template_path"):
                    return ToolResult(
                        success=False,
                        error="template_path is required for template mode"
                    )

                if not template_path.exists():
                    return ToolResult(
                        success=False,
                        error=f"Template not found: {template_path}"
                    )

                template_vars = params.get("template_vars", {})

                result_path = generator.generate_from_template(
                    template_path,
                    template_vars,
                    output_path
                )

            elif mode == "structure":
                if not params.get("structure"):
                    return ToolResult(
                        success=False,
                        error="structure is required for structure mode"
                    )

                structure = params["structure"]

                result_path = generator.create_from_structure(
                    structure,
                    output_path,
                    metadata=metadata
                )

            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown mode: {mode}. Use 'template' or 'structure'"
                )

            logger.info(f"Generated Word document: {result_path}")

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
            logger.error(f"Missing dependency: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={
                    "help": "Install required packages: pip install python-docx python-docxtpl"
                }
            )
        except Exception as e:
            logger.error(f"Failed to generate Word document: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to generate Word document: {str(e)}"
            )
