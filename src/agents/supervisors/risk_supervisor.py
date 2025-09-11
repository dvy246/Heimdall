from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.config.logging_config import logger
from langgraph.graph.base import CompiledGraph
from src.model_schemas.schemas import FullRiskReport
from src.agents.domain.risk_agents.risk import financial_risk_agent, news_risk_agent, technical_risk_agent

logger.info("Creating risk supervisor...")
risk_supervisor: CompiledGraph = create_supervisor(
    [financial_risk_agent, news_risk_agent, technical_risk_agent],
    model=model,
    response_format=FullRiskReport,
    prompt=load_supervisor_prompt('risk_supervisor')
).compile(name="risk_supervisor")
logger.info("Risk supervisor created successfully.")
