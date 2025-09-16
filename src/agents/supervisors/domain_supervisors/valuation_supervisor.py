from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.config.logging_config import logger
from src.agents.domain.valuation.valuation import (
    peer_discovery_agent, 
    comps_valuation_agent,
    free_cash_flow_forecaster, 
    wacc_analyst, 
    dcf_valuation_analyst
)

# Comps Supervisor
logger.info("Creating Comps supervisor...")
comps_supervisor = create_supervisor(
    [peer_discovery_agent, comps_valuation_agent],
    model=model,
    name="comps_supervisor",
    prompt=load_supervisor_prompt('comps_supervisor')
).compile(name="comps_supervisor")
logger.info("Comps supervisor created successfully.")

# DCF Supervisor
logger.info("Creating DCF supervisor...")
dcf_supervisor = create_supervisor(
    model=model,
    agents=[free_cash_flow_forecaster, wacc_analyst, dcf_valuation_analyst],
    name="dcf_supervisor",
    prompt=load_supervisor_prompt('dcf_supervisor')
).compile(name="dcf_supervisor")
logger.info("DCF supervisor created successfully.")

# Main Valuation Supervisor
valuation_supervisor = create_supervisor(
    [comps_supervisor, dcf_supervisor],
    model=model,
    name="valuation_supervisor", 
    prompt=load_supervisor_prompt('valuation_supervisor')
).compile(name="valuation_supervisor")
