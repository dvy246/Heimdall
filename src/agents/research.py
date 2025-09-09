from typing import List
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.graph.base import CompiledGraph
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.tools.financial import get_latest_10k_filing, company_overview, get_cashflow, get_earnings, get_income_statements
from src.tools.news import search_web, analyze_news_sentiment
from src.tools.market import get_technical_analysis
from langgraph_swarm import create_handoff_tool
from src.config.logging_config import logger
from src.prompts import load_prompt
from src.prompts import load_supervisor_prompt

# Handoff tools
handoff_to_insider_agent_tool: BaseTool = create_handoff_tool(
    agent_name="insider_agent",
    description="Delegate insider trading analysis."
)
handoff_to_quant_analyst_tool: BaseTool = create_handoff_tool(
    agent_name="quantitative_analyst",
    description="Delegate quantitative analysis."
)
handoff_to_librarian: BaseTool = create_handoff_tool(
    agent_name="librarian",
    description="Handoff to librarian for data ingestion or querying."
)

# Research Team Agents
logger.info("Creating research team agents...")
financial_analyst: CompiledGraph = create_react_agent(
    model=model,
    tools=[get_latest_10k_filing, company_overview, get_cashflow, get_earnings, get_income_statements, handoff_to_librarian],
    name='financial_analyst',
    prompt=load_prompt('financial_analyst'),
)

news_analyst: CompiledGraph = create_react_agent(
    model=model,
    tools=[search_web, analyze_news_sentiment, handoff_to_insider_agent_tool],
    name='news_analyst',
    prompt=load_prompt('news_analyst'),
)

technical_analyst: CompiledGraph = create_react_agent(
    model=model,
    name='technical_analyst',
    tools=[get_technical_analysis, handoff_to_quant_analyst_tool, handoff_to_librarian],
    prompt=load_prompt('technical_analyst'),
)
logger.info("Research team agents created successfully.")

# Research Supervisor
logger.info("Creating research supervisor...")
research_supervisor: CompiledGraph = create_supervisor(
    [financial_analyst, news_analyst, technical_analyst],
    model=model,
    prompt=load_supervisor_prompt('research_supervisor')
).compile(name="research_supervisor")
logger.info("Research supervisor created successfully.")
