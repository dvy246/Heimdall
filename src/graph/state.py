from typing import TypedDict, Annotated, Optional, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class HeimdallState(TypedDict, total=False):
    """
    State management for the Heimdall financial analysis system.

    This TypedDict defines the complete state structure used throughout the
    LangGraph workflow for company analysis. All fields are optional to allow
    for flexible state evolution during analysis.

    Attributes:
        ticker (str): Stock ticker symbol (e.g., "AAPL").
        company_name (str): Full company name.
        mission_plan (Optional[str]): High-level analysis objectives.
        financial_report (Optional[str]): Financial statement analysis results.
        news_report (Optional[str]): News sentiment and analysis.
        technical_report (Optional[str]): Technical indicators and chart analysis.
        research_report (Optional[str]): Comprehensive research summary.
        economic_report (Optional[str]): Macroeconomic context and trends.
        risk_report (Optional[str]): Risk assessment and mitigation strategies.
        valuation_report (Optional[str]): Company valuation analysis.
        dcf_analysis (Optional[str]): Discounted Cash Flow analysis.
        comps_analysis (Optional[str]): Comparable company analysis.
        precedent_analysis (Optional[str]): Precedent transaction analysis.
        final_report (Optional[str]): Complete integrated analysis report.
        validation_report (Optional[str]): Quality assurance and validation results.
        messages (Annotated[List[BaseMessage], add_messages]): LangChain message history with add_messages annotation.
    """
    ticker: str
    company_name: str
    mission_plan: Optional[str]
    financial_report: Optional[str]
    news_report: Optional[str]
    technical_report: Optional[str]
    research_report: Optional[str]
    economic_report: Optional[str]
    risk_report: Optional[str]
    valuation_report: Optional[str]
    dcf_analysis: Optional[str]
    comps_analysis: Optional[str]
    precedent_analysis: Optional[str]
    final_report: Optional[str]
    validation_report: Optional[str]
    messages: Annotated[List[BaseMessage], add_messages]
