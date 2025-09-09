from typing import List, Optional, Literal, Tuple, Dict, Any, Annotated
from pydantic import BaseModel, Field
from datetime import datetime, date

class Sentiment(BaseModel):
    """
    Represents the sentiment analysis result of a given text.
    """
    sentiment: Literal['positive', 'negative', 'neutral'] = Field(..., description="Classification of the sentiment (positive, negative, or neutral).")
    reason: str = Field(..., description="Detailed reason for the sentiment classification.")
    positive_factors: str = Field(..., description="List of positive factors affecting the sentiment.")
    negative_factors: str = Field(..., description="List of negative factors affecting the sentiment.")
    neutral_factors: str = Field(..., description="List of neutral factors affecting the sentiment.")

class TickerResponse(BaseModel):
    """
    Represents a response containing a stock ticker symbol.
    """
    ticker: str = Field(..., description="The official stock ticker symbol for the company (e.g., MSFT for Microsoft).")

class FinancialKPI(BaseModel):
    """
    Represents a single Financial Key Performance Indicator.
    """
    name: str = Field(..., description="Name of the KPI (e.g., 'Revenue', 'Net Income').")
    value: float = Field(..., description="The numerical value of the KPI.")
    unit: Optional[str] = Field(None, description="The unit of the KPI (e.g., 'USD', '%').")
    notes: Optional[str] = Field(None, description="Any additional notes or context for the KPI.")

class ReportSection(BaseModel):
    """
    Represents a section within a larger report.
    """
    title: str = Field(..., description="The title of the report section.")
    content: str = Field(..., description="The textual content of the report section.")

class Attachment(BaseModel):
    """
    Represents an attachment linked to a report.
    """
    filename: str = Field(..., description="The filename of the attachment.")
    description: Optional[str] = Field(None, description="A brief description of the attachment.")
    url: Optional[str] = Field(None, description="URL where the attachment can be accessed.")

class FinancialAnalysisReport(BaseModel):
    """
    Comprehensive financial analysis report for a company.
    """
    report_id: str = Field(..., description="Unique identifier for the report.")
    title: str = Field(..., description="The title of the financial analysis report.")
    prepared_by: Optional[str] = Field(None, description="The entity or individual who prepared the report.")
    prepared_for: str = Field(..., description="The entity or individual for whom the report was prepared.")
    date: date = Field(..., description="The date the report was prepared.")
    summary: str = Field(..., description="An executive summary of the report's key findings.")
    kpis: List[FinancialKPI] = Field(..., description="A list of key financial performance indicators.")
    findings: List[ReportSection] = Field(..., description="Detailed findings from the financial analysis.")
    recommendations: List[ReportSection] = Field(..., description="Actionable recommendations based on the analysis.")
    attachments: Optional[List[Attachment]] = Field(None, description="Optional list of attachments to the report.")
    notes: Optional[str] = Field(None, description="Any additional notes or disclaimers.")

class ComplianceReport(BaseModel):
    """
    Report detailing the results of a regulatory compliance review.
    """
    report_id: str = Field(..., description="Unique ID for the compliance review.")
    reviewed_on: datetime = Field(default_factory=datetime.utcnow, description="Date and time of compliance review (UTC).")
    reviewer: str = Field(..., description="Name or role of the compliance agent/team.")
    query: str = Field(..., description="The original query or context that was reviewed for compliance.")
    overall_status: Literal["Compliant", "Partially Compliant", "Non-Compliant"] = Field(
        ..., description="Final verdict of the compliance check."
    )
    executive_summary: str = Field(..., description="High-level summary of the compliance assessment.")
    findings: List[str] = Field(
        default_factory=list,
        description="Bullet points of specific compliance observations, including rule references inline."
    )
    severity: Literal["Low", "Medium", "High", "Critical"] = Field(
        "Medium", description="Overall severity rating of identified compliance risks."
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Clear steps and actions recommended to achieve or maintain compliance."
    )
    regulatory_issues: List[str] = Field(
        default_factory=list,
        description="Specific regulatory issues identified and the reasons for their classification."
    )

class WACCOutput(BaseModel):
    """
    Structured output for the WACC (Weighted Average Cost of Capital) Analyst.
    """
    wacc: float = Field(..., description="The final calculated Weighted Average Cost of Capital.")
    risk_free_rate: float = Field(..., description="The risk-free rate used in the calculation.")
    beta: float = Field(..., description="The company's stock beta used in the calculation.")
    cost_of_equity: float = Field(..., description="The calculated cost of equity.")
    assumptions: str = Field(..., description="Key assumptions used in the WACC calculation.")

class UFCF_Forecast(BaseModel):
    """
    Structured output for the Unlevered Free Cash Flow (UFCF) Forecast.
    """
    forecasted_ufcf: List[float] = Field(description="The projected Unlevered Free Cash Flow for the next 5 years.")
    assumptions: str = Field(
        ...,
        description='Assumptions made in order to calculate the free cash flows.'
    )

class FinalDCFReport(BaseModel):
    """
    Final DCF Valuation Report containing the intrinsic value per share, key assumptions, and overall judgment.
    """
    intrinsic_value_per_share: float = Field(
        ...,
        description="The estimated intrinsic value per share from the DCF analysis."
    )
    assumptions: str = Field(
        ...,
        description="Key assumptions used in the DCF valuation (e.g., WACC, terminal growth rate, forecast period, growth rates, etc.)."
    )
    judgment: Literal["overvalued", "undervalued", "fairly valued"] = Field(
        ...,
        description="An overall assessment or conclusion regarding the valuation result (e.g., whether the stock appears undervalued, overvalued, or fairly valued based on the analysis)."
    )

class PeerCompanies(BaseModel):
    """
    Structured output for the Peer Discovery Agent.
    """
    peer_tickers: List[str] = Field(
        description="A list of the ticker symbols for the identified comparable peer companies."
    )
    rationale: str = Field(
        description="A brief justification for why these companies were chosen as peers, based on industry, size, geography, growth, and profitability."
    )

class CompsValuationReport(BaseModel):
    """
    Structured output for the Comparable Companies Valuation Agent.
    """
    valuation_range: Tuple[float, float] = Field(
        description="The low and high valuation per share for the target company based on comparable company multiples."
    )
    summary_table: str = Field(
        description="A markdown-formatted table summarizing the key financial metrics and valuation multiples for the peer group and the target company."
    )
    summary: str = Field(
        description="A concluding summary of the comparable company analysis."
    )

class ValuationOutput(BaseModel):
    """
    Comprehensive valuation output combining multiple methodologies.
    """
    dcf_valuation: float = Field(..., description="Discounted Cash Flow (DCF) valuation result.")
    dcf_valuation_range: Optional[Tuple[float, float]] = Field(
        default=None, description="Range for DCF valuation (low, high)."
    )
    dcf_summary: str = Field(..., description="Summary of DCF analysis including key assumptions.")
    comps_valuation: float = Field(..., description="Valuation based on comparable companies.")
    comps_summary: str = Field(..., description="Summary of comparable companies analysis.")
    comps_metrics: Optional[Dict[str, Any]] = Field(
        default=None, description="Key valuation metrics from comparable analysis."
    )
    qualitative_factors: str = Field(
        ..., description="Qualitative factors considered in valuation."
    )
    macroeconomic_context: str = Field(
        ..., description="Macroeconomic context relevant to valuation."
    )
    industry_outlook: str = Field(
        ..., description="Industry-specific trends and outlook."
    )
    current_market_price: float = Field(
        ..., description="Current market price of the asset."
    )
    valuation_vs_market: float = Field(
        ..., description="Percentage difference between valuation and market price."
    )
    final_recommendation: Literal["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"] = Field(
        ..., description="Final investment recommendation."
    )
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Confidence score in the recommendation (0-1)."
    )
    valuation_conclusion: Literal['overvalued', 'undervalued', 'fairly valued'] = Field(
        ..., description="Valuation conclusion relative to market."
    )
    assumptions_taken: List[str] = Field(
        ..., description="List of key assumptions taken in the analysis."
    )
    sensitivity_analysis: Optional[str] = Field(
        default=None, description="Sensitivity analysis summary."
    )
    key_risks: str = Field(
        ..., description="Key risks for the company which can affect its valuation."
    )
    risk_level: Literal['Low', 'Medium', 'High'] = Field(
        ..., description="Overall risk level assessment."
    )
    valuation_date: datetime = Field(
        default_factory=datetime.now, description="Date and time of valuation."
    )
    ticker: str = Field(..., description="Company ticker symbol.")
    currency: str = Field(default="USD", description="Currency used for valuation.")
    executive_summary: str = Field(
        ..., description="Executive summary of the valuation."
    )

class IndustryTrendsOutput(BaseModel):
    """
    Structured output for Industry Trends Analysis.
    """
    industry_overview: str = Field(..., description="Comprehensive overview of the company's industry sector, market size, and strategic positioning.")
    key_trends: List[str] = Field(..., description="Major industry trends, technological disruptions, and emerging patterns affecting the company.")
    regulatory_changes: List[str] = Field(..., description="Significant regulatory changes, compliance requirements, and upcoming policy impacts.")
    market_dynamics: str = Field(..., description="Current market conditions, competitive intensity, supply-demand dynamics, and pricing trends.")
    growth_drivers: List[str] = Field(..., description="Primary factors driving industry expansion, innovation catalysts, and market opportunities.")
    challenges: List[str] = Field(..., description="Major industry headwinds, structural challenges, and potential disruption risks.")
    market_outlook: str = Field(..., description="Forward-looking assessment of industry prospects and expected developments.")

class BusinessSegmentsOutput(BaseModel):
    """
    Structured output for Business Segments Analysis.
    """
    segment_breakdown: Dict[str, Dict[str, Any]] = Field(..., description="Detailed performance metrics and KPIs breakdown by business segments.")
    revenue_contribution: Dict[str, float] = Field(..., description="Revenue contribution percentage and absolute values by segment.")
    profitability_analysis: Dict[str, str] = Field(..., description="Margin analysis, ROI, and profitability trends for each segment.")
    geographic_performance: Dict[str, str] = Field(..., description="Regional performance analysis including market penetration and growth rates.")
    growth_segments: List[str] = Field(..., description="High-growth business segments with expansion potential and strategic importance.")
    underperforming_segments: List[str] = Field(..., description="Segments facing headwinds, declining performance, or strategic challenges.")
    segment_synergies: str = Field(..., description="Cross-segment synergies, integration opportunities, and portfolio optimization.")

class SWOTOutput(BaseModel):
    """
    Structured output for SWOT Analysis.
    """
    strengths: List[str] = Field(..., description="Core competencies, competitive advantages, and internal capabilities.")
    weaknesses: List[str] = Field(..., description="Internal limitations, resource constraints, and areas requiring improvement.")
    opportunities: List[str] = Field(..., description="Market opportunities, growth potential, and strategic expansion possibilities.")
    threats: List[str] = Field(..., description="External risks, competitive pressures, and market challenges.")
    strategic_recommendations: List[str] = Field(..., description="Actionable strategic initiatives and recommendations based on SWOT matrix.")
    strategic_priorities: List[str] = Field(..., description="Top strategic priorities ranked by impact and feasibility.")

class RiskAssessmentOutput(BaseModel):
    """
    Structured output for Risk Assessment Analysis.
    """
    operational_risks: List[str] = Field(..., description="Key operational risks and business continuity concerns.")
    financial_risks: List[str] = Field(..., description="Financial risks including liquidity, credit, and market risks.")
    strategic_risks: List[str] = Field(..., description="Strategic risks affecting long-term competitiveness and market position.")
    mitigation_strategies: Dict[str, str] = Field(..., description="Risk mitigation strategies and contingency plans.")

class BusinessOperationsOutput(BaseModel):
    """
    Comprehensive Business and Operations Analysis Output.
    """
    company_overview: str = Field(..., description="Executive summary covering business model, value proposition, and operational framework.")
    industry_analysis: IndustryTrendsOutput = Field(..., description="Comprehensive industry trends and market dynamics analysis.")
    business_segments: BusinessSegmentsOutput = Field(..., description="Detailed business segments performance and strategic analysis.")
    swot_analysis: SWOTOutput = Field(..., description="Strategic SWOT analysis with actionable insights and priorities.")
    competitive_positioning: str = Field(..., description="Market positioning analysis including competitive advantages and differentiation strategy.")
    operational_efficiency: str = Field(..., description="Operational excellence assessment covering efficiency metrics, process optimization, and scalability.")
    risk_assessment: RiskAssessmentOutput = Field(..., description="Comprehensive risk analysis and mitigation framework.")
    strategic_outlook: str = Field(..., description="Forward-looking strategic assessment and growth trajectory analysis.")
    key_performance_indicators: Dict[str, str] = Field(..., description="Critical KPIs and performance metrics for business monitoring.")

class RiskSection(BaseModel):
    """
    Base schema for a section of a risk report.
    """
    summary: Annotated[str, Field(description="A concise, formal summary of the key risks in this category.")]
    main_threats: Annotated[List[str], Field(description="A prioritized list of the most significant threats identified.")]
    critical_risks: Annotated[List[str], Field(description="A list of the most critical and urgent risks requiring immediate attention.")]
    moderate_risks: Annotated[List[str], Field(description="A list of moderate risks that should be monitored but are less urgent.")]
    minor_risks: Annotated[List[str], Field(description="A list of minor or low-probability risks.")]
    overall_risk_level: Annotated[Literal['High', 'Medium', 'Low', 'Very Low'], Field(description="A formal assessment of the overall risk level for this category.")]

class FinancialRiskSection(RiskSection):
    """
    Specific schema for the financial risk section of a report.
    """
    specific_risks: Annotated[List[str], Field(description="A detailed list of financial risks identified, with supporting evidence.")]
    rationale: Annotated[List[str], Field(description="A list of reasons and justifications for the financial risk assessment.")]

class NewsRiskSection(RiskSection):
    """
    Specific schema for the news-related risk section of a report.
    """
    specific_risks: Annotated[List[str], Field(description="A detailed list of news-related risks identified, with supporting evidence.")]
    rationale: Annotated[List[str], Field(description="A list of reasons and justifications for the news risk assessment.")]

class TechnicalRiskSection(RiskSection):
    """
    Specific schema for the technical risk section of a report.
    """
    specific_risks: Annotated[List[str], Field(description="A detailed list of technical risks identified, with supporting evidence.")]
    rationale: Annotated[List[str], Field(description="A list of reasons and justifications for the technical risk assessment.")]

class FullRiskReport(BaseModel):
    """
    Comprehensive risk report combining financial, news, and technical risk assessments.
    """
    executive_summary: Annotated[str, Field(description="A formal executive summary of the overall risk profile, highlighting the most material risks across all categories.")]
    financial: FinancialRiskSection
    news: NewsRiskSection
    technical: TechnicalRiskSection
    conclusion: Annotated[str, Field(description="A formal concluding statement summarizing the overall risk posture and any recommended actions or mitigations.")]

class FactCheckResult(BaseModel):
    """
    Individual fact check result for a specific claim.
    """
    claim: str = Field(description="The specific claim being fact-checked.")
    is_accurate: bool = Field(description="Whether the claim is factually accurate.")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in the fact-check (0-1).")
    supporting_sources: List[str] = Field(description="Sources that support the claim.")
    contradicting_sources: List[str] = Field(description="Sources that contradict the claim.")
    verification_method: str = Field(description="How this fact was verified.")

class DataConsistencyCheck(BaseModel):
    """
    Check for data consistency across sources.
    """
    metric_name: str = Field(description="Name of the financial metric being checked.")
    primary_value: Optional[float] = Field(description="Value from primary source.")
    secondary_value: Optional[float] = Field(description="Value from secondary source.")
    variance_percentage: Optional[float] = Field(description="Percentage difference between sources.")
    is_consistent: bool = Field(description="Whether values are within acceptable variance.")
    acceptable_variance: float = Field(default=5.0, description="Acceptable variance percentage.")
    data_freshness: str = Field(description="How fresh the data is (real-time, daily, etc.).")

class SourceReliability(BaseModel):
    """
    Assessment of data source reliability.
    """
    source_name: str = Field(description="Name of the data source.")
    reliability_score: float = Field(ge=0, le=10, description="Reliability score (0-10).")
    last_updated: Optional[datetime] = Field(description="When the source was last updated.")
    data_freshness: str = Field(description="How fresh the data is (real-time, daily, etc.).")
    known_issues: List[str] = Field(description="Known issues or limitations with this source.")

class ComprehensiveFactCheck(BaseModel):
    """
    Complete fact-checking report for a stock ticker.
    """
    ticker: str = Field(description="Stock ticker being analyzed.")
    fact_check_results: List[FactCheckResult] = Field(description="Individual fact check results.")
    data_consistency_checks: List[DataConsistencyCheck] = Field(description="Cross-source data consistency checks.")
    source_reliability: List[SourceReliability] = Field(description="Source reliability assessments.")
    overall_accuracy_score: float = Field(ge=0.0, le=1.0, description="Overall accuracy score (0-1).")
    critical_issues: List[str] = Field(description="Critical accuracy issues found.")
    recommendations: List[str] = Field(description="Recommendations for improving accuracy.")
    fact_check_timestamp: datetime = Field(default_factory=datetime.now)
    summary: Optional[str] = Field(None, description="Summary of the fact-checking report.")

class ValidationReport(BaseModel):
    """
    Provides the validation results for a professional report, including grammatical errors and all required validations.
    """
    is_valid: bool = Field(description="Indicates whether the report passed all validation checks.")
    grammatical_errors: List[str] = Field(default_factory=list, description="List of grammatical errors found in the report.")
    missing_sections: List[str] = Field(default_factory=list, description="Sections that are missing or incomplete.")
    formatting_issues: List[str] = Field(default_factory=list, description="Formatting or style issues detected.")
    data_inconsistencies: List[str] = Field(default_factory=list, description="Detected inconsistencies in data or facts.")
    citation_issues: List[str] = Field(default_factory=list, description="Problems with citations or references.")
    warnings: List[str] = Field(default_factory=list, description="Non-critical warnings or suggestions for improvement.")
    checked_at: datetime = Field(default_factory=datetime.now, description="Timestamp when validation was performed.")
    summary: Optional[str] = Field(None, description="Brief summary of the validation results.")

class EvalReport(BaseModel):
    """
    Evaluation report for assessing the quality and professionalism of a financial report.
    """
    grade: Literal['PASS', 'FAIL'] = Field(description='Final grade of the report based on your evaluation.')
    overall_score: Optional[float] = Field(default=None, description='Overall numeric score (0-100) reflecting the report quality.')
    reasons: List[str] = Field(description='Key reasons for the assigned grade, in bullet points.')
    recommendations: List[str] = Field(description='Actionable recommendations for improvement, in bullet points.')
    clarity: Dict[str, Any] = Field(
        description='Clarity evaluation details.',
        example={
            "score": "1-5",
            "assessment": "Language is precise and unambiguous for a financial audience.",
            "issues": ["Some jargon is not explained."],
            "suggestions": ["Define technical terms."]
        }
    )
    objectivity: Dict[str, Any] = Field(
        description='Objectivity evaluation details.',
        example={
            "score": "1-5",
            "assessment": "Tone is neutral and unbiased.",
            "issues": [],
            "suggestions": []
        }
    )
    completeness: Dict[str, Any] = Field(
        description='Completeness evaluation details.',
        example={
            "score": "1-5",
            "assessment": "All key financial areas are addressed.",
            "issues": ["Risk section is brief."],
            "suggestions": ["Expand risk analysis."]
        }
    )
    logical_consistency: Dict[str, Any] = Field(
        description='Logical consistency evaluation details.',
        example={
            "score": "1-5",
            "assessment": "Conclusions follow from evidence.",
            "issues": [],
            "suggestions": []
        }
    )
    professionalism: Dict[str, Any] = Field(
        description='Professionalism evaluation details.',
        example={
            "score": "1-5",
            "assessment": "Report is well-formatted and suitable for executive review.",
            "issues": ["Formatting is inconsistent."],
            "suggestions": ["Standardize section headings."]
        }
    )
    reviewed_at: Optional[datetime] = Field(default_factory=datetime.now, description='Timestamp of evaluation.')
    summary: str = Field(description='One-paragraph executive summary of the evaluation.')

class Sector(BaseModel):
    """
    Represents a financial sector.
    """
    sector: str = Field(
        description=(
            "The sector to fetch data for. Must be one of: "
            "Energy, Technology, Healthcare, Financial Services, Consumer Cyclical, "
            "Consumer Defensive, Industrials, Basic Materials, Real Estate, Utilities, Communication Services."
        )
    )

class Validate(BaseModel):
    """
    Schema for validating if an answer is correct based on context.
    """
    is_correct: bool = Field(..., description='True if the answer is supported by context, False otherwise.')
