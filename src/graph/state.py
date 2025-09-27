from typing import TypedDict, Annotated, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator


class HeimdallState(TypedDict):
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
        final_report (Optional[str]): Complete integrated analysis report.
        validation_report (Optional[str]): Quality assurance and validation results.
        messages (Annotated[List[BaseMessage], add_messages]): LangChain message history with add_messages annotation.
    """
    # Session metadata
    rag_path: str
    session_id: str
    timestamp: Optional[str]
    
    # Input parameters
    ticker: str
    company_name: str
    
    # Phase 1: Mission Planning
    mission_plan: Optional[str]
    
    # Phase 2: Domain Analysis
    financial_report: Optional[str]
    news_report: Optional[str]
    technical_report: Optional[str]
    research_report: Optional[str]
    economic_report: Optional[str]
    risk_report: Optional[str]
    valuation_report: Optional[str]
    dcf_analysis: Optional[str]
    comps_analysis: Optional[str]
    business_operations_report: Optional[str]
    
    # Phase 3: Synthesis & Assembly
    section_drafts: Optional[Dict[str, str]]
    draft_report: Optional[str]
    
    # Phase 4: Adversarial Gauntlet
    validation_report: Optional[str]
    compliance_report: Optional[str]
    socratic_critique: Optional[str]
    grounding_report: Optional[str]
    adversarial_gauntlet_report: Optional[str]
    iteration_count: Annotated[int, operator.add]
    max_iterations: int
    decision_report: Optional[str]
    
    # Phase 5: Human Collaboration
    human_feedback: Optional[str]
    human_feedback_report: Optional[str]
    applied_feedback: Optional[bool]
    
    # Phase 6: Finalization
    final_report: Optional[str]
    report_format: Optional[str]
    
    # Node outputs (for conditional routing)
    main_supervisor_output: Optional[Dict[str, Any]]
    decision_output: Optional[Dict[str, Any]]
    
    # Message history
    messages: Annotated[List[BaseMessage], add_messages]