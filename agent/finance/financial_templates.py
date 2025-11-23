"""
Financial Templates for JARVIS.

Pre-built prompts and workflows for CFO tasks including:
- Budget analysis
- Cash flow forecasting
- Financial reporting
- Variance analysis
- KPI dashboards
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class TemplateCategory(Enum):
    """Categories of financial templates."""
    BUDGETING = "budgeting"
    FORECASTING = "forecasting"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
    COMPLIANCE = "compliance"
    PLANNING = "planning"


@dataclass
class FinancialTemplate:
    """A pre-built financial analysis template."""
    id: str
    name: str
    category: TemplateCategory
    description: str
    prompt_template: str
    required_inputs: List[str]
    optional_inputs: List[str] = field(default_factory=list)
    output_format: str = "text"
    example_output: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "required_inputs": self.required_inputs,
            "optional_inputs": self.optional_inputs,
            "output_format": self.output_format
        }

    def generate_prompt(self, inputs: Dict[str, Any]) -> str:
        """Generate the full prompt with user inputs."""
        prompt = self.prompt_template

        for key, value in inputs.items():
            placeholder = f"{{{key}}}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(value))

        return prompt


# Pre-built financial templates
FINANCIAL_TEMPLATES: Dict[str, FinancialTemplate] = {

    # ========== BUDGETING TEMPLATES ==========

    "budget_variance_analysis": FinancialTemplate(
        id="budget_variance_analysis",
        name="Budget Variance Analysis",
        category=TemplateCategory.BUDGETING,
        description="Analyze actual vs budget performance and identify key variances",
        required_inputs=["actual_figures", "budget_figures", "period"],
        optional_inputs=["department", "prior_year"],
        prompt_template="""Perform a comprehensive budget variance analysis for {period}.

ACTUAL FIGURES:
{actual_figures}

BUDGET FIGURES:
{budget_figures}

Please provide:
1. **Variance Summary Table**
   - Line item, Budget, Actual, Variance ($), Variance (%)
   - Flag significant variances (>10%)

2. **Key Variance Drivers**
   - Top 5 favorable variances with explanations
   - Top 5 unfavorable variances with explanations

3. **Root Cause Analysis**
   - Identify underlying factors for major variances
   - Distinguish between timing vs permanent variances

4. **Recommendations**
   - Corrective actions for unfavorable variances
   - Opportunities from favorable variances

5. **Risk Assessment**
   - Impact on full-year forecast
   - Key assumptions to monitor

Format the output as a structured CFO briefing document.""",
        output_format="report"
    ),

    "zero_based_budget": FinancialTemplate(
        id="zero_based_budget",
        name="Zero-Based Budget Builder",
        category=TemplateCategory.BUDGETING,
        description="Build a zero-based budget from scratch with justifications",
        required_inputs=["department", "fiscal_year", "strategic_priorities"],
        optional_inputs=["headcount", "prior_year_spend"],
        prompt_template="""Create a zero-based budget for {department} for fiscal year {fiscal_year}.

STRATEGIC PRIORITIES:
{strategic_priorities}

Build the budget from zero, justifying every expense. Include:

1. **Personnel Costs**
   - Required headcount with role justifications
   - Salary benchmarks and ranges
   - Benefits and overhead allocation

2. **Operating Expenses**
   - Technology/software needs
   - Professional services
   - Travel and entertainment
   - Office and supplies

3. **Capital Expenditures**
   - Equipment and infrastructure
   - ROI analysis for major items

4. **Budget Summary**
   - Total by category
   - Comparison to typical industry benchmarks
   - Efficiency metrics

5. **Assumptions & Risks**
   - Key assumptions made
   - Sensitivity analysis

Prioritize expenses as: Critical / Important / Nice-to-have""",
        output_format="budget"
    ),

    # ========== FORECASTING TEMPLATES ==========

    "cash_flow_forecast": FinancialTemplate(
        id="cash_flow_forecast",
        name="Cash Flow Forecast",
        category=TemplateCategory.FORECASTING,
        description="13-week rolling cash flow forecast",
        required_inputs=["current_cash", "receivables", "payables", "recurring_revenue"],
        optional_inputs=["seasonality", "planned_capex", "debt_service"],
        prompt_template="""Generate a 13-week rolling cash flow forecast.

STARTING POSITION:
- Current Cash: {current_cash}
- Accounts Receivable: {receivables}
- Accounts Payable: {payables}
- Recurring Revenue: {recurring_revenue}

Create a detailed weekly forecast including:

1. **Cash Inflows**
   - Collections from AR (apply typical DSO)
   - New sales projections
   - Other income

2. **Cash Outflows**
   - Payroll (bi-weekly or monthly)
   - Vendor payments (AP aging)
   - Rent and fixed costs
   - Debt service
   - Planned CAPEX

3. **Weekly Summary**
   | Week | Beginning Cash | Inflows | Outflows | Net Change | Ending Cash |

4. **Cash Runway Analysis**
   - Weeks of cash remaining
   - Minimum cash threshold
   - Action triggers

5. **Scenario Analysis**
   - Base case
   - Optimistic (+20% revenue)
   - Pessimistic (-20% revenue)

6. **Recommendations**
   - Cash optimization opportunities
   - Working capital improvements
   - Financing needs if applicable""",
        output_format="forecast"
    ),

    "revenue_forecast": FinancialTemplate(
        id="revenue_forecast",
        name="Revenue Forecast Model",
        category=TemplateCategory.FORECASTING,
        description="Build a bottoms-up revenue forecast",
        required_inputs=["current_arr", "sales_pipeline", "churn_rate"],
        optional_inputs=["expansion_rate", "lead_conversion", "market_growth"],
        prompt_template="""Build a 12-month revenue forecast model.

CURRENT STATE:
- Current ARR: {current_arr}
- Sales Pipeline: {sales_pipeline}
- Historical Churn Rate: {churn_rate}

Create a comprehensive revenue model:

1. **Revenue Drivers Analysis**
   - New customer acquisition
   - Expansion revenue
   - Churn and contraction
   - Pricing changes

2. **Monthly Forecast**
   | Month | Starting MRR | New | Expansion | Churn | Ending MRR | ARR |

3. **Cohort Analysis**
   - Revenue by customer cohort
   - Retention curves

4. **Key Metrics Projection**
   - Net Revenue Retention (NRR)
   - Gross Revenue Retention (GRR)
   - Average Revenue Per Account (ARPA)
   - Customer Lifetime Value (LTV)

5. **Assumptions & Sensitivity**
   - Key assumptions documented
   - Impact of ±10% on key variables

6. **Growth Analysis**
   - YoY growth rate
   - Path to targets
   - Gaps and risks""",
        output_format="model"
    ),

    # ========== ANALYSIS TEMPLATES ==========

    "financial_health_check": FinancialTemplate(
        id="financial_health_check",
        name="Financial Health Check",
        category=TemplateCategory.ANALYSIS,
        description="Comprehensive financial health assessment",
        required_inputs=["income_statement", "balance_sheet"],
        optional_inputs=["cash_flow_statement", "industry"],
        prompt_template="""Perform a comprehensive financial health check.

INCOME STATEMENT:
{income_statement}

BALANCE SHEET:
{balance_sheet}

Analyze and provide:

1. **Profitability Analysis**
   - Gross margin and trend
   - Operating margin
   - Net profit margin
   - EBITDA margin

2. **Liquidity Analysis**
   - Current ratio
   - Quick ratio
   - Working capital
   - Cash conversion cycle

3. **Leverage Analysis**
   - Debt-to-equity ratio
   - Interest coverage ratio
   - Debt service coverage

4. **Efficiency Metrics**
   - Asset turnover
   - Inventory turnover
   - Receivables turnover
   - Payables turnover

5. **Return Metrics**
   - Return on Assets (ROA)
   - Return on Equity (ROE)
   - Return on Invested Capital (ROIC)

6. **Health Score Card**
   | Metric | Value | Benchmark | Status |
   (Green/Yellow/Red for each)

7. **Priority Recommendations**
   - Immediate actions
   - 90-day improvements
   - Strategic initiatives""",
        output_format="analysis"
    ),

    "unit_economics_analysis": FinancialTemplate(
        id="unit_economics_analysis",
        name="Unit Economics Analysis",
        category=TemplateCategory.ANALYSIS,
        description="Analyze customer unit economics and profitability",
        required_inputs=["cac", "ltv", "arpu", "gross_margin"],
        optional_inputs=["payback_period", "cohort_data"],
        prompt_template="""Analyze unit economics for the business.

INPUTS:
- Customer Acquisition Cost (CAC): {cac}
- Customer Lifetime Value (LTV): {ltv}
- Average Revenue Per User (ARPU): {arpu}
- Gross Margin: {gross_margin}

Provide comprehensive analysis:

1. **Core Metrics**
   - LTV:CAC ratio (target >3x)
   - Gross margin-adjusted LTV
   - CAC payback period (months)

2. **Profitability Analysis**
   - Contribution margin per customer
   - Break-even point
   - Customer profitability tiers

3. **Cohort Performance**
   - LTV by acquisition cohort
   - Retention curves
   - Revenue quality

4. **Channel Economics**
   - CAC by acquisition channel
   - Channel ROI comparison
   - Optimal channel mix

5. **Improvement Opportunities**
   - CAC reduction strategies
   - LTV expansion levers
   - Margin improvement tactics

6. **Scenario Modeling**
   - Impact of 10% CAC reduction
   - Impact of 10% LTV increase
   - Combined improvement scenario""",
        output_format="analysis"
    ),

    # ========== REPORTING TEMPLATES ==========

    "board_financial_update": FinancialTemplate(
        id="board_financial_update",
        name="Board Financial Update",
        category=TemplateCategory.REPORTING,
        description="Executive summary for board meetings",
        required_inputs=["period", "revenue", "expenses", "key_metrics"],
        optional_inputs=["strategic_updates", "risks"],
        prompt_template="""Prepare a board-ready financial update for {period}.

FINANCIAL RESULTS:
- Revenue: {revenue}
- Expenses: {expenses}

KEY METRICS:
{key_metrics}

Create an executive summary including:

1. **Executive Summary** (1 paragraph)
   - Overall performance headline
   - Key wins and challenges

2. **Financial Highlights**
   | Metric | Actual | Budget | Variance | Prior Year |
   - Revenue
   - Gross Profit
   - EBITDA
   - Net Income
   - Cash Position

3. **Key Performance Indicators**
   - Operational KPIs with trends
   - Visual indicators (↑↓→)

4. **Strategic Progress**
   - Progress against annual goals
   - Major milestones achieved

5. **Risks & Mitigations**
   - Top 3 financial risks
   - Mitigation actions

6. **Outlook**
   - Full-year forecast update
   - Key assumptions
   - Guidance changes if any

7. **Ask of the Board**
   - Decisions needed
   - Discussion items

Keep it concise - board members have limited time.""",
        output_format="presentation"
    ),

    "monthly_close_report": FinancialTemplate(
        id="monthly_close_report",
        name="Monthly Close Report",
        category=TemplateCategory.REPORTING,
        description="Comprehensive monthly financial close package",
        required_inputs=["month", "income_statement", "balance_sheet"],
        optional_inputs=["cash_flow", "departmental_detail"],
        prompt_template="""Prepare the monthly financial close report for {month}.

INCOME STATEMENT:
{income_statement}

BALANCE SHEET:
{balance_sheet}

Generate a complete close package:

1. **Income Statement Analysis**
   - Revenue by product/segment
   - Gross profit analysis
   - Operating expense breakdown
   - Net income reconciliation

2. **Balance Sheet Analysis**
   - Working capital changes
   - Debt and equity movements
   - Key account reconciliations

3. **Cash Flow Summary**
   - Operating cash flow
   - Investing activities
   - Financing activities
   - Cash bridge

4. **Variance Commentary**
   - Budget vs actual (material items)
   - Prior year comparison
   - Management explanations

5. **Key Metrics Dashboard**
   - Financial KPIs
   - Operating metrics
   - Trend charts (describe)

6. **Accounting Matters**
   - Significant estimates
   - Unusual transactions
   - Audit considerations

7. **Appendices**
   - Detailed schedules
   - Supporting documentation""",
        output_format="report"
    ),

    # ========== COMPLIANCE TEMPLATES ==========

    "audit_preparation": FinancialTemplate(
        id="audit_preparation",
        name="Audit Preparation Checklist",
        category=TemplateCategory.COMPLIANCE,
        description="Prepare for external audit with comprehensive checklist",
        required_inputs=["fiscal_year", "audit_firm"],
        optional_inputs=["prior_audit_findings", "risk_areas"],
        prompt_template="""Prepare audit readiness checklist for fiscal year {fiscal_year} audit by {audit_firm}.

Create a comprehensive preparation plan:

1. **Pre-Audit Timeline**
   - 90 days before: Document preparation
   - 60 days before: Internal review
   - 30 days before: Final reconciliations
   - Audit week: Support and queries

2. **Document Checklist**
   □ Trial balance
   □ Bank reconciliations
   □ AR/AP aging reports
   □ Fixed asset register
   □ Inventory counts
   □ Debt schedules
   □ Equity roll-forward
   □ Revenue recognition support
   □ Expense accruals
   □ Intercompany reconciliations

3. **Account Reconciliations**
   - Status of all balance sheet accounts
   - Open items resolution plan

4. **Internal Control Documentation**
   - Control matrices
   - Walkthrough documentation
   - Testing results

5. **Risk Areas**
   - Revenue recognition
   - Estimates and judgments
   - Related party transactions
   - Subsequent events

6. **PBC (Prepared by Client) List**
   - Standard PBC items
   - Custom requests from prior year
   - Deadlines for each item

7. **Team Assignments**
   - Primary contacts by area
   - Backup coverage
   - Escalation path""",
        output_format="checklist"
    ),

    # ========== PLANNING TEMPLATES ==========

    "strategic_financial_plan": FinancialTemplate(
        id="strategic_financial_plan",
        name="3-Year Financial Plan",
        category=TemplateCategory.PLANNING,
        description="Long-term financial planning and modeling",
        required_inputs=["current_financials", "growth_targets", "strategic_initiatives"],
        optional_inputs=["market_data", "competitive_info"],
        prompt_template="""Develop a 3-year strategic financial plan.

CURRENT STATE:
{current_financials}

GROWTH TARGETS:
{growth_targets}

STRATEGIC INITIATIVES:
{strategic_initiatives}

Build a comprehensive financial plan:

1. **Executive Summary**
   - Vision and financial goals
   - Key strategies
   - Investment requirements
   - Expected returns

2. **Revenue Plan**
   - Year 1, 2, 3 projections
   - Growth drivers by segment
   - New product/market contributions
   - Pricing strategy impact

3. **Cost Structure Evolution**
   - Fixed vs variable cost shift
   - Economies of scale
   - Investment requirements
   - Headcount plan

4. **Profitability Roadmap**
   | Year | Revenue | Gross Margin | EBITDA | Net Income |
   - Path to target margins
   - Break-even analysis

5. **Capital Requirements**
   - Operating investments
   - Capital expenditures
   - Working capital needs
   - Funding sources

6. **Scenario Planning**
   - Base case
   - Upside case
   - Downside case
   - Break-even scenario

7. **Key Milestones**
   - Financial milestones by quarter
   - Leading indicators to track
   - Decision gates

8. **Risk Factors**
   - Key risks and mitigations
   - Sensitivity analysis
   - Contingency plans""",
        output_format="plan"
    ),

    "pricing_analysis": FinancialTemplate(
        id="pricing_analysis",
        name="Pricing Analysis & Strategy",
        category=TemplateCategory.PLANNING,
        description="Analyze pricing and develop optimization strategies",
        required_inputs=["current_pricing", "costs", "market_data"],
        optional_inputs=["competitor_pricing", "elasticity_data"],
        prompt_template="""Analyze current pricing and develop optimization strategy.

CURRENT PRICING:
{current_pricing}

COST STRUCTURE:
{costs}

MARKET DATA:
{market_data}

Provide comprehensive pricing analysis:

1. **Current State Analysis**
   - Price points by product/tier
   - Gross margins by offering
   - Revenue mix and trends

2. **Cost Analysis**
   - Unit economics breakdown
   - Cost drivers
   - Break-even pricing

3. **Market Comparison**
   - Competitive positioning
   - Price-value map
   - Market gaps

4. **Elasticity Assessment**
   - Estimated price sensitivity
   - Volume impact modeling
   - Customer segment analysis

5. **Pricing Recommendations**
   - Optimal price points
   - Packaging suggestions
   - Discount strategy
   - Implementation timeline

6. **Financial Impact**
   - Revenue impact scenarios
   - Margin improvement potential
   - Customer retention risk

7. **Implementation Plan**
   - Rollout strategy
   - Communication plan
   - Exception handling""",
        output_format="analysis"
    ),
}


class FinancialTemplateEngine:
    """Engine for managing and executing financial templates."""

    def __init__(self):
        self.templates = FINANCIAL_TEMPLATES

    def list_templates(self, category: Optional[TemplateCategory] = None) -> List[Dict]:
        """List available templates, optionally filtered by category."""
        templates = []
        for template in self.templates.values():
            if category is None or template.category == category:
                templates.append(template.to_dict())
        return templates

    def get_template(self, template_id: str) -> Optional[FinancialTemplate]:
        """Get a specific template by ID."""
        return self.templates.get(template_id)

    def execute_template(self, template_id: str, inputs: Dict[str, Any]) -> Dict:
        """Execute a template with provided inputs."""
        template = self.get_template(template_id)
        if not template:
            return {"error": f"Template not found: {template_id}"}

        # Validate required inputs
        missing = [inp for inp in template.required_inputs if inp not in inputs]
        if missing:
            return {
                "error": "Missing required inputs",
                "missing_inputs": missing
            }

        # Generate the prompt
        prompt = template.generate_prompt(inputs)

        return {
            "template_id": template_id,
            "template_name": template.name,
            "prompt": prompt,
            "output_format": template.output_format
        }

    def get_categories(self) -> List[Dict]:
        """Get list of template categories with counts."""
        category_counts = {}
        for template in self.templates.values():
            cat = template.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return [
            {"category": cat, "count": count, "description": self._category_description(cat)}
            for cat, count in category_counts.items()
        ]

    def _category_description(self, category: str) -> str:
        """Get description for a category."""
        descriptions = {
            "budgeting": "Budget creation, analysis, and variance reporting",
            "forecasting": "Cash flow, revenue, and financial forecasting",
            "analysis": "Financial health, unit economics, and performance analysis",
            "reporting": "Board updates, monthly close, and executive reporting",
            "compliance": "Audit preparation and regulatory compliance",
            "planning": "Strategic planning, pricing, and long-term modeling"
        }
        return descriptions.get(category, "Financial analysis templates")

    def search_templates(self, query: str) -> List[Dict]:
        """Search templates by keyword."""
        query_lower = query.lower()
        results = []

        for template in self.templates.values():
            if (query_lower in template.name.lower() or
                query_lower in template.description.lower() or
                query_lower in template.category.value):
                results.append(template.to_dict())

        return results


# Singleton instance
_template_engine = None

def get_template_engine() -> FinancialTemplateEngine:
    """Get or create the template engine instance."""
    global _template_engine
    if _template_engine is None:
        _template_engine = FinancialTemplateEngine()
    return _template_engine
