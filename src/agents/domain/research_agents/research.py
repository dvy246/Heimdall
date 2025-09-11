from typing import List
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.graph.base import CompiledGraph
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.tools.data_providers.sec_tools import get_latest_10k_filing
from src.tools.data_providers.alpha_vantage import company_overview, get_cashflow, get_earnings, get_income_statements
from src.tools.utilities.extra import search_web
from src.tools.analysis.technical_analysis import get_technical_analysis
from src.tools.Rag.rag import query_data
from src.config.logging_config import logger
from src.prompts import load_prompt
from src.prompts import load_supervisor_prompt



# Research Team Agents
logger.info("Creating research team agents...")
financial_analyst: CompiledGraph = create_react_agent(
    model=model,
    tools=[get_latest_10k_filing, company_overview, get_cashflow, get_earnings, get_income_statements, query_data],
    name='financial_analyst',
    prompt=load_prompt('financial_analyst'),
)

news_analyst: CompiledGraph = create_react_agent(
    model=model,
    tools=[search_web],
    name='news_analyst',
    prompt=load_prompt('news_analyst'),
)

technical_analyst: CompiledGraph = create_react_agent(
    model=model,
    name='technical_analyst',
    tools=[get_technical_analysis, query_data],
    prompt=load_prompt('technical_analyst'),
)
logger.info("Research team agents created successfully.")

