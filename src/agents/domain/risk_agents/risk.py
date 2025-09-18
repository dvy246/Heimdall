from typing import List
from langchain_community.tools import yahoo_finance_news
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
# Removed incorrect CompiledGraph import
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.model_schemas.schemas import FinancialRiskSection, NewsRiskSection, TechnicalRiskSection, FullRiskReport
from src.tools.data_providers.sec_tools import get_latest_10k_filing
from src.tools.data_providers.alpha_vantage import company_overview, get_cashflow, get_income_statements, get_balance_sheet, get_earnings
from src.tools.utilities.extra import search_web
from src.tools.analysis.technical_analysis import get_technical_analysis
from src.tools.Market.news import get_market_status
from src.tools.Rag.rag import query_data
from src.config.logging_config import logger
from src.prompts import load_prompt
from src.tools.Market.news import get_latest_news_sentiments, get_global_market_status, get_market_status
from src.tools.agents.handoff_tools import create_handoff_tools_agent
from src.tools.utilities.extra import get_google_finance_data

insider_agent = create_handoff_tools_agent('insider_agent')
quant_analyst = create_handoff_tools_agent('quant')

# Risk Team Agents
logger.info("Creating risk team agents...")
financial_risk_agent = create_react_agent(
    model=model,
    response_format=FinancialRiskSection,
    tools=[
        get_latest_10k_filing, company_overview, get_cashflow,
        get_income_statements, get_balance_sheet, get_earnings,
        query_data,insider_agent,quant_analyst
    ],
    name='financial_risk_agent',
    prompt=load_prompt('financial_risk_agent'),
)

news_risk_agent = create_react_agent(
    model=model,
    tools=[
        search_web, get_latest_news_sentiments,get_global_market_status,get_google_finance_data
    ],
    response_format=NewsRiskSection,
    name='news_risk_agent',
    prompt=load_prompt('news_risk_agent'),
)

technical_risk_agent = create_react_agent(
    model=model,
    tools=[
        get_technical_analysis, get_market_status, query_data,
        get_global_market_status,get_google_finance_data
    ],
    response_format=TechnicalRiskSection,
    name='technical_risk_agent',
    prompt=load_prompt('technical_risk_agent'),
)
logger.info("Risk team agents created successfully.")
