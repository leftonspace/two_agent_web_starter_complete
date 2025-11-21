"""
PHASE 2.4: Document Generation Library

This package provides document generation capabilities for Word, Excel, and PDF formats.

Features:
- Word (.docx): Template-based and structure-based generation
- Excel (.xlsx): Multi-sheet workbooks with formatting and formulas
- PDF: ReportLab-based reports and HTML-to-PDF conversion

Usage:
    from agent.documents.word_generator import WordDocumentGenerator
    from agent.documents.excel_generator import ExcelGenerator
    from agent.documents.pdf_generator import PDFGenerator

    # Generate Word document
    word_gen = WordDocumentGenerator()
    word_gen.create_from_structure(structure, output_path)

    # Generate Excel workbook
    excel_gen = ExcelGenerator()
    excel_gen.create_workbook(sheets, output_path)

    # Generate PDF report
    pdf_gen = PDFGenerator()
    pdf_gen.generate_report(title, content, output_path)
"""

__all__ = [
    "WordDocumentGenerator",
    "ExcelGenerator",
    "PDFGenerator",
]

from .word_generator import WordDocumentGenerator
from .excel_generator import ExcelGenerator
from .pdf_generator import PDFGenerator
