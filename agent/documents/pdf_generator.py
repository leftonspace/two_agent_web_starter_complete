"""
PHASE 2.4: PDF Generator

Generate PDF documents from structured data or HTML.

Features:
- ReportLab-based report generation
- HTML-to-PDF conversion (weasyprint)
- Tables with styling
- Headings and paragraphs
- Page metadata
- PDF merging

Usage:
    generator = PDFGenerator()

    # Generate report
    content = [
        {"type": "heading", "text": "Report Title", "level": 1},
        {"type": "paragraph", "text": "This is a paragraph..."},
        {"type": "table", "data": [[...]], "headers": [...]}
    ]
    generator.generate_report("My Report", content, Path("output/report.pdf"))

    # Convert HTML to PDF
    generator.generate_from_html(Path("page.html"), Path("page.pdf"))
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PDFGenerator:
    """
    Generate PDF documents from structured data or HTML.

    Supports:
    - ReportLab-based reports with tables, headings, paragraphs
    - HTML-to-PDF conversion
    - PDF merging
    - Metadata
    - Custom styling
    """

    def __init__(self, page_size: str = "letter"):
        """
        Initialize PDF generator.

        Args:
            page_size: Page size ("letter", "a4", "legal")
        """
        self.page_size = self._get_page_size(page_size)
        self.styles = None

    def _get_page_size(self, size_name: str):
        """Get page size from reportlab"""
        try:
            from reportlab.lib.pagesizes import letter, A4, legal

            size_map = {
                "letter": letter,
                "a4": A4,
                "legal": legal
            }
            return size_map.get(size_name.lower(), letter)
        except ImportError:
            return None

    def generate_from_html(
        self,
        html_path: Path,
        output_path: Path,
        css_path: Optional[Path] = None
    ) -> Path:
        """
        Convert HTML to PDF using weasyprint.

        Args:
            html_path: Path to HTML file
            output_path: Path to save PDF
            css_path: Optional path to CSS file

        Returns:
            Path to generated PDF

        Raises:
            ImportError: If weasyprint not installed
            FileNotFoundError: If HTML file not found
            Exception: If conversion fails

        Example:
            generator.generate_from_html(
                Path("report.html"),
                Path("report.pdf"),
                Path("styles.css")
            )
        """
        try:
            from weasyprint import HTML, CSS

            html_path = Path(html_path)
            output_path = Path(output_path)

            if not html_path.exists():
                raise FileNotFoundError(f"HTML file not found: {html_path}")

            # Build HTML object
            html = HTML(filename=str(html_path))

            # Add CSS if provided
            stylesheets = []
            if css_path and Path(css_path).exists():
                stylesheets.append(CSS(filename=str(css_path)))

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Generate PDF
            html.write_pdf(str(output_path), stylesheets=stylesheets)

            logger.info(f"Generated PDF from HTML: {output_path}")
            return output_path

        except ImportError:
            raise ImportError(
                "weasyprint is required for HTML-to-PDF conversion. "
                "Install with: pip install weasyprint"
            )
        except Exception as e:
            logger.error(f"Failed to convert HTML to PDF: {e}")
            raise

    def generate_report(
        self,
        title: str,
        content: List[Dict[str, Any]],
        output_path: Path,
        metadata: Optional[Dict[str, str]] = None
    ) -> Path:
        """
        Generate PDF report from structured content using ReportLab.

        Content format:
        [
            {"type": "heading", "text": "Section 1", "level": 1},
            {"type": "paragraph", "text": "Lorem ipsum..."},
            {"type": "table", "data": [["A", "B"], ["C", "D"]], "headers": ["Col1", "Col2"]},
            {"type": "spacer", "height": 0.5},
        ]

        Args:
            title: Document title
            content: List of content blocks
            output_path: Path to save PDF
            metadata: Optional metadata (author, subject, keywords)

        Returns:
            Path to generated PDF

        Raises:
            ImportError: If reportlab not installed
            Exception: If generation fails

        Example:
            content = [
                {"type": "heading", "text": "Summary", "level": 1},
                {"type": "paragraph", "text": "This is the summary..."},
                {
                    "type": "table",
                    "headers": ["Name", "Score"],
                    "data": [["Alice", 95], ["Bob", 87]]
                }
            ]

            generator.generate_report(
                "Quarterly Report",
                content,
                Path("report.pdf"),
                metadata={"author": "Jane Doe", "subject": "Q4 Results"}
            )
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors

            output_path = Path(output_path)

            # Initialize styles
            self.styles = getSampleStyleSheet()

            # Create document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.page_size,
                title=title,
                author=metadata.get("author", "") if metadata else ""
            )

            story = []

            # Add title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor("#1f4788"),
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.3 * inch))

            # Process content blocks
            for block in content:
                block_type = block.get("type")

                if block_type == "heading":
                    self._add_heading(story, block)

                elif block_type == "paragraph":
                    self._add_paragraph(story, block)

                elif block_type == "table":
                    self._add_table_to_story(story, block)

                elif block_type == "spacer":
                    height = block.get("height", 0.5)
                    story.append(Spacer(1, height * inch))

                elif block_type == "page_break":
                    from reportlab.platypus import PageBreak
                    story.append(PageBreak())

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build PDF
            doc.build(story)

            logger.info(f"Generated PDF report: {output_path}")
            return output_path

        except ImportError:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install with: pip install reportlab"
            )
        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise

    def _add_heading(self, story: List, block: Dict[str, Any]) -> None:
        """Add heading to story"""
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.units import inch

        level = block.get("level", 1)
        text = block.get("text", "")

        style_name = f'Heading{min(level, 4)}'  # Max heading level 4
        story.append(Paragraph(text, self.styles[style_name]))
        story.append(Spacer(1, 0.2 * inch))

    def _add_paragraph(self, story: List, block: Dict[str, Any]) -> None:
        """Add paragraph to story"""
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.units import inch

        text = block.get("text", "")
        story.append(Paragraph(text, self.styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))

    def _add_table_to_story(self, story: List, block: Dict[str, Any]) -> None:
        """Add table to story"""
        from reportlab.platypus import Table, TableStyle, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import inch

        data = block.get("data", [])
        headers = block.get("headers")

        if headers:
            data = [headers] + data

        if not data:
            return

        # Create table
        table = Table(data)

        # Apply styling
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])

        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 0.2 * inch))

    def merge_pdfs(
        self,
        pdf_paths: List[Path],
        output_path: Path
    ) -> Path:
        """
        Merge multiple PDFs into one.

        Args:
            pdf_paths: List of PDF paths to merge
            output_path: Path to save merged PDF

        Returns:
            Path to merged PDF

        Raises:
            ImportError: If PyPDF2 not installed
            FileNotFoundError: If any PDF not found
            Exception: If merging fails

        Example:
            generator.merge_pdfs(
                [Path("page1.pdf"), Path("page2.pdf")],
                Path("combined.pdf")
            )
        """
        try:
            from PyPDF2 import PdfMerger

            output_path = Path(output_path)

            # Verify all files exist
            for pdf_path in pdf_paths:
                if not Path(pdf_path).exists():
                    raise FileNotFoundError(f"PDF not found: {pdf_path}")

            # Merge
            merger = PdfMerger()
            for pdf_path in pdf_paths:
                merger.append(str(pdf_path))

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save
            merger.write(str(output_path))
            merger.close()

            logger.info(f"Merged {len(pdf_paths)} PDFs into: {output_path}")
            return output_path

        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF merging. "
                "Install with: pip install PyPDF2"
            )
        except Exception as e:
            logger.error(f"Failed to merge PDFs: {e}")
            raise


# Convenience functions
def generate_pdf_from_html(html_path: Path, output_path: Path) -> Path:
    """
    Convenience function to convert HTML to PDF.

    Args:
        html_path: Path to HTML file
        output_path: Path to save PDF

    Returns:
        Path to generated PDF

    Example:
        generate_pdf_from_html(Path("report.html"), Path("report.pdf"))
    """
    generator = PDFGenerator()
    return generator.generate_from_html(html_path, output_path)


def generate_pdf_report(
    title: str,
    content: List[Dict[str, Any]],
    output_path: Path
) -> Path:
    """
    Convenience function to generate PDF report.

    Args:
        title: Report title
        content: List of content blocks
        output_path: Path to save PDF

    Returns:
        Path to generated PDF

    Example:
        generate_pdf_report(
            "Report",
            [{"type": "paragraph", "text": "..."}],
            Path("report.pdf")
        )
    """
    generator = PDFGenerator()
    return generator.generate_report(title, content, output_path)
