from src.prompts import load_supervisor_prompt
from langgraph_supervisor import create_supervisor
from src.config.settings import model
from src.config.logging_config import logger
from src.model_schemas.schemas import ComprehensiveResearchReport
from src.agents.domain.research_agents.research import financial_analyst, news_analyst, technical_analyst
from src.tools.analysis.report_writer_tool import generate_synthesized_report

logger.info("Creating research supervisor...")
research_supervisor = create_supervisor(
    [financial_analyst, news_analyst, technical_analyst],
    model=model,
    prompt=load_supervisor_prompt('research_supervisor'),
    response_format=ComprehensiveResearchReport,
    tools=[generate_synthesized_report],
    output_mode="last_message"
).compile(name="research_supervisor")
logger.info("Research supervisor created successfully.")