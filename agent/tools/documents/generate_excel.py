"""
PHASE 2.4: Generate Excel Tool

Tool plugin for generating .xlsx Excel spreadsheets with formatting and formulas.

Features:
- Multi-sheet workbooks
- Header formatting
- Column widths
- Freeze panes
- Formulas
- Charts

Usage:
    tool = GenerateExcelTool()
    result = await tool.execute({
        "sheets": {"Sheet1": [["Name", "Score"], ["Alice", 95]]},
        "output_path": "output/grades.xlsx"
    }, context)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from agent.documents.excel_generator import ExcelGenerator
from agent.tools.base import (
    ToolExecutionContext,
    ToolManifest,
    ToolPlugin,
    ToolResult,
)

logger = logging.getLogger(__name__)


class GenerateExcelTool(ToolPlugin):
    """Generate .xlsx Excel spreadsheets with formatting and formulas."""

    def get_manifest(self) -> ToolManifest:
        """Return tool manifest"""
        return ToolManifest(
            name="generate_excel",
            version="1.0.0",
            description="Generate .xlsx Excel spreadsheet with multiple sheets, formatting, and formulas",
            domains=["hr", "legal", "finance", "ops", "marketing", "coding"],
            roles=["manager", "supervisor", "employee", "hr_manager", "finance_controller", "finance_analyst"],
            required_permissions=["filesystem_write", "document_write"],

            input_schema={
                "type": "object",
                "properties": {
                    "sheets": {
                        "type": "object",
                        "description": "Dictionary of sheet_name -> data (2D array)"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to save Excel file (relative to project)"
                    },
                    "formatting": {
                        "type": "object",
                        "description": "Optional formatting per sheet"
                    }
                },
                "required": ["sheets", "output_path"]
            },

            output_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "generated": {"type": "boolean"},
                    "sheets_count": {"type": "integer"},
                    "dry_run": {"type": "boolean"}
                }
            },

            cost_estimate=0.0,
            timeout_seconds=60,
            requires_filesystem=True,

            examples=[
                {
                    "description": "Generate employee spreadsheet",
                    "input": {
                        "sheets": {
                            "Employees": [
                                ["Name", "Department", "Salary"],
                                ["Alice", "Engineering", 120000],
                                ["Bob", "Sales", 95000]
                            ]
                        },
                        "output_path": "output/employees.xlsx",
                        "formatting": {
                            "Employees": {
                                "header_row": 1,
                                "freeze_panes": "A2",
                                "column_widths": {"A": 20, "B": 15, "C": 12}
                            }
                        }
                    }
                }
            ],

            tags=["document", "excel", "xlsx", "spreadsheet"]
        )

    async def execute(
        self,
        params: Dict[str, Any],
        context: ToolExecutionContext
    ) -> ToolResult:
        """Execute Excel generation"""
        try:
            sheets = params["sheets"]
            output_path = Path(context.project_path) / params["output_path"]
            formatting = params.get("formatting")

            if context.dry_run:
                logger.info(f"[DRY RUN] Would generate Excel: {output_path}")
                return ToolResult(
                    success=True,
                    data={
                        "file_path": str(output_path),
                        "generated": False,
                        "sheets_count": len(sheets),
                        "dry_run": True
                    }
                )

            generator = ExcelGenerator()
            result_path = generator.create_workbook(sheets, output_path, formatting)

            logger.info(f"Generated Excel workbook: {result_path}")

            return ToolResult(
                success=True,
                data={
                    "file_path": str(result_path),
                    "generated": True,
                    "sheets_count": len(sheets)
                },
                metadata={
                    "size_bytes": result_path.stat().st_size
                }
            )

        except ImportError as e:
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"help": "Install: pip install openpyxl"}
            )
        except Exception as e:
            logger.error(f"Failed to generate Excel: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to generate Excel: {str(e)}"
            )
