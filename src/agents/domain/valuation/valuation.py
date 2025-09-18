from typing import List
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.model_schemas.schemas import (
    WACCOutput, UFCF_Forecast, FinalDCFReport, PeerCompanies, CompsValuationReport
)
from src.tools.data_providers.alpha_vantage import get_balance_sheet, company_overview,get_shares_outstanding,get_economic_indicators,get_earnings
from src.tools.data_providers.financial_modeling_prep import get_income_statements, get_cashflow
from src.tools.data_providers.finnhub import get_company_overview
from src.tools.utilities.extra import search_web
from src.config.logging_config import logger
from src.prompts import load_prompt
from src.tools.data_providers.alpha_vantage import get_stock_splits
from src.tools.utilities.extra import search_web,search_web2
from src.tools.analysis.dcf import get_dcf,forecast_unleveredc_cash_flows,free_cash_flow,dcf_analyst,net_debt,calculate_wacc,nwc
from src.tools.data_providers.polygon import get_ticker_overview

logger.info("Creating DCF agents...")
free_cash_flow_forecaster = create_react_agent(
    model=model,
    tools=[get_income_statements, get_cashflow, get_balance_sheet,get_stock_splits, forecast_unleveredc_cash_flows, free_cash_flow, nwc,search_web2],
    name="free_cash_flow_forecaster",
    response_format=UFCF_Forecast,
    prompt=load_prompt('free_cash_flow_forecaster'),
)

wacc_analyst = create_react_agent(
    model=model,
    tools=[get_economic_indicators, search_web2, company_overview, get_balance_sheet,get_income_statements,get_cashflow,get_company_overview,calculate_wacc,get_earnings ],
    name="wacc_analyst",
    response_format=WACCOutput,
    prompt=load_prompt('wacc_analyst'),
)

dcf_valuation_analyst = create_react_agent(
    model=model,
    tools=[get_balance_sheet, get_shares_outstanding, dcf_analyst, get_dcf,get_income_statements,get_cashflow,search_web2,net_debt],
    name="dcf_valuation_analyst",
    response_format=FinalDCFReport,
    prompt=load_prompt('dcf_valuation_analyst'),
)
logger.info("DCF agents created successfully.")

dcf_team = [free_cash_flow_forecaster, wacc_analyst, dcf_valuation_analyst]

# Comps Agents
logger.info("Creating Comps agents...")
peer_discovery_agent = create_react_agent(
    model=model,
    tools=[company_overview, search_web,get_ticker_overview],
    name="peer_discovery_agent",
    response_format=PeerCompanies,
    prompt=load_prompt('peer_discovery_agent'),
)

comps_valuation_agent = create_react_agent(
    model=model,
    tools=[ get_income_statements,
        company_overview,
        search_web2,
        get_shares_outstanding,
        get_balance_sheet,
        get_cashflow,],
    name="comps_valuation_agent",
    response_format=CompsValuationReport,
    prompt=load_prompt('comps_valuation_agent'),
)
logger.info("Comps agents created successfully.")

relative_valuation_team = [peer_discovery_agent, comps_valuation_agent]

