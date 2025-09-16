from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.config.logging_config import logger
from src.agents.domain.research_agents.research import financial_analyst, news_analyst, technical_analyst

logger.info("Creating research supervisor...")
research_supervisor = create_supervisor(
    [financial_analyst, news_analyst, technical_analyst],
    model=model,
    prompt=load_supervisor_prompt('research_supervisor')
).compile(name="research_supervisor")
logger.info("Research supervisor created successfully.")
