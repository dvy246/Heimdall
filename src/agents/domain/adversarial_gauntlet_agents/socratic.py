from langgraph.prebuilt import create_react_agent
from src.config.settings import model
from src.model_schemas.schemas import SocraticQuestions
from src.prompts import load_prompt
from src.config.logging_config import logger

logger.info('creating socratic agent')

socratic_agent=create_react_agent(
    model=model,
    prompt=load_prompt('socratic_agent'),
    response_format=SocraticQuestions,
    name='socratic_agent'
)