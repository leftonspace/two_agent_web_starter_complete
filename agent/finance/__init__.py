"""
JARVIS Finance Module

Comprehensive financial analysis tools including:
- Spreadsheet Integration: Natural language queries on spreadsheet data
- Document Intelligence: Contract, invoice, and financial statement analysis
- Financial Templates: Pre-built CFO prompt templates
"""

from .spreadsheet_engine import (
    SpreadsheetEngine,
    SpreadsheetData,
    QueryResult,
    ChartConfig,
)

from .document_intelligence import (
    DocumentIntelligence,
    ContractAnalysis,
    ContractClause,
    RiskAssessment,
    InvoiceData,
    LineItem,
    FinancialStatementData,
    FinancialRatios,
)

from .financial_templates import (
    FinancialTemplateEngine,
    FinancialTemplate,
    TemplateCategory,
)

__all__ = [
    # Spreadsheet Engine
    "SpreadsheetEngine",
    "SpreadsheetData",
    "QueryResult",
    "ChartConfig",
    # Document Intelligence
    "DocumentIntelligence",
    "ContractAnalysis",
    "ContractClause",
    "RiskAssessment",
    "InvoiceData",
    "LineItem",
    "FinancialStatementData",
    "FinancialRatios",
    # Financial Templates
    "FinancialTemplateEngine",
    "FinancialTemplate",
    "TemplateCategory",
]
