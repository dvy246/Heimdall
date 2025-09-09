from typing import List
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph.graph.base import CompiledGraph
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.models.schemas import (
    WACCOutput, UFCF_Forecast, FinalDCFReport, PeerCompanies, CompsValuationReport, ValuationOutput
)
from src.tools.financial import (
    get_income_statements, get_cashflow, get_balance_sheet, get_dcf,
    get_earnings, company_overview, get_sustainability_data
)
from src.tools.market import get_technical_analysis
from src.tools.news import search_web
from src.config.logging_config import logger
from src.prompts import load_prompt

# DCF Agents
logger.info("Creating DCF agents...")
free_cash_flow_forecaster: CompiledGraph = create_react_agent(
    model=model,
    tools=[get_income_statements, get_cashflow, get_balance_sheet, search_web],
    name="free_cash_flow_forecaster",
    response_format=UFCF_Forecast,
    prompt=load_prompt('free_cash_flow_forecaster'),
)

wacc_analyst: CompiledGraph = create_react_agent(
    model=model,
    tools=[get_earnings, search_web, company_overview, get_balance_sheet],
    name="wacc_analyst",
    response_format=WACCOutput,
    prompt=load_prompt('wacc_analyst'),
)

dcf_valuation_analyst: CompiledGraph = create_react_agent(
    model=model,
    tools=[get_balance_sheet, get_dcf, search_web],
    name="dcf_valuation_analyst",
    response_format=FinalDCFReport,
    prompt=load_prompt('dcf_valuation_analyst'),
)
logger.info("DCF agents created successfully.")

# DCF Supervisor
logger.info("Creating DCF supervisor...")
dcf_supervisor: CompiledGraph = create_supervisor(
    model=model,
    agents=[free_cash_flow_forecaster, wacc_analyst, dcf_valuation_analyst],
    name="dcf_supervisor",
    prompt=load_prompt('dcf_supervisor')
).compile(name="dcf_supervisor")
logger.info("DCF supervisor created successfully.")

# Comps Agents
logger.info("Creating Comps agents...")
peer_discovery_agent: CompiledGraph = create_react_agent(
    model=model,
    tools=[company_overview, search_web],
    name="peer_discovery_agent",
    response_format=PeerCompanies,
    prompt=load_prompt('peer_discovery_agent'),
)

comps_valuation_agent: CompiledGraph = create_react_agent(
    model=model,
    tools=[get_income_statements, company_overview, search_web, get_balance_sheet, get_cashflow],
    name="comps_valuation_agent",
    response_format=CompsValuationReport,
    prompt=load_prompt('comps_valuation_agent'),
)
logger.info("Comps agents created successfully.")

# Comps Supervisor
logger.info("Creating Comps supervisor...")
comps_supervisor: CompiledGraph = create_supervisor(
    [peer_discovery_agent, comps_valuation_agent],
    model=model,
    name="comps_supervisor",
    prompt=load_prompt('comps_supervisor')
).compile(name="comps_supervisor")
logger.info("Comps supervisor created successfully.")

# Valuation Supervisor
logger.info("Creating Valuation supervisor...")
valuation_supervisor: CompiledGraph = create_supervisor(
    [comps_supervisor, dcf_supervisor],
    model=model,
    name="valuation_supervisor",
    prompt=load_prompt('valuation_supervisor'),
    response_format=ValuationOutput,
).compile(name="valuation_supervisor")
logger.info("Valuation supervisor created successfully.")
