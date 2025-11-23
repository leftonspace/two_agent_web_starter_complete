# JARVIS Finance Tools

Comprehensive financial analysis tools for business users, CFOs, and finance teams.

## Overview

The Finance module provides three core capabilities:

1. **Spreadsheet Integration** - Natural language queries on CSV/JSON data
2. **Document Intelligence** - Contract, invoice, and financial statement analysis
3. **Financial Templates** - Pre-built CFO prompt templates for common tasks

## Table of Contents

- [Quick Start](#quick-start)
- [Spreadsheet Integration](#spreadsheet-integration)
- [Document Intelligence](#document-intelligence)
- [Financial Templates](#financial-templates)
- [API Reference](#api-reference)

---

## Quick Start

### API Endpoints

All finance APIs are available at `/api/finance/`:

```bash
# Health check
curl http://localhost:8000/api/finance/health

# Query spreadsheet data
curl -X POST http://localhost:8000/api/finance/spreadsheet/query \
  -H "Content-Type: application/json" \
  -d '{"query": "total revenue by quarter", "data": [...]}'

# Analyze a contract
curl -X POST http://localhost:8000/api/finance/document/analyze \
  -H "Content-Type: application/json" \
  -d '{"content": "CONTRACT TEXT...", "document_type": "contract"}'

# Generate a financial template
curl -X POST http://localhost:8000/api/finance/templates/generate \
  -H "Content-Type: application/json" \
  -d '{"template_id": "budget_variance_analysis", "variables": {"period": "Q3 2025"}}'
```

---

## Spreadsheet Integration

Natural language interface for querying and analyzing spreadsheet data.

### Supported Query Types

| Query Type | Examples |
|------------|----------|
| **Aggregations** | "Total revenue", "Average sales", "Count of orders" |
| **Filtering** | "Show orders over $1000", "Filter by region = West" |
| **Sorting** | "Sort by date descending", "Top 10 customers by revenue" |
| **Grouping** | "Revenue by category", "Average sales by month" |
| **Visualizations** | "Chart revenue by quarter", "Pie chart of expenses" |

### API: Query Spreadsheet

```http
POST /api/finance/spreadsheet/query
Content-Type: application/json

{
  "query": "What is the total revenue by region?",
  "data": [
    {"region": "North", "revenue": 50000, "date": "2025-01-15"},
    {"region": "South", "revenue": 35000, "date": "2025-01-16"},
    {"region": "North", "revenue": 42000, "date": "2025-01-17"}
  ],
  "columns": ["region", "revenue", "date"]
}
```

**Response:**
```json
{
  "success": true,
  "query": "What is the total revenue by region?",
  "result_type": "grouped",
  "data": {
    "North": 92000,
    "South": 35000
  },
  "summary": "Revenue grouped by region"
}
```

### API: Upload CSV

```http
POST /api/finance/spreadsheet/upload
Content-Type: multipart/form-data

file: [CSV file]
name: "sales_data" (optional)
```

### API: Generate Formula

```http
POST /api/finance/spreadsheet/formula
Content-Type: application/json

{
  "description": "Sum of revenue where region is North",
  "columns": ["region", "revenue", "date"],
  "format": "excel"
}
```

**Response:**
```json
{
  "formula": "=SUMIF(A:A,\"North\",B:B)",
  "explanation": "Formula to sum of revenue where region is north",
  "format": "excel"
}
```

---

## Document Intelligence

Automated extraction and analysis of business documents.

### Supported Document Types

| Type | Extracted Information |
|------|----------------------|
| **Contracts** | Parties, dates, value, clauses, risk assessment |
| **Invoices** | Vendor, amounts, line items, due dates |
| **Financial Statements** | Metrics, ratios, period, analysis |

### API: Analyze Document

```http
POST /api/finance/document/analyze
Content-Type: application/json

{
  "content": "SERVICE AGREEMENT\n\nThis Agreement is entered into between ABC Corp and XYZ Inc...",
  "document_type": "contract"
}
```

**Contract Response:**
```json
{
  "document_type": "contract",
  "parties": ["ABC Corp", "XYZ Inc"],
  "effective_date": "2025-01-01",
  "expiration_date": "2026-01-01",
  "contract_value": "$120,000",
  "clauses": [
    {
      "type": "termination",
      "content": "Either party may terminate with 30 days notice...",
      "risk_level": "medium",
      "notes": "Standard termination clause"
    },
    {
      "type": "indemnification",
      "content": "Service provider shall indemnify...",
      "risk_level": "high",
      "notes": "Broad indemnification - review carefully"
    }
  ],
  "risk_assessment": {
    "overall_risk": "medium",
    "risk_score": 55,
    "high_risk_areas": ["indemnification", "liability"],
    "recommendations": ["Review indemnification clause with legal"]
  },
  "summary": "Service agreement between ABC Corp and XYZ Inc for $120,000"
}
```

**Invoice Response:**
```json
{
  "document_type": "invoice",
  "invoice_number": "INV-2025-001",
  "invoice_date": "2025-01-15",
  "due_date": "2025-02-15",
  "vendor_name": "Acme Supplies Inc",
  "total_amount": 15750.00,
  "tax_amount": 1250.00,
  "line_items": [
    {"description": "Office supplies", "quantity": 100, "unit_price": 15.00, "amount": 1500.00},
    {"description": "Computer equipment", "quantity": 5, "unit_price": 2850.00, "amount": 14250.00}
  ],
  "payment_terms": "Net 30",
  "summary": "Invoice INV-2025-001 for $15750.00"
}
```

### API: Compare Contracts

```http
POST /api/finance/document/contract/compare
Content-Type: multipart/form-data

contract1: [Contract 1 text]
contract2: [Contract 2 text]
```

**Response:**
```json
{
  "contract1_summary": "Service agreement with standard terms",
  "contract2_summary": "Service agreement with modified liability",
  "contract1_risk_score": 45,
  "contract2_risk_score": 72,
  "differences": [
    {
      "clause_type": "limitation_of_liability",
      "difference": "risk_level_change",
      "contract1_risk": "low",
      "contract2_risk": "high"
    },
    {
      "clause_type": "auto_renewal",
      "difference": "added_in_contract2",
      "risk_level": "medium"
    }
  ],
  "recommendation": "Review highlighted differences carefully before signing."
}
```

### Contract Clause Types Analyzed

| Clause Type | Risk Indicators |
|-------------|-----------------|
| `indemnification` | Unlimited indemnity, broad scope |
| `limitation_of_liability` | Caps, exclusions, consequential damages |
| `termination` | Notice period, termination rights |
| `confidentiality` | Perpetual obligations, scope |
| `intellectual_property` | Work-for-hire, ownership |
| `payment_terms` | Late fees, payment timing |
| `warranty` | Disclaimers, limitations |
| `force_majeure` | Coverage scope |
| `governing_law` | Jurisdiction |
| `dispute_resolution` | Arbitration vs litigation |
| `auto_renewal` | Cancellation windows |
| `non_compete` | Duration, geographic scope |

---

## Financial Templates

Pre-built prompt templates for common CFO and finance tasks.

### Available Templates

| Template ID | Category | Description |
|-------------|----------|-------------|
| `budget_variance_analysis` | Budgeting | Analyze budget vs actual variances |
| `zero_based_budget` | Budgeting | Create zero-based budget |
| `cash_flow_forecast` | Forecasting | 13-week cash flow projection |
| `revenue_forecast` | Forecasting | Revenue projection with scenarios |
| `financial_health_check` | Analysis | Comprehensive financial health assessment |
| `unit_economics_analysis` | Analysis | Analyze unit economics and CAC/LTV |
| `board_financial_update` | Reporting | Board meeting financial summary |
| `monthly_close_report` | Reporting | Month-end close analysis |
| `audit_preparation` | Compliance | Audit readiness checklist |
| `strategic_financial_plan` | Planning | Long-term financial strategy |
| `pricing_analysis` | Analysis | Pricing strategy evaluation |

### API: List Templates

```http
GET /api/finance/templates?category=analysis
```

**Response:**
```json
{
  "templates": [
    {
      "id": "financial_health_check",
      "name": "Financial Health Check",
      "description": "Comprehensive assessment of financial position",
      "category": "analysis",
      "variables": ["company_name", "period", "revenue", "expenses"]
    }
  ],
  "categories": ["budgeting", "forecasting", "analysis", "reporting", "compliance", "planning"]
}
```

### API: Generate Template

```http
POST /api/finance/templates/generate
Content-Type: application/json

{
  "template_id": "budget_variance_analysis",
  "variables": {
    "period": "Q3 2025",
    "department": "Marketing",
    "budget_amount": 500000,
    "actual_amount": 475000
  }
}
```

**Response:**
```json
{
  "template_id": "budget_variance_analysis",
  "name": "Budget Variance Analysis",
  "category": "budgeting",
  "prompt": "Analyze the budget variance for Marketing in Q3 2025.\n\nBudget: $500,000\nActual: $475,000\nVariance: $25,000 (5.0% favorable)\n\nProvide:\n1. Root cause analysis of major variances\n2. Comparison to previous periods\n3. Impact on annual forecast\n4. Recommended actions...",
  "variables_used": ["period", "department", "budget_amount", "actual_amount"]
}
```

### API: Custom Prompt

```http
POST /api/finance/templates/custom
Content-Type: multipart/form-data

task: "Analyze our Q3 SaaS metrics"
context: "ARR: $2.5M, MRR: $210K, Churn: 3.2%, NRR: 115%"
output_format: "executive"
```

---

## Comprehensive Analysis

Combine multiple analysis tools in a single request.

### API: Comprehensive Financial Analysis

```http
POST /api/finance/analyze/comprehensive
Content-Type: multipart/form-data

data: [{"month": "Jan", "revenue": 100000}, {"month": "Feb", "revenue": 120000}]
document: "CONTRACT TEXT..."
template_id: "financial_health_check"
variables: {"company_name": "Acme Corp"}
```

**Response:**
```json
{
  "success": true,
  "results": {
    "spreadsheet": {
      "row_count": 2,
      "columns": ["month", "revenue"],
      "summary": "Loaded 2 rows with 2 columns"
    },
    "document": {
      "type": "contract",
      "risk_score": 55,
      "summary": "Service agreement..."
    },
    "template": {
      "id": "financial_health_check",
      "prompt": "Analyze financial health of Acme Corp..."
    }
  }
}
```

---

## Python SDK Usage

### Spreadsheet Engine

```python
from agent.finance import SpreadsheetEngine

engine = SpreadsheetEngine()

# Load data
engine.load_csv("sales_data.csv", "sales")

# Natural language query
result = engine.query("What is the total revenue by region?", "sales")
print(result.data)  # {'North': 92000, 'South': 35000}
print(result.summary)

# Generate formula
formula = engine.generate_formula(
    "Sum revenue where region is North",
    columns=["region", "revenue"],
    format="excel"
)
print(formula)  # =SUMIF(A:A,"North",B:B)
```

### Document Intelligence

```python
from agent.finance import DocumentIntelligence

doc_intel = DocumentIntelligence()

# Classify document
doc_type = doc_intel.classify_document(document_text)

# Analyze contract
if doc_type == "contract":
    analysis = doc_intel.analyze_contract(document_text)
    print(f"Risk Score: {analysis.risk_assessment.risk_score}")
    for clause in analysis.clauses:
        if clause.risk_level == "high":
            print(f"HIGH RISK: {clause.clause_type}")

# Process invoice
invoice = doc_intel.process_invoice(invoice_text)
print(f"Total: ${invoice.total_amount}")
for item in invoice.line_items:
    print(f"  {item.description}: ${item.amount}")
```

### Financial Templates

```python
from agent.finance import FinancialTemplateEngine

templates = FinancialTemplateEngine()

# List available templates
for template in templates.list_templates("analysis"):
    print(f"{template.id}: {template.description}")

# Generate prompt
prompt = templates.generate("budget_variance_analysis", {
    "period": "Q3 2025",
    "department": "Engineering",
    "budget_amount": 1000000,
    "actual_amount": 950000
})

# Send to JARVIS
response = jarvis.chat(prompt)
```

---

## Use Cases

### 1. CFO Dashboard Integration

```javascript
// Frontend: Fetch financial health
async function getFinancialHealth() {
  const response = await fetch('/api/finance/templates/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      template_id: 'financial_health_check',
      variables: {
        company_name: 'Acme Corp',
        period: 'Q3 2025'
      }
    })
  });
  const data = await response.json();
  // Send prompt to JARVIS chat
  sendToJarvis(data.prompt);
}
```

### 2. Contract Review Workflow

```python
# Automated contract review
def review_contract(contract_path: str):
    with open(contract_path) as f:
        contract_text = f.read()

    analysis = doc_intel.analyze_contract(contract_text)

    # Flag high-risk contracts
    if analysis.risk_assessment.risk_score > 70:
        alert_legal_team(analysis)

    # Generate summary for approval
    return {
        "risk_score": analysis.risk_assessment.risk_score,
        "high_risk_clauses": [
            c.clause_type for c in analysis.clauses
            if c.risk_level == "high"
        ],
        "recommendations": analysis.risk_assessment.recommendations
    }
```

### 3. Automated Invoice Processing

```python
# Batch invoice processing
def process_invoices(invoice_folder: str):
    results = []
    for file in Path(invoice_folder).glob("*.txt"):
        invoice = doc_intel.process_invoice(file.read_text())
        results.append({
            "file": file.name,
            "vendor": invoice.vendor_name,
            "amount": invoice.total_amount,
            "due_date": invoice.due_date
        })
    return results
```

---

## Configuration

### Environment Variables

```bash
# Optional: Configure finance module behavior
FINANCE_MAX_SPREADSHEET_ROWS=100000
FINANCE_CONTRACT_RISK_THRESHOLD=70
FINANCE_ENABLE_CACHING=true
```

### Rate Limits

| Endpoint | Rate Limit |
|----------|------------|
| `/api/finance/spreadsheet/*` | 100 req/min |
| `/api/finance/document/*` | 50 req/min |
| `/api/finance/templates/*` | 200 req/min |

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request (invalid input) |
| 404 | Resource not found |
| 500 | Server error |

---

## Security Considerations

1. **Data Privacy**: Spreadsheet data and documents are processed in-memory and not stored
2. **Authentication**: All API endpoints require authentication
3. **Input Validation**: All inputs are validated before processing
4. **Rate Limiting**: Endpoints are rate-limited to prevent abuse

---

## Changelog

### v1.0.0 (2025-11-23)
- Initial release
- Spreadsheet Integration with natural language queries
- Document Intelligence for contracts, invoices, financial statements
- 11 pre-built financial templates
- REST API endpoints for all features
