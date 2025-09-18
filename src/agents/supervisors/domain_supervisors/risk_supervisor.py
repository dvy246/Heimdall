from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.config.logging_config import logger
from src.model_schemas.schemas import FullRiskReport
from src.agents.domain.risk_agents.risk import financial_risk_agent, news_risk_agent, technical_risk_agent
from src.tools.analysis.report_writer_tool import generate_synthesized_report

logger.info("Creating risk supervisor...")
risk_supervisor = create_supervisor(
    [financial_risk_agent, news_risk_agent, technical_risk_agent],
    model=model,
    response_format=FullRiskReport,
    prompt=load_supervisor_prompt('risk_supervisor'),
    tools=[generate_synthesized_report],
    output_mode="last_message"
).compile(name="risk_supervisor")
logger.info("Risk supervisor created successfully.")
