from langgraph.prebuilt import create_react_agent
from src.tools.agents.Agno.compliance import create_compliance_team
from src.config.settings import model
from src.model_schemas.schemas import ComplianceReport
from src.prompts import load_prompt
from src.config.logging_config import logger

logger.info('creating compliance team')

compliance_agent = create_react_agent(
    model=model,
    name='compliance agent',
    tools=[create_compliance_team],
    prompt=load_prompt('compliance_agent'),
    response_format=ComplianceReport
)
