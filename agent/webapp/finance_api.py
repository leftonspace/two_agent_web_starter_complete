"""
Finance API Router for JARVIS

Provides HTTP endpoints for:
- Spreadsheet queries and analysis
- Document intelligence (contracts, invoices, financial statements)
- Financial template generation
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import json
import tempfile
import os

# Import finance modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finance.spreadsheet_engine import SpreadsheetEngine, SpreadsheetData
from finance.document_intelligence import DocumentIntelligence
from finance.financial_templates import FinancialTemplateEngine, TemplateCategory

router = APIRouter(prefix="/api/finance", tags=["finance"])

# Initialize engines
spreadsheet_engine = SpreadsheetEngine()
document_intelligence = DocumentIntelligence()
template_engine = FinancialTemplateEngine()


# ============================================================================
# Request/Response Models
# ============================================================================

class SpreadsheetQueryRequest(BaseModel):
    """Request for natural language spreadsheet query."""
    query: str = Field(..., description="Natural language query")
    data: List[Dict[str, Any]] = Field(..., description="Spreadsheet data as list of row dicts")
    columns: Optional[List[str]] = Field(None, description="Column names")


class SpreadsheetQueryResponse(BaseModel):
    """Response from spreadsheet query."""
    success: bool
    query: str
    result_type: str
    data: Any
    summary: Optional[str] = None
    chart: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FormulaRequest(BaseModel):
    """Request for formula generation."""
    description: str = Field(..., description="Natural language description of formula")
    columns: List[str] = Field(..., description="Available column names")
    format: str = Field("excel", description="Formula format: excel or sheets")


class FormulaResponse(BaseModel):
    """Generated formula response."""
    formula: str
    explanation: str
    format: str


class DocumentAnalysisRequest(BaseModel):
    """Request for document analysis."""
    content: str = Field(..., description="Document text content")
    document_type: Optional[str] = Field(None, description="Type hint: contract, invoice, financial_statement")


class ContractAnalysisResponse(BaseModel):
    """Contract analysis response."""
    document_type: str
    parties: List[str]
    effective_date: Optional[str]
    expiration_date: Optional[str]
    contract_value: Optional[str]
    clauses: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    summary: str


class InvoiceResponse(BaseModel):
    """Invoice processing response."""
    document_type: str
    invoice_number: Optional[str]
    invoice_date: Optional[str]
    due_date: Optional[str]
    vendor_name: Optional[str]
    total_amount: Optional[float]
    tax_amount: Optional[float]
    line_items: List[Dict[str, Any]]
    payment_terms: Optional[str]
    summary: str


class FinancialStatementResponse(BaseModel):
    """Financial statement analysis response."""
    document_type: str
    statement_type: str
    period: Optional[str]
    company_name: Optional[str]
    metrics: Dict[str, float]
    ratios: Dict[str, Optional[float]]
    analysis: str


class TemplateRequest(BaseModel):
    """Request for financial template."""
    template_id: str = Field(..., description="Template identifier")
    variables: Dict[str, Any] = Field(default_factory=dict, description="Template variables")


class TemplateResponse(BaseModel):
    """Generated template response."""
    template_id: str
    name: str
    category: str
    prompt: str
    variables_used: List[str]


class TemplateListResponse(BaseModel):
    """List of available templates."""
    templates: List[Dict[str, Any]]
    categories: List[str]


# ============================================================================
# Spreadsheet Endpoints
# ============================================================================

@router.post("/spreadsheet/query", response_model=SpreadsheetQueryResponse)
async def query_spreadsheet(request: SpreadsheetQueryRequest):
    """
    Execute a natural language query on spreadsheet data.

    Supports queries like:
    - "What is the total revenue?"
    - "Show me all transactions over $1000"
    - "Average sales by region"
    - "Sort by date descending"
    """
    try:
        # Load data into engine
        columns = request.columns or (list(request.data[0].keys()) if request.data else [])
        spreadsheet_data = SpreadsheetData(
            columns=columns,
            rows=request.data,
            name="uploaded_data"
        )
        spreadsheet_engine.data = {"uploaded_data": spreadsheet_data}

        # Execute query
        result = spreadsheet_engine.query(request.query, "uploaded_data")

        return SpreadsheetQueryResponse(
            success=result.success,
            query=result.query,
            result_type=result.result_type,
            data=result.data,
            summary=result.summary,
            chart=result.chart.dict() if result.chart else None,
            error=result.error
        )
    except Exception as e:
        return SpreadsheetQueryResponse(
            success=False,
            query=request.query,
            result_type="error",
            data=None,
            error=str(e)
        )


@router.post("/spreadsheet/upload")
async def upload_spreadsheet(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None)
):
    """
    Upload a CSV file for analysis.

    Returns the parsed data and available columns.
    """
    try:
        # Save uploaded file temporarily
        content = await file.read()

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Load CSV
            dataset_name = name or file.filename or "uploaded"
            data = spreadsheet_engine.load_csv(tmp_path, dataset_name)

            return {
                "success": True,
                "name": dataset_name,
                "columns": data.columns,
                "row_count": len(data.rows),
                "sample_rows": data.rows[:5] if data.rows else []
            }
        finally:
            os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/spreadsheet/formula", response_model=FormulaResponse)
async def generate_formula(request: FormulaRequest):
    """
    Generate a spreadsheet formula from natural language description.

    Example: "Sum of column A where column B is greater than 100"
    """
    try:
        formula = spreadsheet_engine.generate_formula(
            request.description,
            request.columns,
            request.format
        )

        return FormulaResponse(
            formula=formula,
            explanation=f"Formula to {request.description.lower()}",
            format=request.format
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Document Intelligence Endpoints
# ============================================================================

@router.post("/document/analyze")
async def analyze_document(request: DocumentAnalysisRequest):
    """
    Analyze a document and extract structured information.

    Automatically detects document type (contract, invoice, financial statement)
    or uses the provided type hint.
    """
    try:
        # Classify document if type not provided
        doc_type = request.document_type
        if not doc_type:
            doc_type = document_intelligence.classify_document(request.content)

        # Route to appropriate analyzer
        if doc_type == "contract":
            result = document_intelligence.analyze_contract(request.content)
            return ContractAnalysisResponse(
                document_type="contract",
                parties=result.parties,
                effective_date=result.effective_date,
                expiration_date=result.expiration_date,
                contract_value=result.contract_value,
                clauses=[{
                    "type": c.clause_type,
                    "content": c.content[:500],  # Truncate for response
                    "risk_level": c.risk_level,
                    "notes": c.notes
                } for c in result.clauses],
                risk_assessment={
                    "overall_risk": result.risk_assessment.overall_risk,
                    "risk_score": result.risk_assessment.risk_score,
                    "high_risk_areas": result.risk_assessment.high_risk_areas,
                    "recommendations": result.risk_assessment.recommendations
                },
                summary=result.summary
            )

        elif doc_type == "invoice":
            result = document_intelligence.process_invoice(request.content)
            return InvoiceResponse(
                document_type="invoice",
                invoice_number=result.invoice_number,
                invoice_date=result.invoice_date,
                due_date=result.due_date,
                vendor_name=result.vendor_name,
                total_amount=result.total_amount,
                tax_amount=result.tax_amount,
                line_items=[{
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "amount": item.amount
                } for item in result.line_items],
                payment_terms=result.payment_terms,
                summary=f"Invoice {result.invoice_number or 'N/A'} for ${result.total_amount or 0:.2f}"
            )

        elif doc_type == "financial_statement":
            result = document_intelligence.parse_financial_statement(request.content)
            return FinancialStatementResponse(
                document_type="financial_statement",
                statement_type=result.statement_type,
                period=result.period,
                company_name=result.company_name,
                metrics=result.metrics,
                ratios={
                    "gross_margin": result.ratios.gross_margin,
                    "operating_margin": result.ratios.operating_margin,
                    "net_margin": result.ratios.net_margin,
                    "current_ratio": result.ratios.current_ratio,
                    "quick_ratio": result.ratios.quick_ratio,
                    "debt_to_equity": result.ratios.debt_to_equity,
                    "return_on_equity": result.ratios.return_on_equity,
                    "return_on_assets": result.ratios.return_on_assets
                },
                analysis=f"Financial analysis for {result.company_name or 'Unknown'} - {result.period or 'Period N/A'}"
            )
        else:
            # Generic document response
            return {
                "document_type": doc_type or "unknown",
                "content_length": len(request.content),
                "message": "Document type not recognized. Please specify document_type."
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/document/classify")
async def classify_document(content: str = Form(...)):
    """
    Classify a document's type based on its content.

    Returns: contract, invoice, financial_statement, or unknown
    """
    try:
        doc_type = document_intelligence.classify_document(content)
        confidence = 0.9 if doc_type != "unknown" else 0.3

        return {
            "document_type": doc_type,
            "confidence": confidence
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/document/contract/compare")
async def compare_contracts(
    contract1: str = Form(..., description="First contract text"),
    contract2: str = Form(..., description="Second contract text")
):
    """
    Compare two contracts and highlight differences in key clauses.
    """
    try:
        analysis1 = document_intelligence.analyze_contract(contract1)
        analysis2 = document_intelligence.analyze_contract(contract2)

        # Compare clauses
        clauses1 = {c.clause_type: c for c in analysis1.clauses}
        clauses2 = {c.clause_type: c for c in analysis2.clauses}

        all_clause_types = set(clauses1.keys()) | set(clauses2.keys())

        differences = []
        for clause_type in all_clause_types:
            c1 = clauses1.get(clause_type)
            c2 = clauses2.get(clause_type)

            if c1 and c2:
                if c1.risk_level != c2.risk_level:
                    differences.append({
                        "clause_type": clause_type,
                        "difference": "risk_level_change",
                        "contract1_risk": c1.risk_level,
                        "contract2_risk": c2.risk_level
                    })
            elif c1 and not c2:
                differences.append({
                    "clause_type": clause_type,
                    "difference": "removed_in_contract2",
                    "risk_level": c1.risk_level
                })
            elif c2 and not c1:
                differences.append({
                    "clause_type": clause_type,
                    "difference": "added_in_contract2",
                    "risk_level": c2.risk_level
                })

        return {
            "contract1_summary": analysis1.summary,
            "contract2_summary": analysis2.summary,
            "contract1_risk_score": analysis1.risk_assessment.risk_score,
            "contract2_risk_score": analysis2.risk_assessment.risk_score,
            "differences": differences,
            "recommendation": "Review highlighted differences carefully before signing."
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Financial Template Endpoints
# ============================================================================

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(category: Optional[str] = None):
    """
    List all available financial templates.

    Optionally filter by category: budgeting, forecasting, analysis,
    reporting, compliance, planning
    """
    try:
        templates = template_engine.list_templates(category)

        return TemplateListResponse(
            templates=[{
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category.value,
                "variables": t.variables
            } for t in templates],
            categories=[c.value for c in TemplateCategory]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    """
    Get details for a specific template.
    """
    try:
        template = template_engine.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category.value,
            "variables": template.variables,
            "example_output": template.example_output,
            "prompt_preview": template.prompt_template[:200] + "..."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/templates/generate", response_model=TemplateResponse)
async def generate_template(request: TemplateRequest):
    """
    Generate a financial analysis prompt from a template.

    Available templates:
    - budget_variance_analysis
    - zero_based_budget
    - cash_flow_forecast
    - revenue_forecast
    - financial_health_check
    - unit_economics_analysis
    - board_financial_update
    - monthly_close_report
    - audit_preparation
    - strategic_financial_plan
    - pricing_analysis
    """
    try:
        result = template_engine.generate(request.template_id, request.variables)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Template '{request.template_id}' not found"
            )

        template = template_engine.get_template(request.template_id)

        return TemplateResponse(
            template_id=request.template_id,
            name=template.name,
            category=template.category.value,
            prompt=result,
            variables_used=list(request.variables.keys())
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/templates/custom")
async def create_custom_prompt(
    task: str = Form(..., description="Financial task description"),
    context: str = Form(None, description="Additional context"),
    output_format: str = Form("detailed", description="Output format: brief, detailed, executive")
):
    """
    Generate a custom CFO-style prompt for any financial task.
    """
    try:
        prompt = template_engine.create_custom_prompt(task, context, output_format)

        return {
            "task": task,
            "output_format": output_format,
            "prompt": prompt
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Combined Analysis Endpoints
# ============================================================================

@router.post("/analyze/comprehensive")
async def comprehensive_financial_analysis(
    data: Optional[str] = Form(None, description="JSON spreadsheet data"),
    document: Optional[str] = Form(None, description="Document text"),
    template_id: Optional[str] = Form(None, description="Template to use"),
    variables: Optional[str] = Form(None, description="JSON template variables")
):
    """
    Perform comprehensive financial analysis combining multiple tools.

    Can process spreadsheet data, documents, and generate templated analysis.
    """
    results = {}

    try:
        # Process spreadsheet data if provided
        if data:
            parsed_data = json.loads(data)
            if isinstance(parsed_data, list) and parsed_data:
                columns = list(parsed_data[0].keys())
                spreadsheet_data = SpreadsheetData(
                    columns=columns,
                    rows=parsed_data,
                    name="analysis_data"
                )
                spreadsheet_engine.data = {"analysis_data": spreadsheet_data}

                # Run basic analysis queries
                results["spreadsheet"] = {
                    "row_count": len(parsed_data),
                    "columns": columns,
                    "summary": f"Loaded {len(parsed_data)} rows with {len(columns)} columns"
                }

        # Process document if provided
        if document:
            doc_type = document_intelligence.classify_document(document)
            results["document"] = {
                "type": doc_type,
                "length": len(document)
            }

            if doc_type == "contract":
                analysis = document_intelligence.analyze_contract(document)
                results["document"]["risk_score"] = analysis.risk_assessment.risk_score
                results["document"]["summary"] = analysis.summary
            elif doc_type == "invoice":
                invoice = document_intelligence.process_invoice(document)
                results["document"]["total"] = invoice.total_amount
                results["document"]["vendor"] = invoice.vendor_name
            elif doc_type == "financial_statement":
                statement = document_intelligence.parse_financial_statement(document)
                results["document"]["type"] = statement.statement_type
                results["document"]["metrics"] = statement.metrics

        # Generate template if requested
        if template_id:
            template_vars = json.loads(variables) if variables else {}
            prompt = template_engine.generate(template_id, template_vars)
            if prompt:
                results["template"] = {
                    "id": template_id,
                    "prompt": prompt
                }

        return {
            "success": True,
            "results": results
        }

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Health check
@router.get("/health")
async def finance_health():
    """Check finance API health status."""
    return {
        "status": "healthy",
        "modules": {
            "spreadsheet_engine": "active",
            "document_intelligence": "active",
            "template_engine": "active"
        },
        "templates_available": len(template_engine.templates)
    }
