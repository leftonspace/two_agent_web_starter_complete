"""
Document Intelligence for JARVIS.

Provides AI-powered analysis of business documents including:
- Contract analysis
- Invoice processing
- Financial statement parsing
- Document classification
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class DocumentType(Enum):
    """Supported document types."""
    CONTRACT = "contract"
    INVOICE = "invoice"
    FINANCIAL_STATEMENT = "financial_statement"
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    PURCHASE_ORDER = "purchase_order"
    RECEIPT = "receipt"
    BANK_STATEMENT = "bank_statement"
    TAX_DOCUMENT = "tax_document"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Risk levels for document analysis."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ExtractedEntity:
    """An entity extracted from a document."""
    entity_type: str
    value: Any
    confidence: float
    location: Optional[str] = None
    normalized_value: Optional[Any] = None


@dataclass
class ContractClause:
    """A clause extracted from a contract."""
    clause_type: str
    text: str
    risk_level: RiskLevel
    summary: str
    recommendations: List[str] = field(default_factory=list)


@dataclass
class InvoiceData:
    """Structured invoice data."""
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    customer_name: Optional[str] = None
    customer_address: Optional[str] = None
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    currency: str = "USD"
    line_items: List[Dict] = field(default_factory=list)
    payment_terms: Optional[str] = None
    bank_details: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "invoice_number": self.invoice_number,
            "invoice_date": self.invoice_date,
            "due_date": self.due_date,
            "vendor": {
                "name": self.vendor_name,
                "address": self.vendor_address
            },
            "customer": {
                "name": self.customer_name,
                "address": self.customer_address
            },
            "amounts": {
                "subtotal": self.subtotal,
                "tax": self.tax_amount,
                "total": self.total_amount,
                "currency": self.currency
            },
            "line_items": self.line_items,
            "payment_terms": self.payment_terms,
            "bank_details": self.bank_details
        }


@dataclass
class FinancialStatementData:
    """Structured financial statement data."""
    statement_type: str
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    company_name: Optional[str] = None
    currency: str = "USD"
    metrics: Dict[str, float] = field(default_factory=dict)
    line_items: Dict[str, float] = field(default_factory=dict)
    ratios: Dict[str, float] = field(default_factory=dict)
    year_over_year: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "statement_type": self.statement_type,
            "period": {
                "start": self.period_start,
                "end": self.period_end
            },
            "company_name": self.company_name,
            "currency": self.currency,
            "metrics": self.metrics,
            "line_items": self.line_items,
            "ratios": self.ratios,
            "year_over_year": self.year_over_year
        }


@dataclass
class ContractAnalysis:
    """Complete contract analysis result."""
    document_type: DocumentType
    parties: List[str]
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    contract_value: Optional[float] = None
    currency: str = "USD"
    key_clauses: List[ContractClause] = field(default_factory=list)
    obligations: List[str] = field(default_factory=list)
    risks: List[Dict] = field(default_factory=list)
    summary: str = ""
    overall_risk: RiskLevel = RiskLevel.MEDIUM

    def to_dict(self) -> Dict:
        return {
            "document_type": self.document_type.value,
            "parties": self.parties,
            "dates": {
                "effective": self.effective_date,
                "expiration": self.expiration_date
            },
            "value": {
                "amount": self.contract_value,
                "currency": self.currency
            },
            "key_clauses": [
                {
                    "type": c.clause_type,
                    "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,
                    "risk_level": c.risk_level.value,
                    "summary": c.summary,
                    "recommendations": c.recommendations
                }
                for c in self.key_clauses
            ],
            "obligations": self.obligations,
            "risks": self.risks,
            "summary": self.summary,
            "overall_risk": self.overall_risk.value
        }


class DocumentIntelligence:
    """AI-powered document intelligence engine."""

    # Common contract clause patterns
    CONTRACT_PATTERNS = {
        "indemnification": [
            r"indemnif(?:y|ication)",
            r"hold harmless",
            r"defend and indemnify"
        ],
        "limitation_of_liability": [
            r"limitation of liability",
            r"limit(?:ed)? liability",
            r"aggregate liability",
            r"cap on damages"
        ],
        "termination": [
            r"terminat(?:e|ion)",
            r"cancel(?:lation)?",
            r"right to terminate"
        ],
        "confidentiality": [
            r"confidential(?:ity)?",
            r"non-disclosure",
            r"proprietary information"
        ],
        "intellectual_property": [
            r"intellectual property",
            r"copyright",
            r"patent",
            r"trademark",
            r"trade secret"
        ],
        "payment_terms": [
            r"payment terms",
            r"net \d+",
            r"due upon receipt",
            r"payment schedule"
        ],
        "warranty": [
            r"warrant(?:y|ies)",
            r"guarantee",
            r"as-is"
        ],
        "force_majeure": [
            r"force majeure",
            r"act of god",
            r"unforeseeable circumstances"
        ],
        "governing_law": [
            r"governing law",
            r"jurisdiction",
            r"choice of law"
        ],
        "dispute_resolution": [
            r"dispute resolution",
            r"arbitration",
            r"mediation"
        ],
        "auto_renewal": [
            r"auto(?:matic)?[- ]?renew(?:al)?",
            r"evergreen",
            r"automatic extension"
        ],
        "non_compete": [
            r"non[- ]?compete",
            r"restrictive covenant",
            r"exclusivity"
        ]
    }

    # Invoice patterns
    INVOICE_PATTERNS = {
        "invoice_number": [
            r"invoice\s*(?:#|no\.?|number)?\s*:?\s*([A-Z0-9-]+)",
            r"inv\s*(?:#|no\.?)?\s*:?\s*([A-Z0-9-]+)"
        ],
        "date": [
            r"(?:invoice\s+)?date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{4}-\d{2}-\d{2})"
        ],
        "due_date": [
            r"due\s+date\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"payment\s+due\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        ],
        "total": [
            r"total\s*:?\s*\$?\s*([\d,]+\.?\d*)",
            r"amount\s+due\s*:?\s*\$?\s*([\d,]+\.?\d*)",
            r"balance\s+due\s*:?\s*\$?\s*([\d,]+\.?\d*)"
        ],
        "subtotal": [
            r"subtotal\s*:?\s*\$?\s*([\d,]+\.?\d*)"
        ],
        "tax": [
            r"(?:sales\s+)?tax\s*:?\s*\$?\s*([\d,]+\.?\d*)",
            r"vat\s*:?\s*\$?\s*([\d,]+\.?\d*)"
        ]
    }

    # Financial statement patterns
    FINANCIAL_PATTERNS = {
        "revenue": [
            r"(?:total\s+)?revenue\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)",
            r"net\s+sales\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)"
        ],
        "gross_profit": [
            r"gross\s+profit\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)"
        ],
        "operating_income": [
            r"operating\s+income\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)",
            r"EBIT\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)"
        ],
        "net_income": [
            r"net\s+income\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)",
            r"net\s+profit\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)"
        ],
        "total_assets": [
            r"total\s+assets\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)"
        ],
        "total_liabilities": [
            r"total\s+liabilities\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)"
        ],
        "equity": [
            r"(?:total\s+)?(?:shareholders?\s+)?equity\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)"
        ],
        "cash": [
            r"cash\s+and\s+cash\s+equivalents?\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)"
        ]
    }

    def classify_document(self, text: str) -> DocumentType:
        """Classify the type of document based on content."""
        text_lower = text.lower()

        # Check for specific document indicators
        if any(kw in text_lower for kw in ['invoice', 'bill to', 'ship to', 'amount due']):
            return DocumentType.INVOICE

        if any(kw in text_lower for kw in ['balance sheet', 'assets', 'liabilities', 'equity']):
            return DocumentType.BALANCE_SHEET

        if any(kw in text_lower for kw in ['income statement', 'revenue', 'expenses', 'net income']):
            return DocumentType.INCOME_STATEMENT

        if any(kw in text_lower for kw in ['cash flow', 'operating activities', 'investing activities']):
            return DocumentType.CASH_FLOW

        if any(kw in text_lower for kw in ['agreement', 'contract', 'hereby', 'parties', 'whereas']):
            return DocumentType.CONTRACT

        if any(kw in text_lower for kw in ['purchase order', 'p.o.', 'po number']):
            return DocumentType.PURCHASE_ORDER

        if any(kw in text_lower for kw in ['receipt', 'thank you for your purchase']):
            return DocumentType.RECEIPT

        return DocumentType.UNKNOWN

    def analyze_contract(self, text: str) -> ContractAnalysis:
        """Analyze a contract document."""
        analysis = ContractAnalysis(
            document_type=DocumentType.CONTRACT,
            parties=[]
        )

        # Extract parties
        party_patterns = [
            r'between\s+([^,]+),?\s+(?:and|&)\s+([^,]+)',
            r'party\s+(?:a|1)\s*:\s*([^\n]+)',
            r'"([^"]+)"\s+\((?:the\s+)?"(?:company|vendor|client|customer)"\)'
        ]

        for pattern in party_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    analysis.parties.extend([p.strip() for p in match if p.strip()])
                else:
                    analysis.parties.append(match.strip())

        # Extract dates
        date_pattern = r'(?:effective|dated?|commence)\s*(?:date|as of)?\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        date_match = re.search(date_pattern, text, re.IGNORECASE)
        if date_match:
            analysis.effective_date = date_match.group(1)

        expiry_pattern = r'(?:expir(?:es?|ation)|terminat(?:es?|ion)|end)\s*(?:date)?\s*:?\s*(\w+\s+\d{1,2},?\s+\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        expiry_match = re.search(expiry_pattern, text, re.IGNORECASE)
        if expiry_match:
            analysis.expiration_date = expiry_match.group(1)

        # Extract contract value
        value_pattern = r'(?:contract\s+)?(?:value|amount|consideration)\s*:?\s*\$?\s*([\d,]+(?:\.\d+)?)'
        value_match = re.search(value_pattern, text, re.IGNORECASE)
        if value_match:
            analysis.contract_value = float(value_match.group(1).replace(',', ''))

        # Analyze clauses
        analysis.key_clauses = self._extract_clauses(text)

        # Identify risks
        risks = []
        high_risk_count = 0

        for clause in analysis.key_clauses:
            if clause.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
                high_risk_count += 1
                risks.append({
                    "clause": clause.clause_type,
                    "risk_level": clause.risk_level.value,
                    "issue": clause.summary
                })

        analysis.risks = risks

        # Determine overall risk
        if high_risk_count >= 3:
            analysis.overall_risk = RiskLevel.HIGH
        elif high_risk_count >= 1:
            analysis.overall_risk = RiskLevel.MEDIUM
        else:
            analysis.overall_risk = RiskLevel.LOW

        # Generate summary
        analysis.summary = self._generate_contract_summary(analysis)

        return analysis

    def _extract_clauses(self, text: str) -> List[ContractClause]:
        """Extract and analyze contract clauses."""
        clauses = []

        for clause_type, patterns in self.CONTRACT_PATTERNS.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                if matches:
                    # Get context around the match
                    for match in matches[:1]:  # Take first match per clause type
                        start = max(0, match.start() - 100)
                        end = min(len(text), match.end() + 500)
                        context = text[start:end]

                        # Analyze risk level based on clause type
                        risk_level, summary, recommendations = self._analyze_clause_risk(
                            clause_type, context
                        )

                        clauses.append(ContractClause(
                            clause_type=clause_type,
                            text=context,
                            risk_level=risk_level,
                            summary=summary,
                            recommendations=recommendations
                        ))
                    break

        return clauses

    def _analyze_clause_risk(self, clause_type: str, text: str) -> Tuple[RiskLevel, str, List[str]]:
        """Analyze risk level of a specific clause."""
        text_lower = text.lower()

        # Clause-specific risk analysis
        if clause_type == "limitation_of_liability":
            if "unlimited" in text_lower or "no limit" in text_lower:
                return (
                    RiskLevel.HIGH,
                    "Unlimited liability exposure",
                    ["Negotiate liability cap", "Add insurance requirements"]
                )
            elif any(kw in text_lower for kw in ["consequential", "punitive", "waive"]):
                return (
                    RiskLevel.MEDIUM,
                    "Broad liability waiver included",
                    ["Review scope of waived damages"]
                )

        elif clause_type == "indemnification":
            if "broad form" in text_lower or "sole negligence" in text_lower:
                return (
                    RiskLevel.HIGH,
                    "Broad indemnification obligation",
                    ["Limit to third-party claims", "Cap indemnification amount"]
                )

        elif clause_type == "auto_renewal":
            if re.search(r'auto.*renew', text_lower):
                return (
                    RiskLevel.MEDIUM,
                    "Contract auto-renews - track termination window",
                    ["Set calendar reminder for opt-out period", "Review renewal terms"]
                )

        elif clause_type == "termination":
            if "for convenience" not in text_lower:
                return (
                    RiskLevel.MEDIUM,
                    "No termination for convenience clause found",
                    ["Request termination for convenience provision"]
                )

        elif clause_type == "non_compete":
            if re.search(r'\d+\s*year', text_lower):
                years = re.search(r'(\d+)\s*year', text_lower)
                if years and int(years.group(1)) > 2:
                    return (
                        RiskLevel.HIGH,
                        f"Non-compete period exceeds 2 years",
                        ["Negotiate shorter non-compete period"]
                    )

        # Default risk assessment
        return (
            RiskLevel.LOW,
            f"{clause_type.replace('_', ' ').title()} clause found",
            []
        )

    def _generate_contract_summary(self, analysis: ContractAnalysis) -> str:
        """Generate a human-readable contract summary."""
        lines = []

        if analysis.parties:
            lines.append(f"This is a contract between {' and '.join(analysis.parties[:2])}.")

        if analysis.effective_date:
            lines.append(f"Effective date: {analysis.effective_date}")

        if analysis.expiration_date:
            lines.append(f"Expiration date: {analysis.expiration_date}")

        if analysis.contract_value:
            lines.append(f"Contract value: ${analysis.contract_value:,.2f}")

        if analysis.key_clauses:
            lines.append(f"\nKey clauses identified: {len(analysis.key_clauses)}")

        if analysis.risks:
            lines.append(f"Risk items requiring attention: {len(analysis.risks)}")

        lines.append(f"\nOverall risk assessment: {analysis.overall_risk.value.upper()}")

        return "\n".join(lines)

    def process_invoice(self, text: str) -> InvoiceData:
        """Extract structured data from an invoice."""
        invoice = InvoiceData()

        # Extract invoice number
        for pattern in self.INVOICE_PATTERNS["invoice_number"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice.invoice_number = match.group(1)
                break

        # Extract dates
        for pattern in self.INVOICE_PATTERNS["date"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice.invoice_date = match.group(1)
                break

        for pattern in self.INVOICE_PATTERNS["due_date"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice.due_date = match.group(1)
                break

        # Extract amounts
        for pattern in self.INVOICE_PATTERNS["total"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice.total_amount = float(match.group(1).replace(',', ''))
                break

        for pattern in self.INVOICE_PATTERNS["subtotal"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice.subtotal = float(match.group(1).replace(',', ''))
                break

        for pattern in self.INVOICE_PATTERNS["tax"]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice.tax_amount = float(match.group(1).replace(',', ''))
                break

        # Extract vendor name (usually at top of invoice)
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 3 and not any(c.isdigit() for c in line[:10]):
                invoice.vendor_name = line
                break

        # Detect currency
        if '$' in text:
            invoice.currency = "USD"
        elif '€' in text:
            invoice.currency = "EUR"
        elif '£' in text:
            invoice.currency = "GBP"

        # Extract line items (simplified)
        line_item_pattern = r'([A-Za-z][A-Za-z\s]+)\s+(\d+)\s+\$?([\d,]+\.?\d*)\s+\$?([\d,]+\.?\d*)'
        for match in re.finditer(line_item_pattern, text):
            invoice.line_items.append({
                "description": match.group(1).strip(),
                "quantity": int(match.group(2)),
                "unit_price": float(match.group(3).replace(',', '')),
                "total": float(match.group(4).replace(',', ''))
            })

        return invoice

    def parse_financial_statement(self, text: str) -> FinancialStatementData:
        """Parse a financial statement and extract key metrics."""
        doc_type = self.classify_document(text)

        statement = FinancialStatementData(
            statement_type=doc_type.value
        )

        # Extract company name (usually first non-empty line)
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 3:
                if not any(kw in line.lower() for kw in ['balance sheet', 'income statement', 'cash flow']):
                    statement.company_name = line
                    break

        # Extract financial metrics
        for metric, patterns in self.FINANCIAL_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = float(match.group(1).replace(',', ''))
                    statement.metrics[metric] = value
                    break

        # Calculate common financial ratios if we have the data
        if statement.metrics:
            statement.ratios = self._calculate_ratios(statement.metrics)

        return statement

    def _calculate_ratios(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate common financial ratios."""
        ratios = {}

        # Profitability ratios
        if 'net_income' in metrics and 'revenue' in metrics and metrics['revenue'] > 0:
            ratios['net_profit_margin'] = (metrics['net_income'] / metrics['revenue']) * 100

        if 'gross_profit' in metrics and 'revenue' in metrics and metrics['revenue'] > 0:
            ratios['gross_profit_margin'] = (metrics['gross_profit'] / metrics['revenue']) * 100

        if 'operating_income' in metrics and 'revenue' in metrics and metrics['revenue'] > 0:
            ratios['operating_margin'] = (metrics['operating_income'] / metrics['revenue']) * 100

        # Balance sheet ratios
        if 'total_assets' in metrics and 'total_liabilities' in metrics:
            if metrics['total_liabilities'] > 0:
                ratios['debt_to_assets'] = (metrics['total_liabilities'] / metrics['total_assets']) * 100

        if 'net_income' in metrics and 'total_assets' in metrics and metrics['total_assets'] > 0:
            ratios['return_on_assets'] = (metrics['net_income'] / metrics['total_assets']) * 100

        if 'net_income' in metrics and 'equity' in metrics and metrics['equity'] > 0:
            ratios['return_on_equity'] = (metrics['net_income'] / metrics['equity']) * 100

        return ratios

    def analyze_document(self, text: str, document_type: Optional[DocumentType] = None) -> Dict:
        """
        Analyze any document and return structured data.

        Args:
            text: Document text content
            document_type: Optional type hint

        Returns:
            Structured analysis based on document type
        """
        # Classify if not provided
        if not document_type:
            document_type = self.classify_document(text)

        result = {
            "document_type": document_type.value,
            "analysis": None
        }

        if document_type == DocumentType.CONTRACT:
            analysis = self.analyze_contract(text)
            result["analysis"] = analysis.to_dict()

        elif document_type == DocumentType.INVOICE:
            invoice = self.process_invoice(text)
            result["analysis"] = invoice.to_dict()

        elif document_type in (DocumentType.BALANCE_SHEET, DocumentType.INCOME_STATEMENT,
                               DocumentType.CASH_FLOW, DocumentType.FINANCIAL_STATEMENT):
            statement = self.parse_financial_statement(text)
            result["analysis"] = statement.to_dict()

        else:
            # For unknown types, return basic extraction
            result["analysis"] = {
                "word_count": len(text.split()),
                "line_count": len(text.split('\n')),
                "detected_amounts": self._extract_amounts(text),
                "detected_dates": self._extract_dates(text)
            }

        return result

    def _extract_amounts(self, text: str) -> List[Dict]:
        """Extract monetary amounts from text."""
        amounts = []
        pattern = r'\$\s*([\d,]+\.?\d*)'

        for match in re.finditer(pattern, text):
            amounts.append({
                "value": float(match.group(1).replace(',', '')),
                "currency": "USD"
            })

        return amounts[:20]  # Limit results

    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        dates = []
        patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}-\d{2}-\d{2}',
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)

        return list(set(dates))[:10]  # Unique dates, limited


# Singleton instance
_doc_intelligence = None

def get_document_intelligence() -> DocumentIntelligence:
    """Get or create the document intelligence instance."""
    global _doc_intelligence
    if _doc_intelligence is None:
        _doc_intelligence = DocumentIntelligence()
    return _doc_intelligence
