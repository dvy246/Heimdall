from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.config.logging_config import logger
from src.agents.domain.valuation.valuation import relative_valuation_team,dcf_team
from src.model_schemas.schemas import (FinalDCFReport,ValuationOutput,
CompsValuationReport)
from src.tools.analysis.report_writer_tool import generate_synthesized_report

# Comps Supervisor
logger.info("Creating Comps supervisor...")
comps_supervisor = create_supervisor(
    relative_valuation_team,
    model=model,
    prompt=load_supervisor_prompt('comps_supervisor'),
    response_format=CompsValuationReport,
    tools=[generate_synthesized_report],
    output_mode="last_message"
).compile(name="comps_supervisor")
logger.info("Comps supervisor created successfully.")

# DCF Supervisor
logger.info("Creating DCF supervisor...")
dcf_supervisor = create_supervisor(
    dcf_team,
    model=model,
    prompt=load_supervisor_prompt('dcf_supervisor'),
    response_format=FinalDCFReport,
    tools=[generate_synthesized_report],
    output_mode="last_message"
).compile(name="dcf_supervisor")
logger.info("DCF supervisor created successfully.")

# Main Valuation Supervisor
valuation_supervisor = create_supervisor(
    [comps_supervisor, dcf_supervisor],
    model=model, 
    prompt=load_supervisor_prompt('valuation_supervisor'),
    response_format=ValuationOutput,
    tools=[generate_synthesized_report],
    output_mode="last_message"
).compile(name="valuation_supervisor")
