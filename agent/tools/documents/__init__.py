"""
PHASE 2.4: Document Generation Tool Plugins

This package contains tool plugins for document generation:
- generate_word: Generate .docx Word documents
- generate_excel: Generate .xlsx Excel spreadsheets
- generate_pdf: Generate PDF reports

These tools wrap the document generation libraries and expose them through
the plugin system from Phase 2.1.
"""

__all__ = [
    "GenerateWordDocumentTool",
    "GenerateExcelTool",
    "GeneratePDFTool",
]
