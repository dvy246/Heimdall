from agno.agent import Agent
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.thinking import ThinkingTools
from src.config.settings import model2
from langchain_core.tools import tool
from src.config.logging_config import logger
from typing import Optional

@tool('financial_analysis_report_maker')
def financial_analysis_report_maker(company_name: str) -> str:
    """
    Creates a comprehensive financial analysis report for a given company.
    
    Args:
        company_name (str): Name of the company to analyze
        
    Returns:
        str: Comprehensive financial analysis report
        
    Raises:
        ValueError: If company_name is empty or invalid
    """
    if not company_name or not isinstance(company_name, str):
        logger.error(f"Invalid company name provided: {company_name}")
        raise ValueError("Company name must be a non-empty string")

    logger.info(f"Starting financial analysis for company: {company_name}")
    
    try:
        company_overview_agent = Agent(
            name="Web Search Agent",
            role="Search the web for information",
            model=model2,
            tools=[
                DuckDuckGoTools(),
                YFinanceTools(company_news=True, company_info=True),
                ThinkingTools(add_instructions=True)
            ],
            instructions=["Always include sources and verification steps"]
        )
        logger.debug("Web Search Agent initialized successfully")

        finance_agent = Agent(
            name="Finance AI Agent", 
            role="Analyze financial data and provide quantitative insights",
            model=model2,
            tools=[
                YFinanceTools(
                    stock_price=True,
                    analyst_recommendations=True,
                    stock_fundamentals=True,
                    company_news=True,
                    historical_prices=True,
                    company_info=True,
                    enable_all=True
                ),
                ThinkingTools(add_instructions=True)
            ],
            instructions=["Use tables for data presentation", "Include data sources"],
            enable_agentic_memory=False
        )
        logger.debug("Finance Agent initialized successfully")

        coordinator = Team(
            name="Finance Editor",
            mode="coordinate",
            model=model2,
            members=[company_overview_agent, finance_agent],
            description="Senior financial editor for comprehensive analysis",
            instructions=[
                "Gather relevant market intelligence from web search agent",
                "Obtain detailed financial analysis from finance agent",
                "Integrate findings with proper citations",
                "Include key metrics: financials, stock performance, analyst ratings",
                "Validate data consistency across sources"
            ],
            add_datetime_to_instructions=True,
            enable_agentic_memory=False
        )
        logger.info("Team coordinator initialized successfully")

        result = coordinator.run(f"Provide a comprehensive financial analysis of {company_name}")
        logger.info("Financial analysis completed successfully")
        
        return str(result)

    except Exception as e:
        logger.error(f"Error during financial analysis: {str(e)}", exc_info=True)
        raise